"""
Tests for mutation_example.py
"""

import pytest
from mutation_example import add, subtract, multiply, divide, is_positive, is_even

def test_add():
    """Test add function"""
    assert add(1, 2) == 3
    assert add(-1, 1) == 0
    assert add(0, 0) == 0

def test_subtract():
    """Test subtract function"""
    assert subtract(3, 2) == 1
    assert subtract(1, 1) == 0
    assert subtract(0, 5) == -5

def test_multiply():
    """Test multiply function"""
    assert multiply(2, 3) == 6
    assert multiply(-2, 3) == -6
    assert multiply(0, 5) == 0

def test_divide():
    """Test divide function"""
    assert divide(6, 2) == 3
    assert divide(5, 2) == 2.5
    assert divide(0, 5) == 0
    
    with pytest.raises(ValueError):
        divide(5, 0)

def test_is_positive():
    """Test is_positive function"""
    assert is_positive(5) is True
    assert is_positive(0) is False
    assert is_positive(-5) is False

def test_is_even():
    """Test is_even function"""
    assert is_even(2) is True
    assert is_even(0) is True
    assert is_even(3) is False
    assert is_even(-2) is True