"""Unit tests for query module."""
from src.query import flatten, list_to_str, bean_text_from_obj, reconstruct_pours


class TestFlatten:
    """Test the flatten function."""
    
    def test_flatten_simple_dict(self):
        """Test flattening a simple dictionary."""
        d = {"a": 1, "b": 2}
        result = flatten(d)
        assert result == {"a": 1, "b": 2}
    
    def test_flatten_nested_dict(self):
        """Test flattening a nested dictionary."""
        d = {"a": {"b": 1, "c": 2}, "d": 3}
        result = flatten(d)
        assert result == {"a.b": 1, "a.c": 2, "d": 3}
    
    def test_flatten_deeply_nested(self):
        """Test flattening a deeply nested dictionary."""
        d = {"a": {"b": {"c": 1}}}
        result = flatten(d)
        assert result == {"a.b.c": 1}
    
    def test_flatten_empty_dict(self):
        """Test flattening an empty dictionary."""
        result = flatten({})
        assert result == {}


class TestListToStr:
    """Test the list_to_str function."""
    
    def test_list_conversion(self):
        """Test converting a list to string."""
        result = list_to_str([1, 2, 3])
        assert result == "1, 2, 3"
    
    def test_string_passthrough(self):
        """Test that strings pass through unchanged."""
        result = list_to_str("hello")
        assert result == "hello"
    
    def test_empty_list(self):
        """Test converting an empty list."""
        result = list_to_str([])
        assert result == ""


class TestBeanTextFromObj:
    """Test the bean_text_from_obj function."""
    
    def test_simple_bean_object(self):
        """Test converting a simple bean object to text."""
        obj = {
            "bean.name": "Ethiopian Yirgacheffe",
            "bean.process": "Washed",
            "bean.roast_level": "Light"
        }
        result = bean_text_from_obj(obj)
        assert "Ethiopian Yirgacheffe" in result
        assert "Washed" in result
        assert "Light" in result
    
    def test_nested_bean_object(self):
        """Test converting a nested bean object to text."""
        obj = {
            "bean": {
                "name": "Colombian Supremo",
                "process": "Natural",
                "roast_level": "Medium"
            }
        }
        result = bean_text_from_obj(obj)
        assert "Colombian Supremo" in result
    
    def test_empty_object(self):
        """Test converting an empty object."""
        result = bean_text_from_obj({})
        assert result == ""
    
    def test_with_flavor_notes_list(self):
        """Test bean object with flavor notes as a list."""
        obj = {
            "bean.name": "Kenya AA",
            "bean.flavor_notes": ["citrus", "berry", "chocolate"]
        }
        result = bean_text_from_obj(obj)
        assert "Kenya AA" in result
        assert "citrus, berry, chocolate" in result


class TestReconstructPours:
    """Test the reconstruct_pours function."""
    
    def test_single_pour(self):
        """Test reconstructing a single pour."""
        meta = {
            "brewing.pours.0.start": "0:00",
            "brewing.pours.0.end": "0:30",
            "brewing.pours.0.water_added": 50
        }
        result = reconstruct_pours(meta)
        assert len(result) == 1
        assert result[0]["start"] == "0:00"
        assert result[0]["end"] == "0:30"
        assert result[0]["water_added"] == 50
    
    def test_multiple_pours(self):
        """Test reconstructing multiple pours."""
        meta = {
            "brewing.pours.0.start": "0:00",
            "brewing.pours.0.end": "0:30",
            "brewing.pours.0.water_added": 50,
            "brewing.pours.1.start": "0:45",
            "brewing.pours.1.end": "1:15",
            "brewing.pours.1.water_added": 100
        }
        result = reconstruct_pours(meta)
        assert len(result) == 2
        assert result[0]["water_added"] == 50
        assert result[1]["water_added"] == 100
    
    def test_no_pours(self):
        """Test with no pour data."""
        meta = {"other.key": "value"}
        result = reconstruct_pours(meta)
        assert result == []
    
    def test_non_sequential_pours(self):
        """Test pours with non-sequential indices."""
        meta = {
            "brewing.pours.0.start": "0:00",
            "brewing.pours.2.start": "1:00",
            "brewing.pours.1.start": "0:30"
        }
        result = reconstruct_pours(meta)
        assert len(result) == 3
        # Should be sorted by index
        assert result[0]["start"] == "0:00"
        assert result[1]["start"] == "0:30"
        assert result[2]["start"] == "1:00"


class TestExtractBrewing:
    """Test the extract_brewing function."""
    
    def test_extract_brewing_basic(self):
        """Test extracting basic brewing data."""
        from src.query import extract_brewing
        meta = {
            "brewing.brewer": "V60",
            "brewing.temperature": 93,
            "brewing.grinding_size": "Medium-fine",
            "brewing.dose": 15,
            "brewing.target_water": 240
        }
        result = extract_brewing(meta)
        assert result["brewer"] == "V60"
        assert result["temperature"] == 93
        assert result["grinding_size"] == "Medium-fine"
        assert result["dose"] == 15
        assert result["target_water"] == 240
    
    def test_extract_brewing_with_pours(self):
        """Test extracting brewing data with pours."""
        from src.query import extract_brewing
        meta = {
            "brewing.brewer": "V60",
            "brewing.pours.0.start": "0:00",
            "brewing.pours.0.end": "0:30",
            "brewing.pours.0.water_added": 50
        }
        result = extract_brewing(meta)
        assert result["brewer"] == "V60"
        assert result["pours"] is not None


class TestExtractEvaluation:
    """Test the extract_evaluation function."""
    
    def test_extract_evaluation_with_liking(self):
        """Test extracting evaluation with liking score."""
        from src.query import extract_evaluation
        meta = {
            "evaluation.liking": 8.5
        }
        result = extract_evaluation(meta)
        assert result is not None
        assert result["liking"] == 8.5
    
    def test_extract_evaluation_with_jag(self):
        """Test extracting evaluation with JAG metrics."""
        from src.query import extract_evaluation
        meta = {
            "evaluation.jag.flavour_intensity": 4,
            "evaluation.jag.acidity": 3,
            "evaluation.jag.mouthfeel": 5
        }
        result = extract_evaluation(meta)
        assert result is not None
        assert "jag" in result
        assert result["jag"]["flavour_intensity"] == 4
        assert result["jag"]["acidity"] == 3
    
    def test_extract_evaluation_empty(self):
        """Test extracting evaluation with no data."""
        from src.query import extract_evaluation
        meta = {}
        result = extract_evaluation(meta)
        assert result is None


class TestComputeEvaluationScore:
    """Test the compute_evaluation_score function."""
    
    def test_compute_score_with_liking(self):
        """Test computing score with liking only."""
        from src.query import compute_evaluation_score
        evaluation = {"liking": 8.0}
        score = compute_evaluation_score(evaluation)
        assert 0 <= score <= 1
        assert score > 0
    
    def test_compute_score_with_jag(self):
        """Test computing score with JAG metrics."""
        from src.query import compute_evaluation_score
        evaluation = {
            "jag": {
                "flavour_intensity": 4,
                "acidity": 3,
                "mouthfeel": 5
            }
        }
        score = compute_evaluation_score(evaluation)
        assert 0 <= score <= 1
    
    def test_compute_score_combined(self):
        """Test computing score with both liking and JAG."""
        from src.query import compute_evaluation_score
        evaluation = {
            "liking": 9.0,
            "jag": {
                "flavour_intensity": 5,
                "acidity": 4,
                "sweetness": 5
            }
        }
        score = compute_evaluation_score(evaluation)
        assert 0 <= score <= 1
        assert score > 0.5  # Should be high with good scores
    
    def test_compute_score_empty(self):
        """Test computing score with no evaluation."""
        from src.query import compute_evaluation_score
        score = compute_evaluation_score(None)
        assert score == 0.0
    
    def test_compute_score_invalid_values(self):
        """Test computing score with invalid values."""
        from src.query import compute_evaluation_score
        evaluation = {
            "liking": "invalid",
            "jag": {"flavour_intensity": "bad"}
        }
        score = compute_evaluation_score(evaluation)
        assert score == 0.0
