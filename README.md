# taskspec

A Python CLI tool that uses LLMs to analyze tasks, break them down into manageable subtasks, and generate structured specification documents.

## Features

- Analyzes tasks and generates comprehensive specifications
- Breaks down tasks into actionable subtasks
- Multi-step analysis process for higher quality results
- Task validation to ensure specifications are complete and actionable
- Custom template support for tailored output formats
- Progress monitoring with rich progress bars
- Response caching system to improve performance and reduce API costs
- Supports multiple LLM providers (Ollama, OpenAI, Anthropic, etc.)
- Input from command line or files
- Optional web search for additional context
- Outputs to stdout or file
- Split phases into individual files for easier management
- Filename generation based on intelligent task summarization
- Configurable via CLI arguments, environment variables, or .env file

## Installation

```bash
# Clone the repository
git clone https://github.com/azmaveth/taskspec.git
cd taskspec

# Install with uv (recommended)
uv install

# Or using pip
pip install -e .
```

## Usage

```bash
# Basic usage
python -m taskspec.main "Build a REST API for a book inventory system"

# Input from file
python -m taskspec.main --input task_description.txt

# Specify output file
python -m taskspec.main "Build a REST API for a book inventory system" --output book_api_spec.md

# Use a different LLM provider and model
python -m taskspec.main "Build a REST API for a book inventory system" --provider openai --model gpt-4o

# Use a custom template
python -m taskspec.main "Build a REST API for a book inventory system" --template my_template.md

# Enable web search for additional context
python -m taskspec.main "Build a REST API for a book inventory system" --search

# Disable validation
python -m taskspec.main "Build a REST API for a book inventory system" --no-validate

# Disable caching
python -m taskspec.main "Build a REST API for a book inventory system" --no-cache

# Use memory cache instead of disk cache
python -m taskspec.main "Build a REST API for a book inventory system" --cache-type memory

# Set custom cache TTL (time-to-live)
python -m taskspec.main "Build a REST API for a book inventory system" --cache-ttl 3600

# Clear cache before running
python -m taskspec.main "Build a REST API for a book inventory system" --clear-cache

# Split design phases into separate files during generation
python -m taskspec.main design "Design a weather monitoring system" --split-phases

# Split design phases with custom output directory 
python -m taskspec.main design "Design a weather monitoring system" --split-phases --output-dir phases/

# Split an existing phases file
python -m taskspec.main split weather_system_20250225_phases.md

# Split with custom prefix and output directory
python -m taskspec.main split weather_system_20250225_phases.md --prefix weather_app --output-dir implementation/

# Suppress stdout output (only write to file)
python -m taskspec.main "Build a REST API for a book inventory system" --output book_api_spec.md --no-stdout

# Enable verbose output
python -m taskspec.main "Build a REST API for a book inventory system" --verbose
```

## Configuration

taskspec can be configured using:

1. Command-line arguments (highest priority)
2. Environment variables
3. `.env` file in the current directory

### Environment Variables

- `LLM_PROVIDER`: LLM provider to use (default: "ollama")
- `LLM_MODEL`: LLM model to use (default provider-specific)
- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key
- `COHERE_API_KEY`: Cohere API key
- `BRAVE_API_KEY`: Brave Search API key
- `MAX_SEARCH_RESULTS`: Maximum number of search results to retrieve (default: 5)
- `MULTI_STEP_ENABLED`: Enable multi-step analysis process (default: true)
- `VALIDATION_ENABLED`: Enable specification validation (default: true)
- `MAX_VALIDATION_ITERATIONS`: Maximum validation iterations (default: 3)
- `CACHE_ENABLED`: Enable response caching (default: true)
- `CACHE_TYPE`: Cache type to use ("disk" or "memory", default: "disk")
- `CACHE_TTL`: Cache time-to-live in seconds (default: 86400)
- `CACHE_PATH`: Custom path for cache storage

## Output Format

By default, the generated specification follows this template (can be customized):

```markdown
# Specification Template
> Ingest the information from this file, implement the Low-Level Tasks, and generate the code that will satisfy the High and Mid-Level Objectives.
## High-Level Objective
- [High level goal goes here - what do you want to build?]
## Mid-Level Objective
- [List of mid-level objectives - what are the steps to achieve the high-level objective?]
- [Each objective should be concrete and measurable]
- [But not too detailed - save details for implementation notes]
## Implementation Notes
- [Important technical details - what are the important technical details?]
- [Dependencies and requirements - what are the dependencies and requirements?]
- [Coding standards to follow - what are the coding standards to follow?]
- [Other technical guidance - what are other technical guidance?]
## Context
### Beginning context
- [List of files that exist at start - what files exist at start?]
### Ending context  
- [List of files that will exist at end - what files will exist at end?]
## Low-Level Tasks
> Ordered from start to finish
1. [First task - what is the first task?]
```aider
What prompt would you run to complete this task?
What file do you want to CREATE or UPDATE?
What function do you want to CREATE or UPDATE?
What are details you want to add to drive the code changes?
What command should be run to test that the changes are correct?
```
```

## Testing

TaskSpec includes a comprehensive test suite with both unit tests and mutation tests. To run tests:

```bash
# Run all unit tests
pytest

# Run tests with coverage report
pytest --cov=taskspec --cov-report=html

# Clean up test artifacts and run specific tests
./run_tests.py --clean --unit --module utils main

# Run mutation tests on specific modules
./run_tests.py --mutation --module utils --max-mutations 5

# Use a custom output directory for all test files
./run_tests.py --unit --all --report --output-dir test_results

# See all testing options
./run_tests.py --help
```

All test output files and artifacts are automatically stored in the `test_output` directory:
- Coverage reports and mutation test results
- All `.md` files generated during tests
- Phase files created by the split functionality
- Any auto-generated specification files

This keeps the main project directory clean. You can specify a custom output directory with the `--output-dir` flag when running tests.

## License

MIT
