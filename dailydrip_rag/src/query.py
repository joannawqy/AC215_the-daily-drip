import argparse, json
import chromadb
from chromadb.utils import embedding_functions

# Use the same bean fields used at ingest to build the query text
BEAN_COLUMNS = [
    "bean.name", "bean.process", "bean.variety", "bean.region",
    "bean.roast_level", "bean.roasted_days", "bean.altitude", "bean.flavor_notes",
]

def flatten(d, parent_key="", sep="."):
    out = {}
    for k, v in d.items():
        key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            out.update(flatten(v, key, sep=sep))
        else:
            out[key] = v
    return out

def list_to_str(v):
    return ", ".join(map(str, v)) if isinstance(v, list) else v

def bean_text_from_obj(obj: dict) -> str:
    flat = flatten(obj) if "bean" in obj or "brewing" in obj or "evaluation" in obj else obj
    parts = []
    for k in BEAN_COLUMNS:
        v = list_to_str(flat.get(k))
        if v is None:
            continue
        parts.append(f"{k}: {v}")
    return " | ".join(parts)

def reconstruct_pours(meta: dict):
    """Rebuild pours from flattened keys brewing.pours.N.{start,end,water_added}"""
    pours = []
    idxs = set()
    for k in meta.keys():
        if k.startswith("brewing.pours."):
            try:
                idxs.add(int(k.split(".")[2]))
            except Exception:
                pass
    for i in sorted(idxs):
        pours.append({
            "start": meta.get(f"brewing.pours.{i}.start"),
            "end": meta.get(f"brewing.pours.{i}.end"),
            "water_added": meta.get(f"brewing.pours.{i}.water_added"),
        })
    return pours

def extract_brewing(meta: dict):
    return {
        "brewer": meta.get("brewing.brewer"),
        "temperature": meta.get("brewing.temperature"),
        "grinding_size": meta.get("brewing.grinding_size"),
        "dose": meta.get("brewing.dose"),
        "target_water": meta.get("brewing.target_water"),
        "pours": reconstruct_pours(meta) or meta.get("brewing.pours_str"),
    }

def extract_evaluation(meta: dict):
    jag = {}
    for k in ("flavour_intensity", "acidity", "mouthfeel", "sweetness", "purchase_intent"):
        val = meta.get(f"evaluation.jag.{k}")
        if val is not None:
            jag[k] = val
    out = {}
    if "evaluation.liking" in meta:
        out["liking"] = meta["evaluation.liking"]
    if jag:
        out["jag"] = jag
    return out or None

def compute_evaluation_score(evaluation):
    """Compute normalized evaluation score (0-1) from liking and JAG metrics."""
    if not evaluation:
        return 0.0
    score, weights_sum = 0.0, 0.0
    
    liking = evaluation.get("liking")
    if liking is not None:
        try:
            score += (float(liking) / 10.0) * 0.6
            weights_sum += 0.6
        except (ValueError, TypeError):
            pass
    
    jag = evaluation.get("jag", {})
    if isinstance(jag, dict):
        jag_keys = ["flavour_intensity", "acidity", "mouthfeel", "sweetness", "purchase_intent"]
        jag_values = []
        for key in jag_keys:
            val = jag.get(key)
            if val is not None:
                try:
                    jag_values.append((float(val) - 1.0) / 4.0)
                except (ValueError, TypeError):
                    pass
        if jag_values:
            score += (sum(jag_values) / len(jag_values)) * 0.4
            weights_sum += 0.4
    
    return score / weights_sum if weights_sum > 0 else 0.0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--persist-dir', required=True)
    ap.add_argument('--q', help="free-text query")
    ap.add_argument('--bean-json', help="path to JSON with a 'bean' object (or full record)")
    ap.add_argument('--bean-inline', help="inline JSON string with a 'bean' object (or full record)")
    ap.add_argument('--k', type=int, default=5)
    ap.add_argument('--json', action='store_true', help="output JSON")
    
    # Reranking parameters
    ap.add_argument('--use-reranking', action='store_true', default=True, help="enable evaluation-based reranking")
    ap.add_argument('--no-reranking', dest='use_reranking', action='store_false', help="disable reranking")
    ap.add_argument('--similarity-weight', type=float, default=0.7, help="weight for similarity (0-1), default 0.7")
    ap.add_argument('--retrieval-multiplier', type=int, default=3, help="fetch k × multiplier results before reranking")
    
    args = ap.parse_args()

    # Build query text from structured bean or free text
    if args.bean_json or args.bean_inline:
        if args.bean_json:
            with open(args.bean_json, "r", encoding="utf-8") as f:
                bean_obj = json.load(f)
        else:
            bean_obj = json.loads(args.bean_inline)
        q_text = bean_text_from_obj(bean_obj)
    elif args.q:
        q_text = args.q
    else:
        raise SystemExit("Provide --bean-json or --bean-inline or --q")

    client = chromadb.PersistentClient(path=args.persist_dir)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    coll = client.get_or_create_collection("coffee_chunks", embedding_function=ef)

    # Fetch more results if reranking is enabled
    n_fetch = args.k * args.retrieval_multiplier if args.use_reranking else args.k
    
    res = coll.query(
        query_texts=[q_text],
        n_results=n_fetch,
        include=["metadatas", "documents", "distances"] 
    )

    docs = res["documents"][0]
    metas = res["metadatas"][0]
    ids = res["ids"][0]
    dists = res["distances"][0]

    # Build candidates with combined scores
    candidates = []
    for doc, meta, id_, dist in zip(docs, metas, ids, dists):
        brewing = extract_brewing(meta)
        evaluation = extract_evaluation(meta)
        
        # Compute combined score if reranking
        combined_score = None
        if args.use_reranking:
            similarity_score = 1.0 / (1.0 + float(dist))
            eval_score = compute_evaluation_score(evaluation)
            evaluation_weight = 1.0 - args.similarity_weight
            combined_score = (args.similarity_weight * similarity_score) + (evaluation_weight * eval_score)
        
        candidates.append({
            "id": id_,
            "distance": float(dist),
            "bean_text": doc,
            "brewing": brewing,
            "evaluation": evaluation,
            "combined_score": combined_score,
        })
    
    # Rerank if enabled
    if args.use_reranking:
        candidates.sort(key=lambda x: x["combined_score"], reverse=True)
    
    # Take top-k with final ranks
    results = []
    for rank, candidate in enumerate(candidates[:args.k], 1):
        result = {
            "rank": rank,
            "id": candidate["id"],
            "score": candidate["distance"],
            "bean_text": candidate["bean_text"],
            "brewing": candidate["brewing"],
            "evaluation": candidate["evaluation"],
            "combined_score": candidate["combined_score"],
        }
        results.append(result)

    if args.json:
        print(json.dumps({"query": q_text, "results": results}, ensure_ascii=False, indent=2))
    else:
        for r in results:
            score_info = f"distance={r['score']:.4f}"
            if r.get('combined_score') is not None:
                score_info += f"  combined_score={r['combined_score']:.4f}"
            print(f"[{r['rank']}] id={r['id']}  {score_info}")
            print("bean_text:", r["bean_text"])
            print("brewing:", json.dumps(r["brewing"], ensure_ascii=False))
            print("evaluation:", json.dumps(r["evaluation"], ensure_ascii=False))
            print("---")

if __name__ == "__main__":
    main()
