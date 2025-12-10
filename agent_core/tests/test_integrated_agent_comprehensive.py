"""Comprehensive integration tests for IntegratedCoffeeAgent."""
from unittest.mock import MagicMock, patch

import pytest

from agent_core.integrated_agent import IntegratedCoffeeAgent
from agent_core.agent import fetch_references, generate_recipe


@pytest.mark.integration
class TestIntegratedAgent:
    """Integration tests for IntegratedCoffeeAgent."""
    
    def test_initialization_default(self):
        """Test agent initialization with default parameters."""
        agent = IntegratedCoffeeAgent()
        assert agent.rag_enabled is True
        assert agent.rag_k == 3
        assert agent.viz_agent is not None
    
    def test_initialization_custom(self):
        """Test agent initialization with custom parameters."""
        agent = IntegratedCoffeeAgent(
            rag_enabled=False,
            rag_k=5
        )
        assert agent.rag_enabled is False
        assert agent.rag_k == 5
    
    @patch('agent_core.integrated_agent.fetch_references')
    @patch('agent_core.integrated_agent.generate_recipe')
    def test_generate_complete_recipe_with_rag(self, mock_generate, mock_fetch):
        """Test generating complete recipe with RAG enabled."""
        # Setup mocks
        mock_fetch.return_value = [
            {"rank": 1, "bean_text": "Reference Bean", "brewing": {"brewer": "V60"}}
        ]
        mock_generate.return_value = {
            "brewing": {
                "brewer": "V60",
                "temperature": 92,
                "dose": 18,
                "target_water": 288,
                "pours": [{"start": 0, "end": 30, "water_added": 288}]
            }
        }
        
        agent = IntegratedCoffeeAgent(rag_enabled=True)
        bean_info = {"name": "Test Bean", "origin": "Ethiopia"}
        
        result = agent.generate_complete_recipe(bean_info, "V60")
        
        assert "bean" in result
        assert "brewing" in result
        assert result["brewing"]["brewer"] == "V60"
        mock_fetch.assert_called_once()
        mock_generate.assert_called_once()
    
    @patch('agent_core.integrated_agent.fetch_references')
    @patch('agent_core.integrated_agent.generate_recipe')
    def test_generate_complete_recipe_without_rag(self, mock_generate, mock_fetch):
        """Test generating complete recipe with RAG disabled."""
        mock_generate.return_value = {
            "brewing": {
                "brewer": "April",
                "temperature": 93,
                "dose": 16,
                "target_water": 240,
                "pours": [{"start": 0, "end": 40, "water_added": 240}]
            }
        }
        
        agent = IntegratedCoffeeAgent(rag_enabled=False)
        bean_info = {"name": "No RAG Bean", "origin": "Colombia"}
        
        result = agent.generate_complete_recipe(bean_info, "April")
        
        assert "brewing" in result
        mock_fetch.assert_not_called()
        mock_generate.assert_called_once()
    
    @patch('agent_core.integrated_agent.fetch_references')
    @patch('agent_core.integrated_agent.generate_recipe')
    def test_generate_complete_recipe_rag_failure_handling(self, mock_generate, mock_fetch):
        """Test that RAG failures are handled gracefully."""
        mock_fetch.side_effect = Exception("RAG service unavailable")
        mock_generate.return_value = {
            "brewing": {
                "brewer": "V60",
                "temperature": 92,
                "grinding_size": 22,
                "dose": 18,
                "target_water": 288,
                "pours": [{"start": 0, "end": 30, "water_added": 288}]
            }
        }
        
        agent = IntegratedCoffeeAgent(rag_enabled=True)
        bean_info = {"name": "Test Bean"}
        
        # Should not raise, should continue without references
        result = agent.generate_complete_recipe(bean_info, "V60")
        assert "brewing" in result
    
    def test_visualize_recipe(self):
        """Test recipe visualization."""
        agent = IntegratedCoffeeAgent()
        recipe = {
            "bean": {
                "name": "Test Bean",
                "flavor_notes": ["fruity", "citrus"]
            },
            "brewing": {
                "brewer": "V60",
                "temperature": 92,
                "grinding_size": 22,
                "dose": 18,
                "target_water": 288,
                "pours": [
                    {"start": 0, "end": 30, "water_added": 100},
                    {"start": 30, "end": 60, "water_added": 100},
                    {"start": 60, "end": 90, "water_added": 88}
                ]
            }
        }
        
        result = agent.visualize_recipe(recipe, output_formats=["html", "ascii"])
        assert isinstance(result, dict)
        # Visualization agent should return some format
        assert len(result) > 0
    
    def test_visualize_recipe_all_formats(self):
        """Test recipe visualization with all formats."""
        agent = IntegratedCoffeeAgent()
        recipe = {
            "bean": {
                "name": "Test Bean",
                "flavor_notes": ["chocolate", "caramel"]
            },
            "brewing": {
                "brewer": "V60",
                "temperature": 92,
                "grinding_size": 22,
                "dose": 18,
                "target_water": 288,
                "pours": [{"start": 0, "end": 30, "water_added": 288}]
            }
        }
        
        result = agent.visualize_recipe(recipe, output_formats=["html", "mermaid", "ascii"])
        assert isinstance(result, dict)

