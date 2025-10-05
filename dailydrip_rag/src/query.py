import argparse
import chromadb
from chromadb.utils import embedding_functions

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--persist-dir', required=True)
    ap.add_argument('--q', required=True)
    ap.add_argument('--k', type=int, default=5)
    args = ap.parse_args()

    client = chromadb.PersistentClient(path=args.persist_dir)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    coll = client.get_or_create_collection("coffee_chunks", embedding_function=ef)

    res = coll.query(query_texts=[args.q], n_results=args.k)
    for rank, (doc, meta, id_) in enumerate(zip(res['documents'][0], res['metadatas'][0], res['ids'][0]), 1):
        print(f"[{rank}] id={id_}\n{doc}\nmeta_keys={list(meta.keys())[:8]}\n---")

if __name__ == "__main__":
    main()
