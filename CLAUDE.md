# TaskSpec Development Guide

## Build & Run Commands
- Run application: `ts`
- Run specific task: `ts analyze "Task description"`
- Run with input file: `ts analyze --input task.txt`
- Use wrapper script directly: `./bin/ts analyze "Task description"`
- Install dependencies: `uv pip install -e .` or `pip install -e .`
- Install dev dependencies: `uv pip install -e ".[dev]"` or `pip install -e ".[dev]"`
- Install ts command: `python3 bin/install_ts`

## Testing Commands
- Run all tests: `uv run -m pytest`
- Run specific test module: `uv run -m pytest tests/test_file.py`
- Run specific test function: `uv run -m pytest tests/test_file.py::test_function`
- Run with coverage: `uv run -m pytest --cov=taskspec`
- Generate coverage report: `uv run -m pytest --cov=taskspec --cov-report=html`
- Run verbose tests: `uv run -m pytest -v` 

### Comprehensive Test Script
Use the run_tests.py script for running tests and cleaning up artifacts:
- Run unit tests for specific modules: `./run_tests.py --unit --module main utils`
- Run unit tests with coverage report: `./run_tests.py --unit --all --report`
- Clean up test artifacts: `./run_tests.py --clean`
- Preview cleanup without deleting: `./run_tests.py --clean --dry-run`
- Full test suite with cleanup: `./run_tests.py --unit --all --report --clean`
- Use custom output directory: `./run_tests.py --unit --all --output-dir test_results`

All test output files (coverage reports, etc.) will be organized in the "test_output" 
directory by default to keep the filesystem clean. You can specify a custom output 
directory with the --output-dir flag.

## Simple Mutation Testing Demo
For a quick demonstration of how mutation testing works, run:
- `./run_mutation_simple.py`

This script applies mutations to a sample file and verifies that tests can detect them.

Note: The full mutation testing features requiring mutmut may not be working properly in the 
current environment. If you need to run mutation tests on actual project files, you'll
need to install mutmut directly: `uv pip install mutmut` and then run the commands
manually according to the mutmut documentation.

## Test Status (as of latest run)
- Overall coverage: ~65%
- Full coverage: cache/memory_cache.py, cache/base.py, config.py, search.py, template.py
- High coverage: disk_cache.py (93%), analyzer.py (92%), llm.py (89%)
- Moderate coverage: utils.py (79%)
- Lower coverage: design.py (56%), python_detector.py (13%)
- Not covered: main.py in root directory (0%)
- Total test count: 151 tests

## Code Style Guidelines
- Use Python 3.12+ features
- Follow PEP 8 conventions for naming and formatting
- Type hints required for all function parameters and return values
- Imports order: stdlib → third-party → local modules
- Error handling: use try/except with specific exceptions
- Use f-strings for string formatting
- Document all functions with docstrings ("""description + Args/Returns""")
- For imports across modules use `from taskspec.module import X`

## Python Command Detection
The `ts` command and test scripts automatically detect the appropriate Python command with this priority:
1. uv (if available)
2. python3 (if available)
3. python (only if it's Python 3.x)

This makes the application and tests work across different Python environments without manual configuration.

## Architecture Guidelines
- Modular design with clear separation of concerns
- Cache implementation follows base.py interface
- Use pydantic models for data validation
- Rich library for console output formatting
- Configuration via environment variables or .env files

## Testing Guidelines
- Write unit tests for all new functionality
- Mock external dependencies (especially LLM calls)
- Use pytest fixtures for common test setup
- Include tests for edge cases and error handling
- Use patch decorators for mocking functions