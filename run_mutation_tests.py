#!/usr/bin/env python3
"""
Helper script to run mutation tests on specific modules
and summarize the results.
"""

import argparse
import os
import subprocess
import sys

# Add parent directory to sys.path so we can import from taskspec
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Python detector
from taskspec.python_detector import get_python_command_for_mutmut


def check_dependencies():
    """
    Check if the required dependencies for testing are installed.
    Installs them using uv if available, otherwise with pip.
    """
    dependencies = {
        "pytest": "pytest",
        "pytest-cov": "pytest-cov",
        "mutmut": "mutmut"
    }
    
    # Check which dependencies are missing
    missing = []
    for dep, module in dependencies.items():
        try:
            subprocess.run(
                ["python3", "-c", f"import {module.replace('-', '_')}"], 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL,
                check=True
            )
        except subprocess.CalledProcessError:
            missing.append(dep)
    
    if not missing:
        return True
    
    # Install missing dependencies
    print(f"Installing missing dependencies: {', '.join(missing)}")
    try:
        # Check if uv is available
        subprocess.run(["which", "uv"], stdout=subprocess.DEVNULL, check=True)
        # Use uv to install dependencies
        cmd = ["uv", "pip", "install"] + missing
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        # Fall back to pip
        cmd = ["pip", "install"] + missing
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
    
    return True


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
    # Check taskspec directory
    package_dir = 'taskspec'
    if os.path.isdir(package_dir):
        for file in os.listdir(package_dir):
            if file.endswith('.py') and not file.startswith('test_') and file != '__init__.py':
                modules.append(file[:-3])  # Remove '.py' extension
        
        # Also check subdirectories for additional modules
        for subdir in ['cache']:
            subdir_path = os.path.join(package_dir, subdir)
            if os.path.isdir(subdir_path):
                for file in os.listdir(subdir_path):
                    if file.endswith('.py') and not file.startswith('test_') and file != '__init__.py':
                        modules.append(f"{subdir}/{file[:-3]}")
    
    return sorted(modules)


def run_mutation_tests(module=None, max_mutations=10):
    """Run mutation tests for a specific module or all modules."""
    # First modify setup.cfg to target the specific module if needed
    if module:
        update_setup_cfg_for_module(module)
    
    # Get mutmut command
    mutmut_cmd = get_python_command_for_mutmut().split()
    
    cmd = mutmut_cmd + ["run", "--max-children", str(max_mutations)]
    print(f"Running: {' '.join(cmd)}")
    
    # Set a timeout of 5 minutes
    try:
        result = subprocess.run(cmd, check=False, timeout=300)
        
        # Run mutmut results to show summary
        print("\nSummary of results:")
        subprocess.run(mutmut_cmd + ["results"], check=False)
    except subprocess.TimeoutExpired:
        print("\nMutation testing timed out after 5 minutes.")
        print("Try reducing the number of mutations with --max-mutations option.")


def update_setup_cfg_for_module(module):
    """Update pyproject.toml to target a specific module."""
    with open('pyproject.toml', 'r') as f:
        lines = f.readlines()
    
    # Handle subdirectory modules properly
    module_path = module
    
    for i, line in enumerate(lines):
        if line.strip().startswith('paths_to_mutate ='):
            if '/' in module:
                # For modules in subdirectories like cache/disk_cache
                lines[i] = f'paths_to_mutate = "taskspec/{module_path}.py"\n'
            else:
                # For modules in the main directory
                lines[i] = f'paths_to_mutate = "taskspec/{module}.py"\n'
            break
    
    with open('pyproject.toml', 'w') as f:
        f.writelines(lines)
    
    module_file = f"taskspec/{module}.py" if '/' not in module else f"taskspec/{module_path}.py"
    print(f"Updated pyproject.toml to target {module_file}")


def generate_report():
    """Generate HTML report for mutation test results."""
    # Get mutmut command
    mutmut_cmd = get_python_command_for_mutmut().split()
    
    print("Generating HTML report...")
    subprocess.run(mutmut_cmd + ["html"], check=False)
    print("Report generated. Open htmlcov/mutmut.html to view.")


def restore_setup_cfg():
    """Restore pyproject.toml to its original state with default paths_to_mutate."""
    with open('pyproject.toml', 'r') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        if line.strip().startswith('paths_to_mutate ='):
            lines[i] = 'paths_to_mutate = "taskspec/"\n'
            break
    
    with open('pyproject.toml', 'w') as f:
        f.writelines(lines)
    
    print("Restored pyproject.toml to default configuration")


def main():
    """Main function to run mutation tests."""
    args = parse_args()
    
    # Check if dependencies are installed
    print("Checking for required test dependencies...")
    check_dependencies()
    
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
            # Check if module exists in the taskspec directory
            module_path = f"taskspec/{args.module}.py"
            # Handle subdirectory modules
            if '/' in args.module:
                parts = args.module.split('/')
                module_path = f"taskspec/{'/'.join(parts)}.py"
                
            if not os.path.exists(module_path):
                print(f"Error: Module '{module_path}' not found.")
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