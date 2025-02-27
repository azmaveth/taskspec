"""
Common test fixtures and configuration for taskspec tests.
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client for testing."""
    mock_client = MagicMock()
    mock_client.complete.return_value = "Mock LLM response"
    mock_client.chat_with_history.return_value = "Mock chat response"
    return mock_client

@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    mock_config = MagicMock()
    mock_config.llm_provider = "test_provider"
    mock_config.llm_model = "test_model"
    mock_config.cache_enabled = True
    mock_config.cache_type = "memory"
    mock_config.cache_ttl = 3600
    return mock_config

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    tmp_dir = tempfile.mkdtemp()
    yield Path(tmp_dir)
    shutil.rmtree(tmp_dir)

@pytest.fixture
def sample_task():
    """Sample task description for testing."""
    return """
    Build a REST API for a book inventory system with the following features:
    - Add, update, delete, and list books
    - Search for books by title, author, or ISBN
    - User authentication and authorization
    - Rate limiting
    """

@pytest.fixture
def sample_design_doc():
    """Sample design document for testing."""
    return """
    # Weather Monitoring System Design
    
    ## Overview
    Create a weather monitoring system that collects data from various sensors,
    processes it, and provides alerts when certain thresholds are exceeded.
    
    ## Key Features
    - Sensor data collection
    - Data processing and storage
    - Alert system
    - User dashboard
    
    ## Technical Stack
    - Python for backend processing
    - PostgreSQL for data storage
    - React for frontend dashboard
    - Docker for containerization
    """