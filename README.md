# TaskSpec

TaskSpec is a Python CLI tool that uses LLMs to analyze tasks, break them down into manageable subtasks, and generate structured specification documents. It's designed to assist in planning and implementing software projects by providing detailed task analysis.

## Features

- Analyzes tasks and generates comprehensive specifications
- Breaks down tasks into actionable subtasks
- Interactive design mode with guided dialog for system design
- Automatic analysis of subtasks from design documents
- Supports multiple LLM providers (Ollama, OpenAI, Anthropic, Cohere)
- Response caching system to improve performance and reduce API costs
- Optional web search for additional context
- Split phases into individual files for easier management

## Installation

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Quick Installation

```bash
# Clone the repository
git clone https://github.com/azmaveth/taskspec.git
cd taskspec

# Install dependencies using uv (recommended)
uv pip install -e .

# Or using standard pip
pip install -e .

# Install the 'ts' command to your PATH (recommended)
bin/install_ts
```

The `install_ts` script will:
1. Create a wrapper script named `ts` in your user's bin directory
2. Make the script executable
3. Add the directory to your PATH if needed (with instructions)

After installation, you might need to restart your terminal or run `source ~/.bashrc` (or equivalent) to update your PATH.

## Running TaskSpec

### Method 1: Using the installed `ts` command (recommended)

After running the `install_ts` script, you can use the `ts` command from anywhere:

```bash
# Check if installation was successful
ts --help

# Run a task analysis
ts analyze "Build a REST API for a book inventory system"

# Design a system interactively
ts design --interactive
```

The `ts` command automatically detects whether to use `uv`, `python3`, or `python` based on what's available in your environment.

### Method 2: Using the repository wrapper script

If you haven't installed the `ts` command to your PATH, you can still use the wrapper script directly:

```bash
# From the taskspec directory
./bin/ts analyze "Build a REST API for a book inventory system"
```

### Method 3: Direct execution with uv

```bash
# From the taskspec directory
uv run main.py analyze "Build a REST API for a book inventory system"
```

### Method 4: Direct execution with Python

```bash
# From the taskspec directory
python3 main.py analyze "Build a REST API for a book inventory system"
```

## Commands

TaskSpec offers several commands for different use cases:

### analyze

Analyze a task, break it down into subtasks, and generate a specification document.

```bash
ts analyze "Build a simple note-taking app with Flask"

# Use a file as input
ts analyze --input task_description.txt

# Specify output file
ts analyze "Build a REST API" --output api_spec.md

# Use a specific LLM provider and model
ts analyze "Build a REST API" --provider openai --model gpt-4o

# Add web search for additional context
ts analyze "Build a REST API" --search

# Enable verbose output
ts analyze "Build a REST API" --verbose
```

### design

Analyze a design document, break it into implementation phases and subtasks.

```bash
# Process an existing design document
ts design --input design_document.md

# Create a design document through interactive dialog
ts design --interactive

# Split design phases into separate files
ts design --input design_document.md --split-phases

# Analyze subtasks and generate specifications for each
ts design --input design_document.md --analyze-subtasks

# Output in JSON format
ts design --input design_document.md --format json
```

### split

Split a phases markdown file into separate files.

```bash
# Split a phases file
ts split path/to/phases.md

# Specify output directory and prefix
ts split path/to/phases.md --output-dir phases/ --prefix project
```

## Cache Management

TaskSpec includes a caching system to improve performance and reduce API costs:

```bash
# Disable caching
ts analyze "Build a REST API" --no-cache

# Use memory cache instead of disk cache
ts analyze "Build a REST API" --cache-type memory

# Set custom cache time-to-live (in seconds)
ts analyze "Build a REST API" --cache-ttl 3600

# Clear cache before running
ts analyze "Build a REST API" --clear-cache
```

## Configuration

TaskSpec can be configured using:

1. Command-line arguments (highest priority)
2. Environment variables
3. `.env` file in the current directory

### Using a .env File

The easiest way to configure TaskSpec is to copy the provided `.env.example` file to `.env` and modify it as needed:

```bash
# Copy the example file
cp .env.example .env

# Edit the .env file with your preferred editor
vim .env  # or nano .env, code .env, etc.
```

The `.env.example` file contains all available configuration options with their default values and helpful comments.

### Environment Variables

- `LLM_PROVIDER`: The LLM provider to use (default: "ollama")
- `LLM_MODEL`: The LLM model to use (default depends on provider)
- `OUTPUT_DIRECTORY`: Directory where output files will be saved (default: "output")
- `CACHE_ENABLED`: Enable response caching (default: true)
- `CACHE_TYPE`: Cache type (memory or disk, default: disk)
- `CACHE_PATH`: Path for the disk cache (default: ~/.taskspec/cache.db)
- `CACHE_TTL`: Time-to-live for cache entries in seconds (default: 86400 - 24 hours)

### API Keys

Configure API keys for various services:
- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key
- `COHERE_API_KEY`: Cohere API key
- `BRAVE_API_KEY`: Brave API key (for web search)

## Testing

TaskSpec includes comprehensive test suites that work with different Python environments:

```bash
# Run all tests directly with pytest
uv run -m pytest

# Run tests with coverage
uv run -m pytest --cov=taskspec

# Run a specific test module
uv run -m pytest tests/test_analyzer.py

# Run a specific test function
uv run -m pytest tests/test_analyzer.py::test_format_time

# Generate coverage report
uv run -m pytest --cov=taskspec --cov-report=html
```

The project also provides a test helper script for additional functionality:

```bash
# Run unit tests for specific modules
./run_tests.py --unit --module analyzer utils

# Run all unit tests
./run_tests.py --unit --all

# Clean up test artifacts
./run_tests.py --clean

# Preview files to clean without deleting
./run_tests.py --clean --dry-run

# Use a custom output directory for all test files
./run_tests.py --unit --all --report --output-dir test_results

# See all testing options
./run_tests.py --help
```

### Mutation Testing

TaskSpec supports mutation testing through both automated and manual approaches:

```bash
# Install mutation testing dependencies in a virtual environment
uv venv .local-venv
source .local-venv/bin/activate
uv pip install mutmut pytest pytest-cov pytest-timeout
uv pip install -e .

# Run mutation tests on a specific module
python run_mutation_tests.py --list  # See available modules
python run_mutation_tests.py cache/base

# Run the simplified manual mutation testing script
python manual_mutation_test.py
```

Mutation testing is useful for evaluating test suite quality by introducing small changes (mutations) to the code and verifying that tests can detect them. The project includes:

- `run_mutation_tests.py`: Configures and runs mutmut-based mutation tests
- `manual_mutation_test.py`: A more direct approach that applies specific mutations
- `run_mutation_simple.py`: A quick demonstration of mutation testing principles

The test scripts automatically detect and use the appropriate Python command, with the following priority:
1. uv (if available)
2. python3 (if available)
3. python (only if it's Python 3.x)

## Troubleshooting

### Common Issues

1. **Command not found: ts**
   - Ensure you've run `python3 bin/install_ts`
   - Check if the installation directory is in your PATH
   - Try restarting your terminal

2. **Module not found errors**
   - Ensure you've installed dependencies with `uv pip install -e .` or `pip install -e .`
   - Make sure you're running the command from the correct directory

3. **Permission errors**
   - Ensure the wrapper scripts are executable (`chmod +x bin/ts bin/install_ts`)

4. **LLM Provider errors**
   - Check that you've configured the correct environment variables for your chosen provider
   - If using Ollama, ensure it's running and available

## License

[MIT License](LICENSE.md)
