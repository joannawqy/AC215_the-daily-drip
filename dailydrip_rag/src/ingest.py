import json, argparse
import pandas as pd
from pathlib import Path

INCLUDE_COLUMNS = None  # set to a list to restrict which columns go into text

def to_record(row: dict) -> dict:
    parts = []
    items = row.items() if INCLUDE_COLUMNS is None else [(k, row.get(k)) for k in INCLUDE_COLUMNS]
    for k, v in items:
        if pd.isna(v): 
            continue
        parts.append(f"{k}: {v}")
    text = " | ".join(parts)
    rid = str(row.get('id','row')) + "-" + str(abs(hash(text)))[-6:]
    return {"id": rid, "text": text, "meta": row}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--csv', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('w', encoding='utf-8') as f:
        for _, r in df.iterrows():
            f.write(json.dumps(to_record(r.to_dict()), ensure_ascii=False) + "\n")
    print(f"Wrote records to {out} ({len(df)} rows).")

if __name__ == "__main__":
    main()