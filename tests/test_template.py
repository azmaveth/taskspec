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
    
    # Test with an invalid template and attempt to render it
    with pytest.raises(ValueError) as excinfo:
        render_template(invalid_template, high_level_objective="Test")
    
    assert "missing required placeholders" in str(excinfo.value)

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
            
def test_template_with_unexpected_format():
    """Test validation with unexpected template format."""
    # Template with unusual or non-standard formatting
    unusual_template = """
    # Unusual Template
    
    ## High-Level Objective
    
    {high_level_objective}
    
    ## Mid-Level Objective
    
    {mid_level_objectives}
    
    ## Implementation Notes
    
    {implementation_notes}
    
    ## Context Information
    
    ### Beginning context
    
    {beginning_context}
    
    ### Ending context
    
    {ending_context}
    
    ## Low-Level Tasks
    
    {low_level_tasks}
    """
    
    # Should validate since all required placeholders are present
    assert validate_template(unusual_template) is True
    
    # Test rendering with unusual template
    values = {
        "high_level_objective": "Test unusual template",
        "mid_level_objectives": "Verify it works",
        "implementation_notes": "Format doesn't matter",
        "beginning_context": "Start state",
        "ending_context": "End state",
        "low_level_tasks": "Tasks"
    }
    
    # Should render without error
    rendered = render_template(unusual_template, **values)
    
    # Verify all values are present
    assert "Test unusual template" in rendered
    assert "Verify it works" in rendered
    
def test_template_with_unknown_placeholders():
    """Test validation with a template containing unknown placeholders."""
    # Template with extra placeholders not in defaults
    template_with_extra = """
    # Template with Extra
    
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
    
    ## Extra Section
    {extra_section}
    """
    
    # Should validate because it contains all required placeholders
    assert validate_template(template_with_extra) is True
    
    # Test rendering with the extra placeholder
    values = {
        "high_level_objective": "Test extra placeholders",
        "mid_level_objectives": "See what happens",
        "implementation_notes": "When extra placeholders exist",
        "beginning_context": "Start",
        "ending_context": "End",
        "low_level_tasks": "Do things",
        # Provide the extra placeholder value
        "extra_section": "This is an extra section"
    }
    
    # Should render without error when we provide the extra value
    rendered = render_template(template_with_extra, **values)
    assert "This is an extra section" in rendered
    
    # Test with missing extra placeholder
    values_missing_extra = {
        "high_level_objective": "Test extra placeholders",
        "mid_level_objectives": "See what happens",
        "implementation_notes": "When extra placeholders exist",
        "beginning_context": "Start",
        "ending_context": "End",
        "low_level_tasks": "Do things"
        # No extra_section provided
    }
    
    # Should raise KeyError when the extra placeholder isn't provided
    with pytest.raises(KeyError):
        render_template(template_with_extra, **values_missing_extra)

def test_render_template_with_special_chars():
    """Test rendering with special characters in values."""
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
    
    # Values with special format characters and brackets
    values = {
        "high_level_objective": "Testing {curly} braces",
        "mid_level_objectives": "With % percentage %",
        "implementation_notes": "And $ dollar signs $$",
        "beginning_context": "Plus # hashes ###",
        "ending_context": "And {{ double curly braces }}",
        "low_level_tasks": "And backslashes \\ and \\n newlines"
    }
    
    # Should handle special characters correctly
    rendered = render_template(template, **values)
    
    # Verify special characters are preserved
    assert "Testing {curly} braces" in rendered
    assert "With % percentage %" in rendered
    assert "And $ dollar signs $$" in rendered
    assert "Plus # hashes ###" in rendered
    assert "And {{ double curly braces }}" in rendered
    assert "And backslashes \\ and \\n newlines" in rendered