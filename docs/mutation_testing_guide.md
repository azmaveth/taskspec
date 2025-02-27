# Mutation Testing Guide for TaskSpec

Mutation testing is a technique to evaluate the quality of your tests by introducing small changes (mutations) to the source code and verifying if the tests catch these changes. This guide explains how to implement mutation testing for the TaskSpec project.

## What is Mutation Testing?

Traditional code coverage only tells you which lines of code are executed by your tests, but not whether your tests are actually verifying the functionality correctly. Mutation testing helps address this by:

1. Introducing small changes (mutations) to your source code
2. Running your test suite against each mutation
3. If tests pass with the mutation, it suggests your tests aren't thorough enough
4. If tests fail, the mutation is "killed," indicating your tests are working well

## Basic Mutation Operators

Mutations typically involve simple code changes like:

- Replacing arithmetic operators: `+` → `-`, `*` → `/`, etc.
- Changing comparison operators: `>` → `>=`, `==` → `!=`, etc.
- Removing conditionals: deleting if/else statements
- Altering boolean logic: `and` → `or`, `True` → `False`, etc.
- Modifying return values
- Replacing constants with other values

## Why Mutation Testing?

- **Finds test gaps**: Identifies weaknesses in test suites even with 100% line coverage
- **Improves test quality**: Encourages writing more effective assertions
- **Code quality**: Well-tested code is generally more robust and maintainable

## Setting Up Mutation Testing for TaskSpec

### 1. Installation

The preferred mutation testing library for TaskSpec is mutmut:

```bash
pip install mutmut
```

Or use the project's development dependencies:

```bash
pip install -e ".[dev]"
```

### 2. Configuration

TaskSpec uses configuration in `pyproject.toml`:

```toml
[tool.mutmut]
paths_to_mutate = "."
backup = false
runner = "pytest -xvs"
tests_dir = "tests/"
exclude = """
tests/
venv/
__pycache__/
cache/__pycache__/
htmlcov/
setup.py
run_mutation_tests.py
"""
```

### 3. Helper Script

To make mutation testing easier, TaskSpec includes `run_mutation_tests.py`:

```bash
# List available modules
./run_mutation_tests.py --list

# Test a specific module with limited mutations
./run_mutation_tests.py config --max-mutations 5

# Generate an HTML report
./run_mutation_tests.py config --report
```

### 4. Interpreting Results

Mutmut will report:

- **Killed mutants**: Tests detected the change (good)
- **Survived mutants**: Tests didn't detect the change (bad)
- **Timeout or error**: Mutation caused the tests to hang or error

A good mutation score (% of killed mutants) should be as high as possible.

## Example: Manual Mutation Analysis

Consider this simple function in `mutation_example.py`:

```python
def is_positive(a):
    """Check if a number is positive."""
    return a > 0
```

With tests:

```python
def test_is_positive():
    assert is_positive(5) is True
    assert is_positive(0) is False
    assert is_positive(-5) is False
```

Potential mutations:
- Change `a > 0` to `a >= 0` (caught by test since is_positive(0) would return True)
- Change `a > 0` to `a < 0` (caught because is_positive(5) would return False)
- Change `a > 0` to `a == 0` (caught because both is_positive(5) and is_positive(-5) would return False)

But if we mutation `a > 0` to `a > -10 or a > 0`, our tests won't catch it since we don't have a test with a value less than -10.

## Best Practices

1. **Start small**: Focus on critical modules first
2. **Use timeouts**: Mutation testing can be time-consuming
3. **Be selective**: Some mutations might be impractical to catch
4. **Improve tests**: Add test cases for any survived mutations that matter
5. **Integrate regularly**: Run mutation tests periodically, not just once

## Conclusion

Mutation testing complements traditional code coverage by ensuring your tests actually detect code changes. By running mutation tests regularly on TaskSpec, you can increase confidence in your test suite's effectiveness and catch more bugs before they reach production.