"""Behavioral tests exercising the agent_core logic helpers."""
from types import SimpleNamespace

import json
import pytest
from fastapi import HTTPException

from agent_core import agent


def test_compute_and_normalize_roast_days(monkeypatch):
    class FixedDatetime(agent.datetime):  # type: ignore[attr-defined]
        @classmethod
        def utcnow(cls):
            return cls(2024, 6, 20, 0, 0, 0)

    monkeypatch.setattr(agent, "datetime", FixedDatetime)

    assert agent._compute_roasted_days("2024-06-18") == 2
    assert agent._compute_roasted_days("bad-date") is None

    bean = {"bean_id": "b1", "roasted_on": "2024-06-18", "roasted_days": None}
    normalized = agent._normalize_roast_fields(bean.copy())
    assert normalized["roasted_days"] == 2


def test_clean_payload_and_flatten_dict():
    payload = "```json\n{\"hello\": \"world\"}\n```"
    assert agent.clean_json_payload(payload) == '{"hello": "world"}'

    nested = {"bean": {"name": "Ethiopia", "flavor": {"primary": "citrus"}}}
    flat = agent.flatten_dict(nested)
    assert flat["bean.name"] == "Ethiopia"
    assert flat["bean.flavor.primary"] == "citrus"

    bean_text = agent.bean_text_from_obj({"bean": nested["bean"]})
    assert "bean.name: Ethiopia" in bean_text


def test_reconstruct_extract_and_evaluation_helpers():
    meta = {
        "brewing.brewer": "V60",
        "brewing.temperature": 94,
        "brewing.pours.0.start": 0,
        "brewing.pours.0.end": 30,
        "brewing.pours.0.water_added": 60,
        "brewing.pours.1.start": 30,
        "brewing.pours.1.end": 60,
        "brewing.pours.1.water_added": 140,
        "evaluation.liking": 8,
        "evaluation.jag.flavour_intensity": 4,
    }

    pours = agent.reconstruct_pours(meta)
    assert len(pours) == 2
    brewing = agent.extract_brewing(meta)
    assert brewing["brewer"] == "V60"
    assert brewing["pours"][0]["water_added"] == 60

    evaluation = agent.extract_evaluation(meta)
    assert evaluation["liking"] == 8
    assert evaluation["jag"]["flavour_intensity"] == 4
    assert 0 < agent._compute_evaluation_score(evaluation) < 1


def test_clean_flavor_notes_and_format_record():
    notes = [" citrus ", None, ""]  # type: ignore[list-item]
    assert agent._clean_flavor_notes(notes) == ["citrus"]

    bean = {
        "bean_id": "b42",
        "name": "Kenya",
        "roasted_on": "2024-06-01",
        "roasted_days": 5,
    }
    formatted = agent._format_bean_record(bean)
    assert formatted["bean_id"] == "b42"
    assert formatted["name"] == "Kenya"


def test_load_bean_info_from_path(tmp_path):
    payload = {"bean": {"name": "Panama"}}
    bean_file = tmp_path / "bean.json"
    bean_file.write_text(json.dumps(payload), encoding="utf-8")

    assert agent.load_bean_info(str(bean_file)) == payload
    assert agent.load_bean_info(json.dumps(payload)) == payload


def test_generate_recipe_uses_mocked_openai(monkeypatch):
    recipe_payload = {
        "brewing": {
            "brewer": "V60",
            "temperature": 92,
            "grinding_size": 22,
            "dose": 18,
            "target_water": 288,
            "pours": [{"start": 0, "end": 30, "water_added": 288}],
        }
    }
    func_args_json = json.dumps(recipe_payload)

    class DummyClient:
        def __init__(self):
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(
                    create=lambda **kwargs: SimpleNamespace(
                        choices=[SimpleNamespace(
                            message=SimpleNamespace(
                                function_call=SimpleNamespace(arguments=func_args_json)
                            )
                        )]
                    )
                )
            )

    monkeypatch.setattr(agent, "_get_openai_client", lambda: DummyClient())

    result = agent.generate_recipe({"name": "Test Bean"}, "V60", reference_recipes=[{"rank": 1}])
    assert result["brewing"]["brewer"] == "V60"
    assert result["brewing"]["target_water"] == 288


def test_normalize_and_validate_recipe():
    recipe = {
        "brewing": {
            "brewer": "April",
            "temperature": 93,
            "grinding_size": 20,
            "dose": 16,
            "target_water": 240,
            "pours": [{"start": 0, "end": 40, "water_added": 240}],
        }
    }
    normalized = agent.normalize_recipe(recipe)
    assert normalized["brewing"]["brewer"] == "April"

    agent.validate_recipe(recipe)

    invalid = {
        "brewing": {
            "brewer": "",
            "target_water": 200,
            "pours": [{"start": 0, "end": 30, "water_added": 150}],
        }
    }
    with pytest.raises(ValueError):
        agent.validate_recipe(invalid)


def test_authentication_helpers(monkeypatch):
    dummy_user = {"user_id": "user-1", "email": "owner@example.com", "beans": []}
    monkeypatch.setattr(agent, "_active_tokens", {"token-abc": "user-1"})
    monkeypatch.setattr(agent, "_user_store", {"user-1": dummy_user})

    assert agent._require_authenticated_user("token-abc") == dummy_user
    with pytest.raises(HTTPException):
        agent._require_authenticated_user("missing")

    result = agent.get_authenticated_user(x_auth_token="token-abc")
    assert result == dummy_user


def test_query_reference_routing(monkeypatch, tmp_path):
    service_calls = []
    local_calls = []

    def fake_service(*args, **kwargs):
        service_calls.append((args, kwargs))
        return [{"id": "service"}]

    def fake_local(*args, **kwargs):
        local_calls.append((args, kwargs))
        return [{"id": "local"}]

    monkeypatch.setattr(agent, "_fetch_references_via_service", fake_service)
    monkeypatch.setattr(agent, "_fetch_references_via_local_index", fake_local)

    bean = {"bean": {"name": "Test"}}
    assert agent.query_reference_recipes(bean, rag_service_url="https://example.com", k=2, user_id="test-user")[0]["id"] == "service"
    assert service_calls

    assert agent.query_reference_recipes(bean, rag_service_url=None, persist_dir=tmp_path, k=1)[0]["id"] == "local"
    assert local_calls

    assert agent.query_reference_recipes(bean, rag_service_url=None, persist_dir=tmp_path, k=0) == []


def test_user_payload_conversion(monkeypatch):
    user = {
        "user_id": "user-99",
        "email": "bean@example.com",
        "preferences": {"flavor_notes": ["citrus"]},
        "beans": [
            {
                "bean_id": "b1",
                "name": "Kenya",
                "origin": "Nyeri",
                "roast_level": 2,
                "roasted_on": "2024-05-20",
                "roasted_days": 5,
                "flavor_notes": ["berry"],
                "created_at": "2024-05-21",
                "updated_at": "2024-05-22",
            }
        ],
        "created_at": "2024-05-21",
        "updated_at": "2024-05-22",
    }
    public_payload = agent._user_to_public_payload(user)
    assert public_payload["user_id"] == "user-99"
    assert public_payload["beans"][0]["name"] == "Kenya"
