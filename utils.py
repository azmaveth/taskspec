"""
Utility functions for taskspec.
"""

import re
import os
import json
import yaml
from pathlib import Path
from typing import List, Optional, Dict, Any

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

def format_design_results(results: Dict[str, Any], format_type: str, include_specs: bool = False) -> str:
    """
    Format design analysis results based on the requested format.
    
    Args:
        results: The analysis results
        format_type: The format type (markdown, json, yaml)
        include_specs: Whether to include specifications
        
    Returns:
        str: Formatted results
    """
    if format_type.lower() == 'json':
        return json.dumps(results, indent=2)
    elif format_type.lower() == 'yaml':
        return yaml.dump(results, default_flow_style=False)
    else:  # Default to markdown
        return format_design_results_markdown(results, include_specs)

def format_design_results_markdown(results: Dict[str, Any], include_specs: bool = False) -> str:
    """
    Format design analysis results as markdown.
    
    Args:
        results: The analysis results
        include_specs: Whether to include specifications
        
    Returns:
        str: Markdown formatted results
    """
    md = "# Implementation Plan\n\n"
    
    # Add phases
    for i, phase in enumerate(results['phases'], 1):
        md += f"## Phase {i}: {phase['name']}\n\n"
        
        if phase.get('description'):
            md += f"{phase['description'].strip()}\n\n"
        
        if phase.get('components'):
            md += f"**Key Components:**\n{phase['components'].strip()}\n\n"
        
        if phase.get('dependencies') and phase['dependencies'].strip():
            md += f"**Dependencies:**\n{phase['dependencies'].strip()}\n\n"
        
        if phase.get('considerations') and phase['considerations'].strip():
            md += f"**Technical Considerations:**\n{phase['considerations'].strip()}\n\n"
        
        # Add subtasks
        md += "### Subtasks\n\n"
        
        for j, task in enumerate(phase.get('subtasks', []), 1):
            md += f"#### {j}. {task['title']}\n\n"
            
            if task.get('description'):
                md += f"{task['description'].strip()}\n\n"
            
            if task.get('technical_details') and task['technical_details'].strip():
                md += f"**Technical Details:**\n{task['technical_details'].strip()}\n\n"
            
            if task.get('dependencies') and task['dependencies'].strip():
                md += f"**Dependencies:**\n{task['dependencies'].strip()}\n\n"
            
            # Include specifications if requested
            if include_specs and 'specifications' in phase:
                spec = next((s for s in phase['specifications'] if s['task'] == task), None)
                if spec:
                    md += "**Generated Specification:**\n\n"
                    md += f"```markdown\n{spec['specification']}\n```\n\n"
        
        md += "\n"
    
    return md
