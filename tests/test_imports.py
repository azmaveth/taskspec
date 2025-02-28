"""
Test the imports from the taskspec package.
"""

import os
import sys

# Add the parent directory to sys.path to be able to import taskspec
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_imports():
    """Test that all modules can be imported from the taskspec package."""
    # Basic imports
    from taskspec import config
    from taskspec import llm
    from taskspec import analyzer
    from taskspec import design
    from taskspec import template
    from taskspec import utils
    from taskspec import cache
    from taskspec import python_detector
    
    # Function imports
    from taskspec.config import load_config
    from taskspec.llm import setup_llm_client, complete, chat_with_history
    from taskspec.analyzer import analyze_task
    from taskspec.design import analyze_design_document, format_subtask_for_analysis, create_interactive_design
    from taskspec.template import get_default_template, render_template
    from taskspec.utils import sanitize_filename, generate_task_summary
    from taskspec.cache import get_cache_manager
    from taskspec.python_detector import detect_python_command, get_python_command_for_pytest, get_python_command_for_mutmut
    
    # Test passed if all imports succeed
    print("All imports successful!")
    return True

if __name__ == "__main__":
    # Run as a standalone script
    print("Testing imports from taskspec package...")
    test_imports()
    print("All tests passed!")
