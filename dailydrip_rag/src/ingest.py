import json, argparse
import pandas as pd
from pathlib import Path

# Fields used to build the retrievable "bean text"
BEAN_COLUMNS = [
    "bean.name", "bean.process", "bean.variety", "bean.region",
    "bean.roast_level", "bean.roasted_days", "bean.altitude", "bean.flavor_notes",
]

def flatten(d, parent_key="", sep="."):
    out = {}
    for k, v in d.items():
        key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            out.update(flatten(v, key, sep=sep))
        else:
            out[key] = v
    return out

def list_to_str(v):
    if isinstance(v, list):
        return ", ".join(map(str, v))
    return v

def pours_to_str(pours):
    # pours: list of {"start","end","water_added"}
    if isinstance(pours, list) and pours and isinstance(pours[0], dict):
        return "; ".join(f"{p.get('start')}-{p.get('end')}:{p.get('water_added')}" for p in pours)
    return None

def bean_text(flat: dict) -> str:
    parts = []
    for k in BEAN_COLUMNS:
        v = flat.get(k)
        v = list_to_str(v)
        if v is None or (isinstance(v, float) and pd.isna(v)): 
            continue
        parts.append(f"{k}: {v}")
    return " | ".join(parts)

def make_record(obj: dict) -> dict:
    flat = flatten(obj)

    # also store a readable pours string in meta
    if "brewing.pours" in flat and isinstance(flat["brewing.pours"], list):
        flat["brewing.pours_str"] = pours_to_str(flat["brewing.pours"])

    text = bean_text(flat)  # <— embedding text based on bean profile only
    rid_base = str(flat.get("id") or flat.get("uuid") or flat.get("bean.name") or "")
    rid = (rid_base if rid_base else "row") + "-" + str(abs(hash(text)))[-6:]
    return {"id": rid, "text": text, "meta": flat}

def iter_json_any(path: str):
    """Yield JSON objects from JSON, JSON array, JSONL, or concatenated pretty JSON."""
    with open(path, "r", encoding="utf-8") as f:
        s = f.read()

    # Try whole JSON first
    try:
        data = json.loads(s)
        if isinstance(data, list):
            for it in data: yield it
        else:
            yield data
        return
    except json.JSONDecodeError:
        pass

    # Try JSONL
    try_lines = True
    for line in s.splitlines():
        line = line.strip()
        if not line: 
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            try_lines = False
            break
    if try_lines:
        return

    # Fallback: concatenated JSON objects
    dec = json.JSONDecoder(); i = 0; n = len(s)
    while i < n:
        while i < n and s[i].isspace(): i += 1
        if i >= n: break
        obj, end = dec.raw_decode(s, i)
        if isinstance(obj, list):
            for it in obj: yield it
        else:
            yield obj
        i = end

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", help="CSV input")
    ap.add_argument("--json", help="JSON input (single object or array)")
    ap.add_argument("--jsonl", help="JSONL or concatenated pretty JSON")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    if not (args.csv or args.json or args.jsonl):
        raise SystemExit("Provide one of --csv | --json | --jsonl")

    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f_out:
        if args.csv:
            df = pd.read_csv(args.csv)
            for _, r in df.iterrows():
                f_out.write(json.dumps(make_record(r.to_dict()), ensure_ascii=False) + "\n")
        else:
            src = args.json or args.jsonl
            for obj in iter_json_any(src):
                f_out.write(json.dumps(make_record(obj), ensure_ascii=False) + "\n")

    print(f"Wrote records to {out}")

if __name__ == "__main__":
    main()
