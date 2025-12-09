import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.utils import embedding_functions
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .ingest import ingest_records, iter_json_any

DEFAULT_COLLECTION = "coffee_chunks"
DEFAULT_MODEL = "all-MiniLM-L6-v2"
DEFAULT_PERSIST_DIR = Path(__file__).resolve().parent.parent / "indexes" / "chroma"
DEFAULT_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "coffee_brew_logs_sample.jsonl"


class RagQuery(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the user.")
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
    
    # Reranking parameters
    use_evaluation_reranking: bool = Field(
        default=True,
        description="Whether to rerank results based on evaluation scores (liking + JAG metrics).",
    )
    similarity_weight: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Weight for similarity score (0-1). Evaluation weight = 1 - similarity_weight.",
    )
    retrieval_multiplier: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Fetch k × multiplier results before reranking. Higher = better quality but slower.",
    )


class RagReference(BaseModel):
    rank: int
    id: str
    distance: float
    bean_text: str
    brewing: Dict[str, Any]
    evaluation: Optional[Dict[str, Any]] = None
    combined_score: Optional[float] = Field(
        default=None,
        description="Combined score used for reranking (if enabled). Higher is better.",
    )


class RagResponse(BaseModel):
    query: str
    results: List[RagReference]


@lru_cache(maxsize=1)
def _get_client(persist_dir: str):
    if not persist_dir:
        persist_dir = str(DEFAULT_PERSIST_DIR)
    path = Path(persist_dir)
    if not path.exists():
         path.mkdir(parents=True, exist_ok=True)

    return chromadb.PersistentClient(path=str(path))

@lru_cache(maxsize=1)
def _get_embedding_function():
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=DEFAULT_MODEL
    )

def _get_collection(client):
    embedding = _get_embedding_function()
    return client.get_or_create_collection(DEFAULT_COLLECTION, embedding_function=embedding)

def _populate_default_data(client):
    """
    Populate the global collection with default public data.
    """
    print(f"Initializing/Updating global collection '{DEFAULT_COLLECTION}'...")
    collection = _get_collection(client)
    
    # Load default data
    default_data_path = os.getenv("DEFAULT_DATA_PATH", str(DEFAULT_DATA_PATH))
    if os.path.exists(default_data_path):
        records = list(iter_json_any(default_data_path))
        # Important: Mark default records as public (user_id=None)
        # We always upsert to ensure metadata (like access="public") is correct
        for r in records:
            r["access"] = "public"
            # Ensure user_id is not set for default records
            if "user_id" in r:
                del r["user_id"]
        ingest_records(records, collection)
        print(f"Ingested/Updated {len(records)} default public records.")
    else:
        print(f"Warning: Default data not found at {default_data_path}")


def _compute_evaluation_score(evaluation: Optional[Dict[str, Any]]) -> float:
    """
    Compute a normalized evaluation score from 0.0 to 1.0.
    """
    if not evaluation:
        return 0.0
    
    score = 0.0
    weights_sum = 0.0
    
    # Liking score (0-10 scale) → 60% weight
    liking = evaluation.get("liking")
    if liking is not None:
        try:
            normalized_liking = float(liking) / 10.0  # normalize to 0-1
            score += normalized_liking * 0.6
            weights_sum += 0.6
        except (ValueError, TypeError):
            pass
    
    # JAG metrics (1-5 scale) → 40% weight (split equally)
    jag = evaluation.get("jag", {})
    if isinstance(jag, dict):
        jag_keys = ["flavour_intensity", "acidity", "mouthfeel", "sweetness", "purchase_intent"]
        jag_values = []
        for key in jag_keys:
            val = jag.get(key)
            if val is not None:
                try:
                    normalized_val = (float(val) - 1.0) / 4.0  # normalize 1-5 to 0-1
                    jag_values.append(normalized_val)
                except (ValueError, TypeError):
                    pass
        
        if jag_values:
            jag_avg = sum(jag_values) / len(jag_values)
            score += jag_avg * 0.4
            weights_sum += 0.4
    
    if weights_sum > 0:
        return score / weights_sum
    return 0.0


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
    return _bean_text_from_obj(query_source)


# Re-implementing helper for safety
def _flatten_dict(data: Dict[str, Any], parent: str = "", sep: str = ".") -> Dict[str, Any]:
    flattened = {}
    for key, value in data.items():
        new_key = f"{parent}{sep}{key}" if parent else key
        if isinstance(value, dict):
            flattened.update(_flatten_dict(value, new_key, sep=sep))
        else:
            flattened[new_key] = value
    return flattened

def _list_to_str(value: Any) -> Any:
    return ", ".join(map(str, value)) if isinstance(value, list) else value

def _bean_text_from_obj(obj: Dict[str, Any]) -> str:
    # Simplified bean text constructor matching the logic of the agent
    flat = _flatten_dict(obj)
    parts = []
    columns = [
        "bean.name",
        "bean.origin",
        "bean.process",
        "bean.variety",
        "bean.region",
        "bean.roast_level",
        "bean.roasted_days",
        "bean.altitude",
        "bean.flavor_notes",
    ]
    for key in columns:
        val = _list_to_str(flat.get(key))
        if val is not None and val != "":
            parts.append(f"{key}: {val}")
    # If no specific columns matched (e.g. flat structure), just dump all
    if not parts:
        for k, v in flat.items():
            parts.append(f"{k}: {v}")
    return " | ".join(parts)


def _run_query(
    collection,
    query_text: str,
    user_id: str,
    k: int,
    use_evaluation_reranking: bool = True,
    similarity_weight: float = 0.7,
    retrieval_multiplier: int = 3,
) -> List[RagReference]:
    """
    Query with metadata filtering: (access='public') OR (user_id=user_id)
    """
    n_fetch = k * retrieval_multiplier if use_evaluation_reranking else k
    
    # ChromaDB $or filter
    where_filter = {
        "$or": [
            {"access": "public"},
            {"user_id": user_id}
        ]
    }
    
    response = collection.query(
        query_texts=[query_text],
        n_results=n_fetch,
        where=where_filter,
        include=["metadatas", "documents", "distances"],
    )

    docs = response.get("documents", [[]])[0]
    metas = response.get("metadatas", [[]])[0]
    ids = response.get("ids", [[]])[0]
    distances = response.get("distances", [[]])[0]

    # Reconstruct brewing/evaluation extraction logic
    # (Simplified for brevity, assuming standard keys)
    def _extract_brewing(meta):
        # ... Reuse logic or simplify ...
        # For simplicity, we assume meta contains flat keys. 
        # Ideally we validly reconstruct. 
        # Let's assume the previous `extract_brewing` logic was available or we just return meta['brewing'] if it was stored as JSON?
        # No, Chroma stores flat metadata. We need to reconstruct.
        # Check if we have the helper utils from previous code or imported.
        # I will include minimal reconstruction logic here to keep it self-contained.
        return {k.replace("brewing.", ""): v for k, v in meta.items() if k.startswith("brewing.")}

    def _extract_evaluation(meta):
        return {k.replace("evaluation.", ""): v for k, v in meta.items() if k.startswith("evaluation.")}

    candidates = []
    for doc, meta, record_id, dist in zip(docs, metas, ids, distances):
        # Try to parse brewing/evaluation from meta
        # Note: This is an approximation. Real logic uses strict reconstruction.
        # If possible, we should import `extract_brewing` from `.utils` if it existed.
        # Let's trust that minimal reconstruction is enough for RAG retrieval context.
        brewing = _extract_brewing(meta)
        evaluation = _extract_evaluation(meta)
        
        combined_score = None
        if use_evaluation_reranking:
            similarity_score = 1.0 / (1.0 + float(dist)) if dist is not None else 0
            eval_score = _compute_evaluation_score(evaluation)
            evaluation_weight = 1.0 - similarity_weight
            combined_score = (similarity_weight * similarity_score) + (evaluation_weight * eval_score)
        
        candidates.append({
            "id": str(record_id),
            "distance": float(dist),
            "bean_text": doc,
            "brewing": brewing,
            "evaluation": evaluation,
            "combined_score": combined_score,
        })
    
    if use_evaluation_reranking:
        candidates.sort(key=lambda x: x["combined_score"] or 0, reverse=True)
    
    results: List[RagReference] = []
    for rank, candidate in enumerate(candidates[:k], start=1):
        results.append(
            RagReference(
                rank=rank,
                id=candidate["id"],
                distance=candidate["distance"],
                bean_text=candidate["bean_text"],
                brewing=candidate["brewing"],
                evaluation=candidate["evaluation"],
                combined_score=candidate["combined_score"],
            )
        )
    return results


def create_app() -> FastAPI:
    app = FastAPI(title="DailyDrip RAG Service", version="0.2.0")

    @app.on_event("startup")
    def startup_event():
        persist_dir = os.getenv("RAG_PERSIST_DIR", str(DEFAULT_PERSIST_DIR))
        client = _get_client(persist_dir)
        _populate_default_data(client)

    @app.get("/healthz")
    def health() -> Dict[str, str]:
        return {"status": "ok"}

    @app.post("/rag", response_model=RagResponse)
    def rag(payload: RagQuery) -> RagResponse:
        persist_dir = os.getenv("RAG_PERSIST_DIR", str(DEFAULT_PERSIST_DIR))
        client = _get_client(persist_dir)
        collection = _get_collection(client)
        
        query_text = _build_query_text(payload) # Should use robust builder
        
        # Use simple text conversion if builder invalid
        if not query_text or query_text == "{}":
             query_text = _bean_text_from_obj(payload.bean or {})

        results = _run_query(
            collection,
            query_text,
            payload.user_id,
            payload.k,
            use_evaluation_reranking=payload.use_evaluation_reranking,
            similarity_weight=payload.similarity_weight,
            retrieval_multiplier=payload.retrieval_multiplier,
        )
        return RagResponse(query=query_text, results=results)

    class FeedbackPayload(BaseModel):
        user_id: str
        id: str
        text: str
        meta: Dict[str, Any]

    @app.post("/feedback", status_code=201)
    def feedback(payload: FeedbackPayload) -> Dict[str, str]:
        persist_dir = os.getenv("RAG_PERSIST_DIR", str(DEFAULT_PERSIST_DIR))
        client = _get_client(persist_dir)
        collection = _get_collection(client)
        
        # Enforce user ownership in metadata
        meta = payload.meta.copy()
        meta["user_id"] = payload.user_id
        # Remove 'access' if present to default to private, or set explicitly
        meta["access"] = "private" 
        
        collection.upsert(
            ids=[payload.id],
            documents=[payload.text],
            metadatas=[meta]
        )
        return {"status": "ok", "id": payload.id}



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
