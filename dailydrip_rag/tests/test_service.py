"""Integration tests for RAG service API."""
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pytest


class TestRagService:
    """Test the RAG service endpoints."""
    
    @pytest.fixture
    def mock_chroma_client(self):
        """Mock ChromaDB client."""
        with patch('chromadb.PersistentClient') as mock:
            mock_collection = MagicMock()
            mock_collection.query.return_value = {
                'ids': [['id1', 'id2']],
                'distances': [[0.1, 0.2]],
                'metadatas': [[
                    {'bean.name': 'Test Bean 1', 'evaluation.liking': 8.0},
                    {'bean.name': 'Test Bean 2', 'evaluation.liking': 7.5}
                ]],
                'documents': [['doc1', 'doc2']]
            }
            mock.return_value.get_or_create_collection.return_value = mock_collection
            yield mock
    
    @pytest.fixture
    def client(self, mock_chroma_client):
        """Create test client with mocked dependencies."""
        from src.service import app
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    def test_query_with_text(self, client):
        """Test querying with free text."""
        payload = {
            "user_id": "test-user",
            "query": "Ethiopian coffee with fruity notes",
            "k": 3
        }
        response = client.post("/rag", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)
    
    def test_query_with_bean_object(self, client):
        """Test querying with a bean object."""
        payload = {
            "user_id": "test-user",
            "bean": {
                "name": "Ethiopian Yirgacheffe",
                "process": "Washed",
                "roast_level": "Light"
            },
            "k": 2
        }
        response = client.post("/rag", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
    
    def test_query_with_record(self, client):
        """Test querying with a full record."""
        payload = {
            "user_id": "test-user",
            "record": {
                "bean": {
                    "name": "Colombian Supremo",
                    "process": "Natural"
                },
                "brewing": {
                    "method": "V60"
                }
            },
            "k": 3
        }
        response = client.post("/rag", json=payload)
        assert response.status_code == 200
    
    def test_query_invalid_k(self, client):
        """Test query with invalid k parameter."""
        payload = {
            "user_id": "test-user",
            "query": "test",
            "k": 20  # Exceeds maximum
        }
        response = client.post("/rag", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_query_no_input(self, client):
        """Test query with no input parameters."""
        payload = {"user_id": "test-user", "k": 3}
        response = client.post("/rag", json=payload)
        # Should handle gracefully or return error
        assert response.status_code in [200, 400, 422]
