"""Additional tests to raise backend coverage."""
import json
from typing import Any, Dict, List

import pytest

from fastapi import HTTPException
from src.index import sanitize_meta
from src.ingest import iter_json_any
from src.service import RagQuery, _build_query_text, _compute_evaluation_score, _run_query


class DummyCollection:
    """Simple stand-in for the ChromaDB collection API."""

    def __init__(self, response: Dict[str, List[List[Any]]]):
        self.response = response
        self.queries = []

    def query(self, **kwargs):
        self.queries.append(kwargs)
        return self.response


def test_sanitize_meta_handles_nested_and_list_data():
    """Ensure sanitize_meta flattens nested structures and preserves scalars."""
    meta = {
        "bean": {"name": "Test Bean", "origin": {"country": "Kenya"}},
        "scores": [1, 2, 3],
        "pours": [
            {"start": "0:00", "end": "0:30", "water": 40},
            {"start": "0:45", "end": "1:15", "water": 60},
        ],
        "misc": {"nested": {"value": 42}},
        "notes": ("citrus", "floral"),
    }

    result = sanitize_meta(meta)

    assert result["bean.name"] == "Test Bean"
    assert result["bean.origin.country"] == "Kenya"
    assert result["scores"] == "1, 2, 3"
    assert result["pours.0.start"] == "0:00"
    assert result["pours.1.end"] == "1:15"
    assert result["misc.nested.value"] == 42
    assert result["notes"] == "('citrus', 'floral')"


def test_iter_json_any_supports_multiple_input_formats(tmp_path):
    """Verify iter_json_any yields objects from JSON, JSONL, and concatenated JSON."""
    payload = [{"id": 1}, {"id": 2}]

    as_json = tmp_path / "records.json"
    as_json.write_text(json.dumps(payload), encoding="utf-8")
    assert list(iter_json_any(str(as_json))) == payload

    as_jsonl = tmp_path / "records.jsonl"
    as_jsonl.write_text("\n".join(json.dumps(obj) for obj in payload), encoding="utf-8")
    assert list(iter_json_any(str(as_jsonl))) == payload

    as_concat = tmp_path / "records_concat.json"
    pretty_objects = [json.dumps(obj, indent=2) for obj in payload]
    as_concat.write_text("\n".join(pretty_objects), encoding="utf-8")
    assert list(iter_json_any(str(as_concat))) == payload


def test_compute_evaluation_score_partial_metrics():
    """_compute_evaluation_score should blend liking and partial JAG data."""
    evaluation = {
        "liking": 8.0,
        "jag": {
            "acidity": 4,
            "sweetness": 5,
        },
    }
    score = _compute_evaluation_score(evaluation)
    assert 0.7 < score < 0.9  # normalized blend of liking and jag values


def test_build_query_text_prefers_structured_record():
    """_build_query_text should derive text from bean structures when available."""
    payload = RagQuery(record={"bean": {"name": "Kenya AA", "process": "Washed"}})
    query_text = _build_query_text(payload)
    assert "Kenya AA" in query_text
    assert "process" in query_text

    direct_payload = RagQuery(query="search me")
    assert _build_query_text(direct_payload) == "search me"

    with pytest.raises(HTTPException):
        _build_query_text(RagQuery())


def test_run_query_with_reranking_emphasizes_scores():
    """_run_query should sort by combined score when reranking is enabled."""
    response = {
        "documents": [["Bean 1 text", "Bean 2 text", "Bean 3 text"]],
        "metadatas": [[
            {
                "brewing.brewer": "V60",
                "evaluation.liking": 9,
                "evaluation.jag.flavour_intensity": 5,
            },
            {
                "brewing.brewer": "Kalita",
                "evaluation.liking": 5,
                "evaluation.jag.flavour_intensity": 2,
            },
            {
                "brewing.brewer": "Chemex",
                "evaluation.liking": 6,
                "evaluation.jag.flavour_intensity": 3,
            },
        ]],
        "ids": [["bean-1", "bean-2", "bean-3"]],
        "distances": [[0.2, 0.05, 1.0]],
    }
    collection = DummyCollection(response)

    results = _run_query(
        collection,
        query_text="citrus",
        k=2,
        use_evaluation_reranking=True,
        similarity_weight=0.5,
        retrieval_multiplier=2,
    )

    assert [r.id for r in results] == ["bean-1", "bean-2"]
    assert all(r.combined_score is not None for r in results)
    # ensure collection was asked for more than k results when reranking
    assert collection.queries[0]["n_results"] == 4


def test_run_query_without_reranking_preserves_order():
    """When reranking is disabled, combined_score should be None and order preserved."""
    response = {
        "documents": [["doc A", "doc B"]],
        "metadatas": [[{"brewing.brewer": "Origami"}, {"brewing.brewer": "Flatbed"}]],
        "ids": [["A", "B"]],
        "distances": [[0.3, 0.6]],
    }
    collection = DummyCollection(response)

    results = _run_query(
        collection,
        query_text="berry",
        k=2,
        use_evaluation_reranking=False,
        similarity_weight=0.8,
        retrieval_multiplier=1,
    )

    assert [r.id for r in results] == ["A", "B"]
    assert all(r.combined_score is None for r in results)
