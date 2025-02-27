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
- Overall coverage: 88%
- Full coverage: cache/memory_cache.py, config.py, search.py
- High coverage: template.py (95%), disk_cache.py (93%), analyzer.py (91%), 
  design.py (81%), llm.py (85%)
- Moderate coverage: main.py (56%)
- Total test count: 53 tests

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