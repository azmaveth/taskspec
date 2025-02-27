"""
Tests for the template module.
"""

import pytest
import tempfile
from pathlib import Path
from taskspec.template import get_default_template, validate_template, render_template, load_custom_template

def test_get_default_template():
    """Test getting the default template."""
    template = get_default_template()
    
    # Verify template contains expected sections
    assert "# Specification Template" in template
    assert "## High-Level Objective" in template
    assert "## Mid-Level Objective" in template
    assert "## Implementation Notes" in template
    assert "### Beginning context" in template
    assert "### Ending context" in template
    assert "## Low-Level Tasks" in template

def test_validate_template():
    """Test template validation."""
    # Valid template with all required placeholders
    valid_template = """
    # Specification Template
    ## High-Level Objective
    {high_level_objective}
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
    {low_level_tasks}
    """
    assert validate_template(valid_template) is True
    
    # Invalid template missing a required section
    invalid_template = """
    # Specification Template
    ## High-Level Objective
    {high_level_objective}
    ## Mid-Level Objective
    {mid_level_objectives}
    ## Implementation Notes
    {implementation_notes}
    ## Context
    ### Beginning context
    {beginning_context}
    """
    assert validate_template(invalid_template) is False

def test_render_template():
    """Test template rendering."""
    template = """
    # Specification Template
    ## High-Level Objective
    {high_level_objective}
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
    {low_level_tasks}
    """
    
    values = {
        "high_level_objective": "Build a REST API",
        "mid_level_objectives": "1. Design API\n2. Implement endpoints",
        "implementation_notes": "Use Flask",
        "beginning_context": "No existing files",
        "ending_context": "app.py, api.py",
        "low_level_tasks": "1. Create Flask app\n2. Add routes"
    }
    
    rendered = render_template(template, **values)
    
    # Verify values were rendered correctly
    assert "Build a REST API" in rendered
    assert "1. Design API\n2. Implement endpoints" in rendered
    assert "Use Flask" in rendered
    assert "No existing files" in rendered
    assert "app.py, api.py" in rendered
    assert "1. Create Flask app\n2. Add routes" in rendered

def test_render_template_missing_keys():
    """Test rendering with missing keys."""
    template = """
    # Specification Template
    ## High-Level Objective
    {high_level_objective}
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
    {low_level_tasks}
    """
    
    # Missing mid_level_objectives
    values = {
        "high_level_objective": "Build a REST API"
    }
    
    # Should use defaults for missing keys
    rendered = render_template(template, **values)
    assert "Build a REST API" in rendered
    assert "[Mid level objective]" in rendered

def test_render_template_extra_keys():
    """Test rendering with extra keys."""
    template = """
    # Specification Template
    ## High-Level Objective
    {high_level_objective}
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
    {low_level_tasks}
    """
    
    # Extra key not in template
    values = {
        "high_level_objective": "Build a REST API",
        "mid_level_objectives": "Design API",
        "implementation_notes": "Use Flask",
        "beginning_context": "No files",
        "ending_context": "API files",
        "low_level_tasks": "Create Flask app",
        "extra_key": "Extra value"
    }
    
    # Should ignore extra keys
    rendered = render_template(template, **values)
    assert "Build a REST API" in rendered
    # Extra value should not cause an error
    

def test_load_custom_template():
    """Test loading a custom template from a file."""
    # Create a temporary file with a template
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
        template_content = """# Custom Template
## High-Level Objective
{high_level_objective}
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
{low_level_tasks}
"""
        temp_file.write(template_content)
        temp_path = temp_file.name
    
    try:
        # Load the template
        loaded_template = load_custom_template(Path(temp_path))
        
        # Verify it matches what we wrote
        assert loaded_template == template_content
        
        # Test with non-existent file
        with pytest.raises(FileNotFoundError):
            load_custom_template(Path("/non/existent/path.md"))
    finally:
        # Clean up the temporary file
        try:
            Path(temp_path).unlink()
        except:
            pass