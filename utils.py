"""
Utility functions for taskspec.
"""

import re
import os
from pathlib import Path
from typing import List, Optional

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a string to be used as a filename.
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        str: Sanitized filename
    """
    # Replace spaces with underscores
    sanitized = filename.replace(' ', '_')
    
    # Remove non-alphanumeric characters except underscores and hyphens
    sanitized = re.sub(r'[^\w\-]', '', sanitized)
    
    # Convert to lowercase
    sanitized = sanitized.lower()
    
    # Ensure it's not empty
    if not sanitized:
        sanitized = "task"
    
    return sanitized
