"""
Tests for the analyzer module.
"""

import pytest
from unittest.mock import patch, MagicMock, ANY
import time

from taskspec.analyzer import (
    format_time,
    update_progress_with_eta,
    analyze_task,
    validate_specification,
    extract_components,
    ANALYSIS_SYSTEM_PROMPT,
    TASK_BREAKDOWN_PROMPT,
    REFINEMENT_PROMPT,
    TEMPLATE_FORMAT_PROMPT,
    VALIDATION_PROMPT
)


def test_format_time():
    """Test format_time function for different time ranges."""
    # Test seconds (< 60s)
    assert format_time(30) == "30s"
    
    # Test minutes (60s - 3600s)
    assert format_time(120) == "2.0m"
    assert format_time(1800) == "30.0m"
    
    # Test hours (>= 3600s)
    assert format_time(3600) == "1.0h"
    assert format_time(7200) == "2.0h"


def test_update_progress_with_eta():
    """Test update_progress_with_eta function."""
    # Create a mock Progress instance
    mock_progress = MagicMock()
    
    # Call with no timing data
    update_progress_with_eta(
        progress=mock_progress,
        task_id=1,
        timing_data={},
        completed_weight=0.5,
        step_name="Test Step"
    )
    
    # Verify progress was updated without ETA
    mock_progress.update.assert_called_once_with(
        1, completed=50
    )
    
    # Reset mock
    mock_progress.reset_mock()
    
    # Call with timing data
    update_progress_with_eta(
        progress=mock_progress,
        task_id=1,
        timing_data={"step1": 10.0, "step2": 20.0},
        completed_weight=0.5,
        step_name="Test Step"
    )
    
    # Verify progress was updated with ETA
    mock_progress.update.assert_called_once()
    call_args = mock_progress.update.call_args[0]
    assert call_args[0] == 1  # task_id is positional
    assert "ETA:" in mock_progress.update.call_args[1]["description"]


@patch('taskspec.analyzer.complete')
@patch('taskspec.analyzer.chat_with_history')
@patch('taskspec.analyzer.search_web')
def test_analyze_task_basic(mock_search, mock_chat, mock_complete):
    """Test analyze_task with minimal options."""
    # Set up mocks
    mock_complete.return_value = "Mock initial analysis"
    mock_chat.return_value = "Mock refined analysis"
    mock_search.return_value = []
    
    # Set up a mock progress instance
    mock_progress = MagicMock()
    mock_progress.add_task.return_value = 1
    
    # Create a mock LLM config
    llm_config = {"model": "test-model"}
    
    # Call the function
    result = analyze_task(
        task="Build a web application",
        llm_config=llm_config,
        progress=mock_progress,
        search_enabled=False,
        validate=False
    )
    
    # Verify the search was not called
    mock_search.assert_not_called()
    
    # Verify complete was called
    mock_complete.assert_called_once()
    
    # Verify that chat was called (at least once, not checking exact count)
    assert mock_chat.call_count >= 1
    
    # Verify the result contains the final response
    assert result == "Mock refined analysis"


@patch('taskspec.analyzer.complete')
@patch('taskspec.analyzer.chat_with_history')
@patch('taskspec.analyzer.search_web')
def test_analyze_task_with_search(mock_search, mock_chat, mock_complete):
    """Test analyze_task with search enabled."""
    # Set up mocks
    mock_complete.return_value = "Mock initial analysis"
    mock_chat.return_value = "Mock refined analysis"
    mock_search.return_value = [
        {"title": "Result 1", "description": "Description 1"}
    ]
    
    # Set up a mock progress instance
    mock_progress = MagicMock()
    mock_progress.add_task.return_value = 1
    
    # Create a mock LLM config
    llm_config = {"model": "test-model"}
    
    # Call the function
    result = analyze_task(
        task="Build a web application",
        llm_config=llm_config,
        progress=mock_progress,
        search_enabled=True,
        validate=False
    )
    
    # Verify the search function was called
    mock_search.assert_called_once()
    
    # Verify complete was called
    mock_complete.assert_called_once()
    
    # Verify that chat was called (at least once, not checking exact count)
    assert mock_chat.call_count >= 1
    
    # Check that the search results were added to the prompt
    args, kwargs = mock_complete.call_args
    assert "ADDITIONAL CONTEXT FROM WEB SEARCH" in kwargs["prompt"]


@patch('taskspec.analyzer.complete')
@patch('taskspec.analyzer.chat_with_history')
@patch('taskspec.analyzer.validate_specification')
def test_analyze_task_with_validation(mock_validate, mock_chat, mock_complete):
    """Test analyze_task with validation."""
    # Set up mocks
    mock_complete.return_value = "Mock initial analysis"
    mock_chat.return_value = "Mock formatted spec"
    mock_validate.return_value = "Mock validated spec"
    
    # Set up a mock progress instance
    mock_progress = MagicMock()
    mock_progress.add_task.return_value = 1
    
    # Create a mock LLM config
    llm_config = {"model": "test-model"}
    
    # Call the function
    result = analyze_task(
        task="Build a web application",
        llm_config=llm_config,
        progress=mock_progress,
        validate=True
    )
    
    # Verify the validation function was called
    mock_validate.assert_called_once()
    
    # Verify the result is the validated spec
    assert result == "Mock validated spec"


@patch('taskspec.analyzer.complete')
def test_validate_specification(mock_complete):
    """Test validate_specification function."""
    # Set up mock to return a valid result first time
    mock_complete.return_value = "The specification meets all criteria and is valid"
    
    # Call the function
    result = validate_specification(
        spec_document="Mock spec document",
        llm_config={"model": "test-model"},
        progress=MagicMock(),
        task_id=1
    )
    
    # Verify complete was called with validation prompt
    mock_complete.assert_called_once()
    args, kwargs = mock_complete.call_args
    assert kwargs["prompt"] == VALIDATION_PROMPT.format(spec_document="Mock spec document")
    
    # Verify the result is unchanged when validation passes
    assert result == "Mock spec document"
    
    # Reset mock
    mock_complete.reset_mock()
    
    # Set up mock to return issues on first call, then validation passes
    mock_complete.side_effect = [
        "The specification has the following issues: X, Y, Z",
        "Improved spec",
        "The specification now meets all criteria"
    ]
    
    # Call the function
    result = validate_specification(
        spec_document="Mock spec document",
        llm_config={"model": "test-model"},
        progress=MagicMock(),
        task_id=1
    )
    
    # Verify complete was called multiple times
    assert mock_complete.call_count == 3
    
    # Verify the result is the improved spec
    assert result == "Improved spec"


def test_extract_components():
    """Test extract_components function."""
    spec_document = """
    ## High-Level Objective
    Build a web application.
    
    ## Mid-Level Objective
    Create an API, build UI, etc.
    
    ## Implementation Notes
    Use React, Node.js, etc.
    
    ## Context
    ### Beginning context
    No files exist.
    
    ### Ending context
    Several files will exist.
    
    ## Low-Level Tasks
    1. Create package.json
    2. Install dependencies
    """
    
    components = extract_components(spec_document)
    
    assert components["high_level_objective"] == "Build a web application."
    assert "Create an API" in components["mid_level_objectives"]
    assert "Use React" in components["implementation_notes"]
    assert "No files exist" in components["beginning_context"]
    assert "Several files will exist" in components["ending_context"]
    assert "Create package.json" in components["low_level_tasks"]