import argparse
import json
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from openai import OpenAI
from pydantic import BaseModel, Field

from visualization_agent_v2 import CoffeeBrewVisualizationAgent

try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:  # pragma: no cover - optional dependency
    chromadb = None  # type: ignore[assignment]
    embedding_functions = None  # type: ignore[assignment]

try:
    import httpx
except ImportError:  # pragma: no cover - optional dependency
    httpx = None  # type: ignore[assignment]


SYSTEM_PROMPT = """You are a pour-over coffee brewing assistant.

You will receive a coffee bean description and the name of a pour-over brewer.
Your job is to recommend a complete brewing recipe tailored to that bean and brewer.
You may also receive up to three reference recipes from similar beans; treat them as
inspiration while tailoring the final plan to the provided bean and brewer.
If the user supplies an additional custom request (e.g., dose preference or taste goal),
incorporate it thoughtfully into your final recipe.

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

Your output must be a single JSON object with this structure:
{
  "brewing": {
    "brewer": string,
    "temperature": integer,
    "grinding_size": integer,
    "dose": integer,
    "target_water": integer,
    "pours": [
      {
        "start": integer,
        "end": integer,
        "water_added": integer
      },
      ...
    ]
  }
}

"""


DEFAULT_RAG_PERSIST_DIR = Path(__file__).parent / "dailydrip_rag" / "indexes" / "chroma"
DEFAULT_RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL")
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


def _fetch_references_via_service(
    bean_info: Dict[str, Any], *, rag_service_url: str, k: int
) -> List[Dict[str, Any]]:
    if httpx is None:
        raise RuntimeError("httpx is not installed; cannot call the RAG service.")

    if not rag_service_url:
        raise ValueError("RAG service URL must not be empty.")

    payload: Dict[str, Any] = {"k": k}
    if "bean" in bean_info:
        payload["record"] = bean_info
        if isinstance(bean_info.get("bean"), dict):
            payload["bean"] = bean_info["bean"]
    else:
        payload["bean"] = bean_info

    with httpx.Client(base_url=rag_service_url, timeout=30.0) as client:
        response = client.post("/rag", json=payload)
        if response.status_code != 200:
            detail = response.text
            raise RuntimeError(f"RAG service returned an error ({response.status_code}): {detail}")
        data = response.json()

    results = data.get("results", [])
    references: List[Dict[str, Any]] = []
    for item in results:
        reference = {
            "rank": item.get("rank"),
            "id": item.get("id"),
            "distance": item.get("distance"),
            "bean_text": item.get("bean_text"),
            "brewing": item.get("brewing"),
            "evaluation": item.get("evaluation"),
        }
        references.append(reference)
    return references

def _fetch_references_via_local_index(
    bean_info: Dict[str, Any], *, persist_dir: Path, k: int
) -> List[Dict[str, Any]]:
    if chromadb is None or embedding_functions is None:
        raise RuntimeError("chromadb is not installed; cannot query the local index.")

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

    query_source = bean_info if "bean" in bean_info else {"bean": bean_info}
    query_text = bean_text_from_obj(query_source)
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


def query_reference_recipes(
    bean_info: Dict[str, Any],
    *,
    persist_dir: Path = DEFAULT_RAG_PERSIST_DIR,
    rag_service_url: Optional[str] = DEFAULT_RAG_SERVICE_URL,
    k: int = 3,
) -> List[Dict[str, Any]]:
    """
    Retrieve up to ``k`` similar beans from either the remote RAG service or the local index.
    """
    if k <= 0:
        return []

    if rag_service_url:
        return _fetch_references_via_service(
            bean_info, rag_service_url=rag_service_url, k=k
        )

    return _fetch_references_via_local_index(bean_info, persist_dir=persist_dir, k=k)


@lru_cache(maxsize=1)
def _get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY is not set.")
    return OpenAI(api_key=api_key)


def generate_recipe(
    bean_info: Dict[str, Any],
    brewer: str,
    *,
    reference_recipes: Optional[List[Dict[str, Any]]] = None,
    custom_note: Optional[str] = None,
    model: str = "gpt-4.1-mini",
    temperature: float = 0.6,
    top_p: float = 0.9,
) -> Dict[str, Any]:
    """
    Generate a pour-over recipe for the given bean and brewer.
    Optionally provide RAG reference recipes and a user custom note to steer the output.
    """
    client = _get_openai_client()
    payload: Dict[str, Any] = {
        "bean": bean_info,
        "brewer": brewer,
        "reference_recipes": reference_recipes or [],
    }
    if custom_note:
        payload["custom_note"] = custom_note

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": json.dumps(payload, ensure_ascii=False),
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


class BrewRequest(BaseModel):
    bean: Dict[str, Any] = Field(..., description="Structured JSON description of the coffee bean.")
    brewer: str = Field(
        ...,
        description="Name of the brewer, e.g., V60, April, Orea, or Origami.",
    )
    note: Optional[str] = Field(
        default=None,
        description="Optional customization request, such as desired flavor or pour preference.",
    )
    rag_service_url: Optional[str] = Field(
        default=None,
        description="Override the default RAG service URL when querying references.",
    )
    rag_persist_dir: Optional[str] = Field(
        default=None,
        description="Path to the local Chroma index used when falling back from the service.",
    )
    rag_k: int = Field(default=3, ge=1, le=10, description="Number of RAG references to retrieve.")
    model: str = Field(default="gpt-4.1-mini", description="OpenAI model used to generate recipes.")
    temperature: float = Field(default=0.6, ge=0.0, le=2.0, description="Sampling temperature.")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Nucleus sampling probability.")
    rag_enabled: bool = Field(default=True, description="Whether to perform RAG retrieval.")


class BrewResponse(BaseModel):
    references: List[Dict[str, Any]]
    recipe: Dict[str, Any]


ALLOWED_VIS_FORMATS = {"html", "mermaid", "ascii"}


class VisualizationRequest(BaseModel):
    recipe: Dict[str, Any] = Field(
        ...,
        description="Recipe JSON containing at least bean and brewing sections.",
    )
    formats: List[str] = Field(
        default_factory=lambda: ["html"],
        description="List of visualization formats to generate (choices: html, mermaid, ascii).",
    )


class VisualizationResponse(BaseModel):
    outputs: Dict[str, str]
    summary: Dict[str, Any]


def brew_with_options(
    bean_info: Dict[str, Any],
    brewer: str,
    *,
    note: Optional[str],
    rag_enabled: bool,
    rag_service_url: Optional[str],
    rag_persist_dir: Optional[str],
    rag_k: int,
    model: str,
    temperature: float,
    top_p: float,
) -> BrewResponse:
    references: List[Dict[str, Any]] = []
    if rag_enabled:
        references = query_reference_recipes(
            bean_info,
            persist_dir=Path(rag_persist_dir or DEFAULT_RAG_PERSIST_DIR),
            rag_service_url=rag_service_url or DEFAULT_RAG_SERVICE_URL,
            k=rag_k,
        )

    recipe = generate_recipe(
        bean_info,
        brewer,
        reference_recipes=references,
        custom_note=note,
        model=model,
        temperature=temperature,
        top_p=top_p,
    )
    recipe = normalize_recipe(recipe)
    validate_recipe(recipe)
    return BrewResponse(references=references, recipe=recipe)


def build_visualizations(recipe: Dict[str, Any], formats: List[str]) -> VisualizationResponse:
    if not isinstance(recipe, dict):
        raise ValueError("Recipe payload must be a JSON object.")

    requested = formats or ["html"]
    invalid = [fmt for fmt in requested if fmt not in ALLOWED_VIS_FORMATS]
    if invalid:
        raise ValueError(f"Unsupported visualization formats requested: {', '.join(invalid)}")

    if "bean" not in recipe or "brewing" not in recipe:
        raise ValueError("Recipe must include both 'bean' and 'brewing' sections.")

    viz_agent = CoffeeBrewVisualizationAgent()
    viz_agent.load_recipe(recipe)

    outputs: Dict[str, str] = {}
    if "html" in requested:
        outputs["html"] = viz_agent.generate_html_visualization()
    if "mermaid" in requested:
        outputs["mermaid"] = viz_agent.generate_mermaid_flowchart()
    if "ascii" in requested:
        outputs["ascii"] = viz_agent.generate_ascii_flowchart()

    return VisualizationResponse(outputs=outputs, summary=viz_agent.get_recipe_summary())


app = FastAPI(
    title="DailyDrip Agent Service",
    description="Accepts coffee bean information or recipes, consults the RAG service, and produces brewing plans and visualizations.",
    version="0.2.0",
)


@app.post("/brew", response_model=BrewResponse)
async def brew_endpoint(payload: BrewRequest) -> BrewResponse:
    try:
        return await run_in_threadpool(
            brew_with_options,
            payload.bean,
            payload.brewer,
            note=payload.note,
            rag_enabled=payload.rag_enabled,
            rag_service_url=payload.rag_service_url,
            rag_persist_dir=payload.rag_persist_dir,
            rag_k=payload.rag_k,
            model=payload.model,
            temperature=payload.temperature,
            top_p=payload.top_p,
        )
    except EnvironmentError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/visualize", response_model=VisualizationResponse)
async def visualize_endpoint(payload: VisualizationRequest) -> VisualizationResponse:
    try:
        return await run_in_threadpool(
            build_visualizations,
            payload.recipe,
            payload.formats,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a pour-over recipe with OpenAI or start the HTTP service."
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start the FastAPI service instead of running in CLI mode.",
    )
    parser.add_argument(
        "--bean",
        help="JSON string or path to a JSON file describing the bean (not required in --serve mode).",
    )
    parser.add_argument(
        "--brewer",
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
        "--note",
        help="Optional custom instruction to guide the recipe (e.g., dosing or taste preference).",
    )
    parser.add_argument(
        "--rag-persist-dir",
        default=str(DEFAULT_RAG_PERSIST_DIR),
        help="Path to the RAG persist directory (Chroma).",
    )
    parser.add_argument(
        "--rag-service-url",
        default=os.getenv("RAG_SERVICE_URL"),
        help="Optional HTTP endpoint for the RAG service (for example http://rag:8000).",
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

    if args.serve:
        import uvicorn

        uvicorn.run(
            "agent:app",
            host="0.0.0.0",
            port=int(os.getenv("AGENT_PORT", "9000")),
            reload=False,
        )
        return

    if not args.bean or not args.brewer:
        raise SystemExit("Both --bean and --brewer are required when running in CLI mode.")

    bean_info = load_bean_info(args.bean)
    try:
        response = brew_with_options(
            bean_info,
            args.brewer,
            note=args.note,
            rag_enabled=args.rag_enabled,
            rag_service_url=args.rag_service_url,
            rag_persist_dir=args.rag_persist_dir,
            rag_k=args.rag_k,
            model=args.model,
            temperature=args.temperature,
            top_p=args.top_p,
        )
    except Exception as exc:  # pragma: no cover - best effort
        raise SystemExit(f"Failed to generate recipe: {exc}") from exc

    print("References:")  # noqa: T201
    print(json.dumps(response.references, ensure_ascii=False, indent=2))  # noqa: T201
    output = json.dumps(response.recipe, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output)  # noqa: T201


if __name__ == "__main__":
    main()
