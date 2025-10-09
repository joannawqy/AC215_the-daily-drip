import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI

try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:  # pragma: no cover - optional dependency
    chromadb = None  # type: ignore[assignment]
    embedding_functions = None  # type: ignore[assignment]


SYSTEM_PROMPT = """You are a pour-over coffee brewing assistant.

You will receive a coffee bean description and the name of a pour-over brewer.
Your job is to recommend a complete brewing recipe tailored to that bean and brewer.
You may also receive up to three reference recipes from similar beans; treat them as
inspiration while tailoring the final plan to the provided bean and brewer.

The bean information always arrives as JSON with fields such as: name, process, variety,
region, roast_level, roasted_days, altitude, and flavor_notes. The brewer is one of
["V60", "April", "Orea", "Origami"].

Create a recipe that respects the following constraints:
- temperature: integer Celsius, usually 88-96. Lighter roasts often need hotter water.
- grinding_size: integer clicks on a Comandante C40 grinder, usually 18-28. Lower is finer.
- dose: integer grams of coffee, typically 13-20 g. Flatter brewers (April, Orea) lean lower.
- target_water: integer grams, usually 200-320 g. Keep the brew ratio between 1:15 and 1:17.
- pours: list of pour steps. Each step has start, end (seconds), and water_added (grams).
  * The first step should bloom at time 0.
  * Each step length (end - start) is usually 5-20 seconds.
  * Sum of water_added must equal target_water.
- Always echo back the brewer from the input exactly.


"""


def load_bean_info(bean_source: str) -> Dict[str, Any]:
    """
    Load bean information from a JSON string or a path to a JSON file.
    """
    path = Path(bean_source)
    if path.exists():
        raw = path.read_text(encoding="utf-8")
    else:
        raw = bean_source
    return json.loads(raw)


def clean_json_payload(payload: str) -> str:
    """
    Remove Markdown code fences, if present, before parsing the JSON payload.
    """
    payload = payload.strip()
    if payload.startswith("```"):
        payload = payload.strip("`")
        if payload.lower().startswith("json"):
            payload = payload[4:]
    return payload.strip()


DEFAULT_RAG_PERSIST_DIR = Path(__file__).parent / "dailydrip_rag" / "indexes" / "chroma"
RAG_COLLECTION = "coffee_chunks"
RAG_MODEL = "all-MiniLM-L6-v2"
BEAN_COLUMNS = [
    "bean.name",
    "bean.process",
    "bean.variety",
    "bean.region",
    "bean.roast_level",
    "bean.roasted_days",
    "bean.altitude",
    "bean.flavor_notes",
]


def flatten_dict(data: Dict[str, Any], parent: str = "", sep: str = ".") -> Dict[str, Any]:
    """
    Flatten nested dictionaries using dotted key notation, matching ingest metadata.
    """
    flattened: Dict[str, Any] = {}
    for key, value in data.items():
        new_key = f"{parent}{sep}{key}" if parent else key
        if isinstance(value, dict):
            flattened.update(flatten_dict(value, new_key, sep=sep))
        else:
            flattened[new_key] = value
    return flattened


def _list_to_str(value: Any) -> Any:
    return ", ".join(map(str, value)) if isinstance(value, list) else value


def bean_text_from_obj(obj: Dict[str, Any]) -> str:
    """
    Construct the canonical bean text used for similarity search.
    """
    has_nested = any(isinstance(v, dict) for v in obj.values())
    flat = flatten_dict(obj) if has_nested else obj
    parts: List[str] = []
    for key in BEAN_COLUMNS:
        val = _list_to_str(flat.get(key))
        if val is None:
            continue
        parts.append(f"{key}: {val}")
    return " | ".join(parts)


def reconstruct_pours(meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Rebuild pour steps from flattened metadata keys.
    """
    pours: List[Dict[str, Any]] = []
    indices = set()
    for key in meta.keys():
        if key.startswith("brewing.pours."):
            parts = key.split(".")
            if len(parts) >= 3 and parts[2].isdigit():
                indices.add(int(parts[2]))
    for idx in sorted(indices):
        pours.append(
            {
                "start": meta.get(f"brewing.pours.{idx}.start"),
                "end": meta.get(f"brewing.pours.{idx}.end"),
                "water_added": meta.get(f"brewing.pours.{idx}.water_added"),
            }
        )
    return pours


def extract_brewing(meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract the brewing block from flattened metadata.
    """
    pours = reconstruct_pours(meta)
    return {
        "brewer": meta.get("brewing.brewer"),
        "temperature": meta.get("brewing.temperature"),
        "grinding_size": meta.get("brewing.grinding_size"),
        "dose": meta.get("brewing.dose"),
        "target_water": meta.get("brewing.target_water"),
        "pours": pours or meta.get("brewing.pours_str"),
    }


def extract_evaluation(meta: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract the evaluation block if present.
    """
    evaluation: Dict[str, Any] = {}
    if "evaluation.liking" in meta:
        evaluation["liking"] = meta["evaluation.liking"]
    jag = {}
    for key in (
        "flavour_intensity",
        "acidity",
        "mouthfeel",
        "sweetness",
        "purchase_intent",
    ):
        value = meta.get(f"evaluation.jag.{key}")
        if value is not None:
            jag[key] = value
    if jag:
        evaluation["jag"] = jag
    return evaluation or None


def query_reference_recipes(
    bean_info: Dict[str, Any],
    *,
    persist_dir: Path = DEFAULT_RAG_PERSIST_DIR,
    k: int = 3,
) -> List[Dict[str, Any]]:
    """
    Retrieve up to ``k`` similar beans from the RAG index.
    """
    if chromadb is None or embedding_functions is None:
        raise RuntimeError("chromadb is not installed; cannot query RAG index.")

    if k <= 0:
        return []

    persist_dir = Path(persist_dir)
    if not persist_dir.exists():
        raise FileNotFoundError(f"RAG persist directory not found: {persist_dir}")

    client = chromadb.PersistentClient(path=str(persist_dir))
    embedding = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=RAG_MODEL
    )
    collection = client.get_or_create_collection(
        RAG_COLLECTION, embedding_function=embedding
    )

    query_text = bean_text_from_obj({"bean": bean_info})
    response = collection.query(
        query_texts=[query_text],
        n_results=k,
        include=["metadatas", "documents", "distances"],
    )

    docs = response.get("documents", [[]])[0]
    metas = response.get("metadatas", [[]])[0]
    ids = response.get("ids", [[]])[0]
    distances = response.get("distances", [[]])[0]

    references: List[Dict[str, Any]] = []
    for rank, (doc, meta, record_id, dist) in enumerate(
        zip(docs, metas, ids, distances), start=1
    ):
        brewing = extract_brewing(meta)
        evaluation = extract_evaluation(meta)
        reference = {
            "rank": rank,
            "id": record_id,
            "distance": float(dist),
            "bean_text": doc,
            "brewing": brewing,
            "evaluation": evaluation,
        }
        references.append(reference)

    return references


def generate_recipe(
    bean_info: Dict[str, Any],
    brewer: str,
    *,
    reference_recipes: Optional[List[Dict[str, Any]]] = None,
    model: str = "gpt-4.1-mini",
    temperature: float = 0.6,
    top_p: float = 0.9,
) -> Dict[str, Any]:
    """
    Generate a pour-over recipe for the given bean and brewer.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY is not set.")

    client = OpenAI(api_key=api_key)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": json.dumps(
                {
                    "bean": bean_info,
                    "brewer": brewer,
                    "reference_recipes": reference_recipes or [],
                },
                ensure_ascii=False,
            ),
        },
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
    )
    content = response.choices[0].message.content or ""
    content = clean_json_payload(content)
    recipe = json.loads(content)
    return recipe


def normalize_recipe(recipe: Dict[str, Any]) -> Dict[str, Any]:
    """
    Accept recipes where the brewing block is either top-level or nested under ``brewing``.
    """
    if not isinstance(recipe, dict):
        raise ValueError("Recipe must be a JSON object.")

    brewing = recipe.get("brewing")
    if isinstance(brewing, dict):
        return recipe

    expected = {"brewer", "temperature", "grinding_size", "dose", "target_water", "pours"}
    if expected.issubset(recipe.keys()):
        return {"brewing": recipe}

    raise ValueError("Recipe payload missing brewing block.")


def validate_recipe(recipe: Dict[str, Any]) -> None:
    """
    Perform basic validation to catch common model mistakes early.
    Raises ValueError if the recipe fails a check.
    """
    brewing = recipe.get("brewing")
    if not isinstance(brewing, dict):
        raise ValueError("Missing brewing section.")

    pours = brewing.get("pours")
    if not isinstance(pours, list) or not pours:
        raise ValueError("Pours must be a non-empty list.")

    target = brewing.get("target_water")
    total = sum(step.get("water_added", 0) for step in pours)
    if target != total:
        raise ValueError(
            f"Sum of pours ({total}) does not match target_water ({target})."
        )

    brewer = brewing.get("brewer")
    if not brewer:
        raise ValueError("Brewer is required in brewing section.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a pour-over recipe with OpenAI."
    )
    parser.add_argument(
        "--bean",
        required=True,
        help="JSON string or path to a JSON file describing the bean.",
    )
    parser.add_argument(
        "--brewer",
        required=True,
        help="Name of the brewer (e.g., V60, April, Orea, Origami).",
    )
    parser.add_argument(
        "--model",
        default="gpt-4.1-mini",
        help="OpenAI model to use. Defaults to gpt-4.1-mini.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.6,
        help="Sampling temperature for the model.",
    )
    parser.add_argument(
        "--top-p",
        type=float,
        default=0.9,
        help="Nucleus sampling probability.",
    )
    parser.add_argument(
        "--rag-persist-dir",
        default=str(DEFAULT_RAG_PERSIST_DIR),
        help="Path to the RAG persist directory (Chroma).",
    )
    parser.add_argument(
        "--rag-k",
        type=int,
        default=3,
        help="Number of reference recipes to retrieve from RAG.",
    )
    parser.add_argument(
        "--no-rag",
        dest="rag_enabled",
        action="store_false",
        help="Disable RAG retrieval of reference recipes.",
    )
    parser.set_defaults(rag_enabled=True)
    parser.add_argument(
        "--output",
        help="Optional path to save the recipe JSON. Prints to stdout if omitted.",
    )

    args = parser.parse_args()
    bean_info = load_bean_info(args.bean)
    references: List[Dict[str, Any]] = []
    if args.rag_enabled:
        try:
            references = query_reference_recipes(
                bean_info,
                persist_dir=Path(args.rag_persist_dir),
                k=args.rag_k,
            )
        except Exception as exc:  # pragma: no cover - best effort
            print(f"Warning: skipping RAG references ({exc})", file=sys.stderr)
    recipe = generate_recipe(
        bean_info,
        args.brewer,
        reference_recipes=references,
        model=args.model,
        temperature=args.temperature,
        top_p=args.top_p,
    )
    recipe = normalize_recipe(recipe)

    # Optional validation to spot obvious issues.
    try:
        validate_recipe(recipe)
    except ValueError as exc:
        raise SystemExit(f"Recipe validation failed: {exc}") from exc

    output = json.dumps(recipe, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()
