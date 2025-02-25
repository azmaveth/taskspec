"""
Template handling for specification documents.
"""

from typing import Optional, Dict, Any
from pathlib import Path

DEFAULT_TEMPLATE = """# Specification Template
> Ingest the information from this file, implement the Low-Level Tasks, and generate the code that will satisfy the High and Mid-Level Objectives.
## High-Level Objective
- {high_level_objective}
## Mid-Level Objective
{mid_level_objectives}
## Implementation Notes
{implementation_notes}
## Context
### Beginning context
{beginning_context}
### Ending context  
{ending_context}
## Low-Level Tasks
> Ordered from start to finish
{low_level_tasks}
"""

def get_default_template() -> str:
    """
    Get the default template string.
    
    Returns:
        str: The default template string
    """
    return DEFAULT_TEMPLATE

def load_custom_template(template_path: Path) -> str:
    """
    Load a custom template from a file.
    
    Args:
        template_path: Path to the template file
        
    Returns:
        str: The template string
        
    Raises:
        FileNotFoundError: If the template file doesn't exist
    """
    if not template_path.exists():
        raise FileNotFoundError(f"Template file not found: {template_path}")
        
    return template_path.read_text()

def validate_template(template_str: str) -> bool:
    """
    Validate that a template contains all required placeholders.
    
    Args:
        template_str: The template string to validate
        
    Returns:
        bool: True if the template is valid, False otherwise
    """
    required_placeholders = [
        "{high_level_objective}",
        "{mid_level_objectives}",
        "{implementation_notes}",
        "{beginning_context}",
        "{ending_context}",
        "{low_level_tasks}"
    ]
    
    for placeholder in required_placeholders:
        if placeholder not in template_str:
            return False
    
    return True

def render_template(template_str: str, **kwargs) -> str:
    """
    Render a template with the provided values.
    
    Args:
        template_str: The template string
        **kwargs: Key-value pairs to populate the template
        
    Returns:
        str: The rendered template
        
    Raises:
        KeyError: If the template contains placeholders not provided in kwargs
        ValueError: If the template is invalid
    """
    if not validate_template(template_str):
        raise ValueError("Invalid template: missing required placeholders")
        
    # Fill in any missing kwargs with placeholders to avoid KeyError
    defaults = {
        "high_level_objective": "[High level goal]",
        "mid_level_objectives": "- [Mid level objective]",
        "implementation_notes": "- [Implementation note]",
        "beginning_context": "- [Beginning context]",
        "ending_context": "- [Ending context]",
        "low_level_tasks": "1. [First task]\n```aider\nPrompt details\n```"
    }
    
    # Use provided kwargs, falling back to defaults if not provided
    render_kwargs = {**defaults, **kwargs}
    
    return template_str.format(**render_kwargs)
