import json, argparse
from tqdm import tqdm
import chromadb
from chromadb.utils import embedding_functions

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--chunks', required=True)
    ap.add_argument('--persist-dir', required=True)
    args = ap.parse_args()

    # Use PersistentClient in 0.5.x
    client = chromadb.PersistentClient(path=args.persist_dir)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    coll = client.get_or_create_collection("coffee_chunks", embedding_function=ef)

    ids, docs, metas = [], [], []
    with open(args.chunks) as f:
        for line in tqdm(f, desc="indexing"):
            obj = json.loads(line)
            ids.append(str(obj["id"]))
            docs.append(obj["text"])
            metas.append(obj["meta"])

    B = 256
    for i in range(0, len(ids), B):
        coll.upsert(ids=ids[i:i+B], documents=docs[i:i+B], metadatas=metas[i:i+B])

    # No client.persist() needed in 0.5.x
    print(f"Indexed {len(ids)} chunks → {args.persist_dir}")

if __name__ == "__main__":
    main()
