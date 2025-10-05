#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   scripts/query.sh "your query" [INDEX_DIR] [K] [MIN_LIKE]
Q="${1:-light fruity high clarity}"
INDEX_DIR="${2:-indexes/chroma}"
K="${3:-5}"
MIN_LIKE="${4:-}"  # optional; requires enhanced query.py that supports --min-like

echo "[query] '${Q}' against ${INDEX_DIR} (top ${K})"
if [[ -n "${MIN_LIKE}" ]]; then
  python -m src.query --persist-dir "${INDEX_DIR}" --q "${Q}" --k "${K}" --min-like "${MIN_LIKE}"
else
  python -m src.query --persist-dir "${INDEX_DIR}" --q "${Q}" --k "${K}"
fi
