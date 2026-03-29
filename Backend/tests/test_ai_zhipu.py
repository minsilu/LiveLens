import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from api.main import app

client = TestClient(app)

@patch("api.routes.ai.ZhipuAI")
@patch("api.routes.ai.os.getenv")
def test_analyze_data_success(mock_getenv, mock_zhipuai_class):
    # Mock environment variable
    mock_getenv.return_value = "fake_zhipu_api_key"
    
    # Mock the ZhipuAI client and its create method
    mock_client_instance = MagicMock()
    mock_zhipuai_class.return_value = mock_client_instance
    
    # Mock the response from the API
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "This is a mocked AI response."
    mock_response.choices = [mock_choice]
    
    # Configure the create method to return our mocked response
    mock_client_instance.chat.completions.create.return_value = mock_response
    
    # Test payload
    payload = {
        "input_data": "I need some help analyzing this text.",
        "instructions": "Be concise."
    }
    
    # Make the request
    response = client.post("/ai/analyze", json=payload)
    
    # Assertions
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "analysis": "This is a mocked AI response."
    }
    
    # Verify the client was called with correct parameters
    mock_client_instance.chat.completions.create.assert_called_once()
    call_args = mock_client_instance.chat.completions.create.call_args[1]
    
    assert call_args["model"] == "glm-4"
    assert len(call_args["messages"]) == 2
    assert "LiveLens" in call_args["messages"][0]["content"]
    assert "Be concise." in call_args["messages"][0]["content"]
    assert "I need some help analyzing this text." in call_args["messages"][1]["content"]

@patch("api.routes.ai.ZhipuAI")
@patch("api.routes.ai.os.getenv")
def test_analyze_data_json_input(mock_getenv, mock_zhipuai_class):
    # Mock environment variable
    mock_getenv.return_value = "fake_zhipu_api_key"
    
    # Mock the ZhipuAI client and its create method
    mock_client_instance = MagicMock()
    mock_zhipuai_class.return_value = mock_client_instance
    
    # Mock the response from the API
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "JSON analysis complete."
    mock_response.choices = [mock_choice]
    mock_client_instance.chat.completions.create.return_value = mock_response
    
    # Test payload with JSON object
    payload = {
        "input_data": {"key1": "value1", "key2": [1, 2, 3]}
    }
    
    # Make the request
    response = client.post("/ai/analyze", json=payload)
    
    # Assertions
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "analysis": "JSON analysis complete."
    }
    
    # Verify the client was called and formatted the JSON correctly
    call_args = mock_client_instance.chat.completions.create.call_args[1]
    assert "key1" in call_args["messages"][1]["content"]
    assert "value1" in call_args["messages"][1]["content"]

@patch("api.routes.ai.os.getenv")
def test_analyze_data_missing_api_key(mock_getenv):
    # Mock environment variable to return None
    mock_getenv.return_value = None
    
    # Test payload
    payload = {
        "input_data": "Test text"
    }
    
    # Make the request
    response = client.post("/ai/analyze", json=payload)
    
    # Assertions
    assert response.status_code == 500
    assert "ZHIPUAI_API_KEY is not configured" in response.json()["detail"]

@patch("api.routes.ai.ZhipuAI")
@patch("api.routes.ai.os.getenv")
def test_analyze_data_api_failure(mock_getenv, mock_zhipuai_class):
    # Mock environment variable
    mock_getenv.return_value = "fake_zhipu_api_key"
    
    # Mock the ZhipuAI client to raise an exception
    mock_client_instance = MagicMock()
    mock_zhipuai_class.return_value = mock_client_instance
    mock_client_instance.chat.completions.create.side_effect = Exception("API limit exceeded")
    
    # Test payload
    payload = {
        "input_data": "Test text"
    }
    
    # Make the request
    response = client.post("/ai/analyze", json=payload)
    
    # Assertions
    assert response.status_code == 500
    assert "Failed to analyze data with ZhipuAI: API limit exceeded" in response.json()["detail"]
