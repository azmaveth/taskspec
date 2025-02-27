# Mutation Testing Examples

Mutation testing introduces small changes (mutations) to the source code and runs tests to see if they catch the changes. This document shows examples of potential mutations and whether our tests would catch them.

## Original Functions

```python
def add(a, b):
    """Add two numbers."""
    return a + b

def subtract(a, b):
    """Subtract b from a."""
    return a - b

def multiply(a, b):
    """Multiply two numbers."""
    return a * b

def divide(a, b):
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

def is_positive(a):
    """Check if a number is positive."""
    return a > 0

def is_even(a):
    """Check if a number is even."""
    return a % 2 == 0
```

## Example Mutations

### Mutation 1: Change operator in add
```python
def add(a, b):
    """Add two numbers."""
    return a - b  # Changed from a + b
```
This mutation would be caught by our tests since `add(1, 2)` would return -1 instead of 3.

### Mutation 2: Change operator in subtract
```python
def subtract(a, b):
    """Subtract b from a."""
    return a + b  # Changed from a - b
```
This mutation would be caught by our tests since `subtract(3, 2)` would return 5 instead of 1.

### Mutation 3: Change operator in multiply
```python
def multiply(a, b):
    """Multiply two numbers."""
    return a / b  # Changed from a * b
```
This mutation would be caught by our tests since `multiply(2, 3)` would return 0.6666... instead of 6.

### Mutation 4: Remove error condition in divide
```python
def divide(a, b):
    """Divide a by b."""
    # if b == 0:
    #    raise ValueError("Cannot divide by zero")
    return a / b
```
This mutation would be caught by our tests since `divide(5, 0)` would raise a ZeroDivisionError instead of ValueError.

### Mutation 5: Change comparison in is_positive
```python
def is_positive(a):
    """Check if a number is positive."""
    return a >= 0  # Changed from a > 0
```
This mutation would be caught by our tests since `is_positive(0)` would return True instead of False.

### Mutation 6: Invert logic in is_even
```python
def is_even(a):
    """Check if a number is even."""
    return a % 2 != 0  # Changed from a % 2 == 0
```
This mutation would be caught by our tests since `is_even(2)` would return False instead of True.

## Example of a Mutation That Would Not Be Caught

```python
def is_positive(a):
    """Check if a number is positive."""
    # For numbers less than -10, the function now returns True
    if a < -10:
        return True
    return a > 0
```

Our tests would not catch this mutation because we don't have a test case with a number less than -10.