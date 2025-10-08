import json, argparse
import pandas as pd
from pathlib import Path

INCLUDE_COLUMNS = [

    "bean.name", "bean.process", "bean.variety", "bean.region",
    "bean.roast_level", "bean.roasted_days", "bean.altitude", "bean.flavor_notes",
    "brewing.brewer", "brewing.temperature", "brewing.grinding_size",
    "brewing.dose", "brewing.target_water",
    "evaluation.liking", "evaluation.jag.flavour_intensity",
    "evaluation.jag.acidity", "evaluation.jag.mouthfeel",
    "evaluation.jag.sweetness", "evaluation.jag.purchase_intent",
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

def row_to_text(row: dict) -> str:
    items = row.items() if INCLUDE_COLUMNS is None else [(k, row.get(k)) for k in INCLUDE_COLUMNS]
    parts = []
    for k, v in items:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            continue
        if isinstance(v, list):
            v = ", ".join(map(str, v))
        parts.append(f"{k}: {v}")
    return " | ".join(parts)

def make_record(obj: dict) -> dict:
    flat = flatten(obj)
    text = row_to_text(flat)
    rid_base = str(flat.get("id") or flat.get("uuid") or flat.get("brew_id") or flat.get("bean.name") or "")
    rid = (rid_base if rid_base else "row") + "-" + str(abs(hash(text)))[-6:]
    return {"id": rid, "text": text, "meta": flat}

def iter_json_any(path: str):
    """Yield JSON objects from a single JSON object, a JSON array,
       JSONL (one object per line), OR multiple concatenated pretty-printed objects."""
    with open(path, "r", encoding="utf-8") as f:
        s = f.read()

    try:
        data = json.loads(s)
        if isinstance(data, list):
            for item in data: yield item
        else:
            yield data
        return
    except json.JSONDecodeError:
        pass

    ok_lines = True
    objs = []
    for line in s.splitlines():
        line = line.strip()
        if not line: continue
        try:
            objs.append(json.loads(line))
        except json.JSONDecodeError:
            ok_lines = False
            break
    if ok_lines and objs:
        for o in objs: yield o
        return

    dec = json.JSONDecoder()
    i, n = 0, len(s)
    while i < n:
        while i < n and s[i].isspace(): i += 1
        if i >= n: break
        obj, end = dec.raw_decode(s, i)
        if isinstance(obj, list):
            for item in obj: yield item
        else:
            yield obj
        i = end

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", help="CSV input")
    ap.add_argument("--json", help="JSON input (single object or array)")
    ap.add_argument("--jsonl", help="JSONL input (one object per line, but concatenated JSON also OK)")
    ap.add_argument("--out", required=True, help="Output JSONL of records")
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
