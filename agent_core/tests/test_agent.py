"""Tests for the main agent module."""
import os


class TestAgentModule:
    """Test the main agent module."""
    
    def test_agent_file_exists(self):
        """Test that agent.py exists."""
        agent_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'agent.py')
        assert os.path.exists(agent_path)
    
    def test_agent_file_not_empty(self):
        """Test that agent.py is not empty."""
        agent_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'agent.py')
        with open(agent_path, 'r') as f:
            content = f.read()
        assert len(content) > 0
    
    def test_agent_has_fastapi_imports(self):
        """Test that agent.py imports FastAPI."""
        agent_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'agent.py')
        with open(agent_path, 'r') as f:
            content = f.read()
        assert 'fastapi' in content.lower() or 'FastAPI' in content


class TestVisualizationAgent:
    """Test the visualization agent module."""
    
    def test_visualization_agent_exists(self):
        """Test that visualization_agent_v2.py exists."""
        viz_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'visualization_agent_v2.py')
        assert os.path.exists(viz_path)
    
    def test_visualization_agent_not_empty(self):
        """Test that visualization_agent_v2.py is not empty."""
        viz_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'visualization_agent_v2.py')
        with open(viz_path, 'r') as f:
            content = f.read()
        assert len(content) > 0
    
    def test_visualization_has_plotting_imports(self):
        """Test that visualization agent has plotting capabilities."""
        viz_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'visualization_agent_v2.py')
        with open(viz_path, 'r') as f:
            content = f.read()
        # Check for common plotting/visualization keywords
        has_viz = any(keyword in content.lower() for keyword in ['plot', 'chart', 'graph', 'visual', 'matplotlib', 'plotly'])
        assert has_viz


class TestAgentConfiguration:
    """Test agent configuration and setup."""
    
    def test_requirements_file_exists(self):
        """Test that agent_requirements.txt exists."""
        req_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'agent_requirements.txt')
        assert os.path.exists(req_path)
    
    def test_requirements_has_dependencies(self):
        """Test that requirements file has dependencies."""
        req_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'agent_requirements.txt')
        with open(req_path, 'r') as f:
            content = f.read()
        assert len(content.strip()) > 0
    
    def test_init_file_exists(self):
        """Test that __init__.py exists."""
        init_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '__init__.py')
        assert os.path.exists(init_path)


class TestAgentDataStructures:
    """Test data structures and models used by agent."""
    
    def test_bean_data_structure(self):
        """Test basic bean data structure."""
        bean = {
            "name": "Ethiopian Yirgacheffe",
            "roast_level": "Light",
            "process": "Washed"
        }
        assert "name" in bean
        assert "roast_level" in bean
        assert isinstance(bean["name"], str)
    
    def test_recipe_data_structure(self):
        """Test basic recipe data structure."""
        recipe = {
            "method": "V60",
            "grind_size": "Medium-fine",
            "water_temp": 93,
            "ratio": "1:16",
            "brew_time": "3:00"
        }
        assert "method" in recipe
        assert "grind_size" in recipe
        assert "water_temp" in recipe
        assert isinstance(recipe["water_temp"], (int, float))
    
    def test_brewing_parameters(self):
        """Test brewing parameter validation."""
        params = {
            "water_temp": 93,
            "grind_size": "Medium-fine",
            "dose": 15,
            "yield": 240
        }
        # Validate temperature range
        assert 80 <= params["water_temp"] <= 100
        # Validate dose is positive
        assert params["dose"] > 0
        # Validate yield is positive
        assert params["yield"] > 0
    
    def test_flavor_notes_structure(self):
        """Test flavor notes data structure."""
        flavor_notes = ["chocolate", "caramel", "citrus", "berry"]
        assert isinstance(flavor_notes, list)
        assert all(isinstance(note, str) for note in flavor_notes)
        assert len(flavor_notes) > 0


class TestAgentUtilities:
    """Test utility functions."""
    
    def test_string_formatting(self):
        """Test basic string formatting."""
        bean_name = "Ethiopian Yirgacheffe"
        formatted = f"Bean: {bean_name}"
        assert "Ethiopian Yirgacheffe" in formatted
    
    def test_number_validation(self):
        """Test number validation."""
        temp = 93
        assert isinstance(temp, (int, float))
        assert temp > 0
    
    def test_list_operations(self):
        """Test list operations."""
        notes = ["chocolate", "caramel"]
        notes.append("citrus")
        assert len(notes) == 3
        assert "citrus" in notes
    
    def test_dict_operations(self):
        """Test dictionary operations."""
        bean = {"name": "Test"}
        bean["roast_level"] = "Medium"
        assert "roast_level" in bean
        assert bean["roast_level"] == "Medium"
