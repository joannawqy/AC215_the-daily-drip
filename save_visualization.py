import json
from pathlib import Path

import requests


def main() -> None:
    """Send a visualize request and save the HTML output to out.html."""
    req_path = Path("visualize_request.json")
    if not req_path.exists():
        raise FileNotFoundError("visualize_request.json not found in current directory.")

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

    Path("out.html").write_text(html, encoding="utf-8")
    print("Saved visualization to out.html")


if __name__ == "__main__":
    main()
