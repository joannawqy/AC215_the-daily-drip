#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   scripts/build_index.sh [RECORDS_IN] [CHUNKS_OUT] [INDEX_DIR]
# Defaults:
RECORDS_IN="${1:-data/processed/records.jsonl}"
CHUNKS_OUT="${2:-data/processed/chunks.jsonl}"
INDEX_DIR="${3:-indexes/chroma}"

echo "[chunk] ${RECORDS_IN} -> ${CHUNKS_OUT}"
python -m src.chunk --records "${RECORDS_IN}" --out "${CHUNKS_OUT}"

echo "[index] ${CHUNKS_OUT} -> ${INDEX_DIR}"
python -m src.index --chunks "${CHUNKS_OUT}" --persist-dir "${INDEX_DIR}"

echo "[done] index at: ${INDEX_DIR}"
