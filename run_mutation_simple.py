#!/usr/bin/env python3
"""
Simple mutation testing script for TaskSpec.

This script creates a simple mutation by modifying a function in mutation_example.py
and then runs the tests to see if they catch the mutation.
"""

import os
import sys
import subprocess
import tempfile
import shutil

# Add parent directory to sys.path so we can import from taskspec
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Python detector
from taskspec.python_detector import get_python_command_for_pytest


def make_mutation(mutation_type):
    """Create a mutation in mutation_example.py."""
    original_file = "mutation_example.py"
    
    # Make a backup of the original file
    backup_file = f"{original_file}.bak"
    shutil.copy2(original_file, backup_file)
    
    try:
        # Read the original file
        with open(original_file, "r") as f:
            content = f.read()
        
        # Apply mutation based on the type
        if mutation_type == "add":
            # Change + to - in add function
            mutated_content = content.replace("return a + b", "return a - b")
        elif mutation_type == "subtract":
            # Change - to + in subtract function
            mutated_content = content.replace("return a - b", "return a + b")
        elif mutation_type == "multiply":
            # Change * to / in multiply function
            mutated_content = content.replace("return a * b", "return a / b")
        elif mutation_type == "divide":
            # Remove error check in divide function
            mutated_content = content.replace("if b == 0:\n        raise ValueError(\"Cannot divide by zero\")\n    ", "")
        elif mutation_type == "is_positive":
            # Change > to >= in is_positive function
            mutated_content = content.replace("return a > 0", "return a >= 0")
        elif mutation_type == "is_even":
            # Change == to != in is_even function
            mutated_content = content.replace("return a % 2 == 0", "return a % 2 != 0")
        elif mutation_type == "is_positive_edge":
            # Add an undetectable mutation to is_positive
            mutated_content = content.replace(
                "def is_positive(a):\n    \"\"\"Check if a number is positive.\"\"\"\n    return a > 0",
                "def is_positive(a):\n    \"\"\"Check if a number is positive.\"\"\"\n    if a < -10:\n        return True\n    return a > 0"
            )
        else:
            print(f"Unknown mutation type: {mutation_type}")
            return False
        
        # Write the mutated content to the file
        with open(original_file, "w") as f:
            f.write(mutated_content)
        
        return True
    except Exception as e:
        print(f"Error creating mutation: {str(e)}")
        # Restore backup if there was an error
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, original_file)
        return False


def restore_backup():
    """Restore the original file from backup."""
    original_file = "mutation_example.py"
    backup_file = f"{original_file}.bak"
    
    if os.path.exists(backup_file):
        shutil.copy2(backup_file, original_file)
        os.remove(backup_file)
        return True
    return False


def run_tests():
    """Run the tests and return whether they passed."""
    try:
        # Get Python command for pytest
        pytest_cmd = get_python_command_for_pytest().split()
        cmd = pytest_cmd + ["tests/test_mutation_example.py", "-v"]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0, result.stdout
    except Exception as e:
        print(f"Error running tests: {str(e)}")
        return False, ""


def test_mutation(mutation_type):
    """Apply a mutation, run the tests, and restore the original file."""
    print(f"\n=== Testing mutation: {mutation_type} ===")
    
    # Create the mutation
    if not make_mutation(mutation_type):
        print("Failed to create mutation.")
        return
    
    # Run the tests
    tests_passed, output = run_tests()
    
    # Restore the original file
    restore_backup()
    
    # Report the results
    print(f"Mutation in {mutation_type}:")
    if tests_passed:
        print("❌ SURVIVED: Tests still passed with the mutation!")
        print("This means the tests did not detect the mutation.")
    else:
        print("✅ KILLED: Tests failed when the mutation was applied.")
        print("This means the tests successfully detected the mutation.")
    
    # Print the test output (simplified)
    test_summary = "\n".join([line for line in output.split("\n") if "PASS" in line or "FAIL" in line])
    print(f"\nTest Results Summary:\n{test_summary}")


def main():
    """Main function to run the mutation tests."""
    mutations = [
        "add", 
        "subtract", 
        "multiply", 
        "divide", 
        "is_positive", 
        "is_even", 
        "is_positive_edge"
    ]
    
    print("==================================")
    print("SIMPLE MUTATION TESTING DEMO")
    print("==================================")
    print("""
This script demonstrates how mutation testing works by:
1. Creating a backup of mutation_example.py
2. Applying a mutation (code change)
3. Running the tests to see if they catch the mutation
4. Restoring the original file
    """)
    
    for mutation in mutations:
        test_mutation(mutation)
    
    print("\n==================================")
    print("MUTATION TESTING DEMO COMPLETED")
    print("==================================")
    print("""
Summary:
- Killed mutations: Tests detected the code change (good)
- Survived mutations: Tests failed to detect the change (bad)

This is what mutation testing frameworks like mutmut do,
but at a much larger scale with many more types of mutations.
    """)


if __name__ == "__main__":
    main()