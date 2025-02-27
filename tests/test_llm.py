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
    
    # Test case with both error and cache
    mock_completion.side_effect = Exception("Cache Error Test")
    
    # Create a mock cache that also raises an exception
    mock_cache = MagicMock()
    mock_cache.get.side_effect = Exception("Cache Error")
    
    # Create a test LLM config with cache
    llm_config_with_cache = {
        "provider": "test_provider",
        "model": "test_model",
        "cache": mock_cache
    }
    
    # Call should still raise the LLM error, not the cache error
    with pytest.raises(RuntimeError) as excinfo:
        complete(
            llm_config=llm_config_with_cache,
            prompt="Test prompt"
        )
    
    assert "Cache Error Test" in str(excinfo.value)
    
@patch('litellm.completion')
def test_complete_api_timeout(mock_completion):
    """Test complete function with API timeout."""
    # Mock the litellm response to raise a timeout exception
    mock_completion.side_effect = Exception("Request timed out")
    
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
    
    # Verify the exception contains the timeout error
    assert "timed out" in str(excinfo.value)
    
@patch('litellm.completion')
def test_complete_rate_limit(mock_completion):
    """Test complete function with rate limiting."""
    # Mock the litellm response to raise a rate limit exception
    mock_completion.side_effect = Exception("Rate limit exceeded")
    
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
    
    # Verify the exception contains the rate limit error
    assert "Rate limit" in str(excinfo.value)
    
@patch('litellm.completion')
def test_complete_with_empty_response(mock_completion):
    """Test complete function with empty response from LLM."""
    # Mock the litellm response with empty content
    mock_completion.return_value = MockResponse("")
    
    # Create a test LLM config
    llm_config = {
        "provider": "test_provider",
        "model": "test_model"
    }
    
    # Call the function
    response = complete(
        llm_config=llm_config,
        prompt="Test prompt"
    )
    
    # Verify empty response is returned
    assert response == ""


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
    
@patch('litellm.completion')
def test_chat_with_empty_message_list(mock_completion):
    """Test chat_with_history function with empty message list."""
    # Mock the litellm response
    mock_completion.return_value = MockResponse("Empty message response")
    
    # Create a test LLM config
    llm_config = {
        "provider": "test_provider",
        "model": "test_model"
    }
    
    # Create empty messages list
    messages = []
    
    # Call the function
    response = chat_with_history(
        llm_config=llm_config,
        messages=messages
    )
    
    # Verify the response
    assert response == "Empty message response"
    
    # Verify litellm was called correctly with empty messages
    mock_completion.assert_called_once()
    args, kwargs = mock_completion.call_args
    assert kwargs["messages"] == []
    
@patch('litellm.completion')
def test_chat_with_extremely_long_message(mock_completion):
    """Test chat_with_history with a very long message to test token limit handling."""
    # Mock the litellm response
    mock_completion.return_value = MockResponse("Long message response")
    
    # Create a test LLM config
    llm_config = {
        "provider": "test_provider",
        "model": "test_model"
    }
    
    # Create a message with extremely long content
    long_content = "a" * 10000  # 10,000 character string
    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": long_content}
    ]
    
    # Call the function with a small max_tokens value
    response = chat_with_history(
        llm_config=llm_config,
        messages=messages,
        max_tokens=100  # Small token limit
    )
    
    # Verify the response
    assert response == "Long message response"
    
    # Verify litellm was called with correct max_tokens
    mock_completion.assert_called_once()
    args, kwargs = mock_completion.call_args
    assert kwargs["max_tokens"] == 100
    
@patch('litellm.completion')
def test_chat_with_history_cache_keygeneration(mock_completion):
    """Test that chat_with_history generates different cache keys for different messages."""
    # Mock the litellm response
    mock_completion.return_value = MockResponse("Response 1")
    
    # Create a mock cache
    mock_cache = MagicMock()
    mock_cache.get.return_value = None
    
    # For tracking generated keys
    generated_keys = []
    
    def track_key(prompt, model, temperature):
        key = f"{prompt}:{model}:{temperature}"
        generated_keys.append(key)
        return key
    
    mock_cache.generate_key.side_effect = track_key
    
    # Create a test LLM config with cache
    llm_config = {
        "provider": "test_provider",
        "model": "test_model",
        "cache": mock_cache
    }
    
    # Test with first set of messages
    messages1 = [
        {"role": "user", "content": "Hello"}
    ]
    
    chat_with_history(
        llm_config=llm_config,
        messages=messages1
    )
    
    # Test with second set of messages
    messages2 = [
        {"role": "user", "content": "Different message"}
    ]
    
    chat_with_history(
        llm_config=llm_config,
        messages=messages2
    )
    
    # Verify different cache keys were generated
    assert len(generated_keys) == 2
    assert generated_keys[0] != generated_keys[1]