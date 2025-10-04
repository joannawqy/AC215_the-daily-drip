.PHONY: rag.sample rag.index rag.query
rag.sample:
	python -m src.ingest --csv data/raw/ucdavis_sample.csv --out data/processed/records.jsonl
	python -m src.chunk  --records data/processed/records.jsonl --out data/processed/chunks.jsonl
rag.index: rag.sample
	python -m src.index  --chunks data/processed/chunks.jsonl --persist-dir indexes/chroma
rag.query:
	python -m src.query  --persist-dir indexes/chroma --q "light fruity high clarity"