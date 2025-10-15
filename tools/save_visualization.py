import json
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"


def main() -> None:
    """Send a visualize request and save the HTML output to out.html."""
    req_path = TOOLS_DIR / "visualize_request.json"
    if not req_path.exists():
        raise FileNotFoundError(f"{req_path.name} not found in repository root.")

    payload = json.loads(req_path.read_text(encoding="utf-8"))

    response = requests.post(
        "http://localhost:9000/visualize",
        json=payload,
        timeout=60,
    )
    response.raise_for_status()

    data = response.json()
    html = data.get("outputs", {}).get("html")
    if not html:
        raise ValueError("HTML output missing in response.")

    output_path = REPO_ROOT / "out.html"
    output_path.write_text(html, encoding="utf-8")
    print(f"Saved visualization to {output_path}")


if __name__ == "__main__":
    main()
