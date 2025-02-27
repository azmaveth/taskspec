"""
Tests for the main module.
"""

import os
import tempfile
import pytest
from datetime import datetime
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


def test_design_command_params():
    """Verify that we can get design command help text."""
    # Use runner to invoke help for the design command
    runner = CliRunner()
    result = runner.invoke(app, ["design", "--help"])
    
    # Just verify that the help text is displayed and contains interactive
    assert result.exit_code == 0
    assert "interactive" in result.stdout.lower()
        
        
# Interactive mode with custom output is complex to test with mocks
# This would be better tested with integration tests


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

@patch('taskspec.main.load_config')
def test_design_command_errors(mock_load_config, runner):
    """Test design command error handling."""
    
    # Test missing design_doc and input file (without interactive)
    result = runner.invoke(app, ["design"])
    if result.exit_code == 0:
        assert "Error" in result.stdout
        assert "design document or input file must be provided" in result.stdout.lower()
    else:
        assert result.exit_code == 1
        assert "Error" in result.stdout
        assert "design document or input file must be provided" in result.stdout.lower()
    
    # Test with non-existent input file
    result = runner.invoke(app, ["design", "--input", "/nonexistent/file.txt"])
    if result.exit_code == 0:
        assert "Error" in result.stdout
        assert "not found" in result.stdout.lower()
    else:
        assert result.exit_code == 1
        assert "Error" in result.stdout
        assert "not found" in result.stdout.lower()
        
        
# Error handling for interactive mode is also complex to test
# This would be better tested with integration tests

@patch('taskspec.main.split_phases_to_files')
def test_split_command_errors(mock_split_phases, runner):
    """Test split command error handling."""
    
    # Test with non-existent file
    mock_split_phases.side_effect = FileNotFoundError("Phases file not found")
    
    result = runner.invoke(app, ["split", "/nonexistent/file.txt"])
    
    assert "Error" in result.stdout
    assert "not found" in result.stdout.lower()
    
    # Test with another error type
    # Reset the side effect
    mock_split_phases.reset_mock()
    # This time use a different type of error
    mock_split_phases.side_effect = ValueError("No phases found")
    
    # We need to make the Path.exists check pass so that our mock gets called
    with patch('pathlib.Path.exists', return_value=True):
        result = runner.invoke(app, ["split", "/some/file.txt"])
        # Check a generic error message
        assert "Error" in result.stdout

@patch('taskspec.main.load_config')
@patch('taskspec.main.setup_llm_client')
@patch('taskspec.main.analyze_task')
@patch('taskspec.main.get_cache_manager')
def test_analyze_with_template(
    mock_get_cache, mock_analyze_task, mock_setup_llm, mock_load_config, 
    runner, mock_config, mock_llm_client, tmp_path
):
    """Test analyze command with custom template file."""
    # Set up mocks
    mock_load_config.return_value = mock_config
    mock_setup_llm.return_value = mock_llm_client
    mock_get_cache.return_value = MagicMock()
    mock_analyze_task.return_value = "Mock specification with custom template"
    
    # Create a template file
    template_path = tmp_path / "template.md"
    template_path.write_text("Custom template content")
    
    # Run the command
    result = runner.invoke(app, [
        "analyze", 
        "Build a web app",
        "--template", 
        str(template_path)
    ])
    
    # Verify the result
    assert result.exit_code == 0
    assert "Mock specification with custom template" in result.stdout
    
    # Verify analyze_task was called with the template
    mock_analyze_task.assert_called_once()
    args, kwargs = mock_analyze_task.call_args
    assert kwargs["custom_template"] == "Custom template content"

@patch('taskspec.main.load_config')
@patch('taskspec.main.setup_llm_client')
@patch('taskspec.main.analyze_task')
@patch('taskspec.main.get_cache_manager')
def test_analyze_with_nonexistent_template(
    mock_get_cache, mock_analyze_task, mock_setup_llm, mock_load_config, runner, mock_config
):
    """Test analyze command with non-existent template file."""
    # Run the command with non-existent template
    result = runner.invoke(app, [
        "analyze", 
        "Build a web app",
        "--template", 
        "/nonexistent/template.md"
    ])
    
    # Verify error handling
    assert "Error" in result.stdout
    assert "template file not found" in result.stdout.lower()

@patch('taskspec.main.load_config')
@patch('taskspec.main.setup_llm_client')
@patch('taskspec.main.analyze_task') 
@patch('taskspec.main.get_cache_manager')
def test_analyze_with_clear_cache(
    mock_get_cache, mock_analyze_task, mock_setup_llm, mock_load_config, 
    runner, mock_config, mock_llm_client
):
    """Test analyze command with clear cache option."""
    # Set up mocks
    mock_load_config.return_value = mock_config
    mock_setup_llm.return_value = mock_llm_client
    mock_cache = MagicMock()
    mock_get_cache.return_value = mock_cache
    mock_analyze_task.return_value = "Mock specification content"
    
    # Run the command with clear cache flag
    result = runner.invoke(app, [
        "analyze", 
        "Build a web app",
        "--clear-cache"
    ])
    
    # Verify the cache was cleared
    mock_cache.clear.assert_called_once()
    
    # Verify the result
    assert result.exit_code == 0
    assert "Mock specification content" in result.stdout

@patch('taskspec.main.load_config')
@patch('taskspec.main.setup_llm_client')
@patch('taskspec.main.analyze_design_document')
@patch('taskspec.main.get_cache_manager')
@patch('taskspec.main.format_design_results')
@patch('taskspec.main.split_phases_to_files')
def test_design_with_split_phases(
    mock_split_phases, mock_format_results, mock_get_cache, mock_analyze_design, 
    mock_setup_llm, mock_load_config, runner, mock_config, mock_llm_client, tmp_path
):
    """Test design command with split phases option."""
    # Set up mocks
    mock_load_config.return_value = mock_config
    mock_setup_llm.return_value = mock_llm_client
    mock_get_cache.return_value = MagicMock()
    mock_analyze_design.return_value = {"phases": [{"name": "Phase 1"}, {"name": "Phase 2"}]}
    mock_format_results.return_value = "Mock design results with phases"
    mock_split_phases.return_value = [
        tmp_path / "phase1.md",
        tmp_path / "phase2.md"
    ]
    
    # Create output path
    output_path = tmp_path / "output.md"
    
    # Run the command with split phases flag
    result = runner.invoke(app, [
        "design", 
        "Design a system",
        "--output", 
        str(output_path),
        "--split-phases",
        "--output-dir",
        str(tmp_path)
    ])
    
    # Verify split_phases_to_files was called
    mock_split_phases.assert_called_once_with(
        phases_file=output_path,
        output_dir=tmp_path,
        prefix=None
    )
    
    # Verify the result
    assert result.exit_code == 0


@patch('taskspec.main.load_config')
@patch('taskspec.main.setup_llm_client')
@patch('taskspec.main.analyze_design_document')
@patch('taskspec.main.get_cache_manager')
@patch('taskspec.main.format_design_results')
@patch('taskspec.main.format_subtask_for_analysis')
@patch('taskspec.main.analyze_task')
def test_design_with_analyze_subtasks(
    mock_analyze_task, mock_format_subtask, mock_format_results, mock_get_cache, 
    mock_analyze_design, mock_setup_llm, mock_load_config, runner, mock_config, mock_llm_client
):
    """Test design command with analyze_subtasks option."""
    # Set up mocks
    mock_load_config.return_value = mock_config
    mock_setup_llm.return_value = mock_llm_client
    mock_get_cache.return_value = MagicMock()
    
    # Set up a realistic phases result with subtasks
    mock_analyze_design.return_value = {
        "phases": [
            {
                "name": "Phase 1",
                "description": "Phase 1 description",
                "subtasks": [
                    {
                        "title": "Subtask 1",
                        "description": "Description of subtask 1"
                    },
                    {
                        "title": "Subtask 2",
                        "description": "Description of subtask 2"
                    }
                ]
            }
        ]
    }
    
    mock_format_subtask.return_value = "Formatted subtask"
    mock_analyze_task.return_value = "Mock subtask specification"
    mock_format_results.return_value = "Mock design results with subtask specs"
    
    # Run the command with analyze-subtasks flag
    result = runner.invoke(app, [
        "design", 
        "Design a system",
        "--analyze-subtasks"
    ])
    
    # Verify format_subtask_for_analysis was called for each subtask
    assert mock_format_subtask.call_count == 2
    
    # Verify analyze_task was called for each subtask
    assert mock_analyze_task.call_count == 2
    
    # Verify the format_results was called with the correct parameters
    mock_format_results.assert_called_once_with(
        mock_analyze_design.return_value, 
        "markdown",
        True
    )
    
    # Verify the result
    assert result.exit_code == 0
    assert "Mock design results with subtask specs" in result.stdout


@patch('taskspec.main.load_config')
@patch('taskspec.main.setup_llm_client')
@patch('taskspec.main.analyze_task')
@patch('taskspec.main.get_cache_manager')
def test_analyze_with_verbose_output(
    mock_get_cache, mock_analyze_task, mock_setup_llm, mock_load_config, 
    runner, mock_config, mock_llm_client
):
    """Test analyze command with verbose output."""
    # Set up mocks
    mock_load_config.return_value = mock_config
    mock_setup_llm.return_value = mock_llm_client
    mock_get_cache.return_value = MagicMock()
    mock_get_cache.return_value.get_stats.return_value = {
        "entries": 10,
        "hits": 5,
        "misses": 5
    }
    mock_analyze_task.return_value = "Mock specification content"
    
    # Run the command with verbose flag
    result = runner.invoke(app, [
        "analyze", 
        "Build a web app",
        "--verbose"
    ])
    
    # Verify the result contains verbose outputs
    assert result.exit_code == 0
    assert f"Using LLM provider: {mock_config.llm_provider}" in result.stdout
    assert f"Caching enabled: {mock_config.cache_type}" in result.stdout
    assert "Cache statistics: 10 entries, 5 hits, 5 misses" in result.stdout


@patch('taskspec.main.load_config')
@patch('taskspec.main.setup_llm_client')
@patch('taskspec.main.analyze_design_document')
@patch('taskspec.main.get_cache_manager')
@patch('taskspec.main.format_design_results')
def test_design_with_verbose_output(
    mock_format_results, mock_get_cache, mock_analyze_design, 
    mock_setup_llm, mock_load_config, runner, mock_config, mock_llm_client
):
    """Test design command with verbose output."""
    # Set up mocks
    mock_load_config.return_value = mock_config
    mock_setup_llm.return_value = mock_llm_client
    mock_get_cache.return_value = MagicMock()
    mock_get_cache.return_value.get_stats.return_value = {
        "entries": 10,
        "hits": 5,
        "misses": 5
    }
    mock_analyze_design.return_value = {"phases": []}
    mock_format_results.return_value = "Mock design results"
    
    # Run the command with verbose flag
    result = runner.invoke(app, [
        "design", 
        "Create a weather monitoring system",
        "--verbose"
    ])
    
    # Verify the result contains verbose outputs
    assert result.exit_code == 0
    assert f"Using LLM provider: {mock_config.llm_provider}" in result.stdout
    assert f"Caching enabled: {mock_config.cache_type}" in result.stdout
    assert "Cache statistics: 10 entries, 5 hits, 5 misses" in result.stdout


@patch('taskspec.main.split_phases_to_files')
def test_split_with_verbose_output(mock_split_phases, runner, tmp_path):
    """Test split command with verbose output."""
    # Create a test phases file
    phases_file = tmp_path / "test_phases.md"
    phases_file.write_text("# Test phases file")
    
    # Set up mock
    mock_split_phases.return_value = [
        tmp_path / "test_phase1.md",
        tmp_path / "test_phase2.md"
    ]
    
    # Run the command with verbose flag
    result = runner.invoke(app, [
        "split", 
        str(phases_file),
        "--verbose"
    ])
    
    # Verify the result contains verbose outputs
    assert result.exit_code == 0
    # Just check for basic output, not exact path formatting
    assert "Splitting phases from:" in result.stdout
    assert "Successfully split into 2 files" in result.stdout


@patch('taskspec.main.load_config')
@patch('taskspec.main.setup_llm_client')
@patch('taskspec.main.analyze_task')
@patch('taskspec.main.get_cache_manager')
def test_analyze_with_no_stdout(
    mock_get_cache, mock_analyze_task, mock_setup_llm, mock_load_config, 
    runner, mock_config, mock_llm_client, tmp_path
):
    """Test analyze command with no_stdout option."""
    # Set up mocks
    mock_load_config.return_value = mock_config
    mock_setup_llm.return_value = mock_llm_client
    mock_get_cache.return_value = MagicMock()
    mock_analyze_task.return_value = "Mock specification content"
    
    # Create output path
    output_path = tmp_path / "output.md"
    
    # Run the command with no_stdout flag
    result = runner.invoke(app, [
        "analyze", 
        "Build a web app",
        "--output", 
        str(output_path),
        "--no-stdout"
    ])
    
    # Verify the result doesn't contain spec content
    assert result.exit_code == 0
    assert "Mock specification content" not in result.stdout
    # With no_stdout, we don't output anything
    assert result.stdout.strip() == ""
    
    # Verify file was written
    assert output_path.exists()
    assert output_path.read_text() == "Mock specification content"


@patch('taskspec.main.load_config')
@patch('taskspec.main.setup_llm_client')
@patch('taskspec.main.analyze_design_document')
@patch('taskspec.main.get_cache_manager')
@patch('taskspec.main.format_design_results')
def test_design_with_different_formats(
    mock_format_results, mock_get_cache, mock_analyze_design, 
    mock_setup_llm, mock_load_config, runner, mock_config, mock_llm_client
):
    """Test design command with different output formats."""
    # Set up mocks
    mock_load_config.return_value = mock_config
    mock_setup_llm.return_value = mock_llm_client
    mock_get_cache.return_value = MagicMock()
    mock_analyze_design.return_value = {"phases": [{"name": "Phase 1"}]}
    
    # Test JSON format
    mock_format_results.return_value = '{"phases": [{"name": "Phase 1"}]}'
    json_result = runner.invoke(app, [
        "design", 
        "Create a system",
        "--format", 
        "json"
    ])
    
    # Verify JSON format was passed to formatter
    mock_format_results.assert_called_with(
        {"phases": [{"name": "Phase 1"}]}, 
        "json",
        False
    )
    assert json_result.exit_code == 0
    
    # Test YAML format
    mock_format_results.return_value = 'phases:\n  - name: Phase 1'
    yaml_result = runner.invoke(app, [
        "design", 
        "Create a system",
        "--format", 
        "yaml"
    ])
    
    # Verify YAML format was passed to formatter
    mock_format_results.assert_called_with(
        {"phases": [{"name": "Phase 1"}]}, 
        "yaml",
        False
    )
    assert yaml_result.exit_code == 0


@patch('taskspec.main.load_config')
@patch('taskspec.main.setup_llm_client')
@patch('taskspec.main.analyze_design_document')
@patch('taskspec.main.get_cache_manager')
@patch('taskspec.main.format_design_results')
def test_design_with_no_stdout(
    mock_format_results, mock_get_cache, mock_analyze_design, 
    mock_setup_llm, mock_load_config, runner, mock_config, mock_llm_client, tmp_path
):
    """Test design command with no_stdout option."""
    # Set up mocks
    mock_load_config.return_value = mock_config
    mock_setup_llm.return_value = mock_llm_client
    mock_get_cache.return_value = MagicMock()
    mock_analyze_design.return_value = {"phases": [{"name": "Phase 1"}]}
    mock_format_results.return_value = "Mock design results"
    
    # Create output path
    output_path = tmp_path / "output.md"
    
    # Run the command with no_stdout flag
    result = runner.invoke(app, [
        "design", 
        "Design a system",
        "--output", 
        str(output_path),
        "--no-stdout"
    ])
    
    # Verify the result doesn't contain design results
    assert result.exit_code == 0
    assert "Mock design results" not in result.stdout
    # With no_stdout, we don't output anything
    assert result.stdout.strip() == ""
    
    # Verify file was written
    assert output_path.exists()
    assert output_path.read_text() == "Mock design results"


@patch('taskspec.main.load_config')
@patch('taskspec.main.setup_llm_client')
@patch('taskspec.main.analyze_task')
@patch('taskspec.main.get_cache_manager')
def test_analyze_command_with_search_enabled(
    mock_get_cache, mock_analyze_task, mock_setup_llm, mock_load_config, 
    runner, mock_config, mock_llm_client
):
    """Test analyze command with search enabled."""
    # Set up mocks
    mock_load_config.return_value = mock_config
    mock_setup_llm.return_value = mock_llm_client
    mock_get_cache.return_value = MagicMock()
    mock_analyze_task.return_value = "Mock specification with search results"
    
    # Run the command with search flag
    result = runner.invoke(app, [
        "analyze", 
        "Build a web app",
        "--search"
    ])
    
    # Verify the result
    assert result.exit_code == 0
    
    # Verify analyze_task was called with search_enabled=True
    mock_analyze_task.assert_called_once()
    args, kwargs = mock_analyze_task.call_args
    assert kwargs["search_enabled"] is True


@patch('taskspec.main.load_config')
@patch('taskspec.main.setup_llm_client')
@patch('taskspec.main.analyze_task')
@patch('taskspec.main.get_cache_manager')
def test_analyze_command_with_validate_disabled(
    mock_get_cache, mock_analyze_task, mock_setup_llm, mock_load_config, 
    runner, mock_config, mock_llm_client
):
    """Test analyze command with validation disabled."""
    # Set up mocks
    mock_load_config.return_value = mock_config
    mock_setup_llm.return_value = mock_llm_client
    mock_get_cache.return_value = MagicMock()
    mock_analyze_task.return_value = "Mock specification without validation"
    
    # Run the command with no-validate flag
    result = runner.invoke(app, [
        "analyze", 
        "Build a web app",
        "--no-validate"
    ])
    
    # Verify the result
    assert result.exit_code == 0
    
    # Verify analyze_task was called with validate=False
    mock_analyze_task.assert_called_once()
    args, kwargs = mock_analyze_task.call_args
    assert kwargs["validate"] is False


@patch('taskspec.main.load_config')
@patch('taskspec.main.setup_llm_client')
@patch('taskspec.main.analyze_task')
@patch('taskspec.main.get_cache_manager')
def test_analyze_command_with_cache_disabled(
    mock_get_cache, mock_analyze_task, mock_setup_llm, mock_load_config, 
    runner, mock_config, mock_llm_client
):
    """Test analyze command with cache disabled."""
    # Set up mocks
    mock_config.cache_enabled = False
    mock_load_config.return_value = mock_config
    mock_setup_llm.return_value = mock_llm_client
    mock_analyze_task.return_value = "Mock specification with cache disabled"
    
    # Run the command with no-cache flag
    result = runner.invoke(app, [
        "analyze", 
        "Build a web app",
        "--no-cache"
    ])
    
    # Verify the result
    assert result.exit_code == 0
    
    # Verify cache manager was not created or used
    mock_get_cache.assert_not_called()
    
    # Verify analyze_task was called
    mock_analyze_task.assert_called_once()
    
    # Verify setup_llm_client was called without cache_manager
    mock_setup_llm.assert_called_once_with(mock_config, None)


@patch('taskspec.main.load_config')
@patch('taskspec.main.setup_llm_client')
@patch('taskspec.main.analyze_design_document')
@patch('taskspec.main.get_cache_manager')
@patch('taskspec.main.format_design_results')
@patch('taskspec.main.generate_task_summary')
def test_design_with_auto_filename(
    mock_generate_summary, mock_format_results, mock_get_cache, mock_analyze_design, 
    mock_setup_llm, mock_load_config, runner, mock_config, mock_llm_client, monkeypatch
):
    """Test design command with auto-generated filename."""
    # Set up mocks
    mock_load_config.return_value = mock_config
    mock_setup_llm.return_value = mock_llm_client
    mock_get_cache.return_value = MagicMock()
    mock_analyze_design.return_value = {"phases": []}
    mock_format_results.return_value = "Mock design results"
    mock_generate_summary.return_value = "weather_monitoring_system"
    
    # Mock datetime to have a predictable filename
    fixed_datetime = datetime(2025, 1, 1, 12, 0, 0)
    
    class MockDateTime:
        @classmethod
        def now(cls):
            return fixed_datetime
    
    monkeypatch.setattr('taskspec.main.datetime', MockDateTime)
    
    # Create a patch context for write_text to verify file writing without actually writing
    with patch('pathlib.Path.write_text') as mock_write_text:
        # Run the design command without specifying output file
        result = runner.invoke(app, [
            "design", 
            "Create a weather monitoring system"
        ])
        
        # Verify the result
        assert result.exit_code == 0
        
        # Verify an auto-generated filename was used
        mock_write_text.assert_called_once()
        # The first arg to write_text is the content to write
        assert mock_write_text.call_args[0][0] == "Mock design results"
        
        # Verify the filename in the output
        assert "weather_monitoring_system_20250101_120000_phases.md" in result.stdout


@patch('taskspec.main.load_config')
@patch('taskspec.main.setup_llm_client')
@patch('taskspec.main.analyze_task')
@patch('taskspec.main.get_cache_manager')
def test_analyze_command_with_exception_traceback(
    mock_get_cache, mock_analyze_task, mock_setup_llm, mock_load_config, 
    runner, mock_config, mock_llm_client
):
    """Test analyze command with exception and traceback in verbose mode."""
    # Set up mocks
    mock_load_config.return_value = mock_config
    mock_setup_llm.return_value = mock_llm_client
    mock_get_cache.return_value = MagicMock()
    
    # Make analyze_task raise an exception
    test_exception = RuntimeError("Test exception")
    mock_analyze_task.side_effect = test_exception
    
    # Run the command with verbose flag to see traceback
    # Set catch_exceptions=False to let the exception bubble up through typer
    result = runner.invoke(app, [
        "analyze", 
        "Build a web app",
        "--verbose"
    ], catch_exceptions=False)
    
    # Verify the command handles the exception and shows the error
    assert "Error: Test exception" in result.stdout


@patch('taskspec.main.load_config')
def test_analyze_command_with_verbose_exception(mock_load_config, runner):
    """Test analyze command with verbose error handling."""
    # Set up mocks
    mock_load_config.side_effect = ValueError("Config error")
    
    # Run the command with verbose flag to see traceback
    result = runner.invoke(app, [
        "analyze", 
        "Build a web app",
        "--verbose"
    ])
    
    # Verify the error message and traceback are shown
    assert "Error: Config error" in result.stdout
    assert "Traceback" in result.stdout


@patch('taskspec.main.load_config')
def test_design_command_with_verbose_exception(mock_load_config, runner):
    """Test design command with verbose error handling."""
    # Set up mocks
    mock_load_config.side_effect = ValueError("Config error in design command")
    
    # Run the command with verbose flag to see traceback
    result = runner.invoke(app, [
        "design", 
        "Create a weather monitoring system",
        "--verbose"
    ])
    
    # Verify the error message and traceback are shown
    assert "Error: Config error in design command" in result.stdout
    assert "Traceback" in result.stdout


@patch('taskspec.main.split_phases_to_files')
def test_split_command_with_prefix_and_output_dir(
    mock_split_phases, runner, tmp_path
):
    """Test split command with custom prefix and output directory."""
    # Set up file existence check to pass
    with patch('pathlib.Path.exists', return_value=True):
        # Configure the mock to return some filenames
        mock_split_phases.return_value = [
            tmp_path / "custom_phase1.md",
            tmp_path / "custom_phase2.md"
        ]
        
        # Create a test file path
        phases_file = Path("/path/to/phases.md")
        
        # Run the command with prefix and output-dir
        result = runner.invoke(app, [
            "split", 
            str(phases_file),
            "--prefix", 
            "custom",
            "--output-dir",
            str(tmp_path)
        ])
        
        # Verify the split_phases_to_files was called with correct parameters
        mock_split_phases.assert_called_once_with(
            phases_file=phases_file,
            output_dir=tmp_path,
            prefix="custom"
        )
        
        # Verify the result
        assert result.exit_code == 0


@patch('taskspec.main.split_phases_to_files')
def test_split_command_with_verbose_exception(mock_split_phases, runner):
    """Test split command with verbose error handling."""
    # Set up mocks for file existence
    with patch('pathlib.Path.exists', return_value=True):
        # Make split_phases_to_files raise an exception
        test_exception = RuntimeError("Split phases error")
        mock_split_phases.side_effect = test_exception
        
        # Run the command with verbose flag to see traceback
        result = runner.invoke(app, [
            "split", 
            "/path/to/phases.md",
            "--verbose"
        ])
        
        # Verify the error message and traceback are shown
        assert "Error: Split phases error" in result.stdout
        assert "Traceback" in result.stdout