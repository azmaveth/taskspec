"""
Pytest configuration file for TaskSpec project.
"""

import sys
import os
import pytest

# Add the project root directory to the Python path
# This allows the tests to import modules directly using 'taskspec.module'
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# For pytest running from package directory
pytest_plugins = ["tests.fixtures"]

# Optional: create common fixtures here that can be used across test files
@pytest.fixture
def test_output_dir():
    """Return the path to the test output directory."""
    output_dir = os.path.join(os.path.dirname(__file__), "test_output")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir