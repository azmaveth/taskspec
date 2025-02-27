"""
Tests for the utils module.
"""

import os
import json
import yaml
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from taskspec.utils import (
    sanitize_filename,
    extract_phases_from_markdown,
    split_phases_to_files,
    format_design_results_markdown,
    format_design_results,
    generate_task_summary
)

def test_sanitize_filename():
    """Test sanitize_filename function."""
    # Test with spaces
    assert sanitize_filename("This is a test") == "this_is_a_test"
    
    # Test with special characters
    assert sanitize_filename("Test@file.txt!") == "testfiletxt"
    
    # Test with empty string
    assert sanitize_filename("") == "task"
    
    # Test with only special characters
    assert sanitize_filename("@#$%^&*()") == "task"

def test_extract_phases_from_markdown():
    """Test extract_phases_from_markdown function."""
    # Test with numbered phases
    markdown_content = """# Test Document
    
## Phase 1/3: Setup Project
Setup content here

## Phase 2/3: Implement Features
Features content here

## Phase 3/3: Testing
Testing content here
"""
    phases = extract_phases_from_markdown(markdown_content)
    assert len(phases) == 3
    assert phases[0]['name'] == "Setup Project"
    assert phases[1]['name'] == "Implement Features"
    assert phases[2]['name'] == "Testing"
    
    # Test with regular phase format
    markdown_content = """# Test Document
    
## Phase 1: Setup
Setup content

## Phase 2: Implementation
Implementation content
"""
    phases = extract_phases_from_markdown(markdown_content)
    assert len(phases) == 2
    assert phases[0]['name'] == "Setup"
    assert phases[1]['name'] == "Implementation"
    
    # Test with generic h2 headers
    markdown_content = """# Test Document
    
## Setup
Setup content

## Implementation
Implementation content
"""
    phases = extract_phases_from_markdown(markdown_content)
    assert len(phases) == 2
    assert phases[0]['name'] == "Setup"
    assert phases[1]['name'] == "Implementation"
    
    # Test with no phases
    markdown_content = """# Test Document
    
No phases here.
"""
    phases = extract_phases_from_markdown(markdown_content)
    assert len(phases) == 0

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test files."""
    return tmp_path

def test_split_phases_to_files(temp_dir):
    """Test split_phases_to_files function."""
    # Create a test phases file
    phases_content = """# Test Implementation Plan
    
## Phase 1/2: Setup
Setup content here

## Phase 2/2: Implementation
Implementation content here
"""
    phases_file = temp_dir / "test_phases.md"
    phases_file.write_text(phases_content)
    
    # Test splitting with default settings
    created_files = split_phases_to_files(phases_file)
    assert len(created_files) == 2
    assert (temp_dir / "test_phase1_setup.md").exists()
    assert (temp_dir / "test_phase2_implementation.md").exists()
    
    # Test splitting with custom output dir
    output_dir = temp_dir / "output"
    created_files = split_phases_to_files(phases_file, output_dir=output_dir)
    assert len(created_files) == 2
    assert (output_dir / "test_phase1_setup.md").exists()
    assert (output_dir / "test_phase2_implementation.md").exists()
    
    # Test splitting with custom prefix
    created_files = split_phases_to_files(phases_file, prefix="custom")
    assert len(created_files) == 2
    assert (temp_dir / "custom_phase1_setup.md").exists()
    assert (temp_dir / "custom_phase2_implementation.md").exists()
    
    # Test with non-existent file
    with pytest.raises(FileNotFoundError):
        split_phases_to_files(temp_dir / "nonexistent.md")
    
    # Test with file containing no phases
    no_phases_file = temp_dir / "no_phases.md"
    no_phases_file.write_text("# No phases here")
    with pytest.raises(ValueError):
        split_phases_to_files(no_phases_file)

def test_format_design_results_markdown():
    """Test format_design_results_markdown function."""
    # Create a sample results dictionary
    results = {
        "phases": [
            {
                "name": "Phase 1",
                "description": "Phase 1 description",
                "components": "Component 1, Component 2",
                "dependencies": "Dependency 1, Dependency 2",
                "considerations": "Consideration 1, Consideration 2",
                "subtasks": [
                    {
                        "title": "Subtask 1",
                        "description": "Subtask 1 description",
                        "technical_details": "Technical details 1",
                        "dependencies": "Dependency 1"
                    },
                    {
                        "title": "Subtask 2",
                        "description": "Subtask 2 description",
                        "technical_details": "Technical details 2",
                        "dependencies": "Dependency 2"
                    }
                ]
            }
        ]
    }
    
    # Format results
    markdown = format_design_results_markdown(results)
    
    # Verify the markdown contains all expected sections
    assert "# Implementation Plan" in markdown
    assert "## Phase 1/1: Phase 1" in markdown
    assert "Phase 1 description" in markdown
    assert "**Key Components:**" in markdown
    assert "Component 1, Component 2" in markdown
    assert "**Dependencies:**" in markdown
    assert "Dependency 1, Dependency 2" in markdown
    assert "**Technical Considerations:**" in markdown
    assert "Consideration 1, Consideration 2" in markdown
    assert "### Subtasks" in markdown
    assert "#### 1/2: Subtask 1" in markdown
    assert "Subtask 1 description" in markdown
    assert "**Technical Details:**" in markdown
    assert "Technical details 1" in markdown
    
    # Test with include_specs
    results["phases"][0]["specifications"] = [
        {
            "task": results["phases"][0]["subtasks"][0],
            "specification": "Spec for subtask 1"
        }
    ]
    
    markdown = format_design_results_markdown(results, include_specs=True)
    assert "**Generated Specification:**" in markdown
    assert "```markdown\nSpec for subtask 1\n```" in markdown
    
    # Test handling missing optional fields
    minimal_results = {
        "phases": [
            {
                "name": "Minimal Phase",
                "description": "Minimal description",
                "subtasks": [
                    {
                        "title": "Minimal Subtask",
                        "description": "Minimal subtask description"
                    }
                ]
            }
        ]
    }
    
    markdown = format_design_results_markdown(minimal_results)
    assert "## Phase 1/1: Minimal Phase" in markdown
    assert "Minimal description" in markdown
    assert "#### 1/1: Minimal Subtask" in markdown
    assert "Minimal subtask description" in markdown
    
    # Test with numbered subtasks in title
    numbered_results = {
        "phases": [
            {
                "name": "Phase",
                "description": "Description",
                "subtasks": [
                    {
                        "title": "1. Subtask One",
                        "description": "Description"
                    },
                    {
                        "title": "Task 2: Subtask Two",
                        "description": "Description"
                    }
                ]
            }
        ]
    }
    
    markdown = format_design_results_markdown(numbered_results)
    assert "#### 1/2: Subtask One" in markdown
    assert "#### 2/2: Subtask Two" in markdown

def test_format_design_results():
    """Test format_design_results function for different formats."""
    # Create a simple results dictionary
    results = {
        "phases": [
            {
                "name": "Test Phase",
                "description": "Test description",
                "subtasks": [
                    {
                        "title": "Test Subtask",
                        "description": "Test subtask description"
                    }
                ]
            }
        ]
    }
    
    # Test JSON format
    json_output = format_design_results(results, format_type="json")
    parsed_json = json.loads(json_output)
    assert parsed_json == results
    
    # Test YAML format
    yaml_output = format_design_results(results, format_type="yaml")
    parsed_yaml = yaml.safe_load(yaml_output)
    assert parsed_yaml == results
    
    # Test default markdown format
    markdown_output = format_design_results(results, format_type="markdown")
    assert "# Implementation Plan" in markdown_output
    assert "## Phase 1/1: Test Phase" in markdown_output
    
    # Test with unknown format (should default to markdown)
    unknown_format = format_design_results(results, format_type="unknown_format")
    assert "# Implementation Plan" in unknown_format

@patch('taskspec.llm.complete')
def test_generate_task_summary(mock_complete):
    """Test generate_task_summary function."""
    # Test with short task
    short_task = "Short task content"
    mock_llm_config = {"model": "test-model"}
    
    summary = generate_task_summary(short_task, mock_llm_config)
    assert summary == short_task.strip()
    
    # Test with longer task using LLM
    long_task = "This is a longer task description that should trigger the LLM summarization logic since it's over 40 characters long."
    mock_complete.return_value = "web app creation"
    
    summary = generate_task_summary(long_task, mock_llm_config)
    assert summary == "web_app_creation"
    mock_complete.assert_called_once()
    
    # Test with LLM returning empty string
    mock_complete.reset_mock()
    mock_complete.return_value = ""
    
    summary = generate_task_summary(long_task, mock_llm_config)
    assert summary != ""  # Should use fallback
    
    # Test error handling
    mock_complete.reset_mock()
    mock_complete.side_effect = Exception("LLM error")
    
    summary = generate_task_summary(long_task, mock_llm_config)
    assert summary == sanitize_filename(long_task[:30])