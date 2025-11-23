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


def _compute_evaluation_score(evaluation: Optional[Dict[str, Any]]) -> float:
    """
    Compute a normalized evaluation score from 0.0 to 1.0.
    
    Uses:
    - evaluation.liking (scale 0-10) → weight 60%
    - evaluation.jag metrics (scale 1-5) → weight 40%
      - flavour_intensity, acidity, mouthfeel, sweetness, purchase_intent
    
    Returns 0.0 if no evaluation data exists.
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
    
    # Normalize by actual weights used (handle missing data gracefully)
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
    return bean_text_from_obj(query_source)


def _run_query(
    collection,
    query_text: str,
    k: int,
    use_evaluation_reranking: bool = True,
    similarity_weight: float = 0.7,
    retrieval_multiplier: int = 3,
) -> List[RagReference]:
    """
    Query the collection and optionally rerank by evaluation scores.
    
    Args:
        collection: ChromaDB collection
        query_text: Query string
        k: Number of results to return
        use_evaluation_reranking: Whether to rerank by evaluation scores
        similarity_weight: Weight for similarity (0-1), evaluation_weight = 1 - similarity_weight
        retrieval_multiplier: Fetch k × multiplier results before reranking
    """
    # Fetch more results if reranking is enabled
    n_fetch = k * retrieval_multiplier if use_evaluation_reranking else k
    
    response = collection.query(
        query_texts=[query_text],
        n_results=n_fetch,
        include=["metadatas", "documents", "distances"],
    )

    docs = response.get("documents", [[]])[0]
    metas = response.get("metadatas", [[]])[0]
    ids = response.get("ids", [[]])[0]
    distances = response.get("distances", [[]])[0]

    # Build candidate results with evaluation scores
    candidates = []
    for doc, meta, record_id, dist in zip(docs, metas, ids, distances):
        brewing = extract_brewing(meta)
        evaluation = extract_evaluation(meta)
        
        # Compute combined score if reranking is enabled
        combined_score = None
        if use_evaluation_reranking:
            # Similarity score: convert distance to similarity (lower distance = higher similarity)
            # Assuming distance is L2 distance, normalize using 1/(1+dist)
            similarity_score = 1.0 / (1.0 + float(dist))
            
            # Evaluation score (0-1)
            eval_score = _compute_evaluation_score(evaluation)
            
            # Combined score: weighted average
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
    
    # Rerank by combined score if enabled, otherwise keep original order
    if use_evaluation_reranking:
        candidates.sort(key=lambda x: x["combined_score"], reverse=True)
    
    # Take top-k and assign final ranks
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
    app = FastAPI(title="DailyDrip RAG Service", version="0.1.0")

    @app.get("/healthz")
    def health() -> Dict[str, str]:
        return {"status": "ok"}

    @app.post("/rag", response_model=RagResponse)
    def rag(payload: RagQuery) -> RagResponse:
        persist_dir = os.getenv("RAG_PERSIST_DIR", str(DEFAULT_PERSIST_DIR))
        collection = _get_collection(persist_dir)
        query_text = _build_query_text(payload)
        results = _run_query(
            collection,
            query_text,
            payload.k,
            use_evaluation_reranking=payload.use_evaluation_reranking,
            similarity_weight=payload.similarity_weight,
            retrieval_multiplier=payload.retrieval_multiplier,
        )
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
