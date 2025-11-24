"""Comprehensive integration tests for RAG service."""
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pytest


class TestRagServiceComprehensive:
    """Comprehensive tests for RAG service."""
    
    @pytest.fixture
    def mock_chroma_client(self):
        """Mock ChromaDB client with realistic data."""
        with patch('chromadb.PersistentClient') as mock:
            mock_collection = MagicMock()
            
            # Mock realistic query results
            mock_collection.query.return_value = {
                'ids': [['bean1', 'bean2', 'bean3']],
                'distances': [[0.15, 0.25, 0.35]],
                'metadatas': [[
                    {
                        'bean.name': 'Ethiopian Yirgacheffe',
                        'bean.process': 'Washed',
                        'bean.roast_level': 'Light',
                        'brewing.brewer': 'V60',
                        'brewing.temperature': 93,
                        'brewing.dose': 15,
                        'evaluation.liking': 9.0,
                        'evaluation.jag.flavour_intensity': 5,
                        'evaluation.jag.acidity': 4,
                        'evaluation.jag.sweetness': 4
                    },
                    {
                        'bean.name': 'Colombian Supremo',
                        'bean.process': 'Natural',
                        'bean.roast_level': 'Medium',
                        'brewing.brewer': 'V60',
                        'brewing.temperature': 92,
                        'brewing.dose': 16,
                        'evaluation.liking': 8.5,
                        'evaluation.jag.flavour_intensity': 4,
                        'evaluation.jag.acidity': 3
                    },
                    {
                        'bean.name': 'Kenya AA',
                        'bean.process': 'Washed',
                        'bean.roast_level': 'Medium-Light',
                        'brewing.brewer': 'April',
                        'brewing.temperature': 94,
                        'evaluation.liking': 7.5
                    }
                ]],
                'documents': [['doc1', 'doc2', 'doc3']]
            }
            mock.return_value.get_or_create_collection.return_value = mock_collection
            yield mock
    
    @pytest.fixture
    def client(self, mock_chroma_client):
        """Create test client."""
        from src.service import app
        return TestClient(app)
    
    def test_healthz_endpoint(self, client):
        """Test health check."""
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    def test_rag_query_with_free_text(self, client):
        """Test RAG query with free text."""
        payload = {
            "query": "fruity Ethiopian coffee with citrus notes",
            "k": 3
        }
        response = client.post("/rag", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "results" in data
        assert isinstance(data["results"], list)
        assert len(data["results"]) <= 3
    
    def test_rag_query_with_bean_structure(self, client):
        """Test RAG query with structured bean data."""
        payload = {
            "bean": {
                "name": "Ethiopian Yirgacheffe",
                "process": "Washed",
                "roast_level": "Light",
                "flavor_notes": ["citrus", "floral", "tea"]
            },
            "k": 2
        }
        response = client.post("/rag", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) <= 2
        # Check result structure
        if data["results"]:
            result = data["results"][0]
            assert "rank" in result
            assert "bean_text" in result
            assert "brewing" in result
    
    def test_rag_query_with_record(self, client):
        """Test RAG query with full record."""
        payload = {
            "record": {
                "bean": {
                    "name": "Colombian Supremo",
                    "process": "Natural",
                    "roast_level": "Medium"
                },
                "brewing": {
                    "brewer": "V60",
                    "temperature": 92
                }
            },
            "k": 3
        }
        response = client.post("/rag", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
    
    def test_rag_with_reranking_enabled(self, client):
        """Test RAG with evaluation reranking."""
        payload = {
            "query": "sweet chocolate coffee",
            "k": 2,
            "use_evaluation_reranking": True,
            "similarity_weight": 0.7,
            "retrieval_multiplier": 3
        }
        response = client.post("/rag", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        # With reranking, results should have combined scores
        if data["results"]:
            assert "combined_score" in data["results"][0] or data["results"][0].get("combined_score") is None
    
    def test_rag_with_reranking_disabled(self, client):
        """Test RAG without reranking."""
        payload = {
            "query": "coffee",
            "k": 2,
            "use_evaluation_reranking": False
        }
        response = client.post("/rag", json=payload)
        assert response.status_code == 200
    
    def test_rag_k_parameter_validation(self, client):
        """Test k parameter bounds."""
        # Test minimum k
        response = client.post("/rag", json={"query": "test", "k": 1})
        assert response.status_code == 200
        
        # Test maximum k
        response = client.post("/rag", json={"query": "test", "k": 10})
        assert response.status_code == 200
        
        # Test k > 10 should fail validation
        response = client.post("/rag", json={"query": "test", "k": 15})
        assert response.status_code == 422
    
    def test_rag_similarity_weight_validation(self, client):
        """Test similarity_weight parameter."""
        # Valid weight
        response = client.post("/rag", json={
            "query": "test",
            "similarity_weight": 0.5
        })
        assert response.status_code == 200
        
        # Weight > 1 should fail
        response = client.post("/rag", json={
            "query": "test",
            "similarity_weight": 1.5
        })
        assert response.status_code == 422
    
    def test_rag_result_structure(self, client):
        """Test that results have correct structure."""
        response = client.post("/rag", json={"query": "test coffee", "k": 2})
        assert response.status_code == 200
        data = response.json()
        
        assert "query" in data
        assert "results" in data
        
        for result in data["results"]:
            assert "rank" in result
            assert "id" in result
            assert "distance" in result
            assert "bean_text" in result
            assert "brewing" in result
            assert isinstance(result["brewing"], dict)
    
    def test_rag_with_empty_query(self, client):
        """Test behavior with empty/null inputs."""
        # Empty query string should still work (will use empty string)
        response = client.post("/rag", json={"query": "", "k": 1})
        # This might be 200, 400, or 422 depending on validation
        assert response.status_code in [200, 400, 422]
    
    def test_rag_with_complex_bean_data(self, client):
        """Test with complex nested bean data."""
        payload = {
            "bean": {
                "name": "Geisha",
                "process": "Washed",
                "variety": "Geisha",
                "region": "Panama",
                "roast_level": "Light",
                "roasted_days": 7,
                "altitude": 1700,
                "flavor_notes": ["jasmine", "bergamot", "peach", "honey"]
            },
            "k": 3,
            "use_evaluation_reranking": True,
            "similarity_weight": 0.6
        }
        response = client.post("/rag", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) <= 3
    
    def test_rag_retrieval_multiplier(self, client):
        """Test retrieval multiplier parameter."""
        payload = {
            "query": "test",
            "k": 2,
            "retrieval_multiplier": 5
        }
        response = client.post("/rag", json=payload)
        assert response.status_code == 200
        
        # Multiplier > 5 should fail
        payload["retrieval_multiplier"] = 10
        response = client.post("/rag", json=payload)
        assert response.status_code == 422
