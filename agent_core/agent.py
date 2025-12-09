from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import sys
import threading
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel, EmailStr, Field

from .visualization_agent_v2 import CoffeeBrewVisualizationAgent

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
- temperature: integer Celsius, usually **88-96**. Lighter roasts often need hotter water.
- grinding_size: integer clicks on a Comandante C40 grinder, usually **20-28**. Lower is finer.
- dose: integer grams of coffee, typically **13-20** g. Flatter brewers (April, Orea) lean lower.
- target_water: integer grams, usually **200-320** g. Keep the brew ratio between **1:15** and **1:17**.
- pours: list of pour steps. Each step has start, end (seconds), and water_added (grams).
  * The first step should bloom at time 0.
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


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RAG_PERSIST_DIR = REPO_ROOT / "dailydrip_rag" / "indexes" / "chroma"
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

DATA_DIR = REPO_ROOT / "data"
USER_STORE_PATH = DATA_DIR / "user_store.jsonl"

_user_store_lock = threading.Lock()
_user_store: Dict[str, Dict[str, Any]] = {}
_email_index: Dict[str, str] = {}
_active_tokens: Dict[str, str] = {}


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _compute_roasted_days(roasted_on: Optional[str]) -> Optional[int]:
    if not roasted_on:
        return None
    try:
        roasted_date = datetime.fromisoformat(roasted_on).date()
    except ValueError:
        return None
    delta = (datetime.utcnow().date() - roasted_date).days
    return max(delta, 0)


def _normalize_roast_fields(bean: Dict[str, Any]) -> Dict[str, Any]:
    roasted_on = bean.get("roasted_on")
    computed = _compute_roasted_days(roasted_on)
    if computed is not None:
        bean["roasted_days"] = computed
    elif bean.get("roasted_days") is None:
        bean.pop("roasted_days", None)
    return bean


def _load_user_store() -> None:
    with _user_store_lock:
        _user_store.clear()
        _email_index.clear()
        dirty = False
        if not USER_STORE_PATH.exists():
            return
        with USER_STORE_PATH.open("r", encoding="utf-8") as handle:
            for line in handle:
                payload = line.strip()
                if not payload:
                    continue
                try:
                    record = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                user_id = record.get("user_id")
                email = record.get("email")
                if not user_id or not email:
                    continue
                record.setdefault("preferences", {"flavor_notes": [], "roast_level": None})
                record.setdefault("beans", [])
                if not record.get("password_hash") and record.get("password"):
                    record["password_hash"] = _hash_password(record["password"])
                    record.pop("password", None)
                    dirty = True
                _user_store[user_id] = record
                _email_index[email.lower()] = user_id
        if dirty:
            _persist_user_store()


def _persist_user_store() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with USER_STORE_PATH.open("w", encoding="utf-8") as handle:
        for record in _user_store.values():
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _issue_token(user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    _active_tokens[token] = user_id
    return token


def _format_bean_record(bean: Dict[str, Any]) -> Dict[str, Any]:
    normalized = _normalize_roast_fields(dict(bean))
    return {
        "bean_id": normalized["bean_id"],
        "name": normalized.get("name"),
        "origin": normalized.get("origin"),
        "process": normalized.get("process"),
        "variety": normalized.get("variety"),
        "roast_level": normalized.get("roast_level"),
        "roasted_on": normalized.get("roasted_on"),
        "roasted_days": normalized.get("roasted_days"),
        "altitude": normalized.get("altitude"),
        "flavor_notes": normalized.get("flavor_notes", []),
        "created_at": normalized.get("created_at"),
        "updated_at": normalized.get("updated_at"),
    }


def _clean_flavor_notes(notes: Optional[List[str]]) -> List[str]:
    if not notes:
        return []
    return [note.strip() for note in notes if isinstance(note, str) and note.strip()]


def _user_to_public_payload(user: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "display_name": user.get("display_name"),
        "preferences": user.get("preferences", {"flavor_notes": [], "roast_level": None}),
        "beans": [_format_bean_record(bean) for bean in user.get("beans", [])],
        "created_at": user.get("created_at"),
        "updated_at": user.get("updated_at"),
    }


def _require_authenticated_user(token: Optional[str]) -> Dict[str, Any]:
    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication token.")
    user_id = _active_tokens.get(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    user = _user_store.get(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")
    return user


def get_authenticated_user(
    authorization: Optional[str] = Header(None),
    x_auth_token: Optional[str] = Header(None, alias="X-Auth-Token"),
) -> Dict[str, Any]:
    token = x_auth_token
    if not token and authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
        else:
            token = authorization
    return _require_authenticated_user(token)


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
    bean_info: Dict[str, Any],
    *,
    rag_service_url: str,
    k: int,
    use_evaluation_reranking: bool = True,
    similarity_weight: float = 0.7,
    retrieval_multiplier: int = 3,
) -> List[Dict[str, Any]]:
    if httpx is None:
        raise RuntimeError("httpx is not installed; cannot call the RAG service.")

    if not rag_service_url:
        raise ValueError("RAG service URL must not be empty.")

    payload: Dict[str, Any] = {
        "k": k,
        "use_evaluation_reranking": use_evaluation_reranking,
        "similarity_weight": similarity_weight,
        "retrieval_multiplier": retrieval_multiplier,
    }
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
            "combined_score": item.get("combined_score"),
        }
        references.append(reference)
    return references

def _compute_evaluation_score(evaluation: Optional[Dict[str, Any]]) -> float:
    """Compute normalized evaluation score (0-1) from liking and JAG metrics."""
    if not evaluation:
        return 0.0
    
    score = 0.0
    weights_sum = 0.0
    
    # Liking (0-10) → 60% weight
    liking = evaluation.get("liking")
    if liking is not None:
        try:
            normalized_liking = float(liking) / 10.0
            score += normalized_liking * 0.6
            weights_sum += 0.6
        except (ValueError, TypeError):
            pass
    
    # JAG metrics (1-5) → 40% weight
    jag = evaluation.get("jag", {})
    if isinstance(jag, dict):
        jag_keys = ["flavour_intensity", "acidity", "mouthfeel", "sweetness", "purchase_intent"]
        jag_values = []
        for key in jag_keys:
            val = jag.get(key)
            if val is not None:
                try:
                    normalized_val = (float(val) - 1.0) / 4.0
                    jag_values.append(normalized_val)
                except (ValueError, TypeError):
                    pass
        
        if jag_values:
            jag_avg = sum(jag_values) / len(jag_values)
            score += jag_avg * 0.4
            weights_sum += 0.4
    
    return score / weights_sum if weights_sum > 0 else 0.0


def _fetch_references_via_local_index(
    bean_info: Dict[str, Any],
    *,
    persist_dir: Path,
    k: int,
    use_evaluation_reranking: bool = True,
    similarity_weight: float = 0.7,
    retrieval_multiplier: int = 3,
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
    
    # Fetch more results if reranking is enabled
    n_fetch = k * retrieval_multiplier if use_evaluation_reranking else k
    
    response = collection.query(
        query_texts=[query_text],
        n_results=n_fetch,
        include=["metadatas", "documents", "distances"],
    )

    docs = response.get("documents", [[]])[0]
    metas = response.get("metadatas", [[]])[0]
    ids = response.get("ids", [[]])[0]
    distances = response.get("distances", [[]])[0]

    # Build candidates with combined scores
    candidates = []
    for doc, meta, record_id, dist in zip(docs, metas, ids, distances):
        brewing = extract_brewing(meta)
        evaluation = extract_evaluation(meta)
        
        # Compute combined score if reranking
        combined_score = None
        if use_evaluation_reranking:
            similarity_score = 1.0 / (1.0 + float(dist))
            eval_score = _compute_evaluation_score(evaluation)
            evaluation_weight = 1.0 - similarity_weight
            combined_score = (similarity_weight * similarity_score) + (evaluation_weight * eval_score)
        
        candidates.append({
            "id": record_id,
            "distance": float(dist),
            "bean_text": doc,
            "brewing": brewing,
            "evaluation": evaluation,
            "combined_score": combined_score,
        })
    
    # Rerank if enabled
    if use_evaluation_reranking:
        candidates.sort(key=lambda x: x["combined_score"], reverse=True)
    
    # Return top-k with final ranks
    references: List[Dict[str, Any]] = []
    for rank, candidate in enumerate(candidates[:k], start=1):
        reference = {
            "rank": rank,
            "id": candidate["id"],
            "distance": candidate["distance"],
            "bean_text": candidate["bean_text"],
            "brewing": candidate["brewing"],
            "evaluation": candidate["evaluation"],
            "combined_score": candidate["combined_score"],
        }
        references.append(reference)

    return references


def fetch_references(
    bean_info: Dict[str, Any],
    *,
    persist_dir: Optional[Path] = None,
    rag_service_url: Optional[str] = None,
    k: int = 3,
    user_id: Optional[str] = None,
    use_evaluation_reranking: bool = True,
    similarity_weight: float = 0.7,
    retrieval_multiplier: int = 3,
) -> List[Dict[str, Any]]:
    """
    Retrieve similar past brews using either a local ChromaDB index or a remote RAG service.
    
    Args:
        bean_info: Dictionary containing bean details
        persist_dir: Local ChromaDB directory (used if rag_service_url is None)
        rag_service_url: RAG service URL (if None, uses local index)
        k: Number of results to return
        user_id: User ID for multi-tenant RAG
        use_evaluation_reranking: Whether to rerank by evaluation scores (default: True)
        similarity_weight: Weight for similarity (0-1), evaluation_weight = 1 - similarity_weight (default: 0.7)
        retrieval_multiplier: Fetch k × multiplier results before reranking (default: 3)
    """
    if k <= 0:
        return []

    if rag_service_url:
        if not user_id:
             print("Warning: user_id not provided for RAG service call")
             return []
        return _fetch_references_via_service(
            bean_info,
            rag_service_url=rag_service_url,
            k=k,
            user_id=user_id,
            use_evaluation_reranking=use_evaluation_reranking,
            similarity_weight=similarity_weight,
            retrieval_multiplier=retrieval_multiplier,
        )

    return _fetch_references_via_local_index(
        bean_info,
        persist_dir=persist_dir or DEFAULT_RAG_PERSIST_DIR,
        k=k,
        use_evaluation_reranking=use_evaluation_reranking,
        similarity_weight=similarity_weight,
        retrieval_multiplier=retrieval_multiplier,
    )


@lru_cache(maxsize=1)
def _get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY is not set.")
    return OpenAI(api_key=api_key)


class Pour(BaseModel):
    start: int = Field(..., description="Start time in seconds")
    end: int = Field(..., description="End time in seconds")
    water_added: int = Field(..., description="Amount of water added in this step in grams")


class Brewing(BaseModel):
    brewer: str = Field(..., description="Name of the brewer (e.g., V60, April)")
    temperature: int = Field(..., description="Water temperature in Celsius")
    grinding_size: int = Field(..., description="Grind size (clicks)")
    dose: int = Field(..., description="Coffee dose in grams")
    target_water: int = Field(..., description="Total target water in grams")
    pours: List[Pour] = Field(..., description="List of pour steps")


class Recipe(BaseModel):
    brewing: Brewing = Field(..., description="Brewing details")


def generate_recipe(
    bean_info: Dict[str, Any],
    brewer: str,
    *,
    reference_recipes: Optional[List[Dict[str, Any]]] = None,
    custom_note: Optional[str] = None,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    top_p: float = 0.9,
) -> Dict[str, Any]:
    """
    Generate a pour-over recipe for the given bean and brewer.
    Optionally provide RAG reference recipes and a user custom note to steer the output.
    """
    client = _get_openai_client()
    
    system_prompt = (
        "You are an expert barista specializing in pour-over coffee. "
        "Your goal is to create a precise brewing recipe based on the bean's characteristics "
        "and any provided context."
    )
    
    user_content = f"Bean: {json.dumps(bean_info)}\nBrewer: {brewer}"
    
    if custom_note:
        user_content += f"\nUser Note: {custom_note}"
        
    if reference_recipes:
        refs_str = "\n".join([
            f"- {r.get('bean_text', '')} | Recipe: {json.dumps(r.get('brewing', {}))}"
            for r in reference_recipes
        ])
        user_content += f"\n\nSimilar Past Brews:\n{refs_str}\n\nUse these past brews as inspiration but adapt to the current bean."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            functions=[{
                "name": "generate_recipe",
                "description": "Generate a coffee brewing recipe",
                "parameters": Recipe.model_json_schema()
            }],
            function_call={"name": "generate_recipe"}
        )
        
        func_args = json.loads(completion.choices[0].message.function_call.arguments)
        return func_args
    except Exception as e:
        raise RuntimeError(f"OpenAI API error: {e}")


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


class BeanPayload(BaseModel):
    name: str = Field(..., min_length=1, description="Bean name.")
    origin: Optional[str] = Field(default=None, description="Origin or region.")
    process: Optional[str] = Field(default=None, description="Processing method.")
    variety: Optional[str] = Field(default=None, description="Variety or cultivar.")
    roasted_on: Optional[str] = Field(
        default=None,
        description="Roast date in ISO format (YYYY-MM-DD).",
    )
    roast_level: Optional[int] = Field(
        default=None,
        description="Roast level indicator, typically 0-5.",
    )
    roasted_days: Optional[int] = Field(
        default=None,
        description="Days since roast.",
    )
    altitude: Optional[int] = Field(
        default=None,
        description="Growing altitude in masl.",
    )
    flavor_notes: List[str] = Field(
        default_factory=list,
        description="Collection of flavor notes.",
    )


class BeanRecord(BeanPayload):
    bean_id: str
    created_at: str
    updated_at: str


class UserPreferences(BaseModel):
    flavor_notes: List[str] = Field(
        default_factory=list,
        description="Preferred flavor notes captured as free-form strings.",
    )
    roast_level: Optional[str] = Field(
        default=None,
        description="Preferred roast level descriptor.",
    )


class UserSummary(BaseModel):
    user_id: str
    email: EmailStr
    display_name: Optional[str]
    preferences: UserPreferences
    beans: List[BeanRecord]
    created_at: Optional[str]
    updated_at: Optional[str]


class AuthResponse(BaseModel):
    token: str
    user: UserSummary


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    display_name: Optional[str] = None
    preferences: Optional[UserPreferences] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class PreferencesUpdateRequest(BaseModel):
    flavor_notes: List[str] = Field(default_factory=list)
    roast_level: Optional[str] = None


class BeanCreateRequest(BaseModel):
    bean: BeanPayload


class BeanUpdateRequest(BaseModel):
    bean: BeanPayload


class BeansResponse(BaseModel):
    beans: List[BeanRecord]


class FeedbackRequest(BaseModel):
    bean: Dict[str, Any]
    recipe: Dict[str, Any]
    evaluation: Dict[str, Any]
    rag_persist_dir: Optional[str] = Field(
        default=None,
        description="Path to the local Chroma index.",
    )


def _pours_to_str(pours: Any) -> Optional[str]:
    if isinstance(pours, list) and pours and isinstance(pours[0], dict):
        return "; ".join(f"{p.get('start')}-{p.get('end')}:{p.get('water_added')}" for p in pours)
    return None


def _get_local_collection(persist_dir: Path):
    if chromadb is None or embedding_functions is None:
        raise RuntimeError("chromadb is not installed")
    
    persist_dir.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(persist_dir))
    embedding = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=RAG_MODEL
    )
    return client.get_or_create_collection(
        RAG_COLLECTION, embedding_function=embedding
    )


def brew_with_options(
    bean: Dict[str, Any],
    brewer: str,
    *,
    note: Optional[str] = None,
    rag_enabled: bool = True,
    rag_service_url: Optional[str] = None,
    rag_persist_dir: Optional[str] = None,
    rag_k: int = 3,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    top_p: float = 0.9,
    user_id: Optional[str] = None,
) -> BrewResponse:
    """
    Orchestrates the brewing process:
    1. Retrieve similar recipes (if RAG enabled)
    2. Generate new recipe using LLM
    """
    bean = _normalize_roast_fields(dict(bean))
    flavors = bean.get("flavor_notes")
    if isinstance(flavors, str):
        bean["flavor_notes"] = _clean_flavor_notes([note.strip() for note in flavors.split(",")])
    elif not isinstance(flavors, list):
        bean["flavor_notes"] = []
    else:
        bean["flavor_notes"] = _clean_flavor_notes(flavors)
    references: List[Dict[str, Any]] = []
    if rag_enabled:
        persist_path = Path(rag_persist_dir) if rag_persist_dir else None
        references = fetch_references(
            bean,
            persist_dir=persist_path,
            rag_service_url=rag_service_url,
            k=rag_k,
            user_id=user_id,
        )

    recipe = generate_recipe(
        bean,
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

_default_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
_configured_origins = os.getenv("FRONTEND_ORIGINS")
if _configured_origins:
    origins = [origin.strip() for origin in _configured_origins.split(",") if origin.strip()]
else:
    origins = _default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _load_store_on_startup() -> None:
    _load_user_store()


@app.post("/auth/register", response_model=AuthResponse)
def register_user(payload: RegisterRequest) -> AuthResponse:
    email_key = payload.email.lower()
    with _user_store_lock:
        if email_key in _email_index:
            raise HTTPException(status_code=409, detail="Email already registered.")
        user_id = str(uuid4())
        now = datetime.utcnow().isoformat()
        preferences = payload.preferences.dict() if payload.preferences else {}
        flavor_notes = _clean_flavor_notes(preferences.get("flavor_notes"))
        roast_level = preferences.get("roast_level")
        user_record = {
            "user_id": user_id,
            "email": payload.email,
            "display_name": payload.display_name or payload.email.split("@")[0],
            "password_hash": _hash_password(payload.password),
            "preferences": {
                "flavor_notes": flavor_notes,
                "roast_level": roast_level,
            },
            "beans": [],
            "created_at": now,
            "updated_at": now,
        }
        _user_store[user_id] = user_record
        _email_index[email_key] = user_id
        _email_index[email_key] = user_id
        _persist_user_store()

    # Initialize RAG collection for the new user
    rag_url = os.getenv("RAG_SERVICE_URL") or DEFAULT_RAG_SERVICE_URL
    if httpx and rag_url:
        try:
            # Fire-and-forget-ish: fail silently or log warning to not block registration
            # Use a short timeout
            with httpx.Client(base_url=rag_url, timeout=5.0) as client:
                client.post("/init_user", json={"user_id": user_id})
        except Exception as e:
            # Log but don't fail registration
            print(f"Warning: Failed to initialize RAG collection for {user_id}: {e}")
    token = _issue_token(user_id)
    return AuthResponse(token=token, user=UserSummary(**_user_to_public_payload(user_record)))


@app.post("/auth/login", response_model=AuthResponse)
def login_user(payload: LoginRequest) -> AuthResponse:
    email_key = payload.email.lower()
    with _user_store_lock:
        user_id = _email_index.get(email_key)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid credentials.")
        user_record = _user_store.get(user_id)
    if not user_record or user_record.get("password_hash") != _hash_password(payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    token = _issue_token(user_record["user_id"])
    return AuthResponse(token=token, user=UserSummary(**_user_to_public_payload(user_record)))


@app.get("/profile", response_model=UserSummary)
def get_profile(current_user: Dict[str, Any] = Depends(get_authenticated_user)) -> UserSummary:
    return UserSummary(**_user_to_public_payload(current_user))


@app.put("/profile/preferences", response_model=UserSummary)
def update_preferences(
    payload: PreferencesUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
) -> UserSummary:
    user_id = current_user["user_id"]
    flavor_notes = _clean_flavor_notes(payload.flavor_notes)
    with _user_store_lock:
        user_record = _user_store[user_id]
        user_record["preferences"] = {
            "flavor_notes": flavor_notes,
            "roast_level": payload.roast_level,
        }
        user_record["updated_at"] = datetime.utcnow().isoformat()
        _persist_user_store()
    return UserSummary(**_user_to_public_payload(user_record))


def _get_user_beans(user_record: Dict[str, Any]) -> List[Dict[str, Any]]:
    beans = user_record.setdefault("beans", [])
    return beans


@app.get("/beans", response_model=BeansResponse)
def list_beans(current_user: Dict[str, Any] = Depends(get_authenticated_user)) -> BeansResponse:
    beans = _get_user_beans(current_user)
    dirty = False
    formatted: List[Dict[str, Any]] = []
    for bean in beans:
        before = bean.get("roasted_days")
        _normalize_roast_fields(bean)
        if bean.get("roasted_days") != before:
            dirty = True
        formatted.append(_format_bean_record(bean))
    if dirty:
        current_user["updated_at"] = datetime.utcnow().isoformat()
        _persist_user_store()
    return BeansResponse(beans=formatted)


@app.post("/beans", response_model=BeanRecord, status_code=status.HTTP_201_CREATED)
def create_bean(
    payload: BeanCreateRequest,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
) -> BeanRecord:
    bean_data = payload.bean.dict()
    bean_data["flavor_notes"] = _clean_flavor_notes(bean_data.get("flavor_notes"))
    bean_data = _normalize_roast_fields(bean_data)
    bean_id = str(uuid4())
    now = datetime.utcnow().isoformat()
    bean_record = {
        **bean_data,
        "bean_id": bean_id,
        "created_at": now,
        "updated_at": now,
    }
    user_id = current_user["user_id"]
    with _user_store_lock:
        user_record = _user_store[user_id]
        beans = _get_user_beans(user_record)
        beans.append(bean_record)
        user_record["updated_at"] = now
        _persist_user_store()
    return BeanRecord(**_format_bean_record(bean_record))


@app.put("/beans/{bean_id}", response_model=BeanRecord)
def update_bean(
    bean_id: str,
    payload: BeanUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
) -> BeanRecord:
    bean_data = payload.bean.dict()
    bean_data["flavor_notes"] = _clean_flavor_notes(bean_data.get("flavor_notes"))
    bean_data = _normalize_roast_fields(bean_data)
    now = datetime.utcnow().isoformat()
    user_id = current_user["user_id"]
    with _user_store_lock:
        user_record = _user_store[user_id]
        beans = _get_user_beans(user_record)
        for bean in beans:
            if bean["bean_id"] == bean_id:
                bean.update(bean_data)
                bean["updated_at"] = now
                user_record["updated_at"] = now
                _persist_user_store()
                return BeanRecord(**_format_bean_record(bean))
    raise HTTPException(status_code=404, detail="Bean not found.")


@app.delete("/beans/{bean_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bean(
    bean_id: str,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
) -> None:
    user_id = current_user["user_id"]
    with _user_store_lock:
        user_record = _user_store[user_id]
        beans = _get_user_beans(user_record)
        remaining = [bean for bean in beans if bean["bean_id"] != bean_id]
        if len(remaining) == len(beans):
            raise HTTPException(status_code=404, detail="Bean not found.")
        user_record["beans"] = remaining
        user_record["updated_at"] = datetime.utcnow().isoformat()
        _persist_user_store()


@app.post("/brew", response_model=BrewResponse)
async def brew_endpoint(
    payload: BrewRequest,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
) -> BrewResponse:
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
            user_id=current_user["user_id"],
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


def _sanitize_meta(meta: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    def put(k, v):
        if isinstance(v, (str, int, float, bool)) or v is None:
            out[k] = v
        elif isinstance(v, list):
            if v and all(isinstance(x, dict) for x in v):
                for idx, d in enumerate(v):
                    for kk, vv in d.items():
                        put(f"{k}.{idx}.{kk}", vv)
            else:
                out[k] = ", ".join(map(str, v))
        elif isinstance(v, dict):
            for kk, vv in v.items():
                put(f"{k}.{kk}", vv)
        else:
            out[k] = str(v)
            
    for k, v in meta.items():
        put(k, v)
    return out


@app.post("/feedback", status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    payload: FeedbackRequest,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
) -> Dict[str, str]:
    try:
        bean_data = payload.bean
        recipe = payload.recipe
        brewing = recipe.get("brewing", recipe)
        evaluation = payload.evaluation
        
        combined = {
            "bean": bean_data,
            "brewing": brewing,
            "evaluation": evaluation
        }
        
        flat = flatten_dict(combined)
        
        pours = brewing.get("pours")
        if pours:
            flat["brewing.pours_str"] = _pours_to_str(pours)
            
        text = bean_text_from_obj(flat)
        
        rid_base = str(flat.get("id") or flat.get("uuid") or flat.get("bean.name") or "")
        rid = (rid_base if rid_base else "feedback") + "-" + str(abs(hash(text)))[-6:]
        
        sanitized_meta = _sanitize_meta(flat)
        
        rag_service_url = os.getenv("RAG_SERVICE_URL") or DEFAULT_RAG_SERVICE_URL
        if not rag_service_url:
             raise RuntimeError("RAG_SERVICE_URL is not configured")

        async with httpx.AsyncClient(base_url=rag_service_url, timeout=30.0) as client:
            response = await client.post("/feedback", json={
                "user_id": current_user["user_id"],
                "id": rid,
                "text": text,
                "meta": sanitized_meta
            })
            if response.status_code != 201:
                detail = response.text
                raise RuntimeError(f"RAG service returned an error ({response.status_code}): {detail}")
        
        return {"status": "ok", "id": rid}
        
    except Exception as exc:
        import traceback
        traceback.print_exc()
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
            "agent_core.agent:app",
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
