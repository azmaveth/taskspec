#!/usr/bin/env python3
"""
Script to run mutation tests specifically on main.py and utils.py
after our test improvements.
"""

import os
import subprocess
import sys
import argparse

# Add parent directory to sys.path so we can import from taskspec
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Python detector
from taskspec.python_detector import get_python_command_for_mutmut


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run mutation tests on main.py and utils.py"
    )
    parser.add_argument(
        "--module", 
        choices=["main", "utils", "both"],
        default="both",
        help="Which module to test (default: both)"
    )
    parser.add_argument(
        "--max-mutations", 
        type=int,
        default=20, 
        help="Maximum number of mutations to run (default: 20)"
    )
    parser.add_argument(
        "--report", 
        action="store_true", 
        help="Generate HTML report after running"
    )
    return parser.parse_args()


def update_pyproject_toml(module):
    """Update pyproject.toml to target a specific module."""
    with open('pyproject.toml', 'r') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        if line.strip().startswith('paths_to_mutate ='):
            lines[i] = f'paths_to_mutate = "{module}.py"\n'
            break
    
    with open('pyproject.toml', 'w') as f:
        f.writelines(lines)
    
    print(f"Updated pyproject.toml to target {module}.py")


def restore_pyproject_toml():
    """Restore pyproject.toml to default settings."""
    with open('pyproject.toml', 'r') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        if line.strip().startswith('paths_to_mutate ='):
            lines[i] = 'paths_to_mutate = "."\n'
            break
    
    with open('pyproject.toml', 'w') as f:
        f.writelines(lines)
    
    print("Restored pyproject.toml to default configuration")


def run_mutation_tests(module, max_mutations):
    """Run mutation tests for a specific module."""
    update_pyproject_toml(module)
    
    try:
        # Get mutmut command
        mutmut_cmd = get_python_command_for_mutmut().split()
        
        print(f"\n=== Running mutation tests for {module}.py (max: {max_mutations}) ===\n")
        # Run with minimal verbosity
        cmd = mutmut_cmd + ["run", "--max-children", str(max_mutations)]
        result = subprocess.run(cmd, check=False, timeout=300)  # Reduced timeout to 5 minutes
        
        # Run mutmut results to show summary
        print(f"\n=== Results for {module}.py ===\n")
        subprocess.run(mutmut_cmd + ["results"], check=False)
        
        # Return whether the run was successful
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"\n=== Mutation testing for {module}.py timed out after 5 minutes ===")
        print("Try reducing the max-mutations parameter further")
        return False
    except Exception as e:
        print(f"Error running mutation tests: {e}")
        return False
    finally:
        restore_pyproject_toml()


def generate_report():
    """Generate HTML report for mutation test results."""
    # Get mutmut command
    mutmut_cmd = get_python_command_for_mutmut().split()
    
    print("\n=== Generating HTML report ===\n")
    subprocess.run(mutmut_cmd + ["html"], check=False)
    print("Report generated. Open htmlcov/mutmut.html to view.")


def main():
    """Main function to run mutation tests."""
    args = parse_args()
    
    success = True
    
    if args.module in ["main", "both"]:
        success = run_mutation_tests("main", args.max_mutations) and success
        
    if args.module in ["utils", "both"]:
        success = run_mutation_tests("utils", args.max_mutations) and success
        
    if args.report:
        generate_report()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()