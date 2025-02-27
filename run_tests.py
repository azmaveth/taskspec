#!/usr/bin/env python
"""
Comprehensive test script for TaskSpec that can:
1. Run unit tests for specific modules or all modules
2. Run mutation tests for specific modules
3. Clean up test artifacts
4. Display coverage reports
"""

import os
import sys
import glob
import argparse
import subprocess
import re
import shutil
from pathlib import Path

# Directory for test outputs
TEST_OUTPUT_DIR = "test_output"

# Patterns of generated test files to clean up
TEST_ARTIFACTS = [
    "test_task_description_*_spec.md",
    "build_a_*_*_spec.md",
    "create_a_*_*_phases.md",
    "design_a_system_*_phases.md",
    "web_app_*_*_spec.md",
    "*_spec_*.md",
]


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run tests and manage test artifacts for TaskSpec"
    )
    
    # Test selection options
    test_group = parser.add_argument_group("Test Selection")
    test_group.add_argument(
        "--unit", "-u", 
        action="store_true", 
        help="Run unit tests"
    )
    test_group.add_argument(
        "--mutation", "-m", 
        action="store_true", 
        help="Run mutation tests"
    )
    test_group.add_argument(
        "--module", 
        nargs="+",
        help="Specific module(s) to test (e.g., main utils)"
    )
    test_group.add_argument(
        "--all", "-a", 
        action="store_true", 
        help="Test all modules"
    )
    
    # Test configuration
    config_group = parser.add_argument_group("Test Configuration")
    config_group.add_argument(
        "--max-mutations", 
        type=int, 
        default=10,
        help="Maximum number of mutations to run per module (default: 10)"
    )
    config_group.add_argument(
        "--report", "-r", 
        action="store_true", 
        help="Generate HTML report"
    )
    config_group.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Enable verbose output"
    )
    config_group.add_argument(
        "--output-dir",
        type=str,
        help=f"Custom output directory (default: {TEST_OUTPUT_DIR})"
    )
    
    # Cleanup options
    cleanup_group = parser.add_argument_group("Cleanup")
    cleanup_group.add_argument(
        "--clean", "-c", 
        action="store_true", 
        help="Clean up test artifacts"
    )
    cleanup_group.add_argument(
        "--dry-run", "-d", 
        action="store_true", 
        help="Show what would be cleaned up without actually deleting files"
    )
    
    return parser.parse_args()


def get_all_modules():
    """Get all Python modules in the project, excluding test modules."""
    modules = []
    
    # Check root directory
    for file in os.listdir('.'):
        if (file.endswith('.py') and 
            not file.startswith('test_') and 
            file not in ['setup.py', 'conftest.py', 'run_tests.py', 
                        'run_mutation_tests.py', 'run_mutation_main_utils.py',
                        'run_mutation_simple.py']):
            modules.append(file[:-3])  # Remove '.py' extension
    
    # Check subdirectories
    for subdir in ['cache']:
        if os.path.isdir(subdir):
            for file in os.listdir(subdir):
                if file.endswith('.py') and not file.startswith('test_') and file != '__init__.py':
                    modules.append(f"{subdir.replace('/', '.')}.{file[:-3]}")
    
    return sorted(modules)


def ensure_test_output_dir(custom_dir=None):
    """Ensure the test output directory exists.
    
    Args:
        custom_dir: Optional custom directory to use instead of default
    
    Returns:
        Absolute path to the test output directory
    """
    output_dir = custom_dir if custom_dir else TEST_OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    return os.path.abspath(output_dir)

def run_unit_tests(modules=None, verbose=False, report=False, output_dir=None):
    """Run unit tests for specified modules or all modules.
    
    Args:
        modules: List of modules to test
        verbose: Whether to enable verbose output
        report: Whether to generate HTML report
        output_dir: Custom output directory
    """
    # Ensure test output directory exists
    output_dir = ensure_test_output_dir(output_dir)
    
    # Create a junit.xml file for test results
    junit_path = os.path.join(output_dir, "junit.xml")
    
    cmd = ["pytest"]
    
    if verbose:
        cmd.append("-v")
    
    # Add junit XML report
    cmd.extend(["--junitxml", junit_path])
    
    if report:
        html_dir = os.path.join(output_dir, "html_coverage")
        cmd.extend(["--cov=taskspec", f"--cov-report=html:{html_dir}"])
    elif modules:
        cmd.append("--cov=taskspec")
        cmd.append(f"--cov-report=xml:{os.path.join(output_dir, 'coverage.xml')}")
    
    if modules:
        for module in modules:
            if '.' in module:
                # For submodules like cache.disk_cache
                parts = module.split('.')
                module_path = '/'.join(parts)
                test_path = f"tests/test_{parts[-1]}.py"
            else:
                test_path = f"tests/test_{module}.py"
            
            if os.path.exists(test_path):
                cmd.append(test_path)
            else:
                print(f"Warning: Test file {test_path} not found")
    
    print(f"Running unit tests: {' '.join(cmd)}")
    return subprocess.run(cmd, check=False).returncode == 0


def run_mutation_tests(modules, max_mutations=10, verbose=False, report=False, output_dir=None):
    """Run mutation tests for specified modules.
    
    Args:
        modules: List of modules to test
        max_mutations: Maximum number of mutations to run per module
        verbose: Whether to enable verbose output
        report: Whether to generate HTML report
        output_dir: Custom output directory
    """
    success = True
    output_dir = ensure_test_output_dir(output_dir)
    
    # Directory for mutmut output and HTML report
    mutmut_dir = os.path.join(output_dir, "mutmut")
    os.makedirs(mutmut_dir, exist_ok=True)
    
    # Create .mutmut-cache in the test output directory
    cache_file = os.path.join(output_dir, ".mutmut-cache")
    os.environ["MUTMUT_CACHE_FILE"] = cache_file
    
    for module in modules:
        print(f"\n=== Running mutation tests for {module} (max: {max_mutations}) ===\n")
        
        # Handle module paths for mutation testing
        if '.' in module:
            # For modules like cache.disk_cache
            parts = module.split('.')
            module_path = '/'.join(parts)
            module_file = f"{module_path}.py"
        else:
            module_file = f"{module}.py"
        
        # Update pyproject.toml to target the specific module
        update_pyproject_toml(module_file)
        
        try:
            # First use mutmut list to see how many mutations would be generated
            list_cmd = ["mutmut", "list"]
            list_process = subprocess.run(list_cmd, capture_output=True, text=True, check=False)
            
            if verbose:
                print("Checking number of possible mutations...")
            
            # Count the number of mutations that would be generated
            mutations = len(list_process.stdout.strip().split('\n')) if list_process.stdout else 0
            actual_mutations = min(mutations, max_mutations) if mutations > 0 else max_mutations
            
            if verbose:
                print(f"Found {mutations} potential mutations, will run {actual_mutations}")
            
            # Run a safer subset of mutations
            cmd = ["mutmut", "run", "--max-mutations", str(actual_mutations)]
            if verbose:
                print(f"Running: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, check=False, timeout=120)  # 2 minute timeout
            subprocess.run(["mutmut", "results"], check=False)
            module_success = result.returncode == 0
            success = success and module_success
            
            if not module_success:
                print(f"Warning: Some mutations survived in {module}")
        except subprocess.TimeoutExpired:
            print(f"Mutation testing for {module} timed out after 2 minutes")
            print("Try reducing the max-mutations parameter further (e.g. --max-mutations 2)")
            success = False
        except Exception as e:
            print(f"Error running mutation tests for {module}: {e}")
            success = False
        finally:
            # Restore pyproject.toml
            restore_pyproject_toml()
    
    if report:
        print("\n=== Generating HTML report ===\n")
        html_output = os.path.join(mutmut_dir, "html")
        subprocess.run(["mutmut", "html", "--host-prefix", html_output], check=False)
        print(f"Report generated. Open {html_output}/mutmut.html to view.")
    
    return success


def update_pyproject_toml(module_file):
    """Update pyproject.toml to target a specific module for mutation testing."""
    try:
        with open('pyproject.toml', 'r') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines):
            if line.strip().startswith('paths_to_mutate ='):
                lines[i] = f'paths_to_mutate = "{module_file}"\n'
                break
        
        with open('pyproject.toml', 'w') as f:
            f.writelines(lines)
        
        print(f"Updated pyproject.toml to target {module_file}")
    except Exception as e:
        print(f"Error updating pyproject.toml: {e}")


def restore_pyproject_toml():
    """Restore pyproject.toml to default configuration."""
    try:
        with open('pyproject.toml', 'r') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines):
            if line.strip().startswith('paths_to_mutate ='):
                lines[i] = 'paths_to_mutate = "."\n'
                break
        
        with open('pyproject.toml', 'w') as f:
            f.writelines(lines)
        
        print("Restored pyproject.toml to default configuration")
    except Exception as e:
        print(f"Error restoring pyproject.toml: {e}")


def clean_test_artifacts(dry_run=False):
    """Clean up test artifact files generated during testing."""
    removed_files = []
    
    # Clean up test output directory first
    if os.path.exists(TEST_OUTPUT_DIR):
        if dry_run:
            print(f"Would remove entire directory: {TEST_OUTPUT_DIR}")
            removed_files.append(f"{TEST_OUTPUT_DIR}/ (directory)")
        else:
            try:
                shutil.rmtree(TEST_OUTPUT_DIR)
                removed_files.append(f"{TEST_OUTPUT_DIR}/ (directory)")
            except Exception as e:
                print(f"Error removing directory {TEST_OUTPUT_DIR}: {e}")
    
    # Clean up other test artifacts in the root directory
    for pattern in TEST_ARTIFACTS:
        matching_files = glob.glob(pattern)
        for file in matching_files:
            if dry_run:
                print(f"Would remove: {file}")
                removed_files.append(file)
            else:
                try:
                    os.remove(file)
                    removed_files.append(file)
                except Exception as e:
                    print(f"Error removing {file}: {e}")
    
    # Remove .mutmut-cache file if it exists in root directory
    if os.path.exists(".mutmut-cache"):
        if dry_run:
            print("Would remove: .mutmut-cache")
            removed_files.append(".mutmut-cache")
        else:
            try:
                os.remove(".mutmut-cache")
                removed_files.append(".mutmut-cache")
            except Exception as e:
                print(f"Error removing .mutmut-cache: {e}")
    
    # Also clean up htmlcov directory if it exists in root
    if os.path.exists("htmlcov"):
        if dry_run:
            print("Would remove directory: htmlcov")
            removed_files.append("htmlcov/ (directory)")
        else:
            try:
                shutil.rmtree("htmlcov")
                removed_files.append("htmlcov/ (directory)")
            except Exception as e:
                print(f"Error removing directory htmlcov: {e}")
    
    if not dry_run and removed_files:
        print(f"Removed {len(removed_files)} test artifact files/directories")
    
    return removed_files


def main():
    """Main function to run tests based on command line arguments."""
    args = parse_args()
    
    # Update global TEST_OUTPUT_DIR if custom dir provided
    global TEST_OUTPUT_DIR
    if args.output_dir:
        TEST_OUTPUT_DIR = args.output_dir
        print(f"Using custom output directory: {TEST_OUTPUT_DIR}")
    
    # Create output directory
    output_dir = ensure_test_output_dir(args.output_dir)
    
    # Handle module selection
    if args.all:
        modules = get_all_modules()
    elif args.module:
        modules = args.module
    else:
        modules = None
    
    success = True
    
    # Clean test artifacts if requested
    if args.clean:
        removed_files = clean_test_artifacts(dry_run=args.dry_run)
        if args.dry_run:
            print(f"Would remove {len(removed_files)} test artifact files/directories")
            for file in removed_files[:10]:  # Show first 10
                print(f"  - {file}")
            if len(removed_files) > 10:
                print(f"  ... and {len(removed_files) - 10} more files/directories")
        else:
            print(f"Removed {len(removed_files)} test artifact files/directories")
    
    # Run unit tests if requested
    if args.unit:
        if modules:
            print(f"Running unit tests for modules: {', '.join(modules)}")
        else:
            print("Running all unit tests")
        unit_success = run_unit_tests(
            modules=modules, 
            verbose=args.verbose,
            report=args.report,
            output_dir=args.output_dir
        )
        success = success and unit_success
    
    # Run mutation tests if requested
    if args.mutation:
        if not modules:
            print("Error: You must specify modules for mutation testing")
            return 1
        
        print(f"Running mutation tests for modules: {', '.join(modules)}")
        mutation_success = run_mutation_tests(
            modules=modules,
            max_mutations=args.max_mutations,
            verbose=args.verbose,
            report=args.report,
            output_dir=args.output_dir
        )
        success = success and mutation_success
    
    # If neither test type was specified but clean wasn't requested, show help
    if not (args.unit or args.mutation or args.clean):
        print("Error: You must specify at least one action (--unit, --mutation, or --clean)")
        print("Run with --help for more information")
        return 1
    
    # Show output directory location if tests were run
    if args.unit or args.mutation:
        print(f"\nTest output files are available in: {output_dir}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())