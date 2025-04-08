"""
pytest configuration for tests.
"""

import sys
import os
import pytest

# Add parent directory to sys.path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Add any fixtures here

@pytest.fixture
def test_output_dir():
    """Return the path to the test output directory."""
    output_dir = os.path.join(os.path.dirname(__file__), "test_output")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir
