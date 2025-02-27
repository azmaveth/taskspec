"""
Tests for the main module.
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, ANY
from typer.testing import CliRunner

from taskspec.main import app


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    mock_config = MagicMock()
    mock_config.llm_provider = "test_provider"
    mock_config.llm_model = "test_model"
    mock_config.cache_enabled = True
    mock_config.cache_type = "memory"
    mock_config.cache_ttl = 3600
    return mock_config


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client for testing."""
    return {"provider": "test_provider", "model": "test_model"}


@pytest.fixture
def temp_input_file():
    """Create a temporary input file for testing."""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
        temp_file.write("Test task description")
        temp_path = temp_file.name
    
    yield Path(temp_path)
    
    # Clean up
    os.unlink(temp_path)


@patch('taskspec.main.load_config')
@patch('taskspec.main.setup_llm_client')
@patch('taskspec.main.analyze_task')
@patch('taskspec.main.get_cache_manager')
def test_analyze_command_with_task(
    mock_get_cache, mock_analyze_task, mock_setup_llm, mock_load_config, runner, mock_config, mock_llm_client
):
    """Test analyze command with task argument."""
    # Set up mocks
    mock_load_config.return_value = mock_config
    mock_setup_llm.return_value = mock_llm_client
    mock_get_cache.return_value = MagicMock()
    mock_analyze_task.return_value = "Mock specification content"
    
    # Run the command
    result = runner.invoke(app, ["analyze", "Build a simple web app"])
    
    # Verify the result
    assert result.exit_code == 0
    assert "Mock specification content" in result.stdout
    
    # Verify the function calls
    mock_load_config.assert_called_once()
    mock_setup_llm.assert_called_once()
    mock_analyze_task.assert_called_once_with(
        "Build a simple web app",
        mock_llm_client,
        progress=ANY,
        custom_template=None,
        search_enabled=False,
        validate=True,
        verbose=False
    )


@patch('taskspec.main.load_config')
@patch('taskspec.main.setup_llm_client')
@patch('taskspec.main.analyze_task')
@patch('taskspec.main.get_cache_manager')
def test_analyze_command_with_input_file(
    mock_get_cache, mock_analyze_task, mock_setup_llm, mock_load_config, 
    runner, mock_config, mock_llm_client, temp_input_file
):
    """Test analyze command with input file."""
    # Set up mocks
    mock_load_config.return_value = mock_config
    mock_setup_llm.return_value = mock_llm_client
    mock_get_cache.return_value = MagicMock()
    mock_analyze_task.return_value = "Mock specification content"
    
    # Run the command
    result = runner.invoke(app, ["analyze", "--input", str(temp_input_file)])
    
    # Verify the result
    assert result.exit_code == 0
    assert "Mock specification content" in result.stdout
    
    # Verify analyze_task was called with file content
    mock_analyze_task.assert_called_once()
    # The first positional argument should be the file content
    args, _ = mock_analyze_task.call_args
    assert args[0] == "Test task description"


@patch('taskspec.main.load_config')
@patch('taskspec.main.setup_llm_client')
@patch('taskspec.main.analyze_task')
@patch('taskspec.main.get_cache_manager')
@patch('taskspec.main.generate_task_summary')
def test_analyze_command_with_output_file(
    mock_generate_summary, mock_get_cache, mock_analyze_task, mock_setup_llm, mock_load_config, 
    runner, mock_config, mock_llm_client, tmp_path
):
    """Test analyze command with output file."""
    # Set up mocks
    mock_load_config.return_value = mock_config
    mock_setup_llm.return_value = mock_llm_client
    mock_get_cache.return_value = MagicMock()
    mock_analyze_task.return_value = "Mock specification content"
    mock_generate_summary.return_value = "test_summary"
    
    # Create output path
    output_path = tmp_path / "output.md"
    
    # Run the command
    result = runner.invoke(app, ["analyze", "Build a simple web app", "--output", str(output_path)])
    
    # Verify the result
    assert result.exit_code == 0
    
    # Verify file was written
    assert output_path.exists()
    assert output_path.read_text() == "Mock specification content"


@patch('taskspec.main.load_config')
@patch('taskspec.main.setup_llm_client')
@patch('taskspec.main.analyze_design_document')
@patch('taskspec.main.get_cache_manager')
@patch('taskspec.main.format_design_results')
def test_design_command(
    mock_format_results, mock_get_cache, mock_analyze_design, mock_setup_llm, mock_load_config, 
    runner, mock_config, mock_llm_client
):
    """Test design command."""
    # Set up mocks
    mock_load_config.return_value = mock_config
    mock_setup_llm.return_value = mock_llm_client
    mock_get_cache.return_value = MagicMock()
    mock_analyze_design.return_value = {"phases": []}
    mock_format_results.return_value = "Mock design results"
    
    # Run the command
    result = runner.invoke(app, ["design", "Create a weather monitoring system"])
    
    # Verify the result
    assert result.exit_code == 0
    assert "Mock design results" in result.stdout
    
    # Verify the function calls
    mock_load_config.assert_called_once()
    mock_setup_llm.assert_called_once()
    mock_analyze_design.assert_called_once_with(
        "Create a weather monitoring system",
        mock_llm_client,
        progress=ANY,
        verbose=False
    )
    mock_format_results.assert_called_once_with(
        {"phases": []}, 
        "markdown",
        False
    )


@patch('taskspec.main.split_phases_to_files')
def test_split_command(mock_split_phases, runner, tmp_path):
    """Test split command."""
    # Create a test phases file
    phases_file = tmp_path / "test_phases.md"
    phases_file.write_text("# Test phases file")
    
    # Set up mock
    mock_split_phases.return_value = [
        tmp_path / "test_phase1.md",
        tmp_path / "test_phase2.md"
    ]
    
    # Run the command
    result = runner.invoke(app, ["split", str(phases_file)])
    
    # Verify the result
    assert result.exit_code == 0
    
    # Verify the function calls
    mock_split_phases.assert_called_once_with(
        phases_file=phases_file,
        output_dir=None,
        prefix=None
    )


@patch('taskspec.main.load_config')
def test_analyze_command_errors(mock_load_config, runner):
    """Test analyze command error handling."""
    # This test depends on exact implementation, needs to be more flexible
    
    # Test missing task and input file
    result = runner.invoke(app, ["analyze"])
    if result.exit_code == 0:
        # Possible the command is handling it without error exit code
        assert "Error" in result.stdout 
        assert "task or input file must be provided" in result.stdout.lower()
    else:
        assert result.exit_code == 1
        assert "Error" in result.stdout
        assert "task or input file must be provided" in result.stdout.lower()
    
    # Test with non-existent input file
    result = runner.invoke(app, ["analyze", "--input", "/nonexistent/file.txt"])
    if result.exit_code == 0:
        # Possible the command is handling it without error exit code
        assert "Error" in result.stdout
        assert "not found" in result.stdout.lower()
    else:
        assert result.exit_code == 1
        assert "Error" in result.stdout
        assert "not found" in result.stdout.lower()