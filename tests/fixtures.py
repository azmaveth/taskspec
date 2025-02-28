"""
Common fixtures for pytest.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Create test output directory fixture
@pytest.fixture
def test_output_dir():
    """Create and return a test output directory."""
    output_dir = Path(__file__).parent.parent / "test_output"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

# Mock LLM client fixture
@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client for testing."""
    mock_client = MagicMock()
    mock_client["provider"] = "test_provider"
    mock_client["model"] = "test_model"
    return mock_client

# Mock cache manager fixture
@pytest.fixture
def mock_cache_manager():
    """Create a mock cache manager for testing."""
    mock_cache = MagicMock()
    mock_cache.get.return_value = None  # Default to cache miss
    mock_cache.set.return_value = True  # Default to successful cache set
    mock_cache.get_stats.return_value = {"entries": 0, "hits": 0, "misses": 0}
    return mock_cache
