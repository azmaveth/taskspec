import subprocess
import sys
from pathlib import Path
import os
import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--run-e2e", action="store_true", default=False, help="Run end-to-end tests"
    )


def pytest_runtest_setup(item):
    if "run_e2e" not in item.config.option or not item.config.getoption("run_e2e"):
        if "test_e2e" in str(item.fspath):
            pytest.skip("Skipping E2E tests (use --run-e2e to enable)")

def test_analyze_basic(tmp_path):
    output_file = tmp_path / "spec.md"
    cmd = [
        sys.executable, "-m", "taskspec.main", "analyze",
        "Write a Python function to add two numbers",
        "--output", str(output_file),
        "--no-stdout"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, env={**os.environ, "LLM_MODEL": "llama3.2:latest"})
    assert result.returncode == 0, f"Non-zero exit: {result.stderr}"
    assert output_file.exists(), "Output file was not created"
    content = output_file.read_text()
    assert "Python" in content or "function" in content


def test_design_basic(tmp_path):
    output_file = tmp_path / "design.md"
    cmd = [
        sys.executable, "-m", "taskspec.main", "design",
        "This is a design document for a calculator app",
        "--output", str(output_file),
        "--no-stdout"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, env={**os.environ, "LLM_MODEL": "llama3.2:latest"})
    assert result.returncode == 0, f"Non-zero exit: {result.stderr}"
    assert output_file.exists(), "Output file was not created"
    content = output_file.read_text()
    assert "calculator" in content or "design" in content
def test_help_command():
    cmd = [sys.executable, "-m", "taskspec.main", "--help"]
    result = subprocess.run(cmd, capture_output=True, text=True, env={**os.environ, "LLM_MODEL": "llama3.2:latest"})
    assert result.returncode == 0
    assert "Usage" in result.stdout or "usage" in result.stdout

def test_invalid_command():
    cmd = [sys.executable, "-m", "taskspec.main", "nonexistentcommand"]
    result = subprocess.run(cmd, capture_output=True, text=True, env={**os.environ, "LLM_MODEL": "llama3.2:latest"})
    assert result.returncode != 0
    assert "No such command" in result.stderr or "Error" in result.stderr

def test_split_phases(tmp_path):
    # First generate a design file
    design_file = tmp_path / "design.md"
    cmd_design = [
        sys.executable, "-m", "taskspec.main", "design",
        "Design a simple calculator",
        "--output", str(design_file),
        "--no-stdout"
    ]
    result_design = subprocess.run(cmd_design, capture_output=True, text=True, env={**os.environ, "LLM_MODEL": "llama3.2:latest"})
    assert result_design.returncode == 0
    assert design_file.exists()

    # Now split the design file into phases
    cmd_split = [
        sys.executable, "-m", "taskspec.main", "split",
        str(design_file),
        "--output-dir", str(tmp_path / "phases")
    ]
    result_split = subprocess.run(cmd_split, capture_output=True, text=True, env={**os.environ, "LLM_MODEL": "llama3.2:latest"})
    assert result_split.returncode == 0
    phases_dir = tmp_path / "phases"
    assert phases_dir.exists()
    phase_files = list(phases_dir.glob("*.md"))
    assert len(phase_files) > 0, "No phase files were created"
