"""
Tests for the config module.
"""

import os
import pytest
from unittest.mock import patch

from taskspec.config import load_config, Config

@pytest.fixture
def mock_env_vars():
    """Set up and tear down environment variables for testing."""
    # Store original environment variables
    original_vars = {
        'LLM_PROVIDER': os.environ.get('LLM_PROVIDER'),
        'LLM_MODEL': os.environ.get('LLM_MODEL'),
        'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY'),
        'ANTHROPIC_API_KEY': os.environ.get('ANTHROPIC_API_KEY'),
        'CACHE_ENABLED': os.environ.get('CACHE_ENABLED'),
        'CACHE_TYPE': os.environ.get('CACHE_TYPE'),
        'CACHE_TTL': os.environ.get('CACHE_TTL'),
    }
    
    # Set test environment variables
    os.environ['LLM_PROVIDER'] = 'test_provider'
    os.environ['LLM_MODEL'] = 'test_model'
    os.environ['OPENAI_API_KEY'] = 'test_openai_key'
    os.environ['ANTHROPIC_API_KEY'] = 'test_anthropic_key'
    os.environ['CACHE_ENABLED'] = '1'
    os.environ['CACHE_TYPE'] = 'memory'
    os.environ['CACHE_TTL'] = '3600'
    
    yield
    
    # Restore original environment variables
    for var, value in original_vars.items():
        if value is None:
            if var in os.environ:
                del os.environ[var]
        else:
            os.environ[var] = value

def test_load_config_from_env(mock_env_vars):
    """Test loading configuration from environment variables."""
    config = load_config()
    
    assert config.llm_provider == 'test_provider'
    assert config.llm_model == 'test_model'
    assert config.openai_api_key == 'test_openai_key'
    assert config.anthropic_api_key == 'test_anthropic_key'
    assert config.cache_enabled is True
    assert config.cache_type == 'memory'
    assert config.cache_ttl == 3600

def test_load_config_with_overrides(mock_env_vars):
    """Test loading configuration with overrides."""
    config = load_config(
        provider_override='override_provider',
        model_override='override_model',
        cache_enabled_override=False,
        cache_type_override='disk',
        cache_ttl_override=7200
    )
    
    assert config.llm_provider == 'override_provider'
    assert config.llm_model == 'override_model'
    assert config.openai_api_key == 'test_openai_key'  # From environment
    assert config.anthropic_api_key == 'test_anthropic_key'  # From environment
    assert config.cache_enabled is False  # Overridden
    assert config.cache_type == 'disk'  # Overridden
    assert config.cache_ttl == 7200  # Overridden

def test_load_config_defaults():
    """Test loading configuration with defaults when environment variables are not set."""
    # Use a clean environment
    with patch.dict(os.environ, {}, clear=True):
        config = load_config()
        
        # Check default values
        assert config.llm_provider == 'ollama'
        assert config.llm_model == 'athene-v2'  # Default for ollama
        assert config.openai_api_key is None
        assert config.anthropic_api_key is None
        assert config.cache_enabled is True
        assert config.cache_type == 'disk'
        assert config.cache_ttl == 86400

def test_default_model_by_provider():
    """Test that the default model is set correctly based on the provider."""
    # Test OpenAI provider
    with patch.dict(os.environ, {'LLM_PROVIDER': 'openai'}, clear=True):
        config = load_config()
        assert config.llm_provider == 'openai'
        assert config.llm_model == 'gpt-4o'
    
    # Test Anthropic provider
    with patch.dict(os.environ, {'LLM_PROVIDER': 'anthropic'}, clear=True):
        config = load_config()
        assert config.llm_provider == 'anthropic'
        assert config.llm_model == 'claude-3-opus-20240229'
    
    # Test Cohere provider
    with patch.dict(os.environ, {'LLM_PROVIDER': 'cohere'}, clear=True):
        config = load_config()
        assert config.llm_provider == 'cohere'
        assert config.llm_model == 'command-r'

def test_config_immutability():
    """Test that the Config class is immutable."""
    config = load_config()
    
    # Attempt to modify a field
    with pytest.raises(Exception):  # Should raise an exception due to frozen=True
        config.llm_provider = 'new_provider'