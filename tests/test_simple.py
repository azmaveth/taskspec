"""
A simple test to check if pytest is working.
"""

import sys
import os

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_simple():
    """A simple test that should always pass."""
    assert True, "This test should always pass"

def test_import():
    """Test that we can import from the taskspec module."""
    import taskspec
    assert taskspec.__version__ == "0.1.0"
