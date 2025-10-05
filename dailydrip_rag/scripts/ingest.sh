#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   scripts/ingest.sh [CSV_IN] [RECORDS_OUT]
# Defaults:
CSV_IN="${1:-data/raw/ucdavis_sample.csv}"
RECORDS_OUT="${2:-data/processed/records.jsonl}"

echo "[ingest] csv=${CSV_IN} -> ${RECORDS_OUT}"
python -m src.ingest --csv "${CSV_IN}" --out "${RECORDS_OUT}"
