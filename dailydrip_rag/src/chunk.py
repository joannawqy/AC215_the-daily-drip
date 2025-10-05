import json, argparse
from pathlib import Path
from tqdm import tqdm

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--records', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--max_chars', type=int, default=800)
    args = ap.parse_args()

    src = Path(args.records); dst = Path(args.out)
    dst.parent.mkdir(parents=True, exist_ok=True)

    with src.open() as f_in, dst.open('w', encoding='utf-8') as f_out:
        for line in tqdm(f_in, desc="chunking"):
            rec = json.loads(line); text = rec["text"]
            for i in range(0, len(text), args.max_chars):
                chunk = {"id": f"{rec.get('id','')}_{i}", "text": text[i:i+args.max_chars], "meta": rec["meta"]}
                f_out.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    print(f"Wrote chunks to {dst}")

if __name__ == "__main__":
    main()