# Daily Drip RAG Pipeline

## Prerequisites
- Docker and Docker Compose v2
- `OPENAI_API_KEY` exported in the shell before running the agent or service

## One-Command Pipeline
Build and run the full workflow (raw data → preprocessing → vector index → RAG API → agent):
```bash
make run
```
This is equivalent to `docker compose up --build agent`. The first run builds the images, executes ingest → chunk → index sequentially, and then keeps both the RAG and agent services running. Outputs are written to `dailydrip_rag/data/processed` and `dailydrip_rag/indexes/chroma`.

To refresh the index without starting the long-running services:
```bash
make pipeline    # run ingest → chunk → index only
make rag         # build and start just the RAG API (index must exist)
make down        # stop all containers
```

## Services
- `ingest`: parse the source CSV/JSON/JSONL files into normalized records.
- `chunk`: slice records into manageable chunks ready for embedding.
- `index`: build and persist the Chroma vector index.
- `rag`: FastAPI service exposing `POST /rag` for retrieval.
- `agent`: FastAPI service that queries the RAG API and OpenAI to return a brewing plan.

All services share the volumes `dailydrip_rag/data` and `dailydrip_rag/indexes`. By default, the RAG API listens on `http://localhost:8000` and the agent API listens on `http://localhost:9000`.

## RAG Service API
```
POST /rag
{
  "bean": {...},        # or provide a full record / free-text query
  "record": {...},
  "query": "free-form text",
  "k": 3
}
```

Sample response:
```json
{
  "query": "bean.name: ...",
  "results": [
    {
      "rank": 1,
      "id": "record-123",
      "distance": 0.12,
      "bean_text": "bean.name: ...",
      "brewing": { "...": "..." },
      "evaluation": { "...": "..." }
    }
  ]
}
```

Health check: `GET /healthz`.

## Agent HTTP Service
The container starts the FastAPI application automatically:
```bash
uvicorn agent:app --host 0.0.0.0 --port 9000
```

Example request:
```bash
curl -X POST http://localhost:9000/brew \
  -H "Content-Type: application/json" \
  -d @bean_request.json
```

Example `bean_request.json`:
```json
{
  "bean": { "...": "..." },
  "brewer": "V60",
  "note": "Prefer sweeter cups and a three-stage pour",
  "rag_k": 3
}
```

The response contains a `references` array (retrieved recipes) and a `recipe` object (final brewing plan). To run the CLI outside Docker:
```bash
python agent.py --bean bean.json --brewer V60 \
  --rag-service-url http://localhost:8000
```

Adding `--serve` switches the CLI into HTTP service mode.
