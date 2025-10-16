# AC215 – Milestone 2 – DailyDrip

> Never commit large data files, trained models, or personal API keys/secrets to GitHub.

## Team
- **Team Name:** DailyDrip Collective  
- **Members:** *Update with your Harvard IDs / names here*

## Background & Motivation
Coffee brewing is both an art and a science. Enthusiasts often struggle to dial in grind size, water ratio, pour schedule, and temperature to match their taste preferences. Keeping track of experiments can be overwhelming, especially when juggling multiple beans and brewers.

DailyDrip combines consumer preference data, brewing logs, and generative AI to build a practical assistant that makes everyday coffee brewing easier, more personalized, and more enjoyable. The project targets three coordinated capabilities:
1. **Brewing recipe agent** – recommends brewing parameters tailored to taste goals.
2. **Visualization agent** – renders recipes as timelines that clarify pour cadence and amounts.
3. **RAG-style knowledge base** – stores beans and past brews to ground future recommendations.

## Project Scope (Milestone 2)
- Implement a FastAPI brewing agent that generates complete JSON recipes from bean metadata.
- Provide a visualization agent that converts recipes into HTML/Mermaid/ASCII timelines.
- Maintain a Retrieval-Augmented Generation (RAG) pipeline (ingest → chunk → index → serve) to surface reference brews during recipe generation.
- Package the system in Docker containers and deliver reproducible commands for local testing.

## Repository Organization
The milestone repository is organized around three main areas: data/RAG assets, agent code, and tooling.

```
├── README.md                      # Milestone report & usage guide
├── Makefile                       # Convenience targets for Docker workflows
├── docker-compose.yml             # Orchestrates RAG + agent containers
├── Dockerfile.agent               # Runtime image for the brewing/visualization API
├── agent_core/                    # Core Python package
│   ├── __init__.py
│   ├── agent.py                   # FastAPI brewing agent + CLI entrypoint
│   ├── agent_requirements.txt     # Python dependencies for agent container
│   ├── integrated_agent.py        # A test integration script of two agents
│   └── visualization_agent_v2.py  # Visualization agent
├── dailydrip_rag/                 # RAG Data pipeline (ingest, chunk, index, service)
│   ├── data/processed/
│   ├── indexes/chroma/ 
│   ├── Dockerfile                 # RAG service image
│   └── src/                       # Ingest/chunk/index/service code
├── reports/
│   └── MS2 Report.pdf      # Report of MS2 with some screenshots proving functionality                  
├── tools/
│   ├── bean_request.json          # Sample brew request payload
│   ├── visualize_request.json     # Sample visualization payload
│   └── save_visualization.py      # Helper to fetch HTML visualization

```

> **Note:** `dailydrip_rag/data` and `dailydrip_rag/indexes` contain *small* illustrative artifacts only. Do **not** commit large datasets or full production indexes.

## Data Sources
- **Bean Profiles:** curated JSON snippets describing origin, process, roast, altitude, and flavor notes (synthetic samples for Milestone 2).
- **Brew Logs:** summarized pour-over recipes used to seed the RAG database (stored via JSONL in `dailydrip_rag/data/processed` for demo purposes).
- **External References:** literature and blog resources on pour-over techniques (catalogued in `references/`, not committed). Large datasets remain on private storage; only toy samples are included locally.

## Data & Model Pipeline
1. **Ingest (`dailydrip_rag/src/ingest`)** – normalizes raw bean/brew logs into canonical JSONL records.
2. **Chunk (`dailydrip_rag/src/chunk`)** – slices records into text chunks suited for embedding.
3. **Index (`dailydrip_rag/src/index`)** – builds a Chroma vector index persisted under `dailydrip_rag/indexes/chroma`.
4. **RAG Service (`dailydrip_rag/src/service`)** – exposes REST endpoints to retrieve nearest-neighbor brews for a query bean.

All three steps run via Docker using the Makefile targets described below.

## Agents & Models
- **Brew Agent (`agent_core/agent.py`)**  
  - FastAPI application with `/brew` and `/visualize` endpoints plus a CLI (`python -m agent_core.agent`).  
  - Calls OpenAI’s API (mocked locally) and consults the RAG service when available.  
  - Outputs normalized JSON recipes with validation.
- **Visualization Agent (`agent_core/visualization_agent_v2.py`)**  
  - Generates HTML, Mermaid, and ASCII visual timelines from a recipe dict.  
  - Packaged as a library callable from the brew agent or standalone scripts.
- **Integrated Agent (`agent_core/integrated_agent.py`)**  
  - End-to-end workflow that loads bean data, queries RAG, produces a recipe, and renders visualizations.

## Running the System with Docker

### Prerequisites
- Docker & Docker Compose v2
- `OPENAI_API_KEY` set in environment (or use a mock key when running offline)

### Full Pipeline (build + ingest + agent)
```bash
make run               # builds images, runs ingest → chunk → index, then starts RAG + agent
```

### Targeted Operations
```bash
make pipeline          # ingest → chunk → index only (refresh embeddings)
make rag               # build and run only the RAG API service
make start             # start RAG + agent without rebuilding
make down              # stop all containers
```

### Brew API Usage
```bash
curl -X POST http://localhost:9000/brew \
  -H "Content-Type: application/json" \
  -d @tools/bean_request.json
```

### Visualization Endpoint
```bash
curl -X POST http://localhost:9000/visualize \
  -H "Content-Type: application/json" \
  -d @tools/visualize_request.json
```

### CLI (Outside Docker)
```bash
python -m agent_core.agent \
  --bean bean.json \
  --brewer V60 \
  --rag-service-url http://localhost:8000
```

### Visualization Demo Script
```bash
python tools/save_visualization.py   # saves HTML to out.html using sample payload
```

## Validation & Deliverables
- **Functional Demo:** `/brew` → recipe JSON, `/visualize` → HTML timeline (example stored in `out.html`).
- **RAG Integration:** agent gracefully falls back when RAG is offline; retrieval logs stored in container output.
- **Documentation:** this README + `reports/Statement_of_Work.pdf` describe scope, objectives, and setup.

## Next Steps (Beyond Milestone 2)
1. Collect real user brewing logs and expand RAG coverage.
2. Integrate feedback loop for recipe evaluation and adaptation.
3. Build a lightweight UI to collect preferences and display visualizations interactively.
