"""Unit tests for ingest module."""
import pandas as pd
from src.ingest import flatten, list_to_str, pours_to_str, bean_text, make_record


class TestIngestFlatten:
    """Test the flatten function in ingest module."""
    
    def test_flatten_simple(self):
        """Test flattening a simple dictionary."""
        d = {"a": 1, "b": 2}
        result = flatten(d)
        assert result == {"a": 1, "b": 2}
    
    def test_flatten_nested(self):
        """Test flattening nested dictionaries."""
        d = {"bean": {"name": "Ethiopian", "roast": "Light"}}
        result = flatten(d)
        assert result == {"bean.name": "Ethiopian", "bean.roast": "Light"}


class TestListToStr:
    """Test the list_to_str function."""
    
    def test_list_conversion(self):
        """Test converting list to string."""
        result = list_to_str(["citrus", "berry"])
        assert result == "citrus, berry"
    
    def test_non_list_passthrough(self):
        """Test that non-lists pass through."""
        result = list_to_str("already a string")
        assert result == "already a string"


class TestPoursToStr:
    """Test the pours_to_str function."""
    
    def test_valid_pours(self):
        """Test converting valid pours list."""
        pours = [
            {"start": "0:00", "end": "0:30", "water_added": 50},
            {"start": "0:45", "end": "1:15", "water_added": 100}
        ]
        result = pours_to_str(pours)
        assert "0:00-0:30:50" in result
        assert "0:45-1:15:100" in result
    
    def test_empty_pours(self):
        """Test with empty pours list."""
        result = pours_to_str([])
        assert result is None
    
    def test_non_list_pours(self):
        """Test with non-list input."""
        result = pours_to_str("not a list")
        assert result is None


class TestBeanText:
    """Test the bean_text function."""
    
    def test_bean_text_generation(self):
        """Test generating bean text from flat dict."""
        flat = {
            "bean.name": "Ethiopian Yirgacheffe",
            "bean.process": "Washed",
            "bean.roast_level": "Light"
        }
        result = bean_text(flat)
        assert "Ethiopian Yirgacheffe" in result
        assert "Washed" in result
        assert "Light" in result
    
    def test_bean_text_with_none_values(self):
        """Test bean text skips None values."""
        flat = {
            "bean.name": "Colombian",
            "bean.process": None,
            "bean.roast_level": "Medium"
        }
        result = bean_text(flat)
        assert "Colombian" in result
        assert "Medium" in result
        assert "None" not in result
    
    def test_bean_text_with_nan_values(self):
        """Test bean text skips NaN values."""
        flat = {
            "bean.name": "Kenya AA",
            "bean.altitude": pd.NA,
            "bean.roast_level": "Dark"
        }
        result = bean_text(flat)
        assert "Kenya AA" in result
        assert "Dark" in result


class TestMakeRecord:
    """Test the make_record function."""
    
    def test_make_record_basic(self):
        """Test creating a basic record."""
        obj = {
            "id": "test123",
            "bean": {
                "name": "Test Bean",
                "roast_level": "Medium"
            }
        }
        result = make_record(obj)
        assert "text" in result
        assert "meta" in result
        assert "id" in result
        assert result["id"].startswith("test123")
    
    def test_make_record_with_pours(self):
        """Test creating record with brewing pours."""
        obj = {
            "id": "test456",
            "bean": {"name": "Test Bean"},
            "brewing": {
                "pours": [
                    {"start": "0:00", "end": "0:30", "water_added": 50}
                ]
            }
        }
        result = make_record(obj)
        assert "meta" in result
        # Check that pours_str was created
        assert "brewing.pours_str" in result["meta"]
    
    def test_make_record_generates_text(self):
        """Test that make_record generates text field."""
        obj = {
            "bean": {
                "name": "Ethiopian Yirgacheffe",
                "process": "Washed"
            }
        }
        result = make_record(obj)
        assert "text" in result
        assert len(result["text"]) > 0
        assert "Ethiopian Yirgacheffe" in result["text"]
    
    def test_make_record_with_uuid(self):
        """Test creating record with UUID."""
        obj = {
            "uuid": "uuid-123",
            "bean": {"name": "Test Bean"}
        }
        result = make_record(obj)
        assert "id" in result
        assert "uuid-123" in result["id"]
    
    def test_make_record_complex(self):
        """Test creating record with complex data."""
        obj = {
            "id": "complex-test",
            "bean": {
                "name": "Ethiopian Yirgacheffe",
                "process": "Washed",
                "variety": "Heirloom",
                "region": "Yirgacheffe",
                "roast_level": "Light",
                "roasted_days": 7,
                "altitude": 1800,
                "flavor_notes": ["citrus", "floral", "tea"]
            },
            "brewing": {
                "brewer": "V60",
                "temperature": 93,
                "grinding_size": "Medium-fine",
                "dose": 15,
                "target_water": 240,
                "pours": [
                    {"start": "0:00", "end": "0:45", "water_added": 50},
                    {"start": "1:00", "end": "1:30", "water_added": 90},
                    {"start": "1:45", "end": "2:30", "water_added": 100}
                ]
            },
            "evaluation": {
                "liking": 9.0,
                "jag": {
                    "flavour_intensity": 5,
                    "acidity": 4,
                    "mouthfeel": 5,
                    "sweetness": 4,
                    "purchase_intent": 5
                }
            }
        }
        result = make_record(obj)
        assert "text" in result
        assert "meta" in result
        assert "id" in result
        assert "Ethiopian Yirgacheffe" in result["text"]
        assert "brewing.brewer" in result["meta"]
        assert result["meta"]["brewing.brewer"] == "V60"
        assert "evaluation.liking" in result["meta"]
        assert result["meta"]["evaluation.liking"] == 9.0
