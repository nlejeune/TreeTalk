"""
Unit Tests for TreeTalk API Routes

This module contains unit tests for all FastAPI routes to ensure
proper functionality, error handling, and response formats.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import json
import uuid
from datetime import date

# Mock the database dependencies
@pytest.fixture
def mock_db_session():
    """Mock database session for testing."""
    return AsyncMock()

@pytest.fixture
def client():
    """Create test client with mocked dependencies."""
    from src.backend.main import app
    from src.backend.utils.database import get_database_session
    
    # Override database dependency
    app.dependency_overrides[get_database_session] = lambda: AsyncMock()
    
    return TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns API information."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "TreeTalk API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "healthy"
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "TreeTalk Backend"


class TestAuthRoutes:
    """Test authentication routes."""
    
    def test_auth_health_check(self, client):
        """Test auth service health check."""
        response = client.get("/api/auth/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "TreeTalk Auth"
    
    def test_validate_request(self, client):
        """Test request validation endpoint."""
        response = client.post("/api/auth/validate")
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == True
        assert data["auth_type"] == "public"
    
    def test_auth_status(self, client):
        """Test authentication status endpoint."""
        response = client.get("/api/auth/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["authentication_enabled"] == False
        assert "public" in data["auth_methods"]


class TestConfigRoutes:
    """Test configuration routes."""
    
    @patch('src.backend.models.configuration.Configuration.set_value')
    def test_set_api_key_configuration(self, mock_set_value, client):
        """Test setting API key configuration."""
        mock_set_value.return_value = None
        
        config_data = {
            "openrouter_api_key": "test-api-key-12345",
            "default_model": "openai/gpt-3.5-turbo"
        }
        
        response = client.post("/api/config/api-key", json=config_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "OpenRouter API key" in data["message"]
        assert "Default model" in data["message"]
    
    def test_set_api_key_invalid_key(self, client):
        """Test setting invalid API key."""
        config_data = {
            "openrouter_api_key": "short"  # Too short
        }
        
        response = client.post("/api/config/api-key", json=config_data)
        
        assert response.status_code == 400
        assert "Invalid API key format" in response.json()["detail"]
    
    def test_set_api_key_no_data(self, client):
        """Test setting API key with no data."""
        response = client.post("/api/config/api-key", json={})
        
        assert response.status_code == 400
        assert "No configuration values provided" in response.json()["detail"]
    
    @patch('src.backend.models.configuration.Configuration.get_value')
    def test_get_api_key_status(self, mock_get_value, client):
        """Test getting API key status."""
        mock_get_value.side_effect = lambda db, key, default=None: {
            "openrouter_api_key": "test-key",
            "default_model": "openai/gpt-3.5-turbo"
        }.get(key, default)
        
        response = client.get("/api/config/api-key/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["openrouter_api_key_configured"] == True
        assert data["default_model"] == "openai/gpt-3.5-turbo"
        assert data["chat_available"] == True
    
    @patch('src.backend.models.configuration.Configuration.set_value')
    def test_set_configuration_value(self, mock_set_value, client):
        """Test setting general configuration value."""
        mock_set_value.return_value = None
        
        config_data = {
            "key": "test_setting",
            "value": "test_value"
        }
        
        response = client.post("/api/config/setting", json=config_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["key"] == "test_setting"
    
    def test_set_configuration_invalid_key(self, client):
        """Test setting configuration with invalid key."""
        config_data = {
            "key": "invalid key with spaces and @#$",
            "value": "test_value"
        }
        
        response = client.post("/api/config/setting", json=config_data)
        
        assert response.status_code == 400
        assert "Invalid configuration key format" in response.json()["detail"]
    
    @patch('src.backend.models.configuration.Configuration.get_value')
    def test_get_configuration_value(self, mock_get_value, client):
        """Test getting configuration value."""
        mock_get_value.return_value = "test_value"
        
        response = client.get("/api/config/setting/test_key")
        
        assert response.status_code == 200
        data = response.json()
        assert data["key"] == "test_key"
        assert data["value"] == "test_value"
    
    def test_get_sensitive_configuration_value(self, client):
        """Test getting sensitive configuration value (should fail)."""
        response = client.get("/api/config/setting/openrouter_api_key")
        
        assert response.status_code == 403
        assert "Cannot retrieve sensitive configuration values" in response.json()["detail"]
    
    @patch('src.backend.models.configuration.Configuration.get_value')
    def test_get_nonexistent_configuration_value(self, mock_get_value, client):
        """Test getting non-existent configuration value."""
        mock_get_value.return_value = None
        
        response = client.get("/api/config/setting/nonexistent_key")
        
        assert response.status_code == 404
        assert "Configuration key not found" in response.json()["detail"]


class TestPersonRoutes:
    """Test person management routes."""
    
    @patch('src.backend.services.family_service.FamilyService.search_persons')
    def test_search_persons(self, mock_search, client):
        """Test person search endpoint."""
        mock_search.return_value = [
            {
                "id": str(uuid.uuid4()),
                "display_name": "John Smith",
                "life_span": "1850-1920",
                "search_relevance": 10.0
            }
        ]
        
        response = client.get("/api/persons/search?q=John")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["display_name"] == "John Smith"
        mock_search.assert_called_once()
    
    def test_search_persons_short_query(self, client):
        """Test person search with too short query."""
        response = client.get("/api/persons/search?q=J")
        
        assert response.status_code == 400
        assert "at least 2 characters long" in response.json()["detail"]
    
    @patch('src.backend.services.family_service.FamilyService.get_person_details')
    def test_get_person_details(self, mock_get_details, client):
        """Test getting person details."""
        person_id = str(uuid.uuid4())
        mock_get_details.return_value = {
            "id": person_id,
            "display_name": "John Smith",
            "birth_date": "1850-01-01",
            "events": [],
            "relationships": []
        }
        
        response = client.get(f"/api/persons/{person_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == person_id
        assert data["display_name"] == "John Smith"
        mock_get_details.assert_called_once()
    
    @patch('src.backend.services.family_service.FamilyService.get_person_details')
    def test_get_person_details_not_found(self, mock_get_details, client):
        """Test getting details for non-existent person."""
        mock_get_details.side_effect = ValueError("Person not found")
        person_id = str(uuid.uuid4())
        
        response = client.get(f"/api/persons/{person_id}")
        
        assert response.status_code == 404
        assert "Person not found" in response.json()["detail"]
    
    @patch('src.backend.services.family_service.FamilyService.get_family_tree')
    def test_get_family_tree(self, mock_get_tree, client):
        """Test getting family tree data."""
        person_id = str(uuid.uuid4())
        mock_get_tree.return_value = {
            "focal_person": {"id": person_id, "display_name": "John Smith"},
            "persons": [{"id": person_id, "display_name": "John Smith"}],
            "relationships": [],
            "metadata": {
                "total_persons": 1,
                "total_relationships": 0,
                "max_generations": 4
            }
        }
        
        response = client.get(f"/api/persons/{person_id}/family-tree")
        
        assert response.status_code == 200
        data = response.json()
        assert data["focal_person"]["id"] == person_id
        assert data["metadata"]["total_persons"] == 1
        mock_get_tree.assert_called_once()
    
    @patch('src.backend.services.family_service.FamilyService.get_relationship_path')
    def test_get_relationship_path(self, mock_get_path, client):
        """Test getting relationship path between two persons."""
        person1_id = str(uuid.uuid4())
        person2_id = str(uuid.uuid4())
        
        mock_get_path.return_value = [
            {"person_id": person1_id, "relationship_type": "parent-child", "depth": 1}
        ]
        
        response = client.get(f"/api/persons/{person1_id}/relationship-path/{person2_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["person_id"] == person1_id
        mock_get_path.assert_called_once()
    
    def test_get_relationship_path_same_person(self, client):
        """Test getting relationship path for same person (should fail)."""
        person_id = str(uuid.uuid4())
        
        response = client.get(f"/api/persons/{person_id}/relationship-path/{person_id}")
        
        assert response.status_code == 400
        assert "Cannot find relationship path between the same person" in response.json()["detail"]


class TestChatRoutes:
    """Test chat API routes."""
    
    @patch('src.backend.services.chat_service.ChatService.send_message')
    def test_send_chat_message(self, mock_send_message, client):
        """Test sending chat message."""
        session_id = str(uuid.uuid4())
        mock_send_message.return_value = {
            "session_id": session_id,
            "user_message": {
                "content": "Tell me about John Smith",
                "message_type": "user"
            },
            "ai_message": {
                "content": "Based on your family data...",
                "message_type": "assistant"
            },
            "context_used": True,
            "response_metadata": {}
        }
        
        message_data = {
            "message": "Tell me about John Smith",
            "session_id": session_id
        }
        
        response = client.post("/api/chat/message", json=message_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert data["user_message"]["content"] == "Tell me about John Smith"
        assert "ai_message" in data
        mock_send_message.assert_called_once()
    
    def test_send_empty_chat_message(self, client):
        """Test sending empty chat message."""
        message_data = {
            "message": "",
            "session_id": str(uuid.uuid4())
        }
        
        response = client.post("/api/chat/message", json=message_data)
        
        assert response.status_code == 400
        assert "Message cannot be empty" in response.json()["detail"]
    
    def test_send_too_long_chat_message(self, client):
        """Test sending overly long chat message."""
        message_data = {
            "message": "a" * 5000,  # Too long
            "session_id": str(uuid.uuid4())
        }
        
        response = client.post("/api/chat/message", json=message_data)
        
        assert response.status_code == 400
        assert "Message too long" in response.json()["detail"]
    
    @patch('src.backend.services.chat_service.ChatService.create_chat_session')
    def test_create_chat_session(self, mock_create_session, client):
        """Test creating chat session."""
        session_id = uuid.uuid4()
        mock_session = Mock()
        mock_session.id = session_id
        mock_session.to_dict.return_value = {
            "id": str(session_id),
            "title": "Test Chat",
            "is_active": True
        }
        mock_create_session.return_value = mock_session
        
        session_data = {
            "title": "Test Chat",
            "model_name": "openai/gpt-3.5-turbo"
        }
        
        response = client.post("/api/chat/sessions", json=session_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["session"]["title"] == "Test Chat"
        mock_create_session.assert_called_once()
    
    @patch('src.backend.services.chat_service.ChatService.get_chat_history')
    def test_get_chat_history(self, mock_get_history, client):
        """Test getting chat history."""
        session_id = str(uuid.uuid4())
        mock_get_history.return_value = [
            {
                "message_type": "user",
                "content": "Hello",
                "sequence_number": 1
            },
            {
                "message_type": "assistant",
                "content": "Hi there!",
                "sequence_number": 2
            }
        ]
        
        response = client.get(f"/api/chat/sessions/{session_id}/messages")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["message_type"] == "user"
        assert data[1]["message_type"] == "assistant"
        mock_get_history.assert_called_once()
    
    @patch('src.backend.services.chat_service.ChatService.get_available_models')
    def test_get_available_models(self, mock_get_models, client):
        """Test getting available AI models."""
        mock_get_models.return_value = [
            {
                "id": "openai/gpt-3.5-turbo",
                "name": "GPT-3.5 Turbo",
                "cost_per_1k_tokens": 2.0
            }
        ]
        
        response = client.get("/api/chat/models")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(model["id"] == "openai/gpt-3.5-turbo" for model in data)


if __name__ == "__main__":
    pytest.main([__file__])