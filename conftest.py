"""
Pytest configuration file for TaskSpec project.
"""

import sys
import os

# Add the project root directory to the Python path
# This allows the tests to import modules directly using 'taskspec.module'
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Define any pytest fixtures or hooks here if needed