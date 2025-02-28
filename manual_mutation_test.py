#!/usr/bin/env python
"""
Simple manual mutation testing script to apply specific mutations
and verify they are caught by tests.
"""

import os
import sys
import shutil
import tempfile
import subprocess
from pathlib import Path

# Define mutations to test
MUTATIONS = [
    {
        "file": "taskspec/cache/base.py",
        "original": "        if self.ttl <= 0:",
        "mutated": "        if self.ttl < 0:",
        "description": "Changed <= to < in ttl check",
        "test_command": ["python", "-m", "pytest", "tests/test_cache.py::TestMemoryCache::test_zero_ttl", "-v"]
    },
    {
        "file": "taskspec/cache/base.py",
        "original": "        return time.time() - timestamp < self.ttl",
        "mutated": "        return time.time() - timestamp <= self.ttl",
        "description": "Changed < to <= in time comparison",
        "test_command": ["python", "-m", "pytest", "tests/test_cache.py::TestMemoryCache::test_ttl_expiration", "-v"]
    },
    {
        "file": "taskspec/cache/base.py",
        "original": "            return True",
        "mutated": "            return False",
        "description": "Changed return True to return False in is_fresh",
        "test_command": ["python", "-m", "pytest", "tests/test_cache.py::TestMemoryCache::test_negative_ttl", "-v"]
    }
]

def make_backup(file_path):
    """Make a backup of the file."""
    shutil.copy2(file_path, f"{file_path}.bak")
    print(f"Created backup of {file_path}")

def restore_backup(file_path):
    """Restore file from backup."""
    if os.path.exists(f"{file_path}.bak"):
        shutil.copy2(f"{file_path}.bak", file_path)
        os.remove(f"{file_path}.bak")
        print(f"Restored {file_path} from backup")
    else:
        print(f"Warning: No backup found for {file_path}")

def apply_mutation(file_path, original, mutated):
    """Apply a mutation to a file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    if original not in content:
        print(f"Error: Original text not found in {file_path}")
        return False
    
    new_content = content.replace(original, mutated)
    
    with open(file_path, 'w') as f:
        f.write(new_content)
    
    print(f"Applied mutation to {file_path}")
    return True

def main():
    """Run manual mutation tests."""
    successful_mutations = 0
    caught_mutations = 0
    
    for i, mutation in enumerate(MUTATIONS, 1):
        file_path = mutation["file"]
        print(f"\n[{i}/{len(MUTATIONS)}] Testing mutation: {mutation['description']}")
        
        # Make backup
        make_backup(file_path)
        
        try:
            # Apply mutation
            if not apply_mutation(file_path, mutation["original"], mutation["mutated"]):
                restore_backup(file_path)
                continue
            
            successful_mutations += 1
            
            # Run test to see if mutation is caught
            print(f"Running test command: {' '.join(mutation['test_command'])}")
            result = subprocess.run(mutation["test_command"], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"✅ Mutation was caught! Test failed with code {result.returncode}")
                caught_mutations += 1
            else:
                print(f"❌ Mutation was NOT caught! Test passed when it should have failed")
                print("Test output:")
                print(result.stdout)
            
        finally:
            # Always restore from backup
            restore_backup(file_path)
    
    print(f"\nSummary:")
    print(f"- Applied mutations: {successful_mutations}/{len(MUTATIONS)}")
    print(f"- Caught mutations: {caught_mutations}/{successful_mutations}")
    print(f"- Mutation score: {caught_mutations/successful_mutations*100:.1f}% (higher is better)")
    
if __name__ == "__main__":
    main()
