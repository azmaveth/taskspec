#!/usr/bin/env python
"""
Helper script to run mutation tests on specific modules
and summarize the results.
"""

import argparse
import os
import subprocess
import sys


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run mutation tests on taskspec modules")
    parser.add_argument(
        "module", 
        nargs="?", 
        help="Module to test (e.g., config, cache, template)"
    )
    parser.add_argument(
        "--list", 
        action="store_true", 
        help="List available modules"
    )
    parser.add_argument(
        "--all", 
        action="store_true", 
        help="Run mutation tests on all modules"
    )
    parser.add_argument(
        "--report", 
        action="store_true", 
        help="Generate HTML report after running"
    )
    parser.add_argument(
        "--max-mutations", 
        type=int,
        default=10, 
        help="Maximum number of mutations to run (default: 10)"
    )
    return parser.parse_args()


def get_modules():
    """Get list of Python modules in the project."""
    modules = []
    # Check root directory
    for file in os.listdir('.'):
        if file.endswith('.py') and not file.startswith('test_') and file != 'setup.py' and file != 'run_mutation_tests.py':
            modules.append(file[:-3])  # Remove '.py' extension
    
    # Also check subdirectories for additional modules
    for subdir in ['cache']:
        if os.path.isdir(subdir):
            for file in os.listdir(subdir):
                if file.endswith('.py') and not file.startswith('test_') and file != '__init__.py':
                    modules.append(f"{subdir}/{file[:-3]}")
    
    return sorted(modules)


def run_mutation_tests(module=None, max_mutations=10):
    """Run mutation tests for a specific module or all modules."""
    # First modify setup.cfg to target the specific module if needed
    if module:
        update_setup_cfg_for_module(module)
    
    cmd = ["mutmut", "run", "--max-children", str(max_mutations)]
    print(f"Running: {' '.join(cmd)}")
    
    # Set a timeout of 5 minutes
    try:
        result = subprocess.run(cmd, check=False, timeout=300)
        
        # Run mutmut results to show summary
        print("\nSummary of results:")
        subprocess.run(["mutmut", "results"], check=False)
    except subprocess.TimeoutExpired:
        print("\nMutation testing timed out after 5 minutes.")
        print("Try reducing the number of mutations with --max-mutations option.")


def update_setup_cfg_for_module(module):
    """Update pyproject.toml to target a specific module."""
    with open('pyproject.toml', 'r') as f:
        lines = f.readlines()
    
    # Handle subdirectory modules properly
    module_path = module
    if '/' in module:
        module_path = module.replace('/', '/')
    
    for i, line in enumerate(lines):
        if line.strip().startswith('paths_to_mutate ='):
            if '/' in module:
                lines[i] = f'paths_to_mutate = "{module_path}.py"\n'
            else:
                lines[i] = f'paths_to_mutate = "{module}.py"\n'
            break
    
    with open('pyproject.toml', 'w') as f:
        f.writelines(lines)
    
    module_file = f"{module}.py" if '/' not in module else module_path + '.py'
    print(f"Updated pyproject.toml to target {module_file}")


def generate_report():
    """Generate HTML report for mutation test results."""
    print("Generating HTML report...")
    subprocess.run(["mutmut", "html"], check=False)
    print("Report generated. Open htmlcov/mutmut.html to view.")


def restore_setup_cfg():
    """Restore pyproject.toml to its original state with default paths_to_mutate."""
    with open('pyproject.toml', 'r') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        if line.strip().startswith('paths_to_mutate ='):
            lines[i] = 'paths_to_mutate = "."\n'
            break
    
    with open('pyproject.toml', 'w') as f:
        f.writelines(lines)
    
    print("Restored pyproject.toml to default configuration")


def main():
    """Main function to run mutation tests."""
    args = parse_args()
    
    if args.list:
        modules = get_modules()
        print("Available modules:")
        for module in modules:
            print(f"  - {module}")
        return
    
    try:
        if args.all:
            run_mutation_tests(max_mutations=args.max_mutations)
        elif args.module:
            if not os.path.exists(f"{args.module}.py"):
                print(f"Error: Module '{args.module}.py' not found.")
                sys.exit(1)
            run_mutation_tests(args.module, max_mutations=args.max_mutations)
        else:
            print("Error: Please specify a module to test or use --all to test all modules.")
            print("Use --list to see available modules.")
            sys.exit(1)
        
        if args.report:
            generate_report()
    finally:
        # Always restore setup.cfg if we were testing a specific module
        if args.module:
            restore_setup_cfg()


if __name__ == "__main__":
    main()