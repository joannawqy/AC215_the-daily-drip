# DailyDrip RAG Pipeline

This directory houses the Retrieval-Augmented Generation (RAG) data pipeline that powers DailyDrip’s brewing agent.

## Pipeline Design
1. **Ingest (`src/ingest`)** – Normalizes raw bean and brew logs into JSONL records stored in `data/processed/records.jsonl`.
2. **Chunk (`src/chunk`)** – Splits records into overlapping text chunks (stored in `data/processed/chunks.jsonl`) suitable for embedding.
3. **Index (`src/index`)** – Embeds chunks and persists a Chroma vector store under `indexes/chroma/`.
4. **Service (`src/service`)** – FastAPI service that exposes `/rag` for similarity search over the vector store.

Each component runs inside the shared Docker image defined by `Dockerfile`. The `Makefile` at the repository root orchestrates these stages via Docker Compose:

```bash
make pipeline   # ingest → chunk → index (one-shot refresh)
make rag        # build & run the RAG API (requires index)
make run        # full stack: ingest → chunk → index → rag → agent
```

Sample processed outputs shipped with the repo are lightweight demonstrations only; replace them with real data in private storage when running at scale.

## Usage & Logs
- **Trigger pipeline:** `make pipeline`
- **Start RAG service:** `make rag`
- **Inspect live logs:** `docker compose logs -f rag`

The log stream shows ingest progress, chunking totals, index statistics, and incoming `/rag` requests while the service is running. Use `Ctrl+C` to exit the log tail without stopping the container.
