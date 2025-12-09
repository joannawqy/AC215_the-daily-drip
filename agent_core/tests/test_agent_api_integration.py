"""Integration tests for agent API endpoints."""
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from agent_core.agent import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_openai(monkeypatch):
    """Mock OpenAI client for recipe generation."""
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message = MagicMock()
    mock_completion.choices[0].message.function_call = MagicMock()
    mock_completion.choices[0].message.function_call.arguments = json.dumps({
        "brewing": {
            "brewer": "V60",
            "temperature": 92,
            "grinding_size": 22,
            "dose": 18,
            "target_water": 288,
            "pours": [{"start": 0, "end": 30, "water_added": 288}]
        }
    })
    mock_client.chat.completions.create.return_value = mock_completion
    
    def get_client():
        return mock_client
    
    monkeypatch.setattr("agent_core.agent._get_openai_client", get_client)
    return mock_client


@pytest.mark.integration
class TestAuthEndpoints:
    """Integration tests for authentication endpoints."""
    
    def test_register_user_success(self, client):
        """Test successful user registration."""
        payload = {
            "email": "test@example.com",
            "password": "testpass123",
            "display_name": "Test User"
        }
        response = client.post("/auth/register", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == "test@example.com"
    
    def test_register_duplicate_email(self, client):
        """Test registration with duplicate email fails."""
        payload = {
            "email": "duplicate@example.com",
            "password": "testpass123"
        }
        # First registration
        response1 = client.post("/auth/register", json=payload)
        assert response1.status_code == 200
        
        # Duplicate registration
        response2 = client.post("/auth/register", json=payload)
        assert response2.status_code == 409
    
    def test_login_success(self, client):
        """Test successful login."""
        # Register first
        register_payload = {
            "email": "login@example.com",
            "password": "testpass123"
        }
        client.post("/auth/register", json=register_payload)
        
        # Login
        login_payload = {
            "email": "login@example.com",
            "password": "testpass123"
        }
        response = client.post("/auth/login", json=login_payload)
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        payload = {
            "email": "nonexistent@example.com",
            "password": "wrongpass"
        }
        response = client.post("/auth/login", json=payload)
        assert response.status_code == 401


@pytest.mark.integration
class TestProfileEndpoints:
    """Integration tests for profile endpoints."""
    
    def test_get_profile_requires_auth(self, client):
        """Test that profile endpoint requires authentication."""
        response = client.get("/profile")
        assert response.status_code == 401
    
    def test_get_profile_success(self, client):
        """Test getting user profile."""
        # Register and get token
        register_payload = {
            "email": "profile@example.com",
            "password": "testpass123"
        }
        register_response = client.post("/auth/register", json=register_payload)
        token = register_response.json()["token"]
        
        # Get profile
        response = client.get("/profile", headers={"X-Auth-Token": token})
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert data["email"] == "profile@example.com"
    
    def test_update_preferences(self, client):
        """Test updating user preferences."""
        # Register and get token
        register_payload = {
            "email": "prefs@example.com",
            "password": "testpass123"
        }
        register_response = client.post("/auth/register", json=register_payload)
        token = register_response.json()["token"]
        
        # Update preferences
        prefs_payload = {
            "flavor_notes": ["fruity", "chocolate"],
            "roast_level": "Medium"
        }
        response = client.put("/profile/preferences", json=prefs_payload, headers={"X-Auth-Token": token})
        assert response.status_code == 200
        data = response.json()
        assert data["preferences"]["roast_level"] == "Medium"


@pytest.mark.integration
class TestBeanEndpoints:
    """Integration tests for bean management endpoints."""
    
    def test_list_beans_empty(self, client):
        """Test listing beans for new user."""
        # Register and get token
        register_payload = {
            "email": "beans@example.com",
            "password": "testpass123"
        }
        register_response = client.post("/auth/register", json=register_payload)
        token = register_response.json()["token"]
        
        # List beans
        response = client.get("/beans", headers={"X-Auth-Token": token})
        assert response.status_code == 200
        data = response.json()
        assert "beans" in data
        assert len(data["beans"]) == 0
    
    def test_create_bean(self, client):
        """Test creating a new bean."""
        # Register and get token
        register_payload = {
            "email": "createbean@example.com",
            "password": "testpass123"
        }
        register_response = client.post("/auth/register", json=register_payload)
        token = register_response.json()["token"]
        
        # Create bean - BeanPayload requires name (roast_level is int, not string)
        bean_payload = {
            "bean": {
                "name": "Test Bean",
                "origin": "Ethiopia",
                "process": "Washed",
                "roast_level": 2,  # Integer, not string
                "flavor_notes": ["fruity", "citrus"]
            }
        }
        response = client.post("/beans", json=bean_payload, headers={"X-Auth-Token": token})
        if response.status_code not in [200, 201]:
            print(f"Error response: {response.status_code} - {response.text}")
        assert response.status_code in [200, 201]  # 201 Created is also valid
        data = response.json()
        assert data["name"] == "Test Bean"
        assert "bean_id" in data
    
    def test_update_bean(self, client):
        """Test updating a bean."""
        # Register and get token
        register_payload = {
            "email": "updatebean@example.com",
            "password": "testpass123"
        }
        register_response = client.post("/auth/register", json=register_payload)
        token = register_response.json()["token"]
        
        # Create bean
        bean_payload = {
            "bean": {
                "name": "Original Bean",
                "origin": "Colombia"
            }
        }
        create_response = client.post("/beans", json=bean_payload, headers={"X-Auth-Token": token})
        bean_id = create_response.json()["bean_id"]
        
        # Update bean
        update_payload = {
            "bean": {
                "name": "Updated Bean",
                "origin": "Brazil"
            }
        }
        response = client.put(f"/beans/{bean_id}", json=update_payload, headers={"X-Auth-Token": token})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Bean"
    
    def test_delete_bean(self, client):
        """Test deleting a bean."""
        # Register and get token
        register_payload = {
            "email": "deletebean@example.com",
            "password": "testpass123"
        }
        register_response = client.post("/auth/register", json=register_payload)
        token = register_response.json()["token"]
        
        # Create bean
        bean_payload = {
            "bean": {
                "name": "To Delete",
                "origin": "Kenya"
            }
        }
        create_response = client.post("/beans", json=bean_payload, headers={"X-Auth-Token": token})
        bean_id = create_response.json()["bean_id"]
        
        # Delete bean
        response = client.delete(f"/beans/{bean_id}", headers={"X-Auth-Token": token})
        assert response.status_code == 204
        
        # Verify deleted
        list_response = client.get("/beans", headers={"X-Auth-Token": token})
        assert bean_id not in [b["bean_id"] for b in list_response.json()["beans"]]


@pytest.mark.integration
class TestBrewEndpoints:
    """Integration tests for brewing endpoints."""
    
    def test_brew_recipe(self, client, mock_openai):
        """Test brewing a recipe."""
        # Register and get token
        register_payload = {
            "email": "brew@example.com",
            "password": "testpass123"
        }
        register_response = client.post("/auth/register", json=register_payload)
        token = register_response.json()["token"]
        
        # Brew recipe with bean dict (disable RAG to avoid external service calls)
        brew_payload = {
            "bean": {
                "name": "Brew Bean",
                "origin": "Ethiopia",
                "process": "Washed"
            },
            "brewer": "V60",
            "rag_enabled": False
        }
        response = client.post("/brew", json=brew_payload, headers={"X-Auth-Token": token})
        assert response.status_code == 200
        data = response.json()
        assert "recipe" in data
        assert "references" in data
        assert data["recipe"]["brewing"]["brewer"] == "V60"
    
    def test_brew_with_custom_note(self, client, mock_openai):
        """Test brewing with custom note."""
        # Register and get token
        register_payload = {
            "email": "brewnote@example.com",
            "password": "testpass123"
        }
        register_response = client.post("/auth/register", json=register_payload)
        token = register_response.json()["token"]
        
        # Brew with note (disable RAG to avoid external service calls)
        brew_payload = {
            "bean": {
                "name": "Note Bean",
                "origin": "Colombia"
            },
            "brewer": "April",
            "note": "Make it strong",
            "rag_enabled": False
        }
        response = client.post("/brew", json=brew_payload, headers={"X-Auth-Token": token})
        assert response.status_code == 200


@pytest.mark.integration
class TestVisualizationEndpoints:
    """Integration tests for visualization endpoints."""
    
    def test_visualize_recipe(self, client):
        """Test recipe visualization."""
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
        
        payload = {
            "recipe": recipe,
            "formats": ["html", "ascii"]
        }
        
        response = client.post("/visualize", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "outputs" in data or "html" in data or "ascii" in data or "mermaid" in data

