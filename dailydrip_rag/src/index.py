import json, argparse
from tqdm import tqdm
import chromadb
from chromadb.utils import embedding_functions

def sanitize_meta(meta: dict) -> dict:
    out = {}
    def put(k, v):
        if isinstance(v, (str, int, float, bool)) or v is None:
            out[k] = v
        elif isinstance(v, list):
            if v and all(isinstance(x, dict) for x in v):
                # list of dicts -> flatten with indices
                for idx, d in enumerate(v):
                    for kk, vv in d.items():
                        put(f"{k}.{idx}.{kk}", vv)     # brewing.pours.0.start = 0
            else:
                out[k] = ", ".join(map(str, v))
        elif isinstance(v, dict):
            for kk, vv in v.items():
                put(f"{k}.{kk}", vv)
        else:
            out[k] = str(v)
    for k, v in meta.items():
        put(k, v)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--chunks', required=True)
    ap.add_argument('--persist-dir', required=True)
    args = ap.parse_args()

    client = chromadb.PersistentClient(path=args.persist_dir)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    coll = client.get_or_create_collection("coffee_chunks", embedding_function=ef)

    ids, docs, metas = [], [], []
    with open(args.chunks) as f:
        for line in tqdm(f, desc="indexing"):
            obj = json.loads(line)
            ids.append(str(obj["id"]))
            docs.append(obj["text"])                    # bean-only text
            metas.append(sanitize_meta(obj["meta"]))    # brewing kept here

    B = 256
    for i in range(0, len(ids), B):
        coll.upsert(ids=ids[i:i+B], documents=docs[i:i+B], metadatas=metas[i:i+B])

    print(f"Indexed {len(ids)} chunks → {args.persist_dir}")

if __name__ == "__main__":
    main()
