# TaskSpec Development Guide

## Build & Run Commands
- Run application: `python -m taskspec.main`
- Run specific task: `python -m taskspec.main "Task description"`
- Run with input file: `python -m taskspec.main --input task.txt`
- Install dependencies: `uv install` or `pip install -e .`
- Install dev dependencies: `pip install -e ".[dev]"`

## Testing Commands
- Run all tests: `pytest`
- Run specific test module: `pytest tests/test_file.py`
- Run specific test function: `pytest tests/test_file.py::test_function`
- Run with coverage: `pytest --cov=taskspec`
- Generate coverage report: `pytest --cov=taskspec --cov-report=html`
- Run verbose tests: `pytest -v` 

### Comprehensive Test Script
Use the comprehensive test script for running tests and cleaning up artifacts:
- Run unit tests for specific modules: `./run_tests.py --unit --module main utils`
- Run unit tests with coverage report: `./run_tests.py --unit --all --report`
- Run mutation tests: `./run_tests.py --mutation --module utils --max-mutations 5` 
- Clean up test artifacts: `./run_tests.py --clean`
- Preview cleanup without deleting: `./run_tests.py --clean --dry-run`
- Full test suite with cleanup: `./run_tests.py --unit --all --report --clean`
- Use custom output directory: `./run_tests.py --unit --all --output-dir test_results`

All test output files (coverage reports, mutation reports, etc.) will be organized 
in the "test_output" directory by default to keep the filesystem clean. You can 
specify a custom output directory with the --output-dir flag.

## Mutation Testing Commands
- Run mutation tests: `mutmut run`
- Show mutation test results: `mutmut results`
- Show specific mutation: `mutmut show <id>`
- Apply a mutation: `mutmut apply <id>`
- Generate HTML report: `mutmut html`

### Helper Script for Mutation Testing
- List available modules: `./run_mutation_tests.py --list`
- Test specific module: `./run_mutation_tests.py <module_name>`
- Test all modules: `./run_mutation_tests.py --all`
- Generate HTML report: `./run_mutation_tests.py <module_name> --report`

## Test Status (as of latest run)
- Overall coverage: ~90%
- Full coverage: cache/memory_cache.py, cache/base.py, config.py, search.py, template.py
- High coverage: disk_cache.py (93%), analyzer.py (92%), llm.py (89%), design.py (82%), main.py (92%), utils.py (~92%)
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

## Mutation Testing
- Basic demo: `./run_mutation_simple.py`
- Review example mutations in: `docs/mutation_testing_guide.md`
- Examine our mutation examples in: `mutation_examples.md`
- See real-world examples in: `mutation_example.py` and `tests/test_mutation_example.py`
- Run targeted tests on main.py and utils.py: `./run_mutation_main_utils.py`
  - Test specific module: `./run_mutation_main_utils.py --module main`
  - Test both modules: `./run_mutation_main_utils.py --module both`
  - Generate HTML report: `./run_mutation_main_utils.py --report`

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