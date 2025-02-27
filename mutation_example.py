"""
A simple example file to demonstrate mutation testing.
"""

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