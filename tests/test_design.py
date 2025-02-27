"""
Tests for the design module.
"""

import pytest
from unittest.mock import patch, MagicMock, ANY
import time

from taskspec.design import (
    analyze_design_document,
    extract_phases,
    extract_subtasks,
    format_subtask_for_analysis,
    DESIGN_SYSTEM_PROMPT,
    PHASE_EXTRACTION_PROMPT,
    SUBTASK_GENERATION_PROMPT
)


def test_extract_phases():
    """Test extract_phases function."""
    # Let's just test the fallback behavior which is more reliable
    phases_text = "This is just a plain text with no phase structure."
    phases = extract_phases(phases_text)
    assert len(phases) == 1
    assert phases[0]["name"] == "Implementation Phase"
    assert "plain text" in phases[0]["description"]
    
    # Test with header format variation
    phases_text = """
    # Phase 1: Setup
    Description: Set up the project.
    
    # Phase 2: Development
    Description: Develop the features.
    """
    
    phases = extract_phases(phases_text)
    assert len(phases) == 2
    assert phases[0]["name"] == "Setup"
    assert phases[1]["name"] == "Development"
    
    # Test with numbered format
    phases_text = """
    1. Setup Phase
    Description: Set up the project.
    
    2. Development Phase
    Description: Develop the features.
    """
    
    phases = extract_phases(phases_text)
    assert len(phases) == 2
    assert phases[0]["name"] == "Setup Phase"
    assert phases[1]["name"] == "Development Phase"
    
    # Test with no phases (creates default)
    phases_text = "This is just a plain text with no phase structure."
    phases = extract_phases(phases_text)
    assert len(phases) == 1
    assert phases[0]["name"] == "Implementation Phase"
    assert "plain text" in phases[0]["description"]


def test_extract_subtasks():
    """Test extract_subtasks function."""
    # Test with no subtasks (creates default) - this is more reliable
    subtasks_text = "This is just a plain text with no subtask structure."
    subtasks = extract_subtasks(subtasks_text)
    assert len(subtasks) == 1
    assert subtasks[0]["title"] == "Implementation Task"
    assert "plain text" in subtasks[0]["description"]
    
    # Test with "Subtask" prefix format
    subtasks_text = """
    Subtask 1: Create Database
    Description: Set up the database.
    
    Subtask 2: Implement API
    Description: Create the API.
    """
    
    subtasks = extract_subtasks(subtasks_text)
    assert len(subtasks) == 2
    assert subtasks[0]["title"] == "Create Database"
    assert subtasks[1]["title"] == "Implement API"
    
    # Test with no proper structure (numbered items extraction)
    subtasks_text = """
    1. Create the database schema
    This is the first task to do.
    
    2. Implement API endpoints
    This is the second task to do.
    """
    
    subtasks = extract_subtasks(subtasks_text)
    assert len(subtasks) == 2
    assert "Create the database schema" in subtasks[0]["title"]
    
    # Test with no subtasks (creates default)
    subtasks_text = "This is just a plain text with no subtask structure."
    subtasks = extract_subtasks(subtasks_text)
    assert len(subtasks) == 1
    assert subtasks[0]["title"] == "Implementation Task"
    assert "plain text" in subtasks[0]["description"]


def test_format_subtask_for_analysis():
    """Test format_subtask_for_analysis function."""
    # Test with all fields
    subtask = {
        "title": "Create Database Schema",
        "description": "Design and implement the database schema.",
        "technical_details": "Use PostgreSQL with proper indexes.",
        "dependencies": "None"
    }
    
    formatted = format_subtask_for_analysis(subtask)
    assert "Create Database Schema" in formatted
    assert "Design and implement" in formatted
    assert "Technical details:" in formatted
    assert "PostgreSQL" in formatted
    assert "Dependencies:" in formatted
    
    # Test with numbered title
    subtask = {
        "title": "1. Create Database Schema",
        "description": "Design the schema.",
        "technical_details": "",
        "dependencies": ""
    }
    
    formatted = format_subtask_for_analysis(subtask)
    assert formatted.startswith("Create Database Schema")
    assert "1." not in formatted.split("\n")[0]
    
    # Test with minimal fields
    subtask = {
        "title": "Create Database",
        "description": "",
        "technical_details": "",
        "dependencies": ""
    }
    
    formatted = format_subtask_for_analysis(subtask)
    assert formatted == "Create Database"


@patch('taskspec.design.complete')
def test_analyze_design_document(mock_complete):
    """Test analyze_design_document function."""
    # Use a simpler approach that will be more reliable
    mock_complete.side_effect = [
        # First call: phase extraction
        "This is a simple phase description.",
        # Second call for subtasks
        "This is a simple subtask description."
    ]
    
    # Create a mock progress instance
    mock_progress = MagicMock()
    mock_progress.add_task.return_value = 1
    
    # Create a mock LLM config
    llm_config = {"model": "test-model"}
    
    # Call the function
    result = analyze_design_document(
        design_doc="Sample design document",
        llm_config=llm_config,
        progress=mock_progress,
        verbose=False
    )
    
    # Verify the function calls
    assert mock_complete.call_count >= 1
    
    # Verify first call was for phase extraction
    first_call_args = mock_complete.call_args_list[0][1]
    assert first_call_args["prompt"] == PHASE_EXTRACTION_PROMPT.format(design_doc="Sample design document")
    assert first_call_args["system_prompt"] == DESIGN_SYSTEM_PROMPT
    
    # Verify the result structure
    assert "phases" in result
    assert isinstance(result["phases"], list)
    
    # Verify progress was updated
    assert mock_progress.update.call_count > 0