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

# Print the sys.path to debug
print(f"sys.path in conftest.py: {sys.path}")
