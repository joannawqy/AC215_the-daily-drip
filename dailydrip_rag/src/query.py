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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--persist-dir', required=True)
    ap.add_argument('--q', help="free-text query")
    ap.add_argument('--bean-json', help="path to JSON with a 'bean' object (or full record)")
    ap.add_argument('--bean-inline', help="inline JSON string with a 'bean' object (or full record)")
    ap.add_argument('--k', type=int, default=5)
    ap.add_argument('--json', action='store_true', help="output JSON")
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

    res = coll.query(
    query_texts=[q_text],
    n_results=args.k,
    include=["metadatas", "documents", "distances"] 
    )

    docs = res["documents"][0]
    metas = res["metadatas"][0]
    ids = res["ids"][0]
    dists = res["distances"][0]

    results = []
    for rank, (doc, meta, id_, dist) in enumerate(zip(docs, metas, ids, dists), 1):
        result = {
            "rank": rank,
            "id": id_,
            "score": float(dist),
            "bean_text": doc,                  # the bean-based text used for retrieval
            "brewing": extract_brewing(meta),  # structured brewing block
            "evaluation": extract_evaluation(meta),  # structured evaluation block
        }
        results.append(result)

    if args.json:
        print(json.dumps({"query": q_text, "results": results}, ensure_ascii=False, indent=2))
    else:
        for r in results:
            print(f"[{r['rank']}] id={r['id']}  score={r['score']:.4f}")
            print("bean_text:", r["bean_text"])
            print("brewing:", json.dumps(r["brewing"], ensure_ascii=False))
            print("evaluation:", json.dumps(r["evaluation"], ensure_ascii=False))
            print("---")

if __name__ == "__main__":
    main()
