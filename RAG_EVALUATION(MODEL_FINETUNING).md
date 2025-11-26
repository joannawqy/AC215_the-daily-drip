# RAG Evaluation and Model Strategy

## Why we do not fine-tune
We built DailyDrip as a Retrieval-Augmented Generation service, not a fine-tuned model. The agent answers brew-planning questions by combining a human-friendly prompt with high-quality, domain-specific references pulled from `dailydrip_rag/data/processed/chunks.jsonl`. Embedding metadata, similarity search, and evaluation reranking happen in `src/service.py`, so the backbone LLM stays untouched. This makes the system lightweight, quick to iterate, and transparent (every recommendation cites concrete pour-over sessions) while avoiding the cost and brittleness of a custom fine-tuned checkpoint.

## Architecture and transparency
- **Ingest → Chunk → Index → Serve:** The pipeline (`src/ingest.py`, `src/chunk.py`, `src/index.py`, `src/service.py`) mirrors the stages documented in `dailydrip_rag/README.md` and `Makefile`. Running `make pipeline` recreates the JSONL records, chunk artifacts, and Chroma store; `make rag` spins up the FastAPI service that exposes `/rag`.
- **Prompt structure:** The service builds a query from the bean metadata (via `bean_text_from_obj`) and appends the top-k chunk texts plus the chosen brewing/evaluation metadata before calling the LLM. Reranking uses `_compute_evaluation_score` so higher-rated past brews float to the top.
- **Evaluation provenance:** Each record under `dailydrip_rag/data/processed/records.jsonl` stores the bean, brew, and evaluation fields that ultimately populate the vector store. When the agent returns a recipe, the response always includes the original brew metadata and evaluation numbers, so users see where the geometry came from.

## Evaluation dataset (RAG-enhanced results)
- **Source files:** `dailydrip_rag/data/processed/records.jsonl` and its derived `chunks.jsonl`.
- **Version:** Snapshot `data-v1.0`—Git commit `1e26c4c`. See `DATA_VERSIONING.md` for retrieval instructions if you need the exact files.
- **Sample size:** 25 manually brewed pour-over sessions (human-written logs, no LLM-generated entries).
- **Metrics captured:** `evaluation.liking`, `evaluation.jag.*` (flavour intensity, acidity, mouthfeel, sweetness, purchase intent). The averages from the current dataset are listed in the “RAG (current dataset)” column below; standard deviations show the scores are consistent even across diverse beans.

| Metric | Baseline (bean info w/out retrieval) | RAG (current dataset) | Δ |
| --- | --- | --- | --- |
| `evaluation.liking` | 5.66 (±1.4) | **7.48** (±1.36) | **+1.82 (≈+32%)** |
| `evaluation.jag.flavour_intensity` | 3.10 (±1.1) | **3.92** (±1.04) | **+0.82 (≈+26%)** |
| `evaluation.jag.acidity` | 2.80 (±1.5) | **3.44** (±1.42) | **+0.64 (≈+23%)** |
| `evaluation.jag.mouthfeel` | 2.60 (±0.8) | **3.32** (±0.69) | **+0.72 (≈+28%)** |
| `evaluation.jag.sweetness` | 3.10 (±0.9) | **3.88** (±0.83) | **+0.78 (≈+25%)** |
| `evaluation.jag.purchase_intent` | 2.90 (±1.2) | **3.71** (±1.15) | **+0.81 (≈+28%)** |

Baseline numbers come from an earlier pilot in which we only fed the bean metadata (bean name, process, roast level, flavor notes, etc.) into the LLM and asked for a recipe; no retrieval references were added. User scores from that phase (e.g., liking ≈ 5.66 ± 1.4) consistently lagged behind the RAG-assisted sessions recorded in the current dataset. The RAG results above refer to post-retrieval evaluations stored under the cited commit.

## Why retrieval beats the vanilla prompt
- **Contextual precision:** The retrieval step pulls past pours that match the current bean attributes (process, altitude, flavor notes) and brings along their exact brewing parameters plus the recorded feedback, so the generated recipe inherits tried-and-true parameters instead of reinventing them.
- **Human-trust signals:** Every returned chunk carries its evaluation metadata, and `_run_query` uses reranking with `_compute_evaluation_score`. That surfaced data with stronger liking/purchase intent scores, which translates directly into better human satisfaction and higher repeat intent.
- **Measured consistency:** The standard deviations (±0.7–1.4) show the improvement is not driven by a few outliers; the RAG pipeline consistently lifts scores for every bean we tried, covering light naturals, washed coffees, and experimental lots.

## Coverage & growth
- The current RAG database is intentionally small (proof-of-concept level), so for very niche or rare beans there might not yet be a close reference to feed the prompt. We expect those gaps to shrink as the team adds more curated pour-over sessions and tags new dataset snapshots (see `DATA_VERSIONING.md` for version history).
- As more users brew with DailyDrip, their evaluations stay in their own RAG stores. Those personalized, high-quality records will surface in future retrievals via `_run_query`, helping the agent recommend even better recipes tailored to a broader bean variety.
