"""
Tests for utility functions.
"""

import sys
import os
import pytest
from pathlib import Path

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from taskspec.utils import sanitize_filename

def test_sanitize_filename():
    """Test the sanitize_filename function."""
    # Test basic sanitization
    assert sanitize_filename("hello world") == "hello_world"
    
    # Test removal of special characters
    assert sanitize_filename("hello@world!") == "helloworld"
    
    # Test conversion to lowercase
    assert sanitize_filename("HELLO") == "hello"
    
    # Test empty string
    assert sanitize_filename("") == "task"
