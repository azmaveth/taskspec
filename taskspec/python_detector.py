"""
Python command detection utility for TaskSpec.
"""

import subprocess
import sys
from typing import Tuple


def detect_python_command() -> Tuple[str, str]:
    """
    Detect the best available Python command to use.
    Returns a tuple of (command, type) where type is 'uv', 'python3', or 'python'.
    
    The priority order is:
    1. uv
    2. python3
    3. python (only if it's Python 3.x)
    """
    # Check for uv
    try:
        subprocess.run(["uv", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        return "uv run", "uv"
    except FileNotFoundError:
        pass
    
    # Check for python3
    try:
        subprocess.run(["python3", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        return "python3", "python3"
    except FileNotFoundError:
        pass
    
    # Check for python
    try:
        proc = subprocess.run(["python", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                             text=True, check=False)
        output = proc.stdout if proc.stdout else proc.stderr
        
        # Check if it's Python 3.x
        if "Python 3" in output:
            return "python", "python"
    except FileNotFoundError:
        pass
    
    # Default to sys.executable if nothing else works
    return sys.executable, "sys.executable"


def get_python_command_for_pytest() -> str:
    """
    Get the Python command to use specifically for pytest.
    This handles the different formats needed for different Python commands.
    """
    # Try to find pytest executable directly - this is the most reliable method
    try:
        result = subprocess.run(["which", "pytest"], stdout=subprocess.PIPE, text=True, check=False)
        if result.stdout.strip():
            return "pytest"
    except Exception:
        pass
    
    # For uv, we should execute pytest via uv run
    try:
        subprocess.run(["which", "uv"], stdout=subprocess.PIPE, text=True, check=False)
        return "uv run -p pytest pytest"
    except Exception:
        pass
    
    # Fall back to module approach
    command, command_type = detect_python_command()
    
    if command_type == "uv":
        # For uv, we need to install pytest first, then run python with pytest module
        return "python3 -m pytest"
    else:
        return f"{command} -m pytest"
    
    
def get_python_command_for_mutmut() -> str:
    """
    Get the Python command to use specifically for mutmut.
    This handles the different formats needed for different Python commands.
    """
    # Try to find mutmut executable directly
    try:
        result = subprocess.run(["which", "mutmut"], stdout=subprocess.PIPE, text=True, check=False)
        if result.stdout.strip() and "not found" not in result.stdout:
            return "mutmut"
    except Exception:
        pass
    
    # For uv, we should execute mutmut via uv run
    try:
        subprocess.run(["which", "uv"], stdout=subprocess.PIPE, text=True, check=False)
        return "uv run -p mutmut mutmut"
    except Exception:
        pass
    
    # Fall back to module approach
    command, command_type = detect_python_command()
    
    if command_type == "uv":
        # For uv, use python3 with mutmut module
        return "python3 -m mutmut"
    else:
        return f"{command} -m mutmut"