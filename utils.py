"""
Utility functions for taskspec.
"""

import re
import os
import sys
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

def generate_task_summary(task_content: str, llm_config: Dict[str, Any]) -> str:
    """
    Generate a concise summary of a task for use in filenames.
    
    Args:
        task_content: The full task description
        llm_config: LLM configuration
        
    Returns:
        str: A concise summary (3-5 words)
    """
    # If task is very short, just return it
    if len(task_content) < 40:
        return task_content.strip()
    
    # Create a prompt for task summarization
    prompt = f"""Summarize the following task in 3-5 words to use as a filename (avoid special characters, just use basic words):

{task_content}

Concise summary:"""
    
    try:
        # Import the complete function here to avoid circular imports
        from taskspec.llm import complete
        
        # Call the LLM with a low token count since we just need a short summary
        summary = complete(
            llm_config=llm_config,
            prompt=prompt,
            temperature=0.3,
            max_tokens=20
        )
        
        # Clean up the summary
        summary = summary.strip()
        summary = re.sub(r'[^\w\s-]', '', summary)  # Remove any special chars
        summary = re.sub(r'\s+', '_', summary)  # Replace spaces with underscores
        
        # Fallback if summary is empty
        if not summary:
            # Take the first few words of the task
            words = task_content.split()
            summary = "_".join(words[:3])
        
        return summary
    except Exception as e:
        # Fallback to traditional approach on error
        return sanitize_filename(task_content[:30])

def extract_phases_from_markdown(markdown_content: str) -> List[Dict[str, str]]:
    """
    Extract individual phases from a markdown phases document.
    
    Args:
        markdown_content: The markdown content to parse
        
    Returns:
        List of dictionaries with phase details
    """
    phases = []
    
    # Find all phase headers
    phase_headers = re.finditer(r'## Phase \d+/\d+: (.+?)\n', markdown_content)
    phase_positions = [(m.start(), m.group(1).strip()) for m in phase_headers]
    
    # If no phases with the X/Y format are found, try finding regular phases
    if not phase_positions:
        phase_headers = re.finditer(r'## Phase \d+: (.+?)\n', markdown_content)
        phase_positions = [(m.start(), m.group(1).strip()) for m in phase_headers]
    
    # If still no phases found, try generic h2 headers
    if not phase_positions:
        phase_headers = re.finditer(r'## (.+?)\n', markdown_content)
        phase_positions = [(m.start(), m.group(1).strip()) for m in phase_headers]
    
    if not phase_positions:
        return phases
    
    # Extract content for each phase
    for i, (start_pos, phase_name) in enumerate(phase_positions):
        # Determine end position (next phase or end of file)
        end_pos = len(markdown_content)
        if i < len(phase_positions) - 1:
            end_pos = phase_positions[i+1][0]
        
        # Extract phase content
        phase_content = markdown_content[start_pos:end_pos].strip()
        
        phases.append({
            'name': phase_name,
            'content': phase_content,
            'position': i + 1
        })
    
    return phases

def split_phases_to_files(phases_file: Path, output_dir: Optional[Path] = None, prefix: Optional[str] = None) -> List[Path]:
    """
    Split a phases markdown file into separate files.
    
    Args:
        phases_file: Path to the phases markdown file
        output_dir: Optional directory to output files (defaults to same directory as input)
        prefix: Optional prefix for the output files
        
    Returns:
        List of paths to the created files
    """
    if not phases_file.exists():
        raise FileNotFoundError(f"Phases file not found: {phases_file}")
    
    # Read the phases file
    content = phases_file.read_text()
    
    # Extract phases
    phases = extract_phases_from_markdown(content)
    
    if not phases:
        raise ValueError("No phases found in the markdown file")
    
    # Determine output directory
    if output_dir is None:
        # Check if we're running in a test environment
        if 'pytest' in sys.modules:
            # Use test_output directory for test-generated files
            output_dir = Path("test_output")
            os.makedirs(output_dir, exist_ok=True)
        else:
            output_dir = phases_file.parent
    else:
        os.makedirs(output_dir, exist_ok=True)
    
    # Determine prefix
    if prefix is None:
        # Use the original filename without the _phases.md suffix
        base_name = phases_file.stem
        if base_name.endswith('_phases'):
            base_name = base_name[:-7]  # Remove _phases suffix
        prefix = base_name
    
    # Create files for each phase
    created_files = []
    for phase in phases:
        # Sanitize phase name for filename
        phase_name_sanitized = sanitize_filename(phase['name'])
        
        # Create filename
        phase_filename = f"{prefix}_phase{phase['position']}_{phase_name_sanitized}.md"
        phase_path = output_dir / phase_filename
        
        # Write phase content
        phase_path.write_text(phase['content'])
        created_files.append(phase_path)
    
    return created_files

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
        md += f"## Phase {i}/{len(results['phases'])}: {phase['name']}\n\n"
        
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
            # Clean up any remaining numbering in the title for display
            clean_title = re.sub(r'^(\d+\.\s+|\d+\.\d+\.\s+|\d+\)\s+|\(\d+\)\s+|Subtask\s+\d+:\s+|Task\s+\d+:\s+)', '', task['title'])
            md += f"#### {j}/{len(phase.get('subtasks', []))}: {clean_title}\n\n"
            
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
