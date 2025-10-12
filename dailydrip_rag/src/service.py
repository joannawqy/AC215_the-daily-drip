import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.utils import embedding_functions
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .query import bean_text_from_obj, extract_brewing, extract_evaluation

DEFAULT_COLLECTION = "coffee_chunks"
DEFAULT_MODEL = "all-MiniLM-L6-v2"
DEFAULT_PERSIST_DIR = Path(__file__).resolve().parent.parent / "indexes" / "chroma"


class RagQuery(BaseModel):
    bean: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured description of the coffee bean that will be converted into query text.",
    )
    record: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Full record containing bean/brewing/evaluation data; the bean section is preferred.",
    )
    query: Optional[str] = Field(
        default=None,
        description="Free-text query to use directly. Ignored when bean or record is supplied.",
    )
    k: int = Field(default=3, ge=1, le=10, description="Number of similar references to return.")


class RagReference(BaseModel):
    rank: int
    id: str
    distance: float
    bean_text: str
    brewing: Dict[str, Any]
    evaluation: Optional[Dict[str, Any]] = None


class RagResponse(BaseModel):
    query: str
    results: List[RagReference]


@lru_cache(maxsize=1)
def _get_collection(persist_dir: str, collection: str = DEFAULT_COLLECTION):
    if not persist_dir:
        persist_dir = str(DEFAULT_PERSIST_DIR)
    path = Path(persist_dir)
    if not path.exists():
        raise FileNotFoundError(f"RAG index directory not found: {path}")

    client = chromadb.PersistentClient(path=str(path))
    embedding = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=DEFAULT_MODEL
    )
    return client.get_or_create_collection(collection, embedding_function=embedding)


def _build_query_text(payload: RagQuery) -> str:
    if payload.query:
        return payload.query

    record = payload.record or {}
    bean = payload.bean or record.get("bean")
    if not bean:
        raise HTTPException(
            status_code=400, detail="Provide a bean, full record, or free-text query to perform retrieval."
        )

    query_source = record if "bean" in record else {"bean": bean}
    return bean_text_from_obj(query_source)


def _run_query(collection, query_text: str, k: int) -> List[RagReference]:
    response = collection.query(
        query_texts=[query_text],
        n_results=k,
        include=["metadatas", "documents", "distances"],
    )

    docs = response.get("documents", [[]])[0]
    metas = response.get("metadatas", [[]])[0]
    ids = response.get("ids", [[]])[0]
    distances = response.get("distances", [[]])[0]

    results: List[RagReference] = []
    for rank, (doc, meta, record_id, dist) in enumerate(
        zip(docs, metas, ids, distances), start=1
    ):
        brewing = extract_brewing(meta)
        evaluation = extract_evaluation(meta)
        results.append(
            RagReference(
                rank=rank,
                id=str(record_id),
                distance=float(dist),
                bean_text=doc,
                brewing=brewing,
                evaluation=evaluation,
            )
        )
    return results


def create_app() -> FastAPI:
    app = FastAPI(title="DailyDrip RAG Service", version="0.1.0")

    @app.get("/healthz")
    def health() -> Dict[str, str]:
        return {"status": "ok"}

    @app.post("/rag", response_model=RagResponse)
    def rag(payload: RagQuery) -> RagResponse:
        persist_dir = os.getenv("RAG_PERSIST_DIR", str(DEFAULT_PERSIST_DIR))
        collection = _get_collection(persist_dir)
        query_text = _build_query_text(payload)
        results = _run_query(collection, query_text, payload.k)
        return RagResponse(query=query_text, results=results)

    return app


app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run(
        "src.service:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )


if __name__ == "__main__":
    main()
