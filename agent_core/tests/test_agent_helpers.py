"""Unit tests for agent helper functions."""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agent_core import agent


@pytest.mark.unit
class TestHelperFunctions:
    """Test helper utility functions."""
    
    def test_load_bean_info_from_string(self):
        """Test loading bean info from JSON string."""
        bean_json = '{"name": "Test Bean", "origin": "Ethiopia"}'
        result = agent.load_bean_info(bean_json)
        assert result["name"] == "Test Bean"
        assert result["origin"] == "Ethiopia"
    
    def test_load_bean_info_from_file(self, tmp_path):
        """Test loading bean info from file."""
        bean_file = tmp_path / "bean.json"
        bean_data = {"name": "File Bean", "origin": "Colombia"}
        bean_file.write_text(json.dumps(bean_data))
        
        result = agent.load_bean_info(str(bean_file))
        assert result["name"] == "File Bean"
        assert result["origin"] == "Colombia"
    
    def test_clean_json_payload_with_markdown(self):
        """Test cleaning JSON payload with markdown fences."""
        payload = "```json\n{\"name\": \"Test\"}\n```"
        cleaned = agent.clean_json_payload(payload)
        assert cleaned == '{"name": "Test"}'
    
    def test_clean_json_payload_without_markdown(self):
        """Test cleaning JSON payload without markdown."""
        payload = '{"name": "Test"}'
        cleaned = agent.clean_json_payload(payload)
        assert cleaned == '{"name": "Test"}'
    
    def test_flatten_dict_simple(self):
        """Test flattening simple dictionary."""
        data = {"a": 1, "b": 2}
        result = agent.flatten_dict(data)
        assert result == {"a": 1, "b": 2}
    
    def test_flatten_dict_nested(self):
        """Test flattening nested dictionary."""
        data = {"a": 1, "b": {"c": 2, "d": 3}}
        result = agent.flatten_dict(data)
        assert result == {"a": 1, "b.c": 2, "b.d": 3}
    
    def test_bean_text_from_obj_simple(self):
        """Test generating bean text from simple object."""
        obj = {
            "bean": {
                "name": "Test Bean",
                "origin": "Ethiopia",
                "process": "Washed"
            }
        }
        text = agent.bean_text_from_obj(obj)
        # Should contain at least one of the bean fields
        assert len(text) > 0
        assert "Test Bean" in text or "Ethiopia" in text or "Washed" in text
    
    def test_bean_text_from_obj_nested(self):
        """Test generating bean text from nested object."""
        obj = {
            "bean": {
                "name": "Nested Bean",
                "origin": "Colombia"
            }
        }
        text = agent.bean_text_from_obj(obj)
        assert "Nested Bean" in text
        assert "Colombia" in text
    
    def test_normalize_recipe_top_level_brewing(self):
        """Test normalizing recipe with top-level brewing fields."""
        recipe = {
            "brewer": "V60",
            "temperature": 92,
            "grinding_size": 22,
            "dose": 18,
            "target_water": 288,
            "pours": []
        }
        result = agent.normalize_recipe(recipe)
        assert "brewing" in result
        assert result["brewing"]["brewer"] == "V60"
    
    def test_normalize_recipe_nested_brewing(self):
        """Test normalizing recipe with nested brewing."""
        recipe = {
            "brewing": {
                "brewer": "April",
                "temperature": 93
            }
        }
        result = agent.normalize_recipe(recipe)
        assert result["brewing"]["brewer"] == "April"
    
    def test_validate_recipe_valid(self):
        """Test validating a valid recipe."""
        recipe = {
            "brewing": {
                "brewer": "V60",
                "temperature": 92,
                "grinding_size": 22,
                "dose": 18,
                "target_water": 288,
                "pours": [{"start": 0, "end": 30, "water_added": 288}]
            }
        }
        # Should not raise
        agent.validate_recipe(recipe)
    
    def test_validate_recipe_invalid_brewer(self):
        """Test validating recipe with invalid brewer."""
        recipe = {
            "brewing": {
                "brewer": "InvalidBrewer",
                "temperature": 92,
                "dose": 18,
                "target_water": 288,
                "pours": []
            }
        }
        with pytest.raises(ValueError):
            agent.validate_recipe(recipe)
    
    def test_compute_evaluation_score_with_liking(self):
        """Test computing evaluation score with liking."""
        evaluation = {"liking": 8}
        score = agent._compute_evaluation_score(evaluation)
        assert 0.0 < score <= 1.0
    
    def test_compute_evaluation_score_with_jag(self):
        """Test computing evaluation score with JAG metrics."""
        evaluation = {
            "jag": {
                "acidity": 7,
                "body": 6,
                "sweetness": 8
            }
        }
        score = agent._compute_evaluation_score(evaluation)
        # Score should be normalized (0-1 range)
        assert score >= 0.0
        # JAG scores are averaged and normalized, so should be reasonable
        assert isinstance(score, float)
    
    def test_compute_evaluation_score_empty(self):
        """Test computing evaluation score with empty evaluation."""
        score = agent._compute_evaluation_score(None)
        assert score == 0.0
    
    def test_fetch_references_with_service_url(self, monkeypatch):
        """Test fetching references via service URL."""
        mock_response = {
            "results": [
                {
                    "rank": 1,
                    "id": "test-id",
                    "distance": 0.5,
                    "bean_text": "Test Bean",
                    "brewing": {"brewer": "V60"},
                    "evaluation": {"liking": 8}
                }
            ]
        }
        
        def mock_post(*args, **kwargs):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response
            mock_resp.text = ""
            return mock_resp
        
        with patch("agent_core.agent.httpx") as mock_httpx:
            mock_httpx.Client.return_value.__enter__.return_value.post = mock_post
            mock_httpx.Client.return_value.__exit__ = lambda *args: None
            
            bean_info = {"name": "Test Bean"}
            results = agent._fetch_references_via_service(
                bean_info,
                rag_service_url="https://example.com",
                k=1,
                user_id="test-user"
            )
            assert len(results) == 1
            assert results[0]["id"] == "test-id"
    
    def test_fetch_references_no_httpx(self):
        """Test that fetch_references raises error when httpx not available."""
        with patch("agent_core.agent.httpx", None):
            with pytest.raises(RuntimeError, match="httpx is not installed"):
                agent._fetch_references_via_service(
                    {"name": "Test"},
                    rag_service_url="https://example.com",
                    k=1,
                    user_id="test-user"
                )

