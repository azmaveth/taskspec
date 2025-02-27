"""
Tests for the llm module.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from taskspec.llm import setup_llm_client, complete, chat_with_history
from taskspec.config import Config


class MockResponse:
    """Mock LiteLLM response object."""
    
    def __init__(self, content):
        self.choices = [
            MagicMock(
                message=MagicMock(
                    content=content
                )
            )
        ]


def test_setup_llm_client():
    """Test setup_llm_client function."""
    # Create a test config
    config = Config(
        llm_provider="test_provider",
        llm_model="test_model",
        openai_api_key="test_openai_key",
        anthropic_api_key="test_anthropic_key",
        cohere_api_key="test_cohere_key"
    )
    
    # Create a mock cache manager
    mock_cache = MagicMock()
    
    # Test with environment variables
    with patch.dict(os.environ, {}, clear=True):
        llm_config = setup_llm_client(config, mock_cache)
        
        # Check environment variables were set
        assert os.environ["OPENAI_API_KEY"] == "test_openai_key"
        assert os.environ["ANTHROPIC_API_KEY"] == "test_anthropic_key"
        assert os.environ["COHERE_API_KEY"] == "test_cohere_key"
        
        # Check returned config
        assert llm_config["provider"] == "test_provider"
        assert llm_config["model"] == "test_model"
        assert llm_config["cache"] == mock_cache


@patch('litellm.completion')
def test_complete_without_cache(mock_completion):
    """Test complete function without cache."""
    # Mock the litellm response
    mock_completion.return_value = MockResponse("Test response")
    
    # Create a test LLM config
    llm_config = {
        "provider": "test_provider",
        "model": "test_model"
    }
    
    # Call the function
    response = complete(
        llm_config=llm_config,
        prompt="Test prompt",
        system_prompt="System prompt",
        temperature=0.5
    )
    
    # Verify the response
    assert response == "Test response"
    
    # Verify litellm was called correctly
    mock_completion.assert_called_once()
    args, kwargs = mock_completion.call_args
    assert kwargs["model"] == "test_provider/test_model"
    assert len(kwargs["messages"]) == 2
    assert kwargs["messages"][0]["role"] == "system"
    assert kwargs["messages"][0]["content"] == "System prompt"
    assert kwargs["messages"][1]["role"] == "user"
    assert kwargs["messages"][1]["content"] == "Test prompt"
    assert kwargs["temperature"] == 0.5


@patch('litellm.completion')
def test_complete_with_cache(mock_completion):
    """Test complete function with cache hit and miss."""
    # Mock the litellm response
    mock_completion.return_value = MockResponse("Generated response")
    
    # Create a mock cache
    mock_cache = MagicMock()
    mock_cache.generate_key.return_value = "test_cache_key"
    
    # Test with cache miss
    mock_cache.get.return_value = None
    
    # Create a test LLM config with cache
    llm_config = {
        "provider": "test_provider",
        "model": "test_model",
        "cache": mock_cache
    }
    
    # Call the function
    response = complete(
        llm_config=llm_config,
        prompt="Test prompt"
    )
    
    # Verify the response and cache behavior
    assert response == "Generated response"
    mock_cache.get.assert_called_with("test_cache_key")
    mock_cache.set.assert_called_with("test_cache_key", "Generated response")
    mock_completion.assert_called_once()
    
    # Test with cache hit
    mock_completion.reset_mock()
    mock_cache.get.return_value = "Cached response"
    
    # Call the function again
    response = complete(
        llm_config=llm_config,
        prompt="Test prompt"
    )
    
    # Verify cached response was returned without calling LLM
    assert response == "Cached response"
    mock_cache.get.assert_called_with("test_cache_key")
    mock_completion.assert_not_called()


@patch('litellm.completion')
def test_complete_error_handling(mock_completion):
    """Test complete function error handling."""
    # Mock the litellm response to raise an exception
    mock_completion.side_effect = Exception("LLM API Error")
    
    # Create a test LLM config
    llm_config = {
        "provider": "test_provider",
        "model": "test_model"
    }
    
    # Call the function and expect an exception
    with pytest.raises(RuntimeError) as excinfo:
        complete(
            llm_config=llm_config,
            prompt="Test prompt"
        )
    
    # Verify the exception contains the original error
    assert "LLM API Error" in str(excinfo.value)


@patch('litellm.completion')
def test_chat_with_history(mock_completion):
    """Test chat_with_history function."""
    # Mock the litellm response
    mock_completion.return_value = MockResponse("Chat response")
    
    # Create a test LLM config
    llm_config = {
        "provider": "test_provider",
        "model": "test_model"
    }
    
    # Create test messages
    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"}
    ]
    
    # Call the function
    response = chat_with_history(
        llm_config=llm_config,
        messages=messages,
        temperature=0.7
    )
    
    # Verify the response
    assert response == "Chat response"
    
    # Verify litellm was called correctly
    mock_completion.assert_called_once()
    args, kwargs = mock_completion.call_args
    assert kwargs["model"] == "test_provider/test_model"
    assert kwargs["messages"] == messages
    assert kwargs["temperature"] == 0.7