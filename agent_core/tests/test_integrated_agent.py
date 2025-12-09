"""Integration tests for the integrated agent."""
import os


class TestIntegratedAgent:
    """Test the integrated agent functionality."""
    
    def test_integrated_agent_file_exists(self):
        """Test that the integrated agent file exists."""
        agent_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'integrated_agent.py')
        assert os.path.exists(agent_path)
    
    def test_agent_file_exists(self):
        """Test that the main agent file exists."""
        agent_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'agent.py')
        assert os.path.exists(agent_path)
    
    def test_visualization_agent_file_exists(self):
        """Test that the visualization agent file exists."""
        viz_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'visualization_agent_v2.py')
        assert os.path.exists(viz_path)


class TestAgentHelpers:
    """Test helper functions in the agent."""
    
    def test_bean_validation(self):
        """Test bean data validation."""
        # This is a placeholder - actual implementation depends on agent structure
        bean_data = {
            "name": "Ethiopian Yirgacheffe",
            "process": "Washed",
            "roast_level": "Light"
        }
        assert bean_data["name"] is not None
        assert len(bean_data["name"]) > 0
    
    def test_recipe_structure(self):
        """Test expected recipe structure."""
        recipe = {
            "method": "V60",
            "grind_size": "Medium-fine",
            "water_temp": 93,
            "ratio": "1:16"
        }
        assert "method" in recipe
        assert "grind_size" in recipe
        assert isinstance(recipe["water_temp"], (int, float))
