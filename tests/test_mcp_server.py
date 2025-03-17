import os
import pytest
from fastapi.testclient import TestClient
import json
from unittest.mock import patch, MagicMock

# Import the FastAPI application
from mcp_server import app

# Create a test client
client = TestClient(app)

# Test fixtures
@pytest.fixture
def mock_environment():
    """Set up mock environment variables for testing"""
    with patch.dict(os.environ, {
        "OPENAI_API_KEY": "test-api-key",
        "OPENAI_CHAT_MODEL": "gpt-4o-mini",
        "OPENAI_COMPLETION_MODEL": "gpt-3.5-turbo-instruct",
        "PROMETHEUS_URL": "http://localhost:9090"
    }):
        yield

# Tests for core API functionality
def test_list_models():
    """Test the list_models endpoint"""
    response = client.get("/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    models = data["models"]
    assert isinstance(models, list)
    assert len(models) > 0
    
    # Verify some expected models exist
    model_ids = [model["id"] for model in models]
    expected_models = ["openai-gpt-chat", "git-analyzer", "filesystem", "prometheus"]
    for model_id in expected_models:
        assert model_id in model_ids

def test_get_model_info():
    """Test getting information for a specific model"""
    response = client.get("/v1/models/openai-gpt-chat")
    assert response.status_code == 200
    model = response.json()
    assert model["id"] == "openai-gpt-chat"
    assert "capabilities" in model
    assert "chat" in model["capabilities"]

def test_get_nonexistent_model():
    """Test getting a model that doesn't exist"""
    response = client.get("/v1/models/nonexistent-model")
    assert response.status_code == 404

# Tests for OpenAI endpoints
@pytest.mark.parametrize("model_endpoint", [
    "/v1/models/openai-gpt-chat/chat",
    "/v1/models/openai-gpt-completion/completion"
])
@patch("openai.OpenAI")
def test_openai_endpoints_authentication(mock_openai, model_endpoint, mock_environment):
    """Test OpenAI endpoints require authentication"""
    # Set up mock to simulate API response
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    
    # For chat endpoint
    mock_chat_completion = MagicMock()
    mock_chat_completion.choices = [MagicMock(message=MagicMock(content="Test response"))]
    mock_client.chat.completions.create.return_value = mock_chat_completion
    
    # For completion endpoint
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(text="Test response")]
    mock_client.completions.create.return_value = mock_completion
    
    if "chat" in model_endpoint:
        payload = {
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 50
        }
    else:
        payload = {"prompt": "Hello", "max_tokens": 50}

    response = client.post(model_endpoint, json=payload)
    assert response.status_code == 200  # API should work with mock
    
    # Verify that the appropriate OpenAI method was called
    if "chat" in model_endpoint:
        mock_client.chat.completions.create.assert_called_once()
    else:
        mock_client.completions.create.assert_called_once()

# Tests for Git analysis endpoints
@patch("mcp.git_service.GitService.analyze_repository")
def test_git_analyze_endpoint(mock_analyze):
    """Test the git analyze endpoint"""
    # Set up mock to return analysis
    mock_analyze.return_value = {
        "analysis": "This repository contains a Python project with several modules."
    }
    
    # Call the endpoint
    response = client.post(
        "/v1/models/git-analyzer/analyze",
        json={"repo_url": "https://github.com/test/repo.git"}
    )
    
    # Verify results
    assert response.status_code == 200
    result = response.json()
    assert "analysis" in result
    
    # Verify the service was called
    mock_analyze.assert_called_once_with("https://github.com/test/repo.git")

# Tests for Filesystem endpoints
@patch("mcp.filesystem_service.FilesystemService.list_directory")
def test_filesystem_list_endpoint(mock_list):
    """Test the filesystem list endpoint"""
    mock_list.return_value = {
        "files": ["file1.txt", "file2.py"],
        "directories": ["dir1", "dir2"]
    }
    
    response = client.post(
        "/v1/models/filesystem/list",
        json={"path": "."}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert "entries" in result
    assert "files" in result["entries"]
    assert "directories" in result["entries"]

# Tests for Prometheus endpoints
@patch("mcp.prometheus_service.PrometheusService.query")
def test_prometheus_query_endpoint(mock_query):
    """Test the Prometheus query endpoint"""
    mock_query.return_value = {"status": "success", "data": {"resultType": "vector", "result": []}}
    
    response = client.post(
        "/v1/models/prometheus/query", 
        json={"query": "up"}
    )
    
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "success"
    mock_query.assert_called_once()

# Add more tests for other endpoints as needed 