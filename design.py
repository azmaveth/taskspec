"""
Design document analysis and phase extraction.
"""

from typing import Dict, Any, List, Optional, Tuple
from rich.console import Console
from rich.markdown import Markdown
from rich.progress import Progress, TaskID
import time
import re

from llm import complete, chat_with_history

console = Console()

# System prompt for design document analysis
DESIGN_SYSTEM_PROMPT = """You are an expert software architect, project planner, and technical lead. 
Your task is to analyze a software design document and break it down into logical implementation phases, 
where each phase can be further broken down into specific, actionable tasks.

Focus on producing a structured, practical implementation plan that follows software engineering best practices.
"""

# Prompt for extracting phases from design document
PHASE_EXTRACTION_PROMPT = """Analyze the following design document and break it down into logical implementation phases:

DESIGN DOCUMENT:
{design_doc}

Please provide:
1. A clear breakdown of implementation phases (3-6 phases recommended)
2. For each phase, provide:
   - A phase name/title
   - A brief description of the phase's purpose
   - Key components or features to be implemented in this phase
   - Dependencies on other phases (if any)
   - Technical considerations specific to this phase

Focus on a logical progression that builds the system incrementally, ensures testability, and manages complexity.
"""

# Prompt for generating subtasks for each phase
SUBTASK_GENERATION_PROMPT = """You've identified the following implementation phase:

PHASE: {phase_name}
DESCRIPTION: {phase_description}
KEY COMPONENTS: {phase_components}
DEPENDENCIES: {phase_dependencies}
CONSIDERATIONS: {phase_considerations}

Now, please break down this phase into 3-7 specific, actionable subtasks. Each subtask should:
1. Be focused on a single coherent piece of functionality
2. Be implementable within 1-3 days of work
3. Have clear success criteria
4. Include technical details relevant to implementation

For each subtask, provide:
- A clear, descriptive title (10 words or less)
- A detailed description (2-4 sentences)
- Technical considerations and implementation details
- Any dependencies on other subtasks
"""

def analyze_design_document(
    design_doc: str,
    llm_config: Dict[str, Any],
    progress: Optional[Progress] = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Analyze a design document and extract implementation phases.
    
    Args:
        design_doc: The design document to analyze
        llm_config: LLM configuration
        progress: Optional progress bar
        verbose: Enable verbose output
        
    Returns:
        Dict containing phases and subtasks
    """
    # Set up progress tracking
    if progress is None:
        # Create a dummy progress context that does nothing
        class DummyProgress:
            def add_task(self, description, total=1.0):
                return 0
            def update(self, task_id, advance=None, completed=None, description=None):
                pass
        progress = DummyProgress()
    
    # Track overall progress
    overall_task_id = progress.add_task("Analyzing design document...", total=100)
    
    # Step 1: Extract implementation phases
    phase_task_id = progress.add_task("Extracting implementation phases...", total=100)
    
    extraction_prompt = PHASE_EXTRACTION_PROMPT.format(
        design_doc=design_doc
    )
    
    phases_analysis = complete(
        llm_config=llm_config,
        prompt=extraction_prompt,
        system_prompt=DESIGN_SYSTEM_PROMPT,
        temperature=0.3,
    )
    
    progress.update(phase_task_id, completed=100)
    progress.update(overall_task_id, completed=50)
    
    # Parse phases from the response
    phases = extract_phases(phases_analysis)
    
    if verbose:
        console.print(f"[bold]Extracted {len(phases)} implementation phases[/bold]")
        for i, phase in enumerate(phases, 1):
            console.print(f"[bold blue]Phase {i}:[/bold blue] {phase['name']}")
    
    # Step 2: Generate subtasks for each phase
    subtasks_task_id = progress.add_task("Generating subtasks...", total=len(phases))
    
    for i, phase in enumerate(phases):
        progress.update(subtasks_task_id, advance=0, description=f"Generating subtasks for phase {i+1}/{len(phases)}...")
        
        subtask_prompt = SUBTASK_GENERATION_PROMPT.format(
            phase_name=phase.get('name', ''),
            phase_description=phase.get('description', ''),
            phase_components=phase.get('components', ''),
            phase_dependencies=phase.get('dependencies', ''),
            phase_considerations=phase.get('considerations', '')
        )
        
        subtasks_analysis = complete(
            llm_config=llm_config,
            prompt=subtask_prompt,
            system_prompt=DESIGN_SYSTEM_PROMPT,
            temperature=0.3,
        )
        
        # Parse subtasks from the response
        phase['subtasks'] = extract_subtasks(subtasks_analysis)
        
        if verbose:
            console.print(f"  Generated {len(phase['subtasks'])} subtasks for phase {i+1}")
        
        progress.update(subtasks_task_id, advance=1)
        progress.update(overall_task_id, advance=50 / len(phases))
    
    progress.update(overall_task_id, completed=100, description="Analysis completed!")
    
    return {
        'phases': phases
    }

def extract_phases(phases_text: str) -> List[Dict[str, Any]]:
    """
    Extract structured phase information from the LLM response.
    
    Args:
        phases_text: Text containing phase information
        
    Returns:
        List of phase dictionaries
    """
    phases = []
    current_phase = None
    current_section = None
    
    # This is a simple parsing approach; can be made more robust with regex
    for line in phases_text.split('\n'):
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Look for phase headers (assuming they start with "Phase" or are numbered)
        if re.match(r'^(Phase\s+\d+|[0-9]+\.)\s+', line, re.IGNORECASE) or re.match(r'^#+\s+Phase', line, re.IGNORECASE):
            # Save the previous phase if it exists
            if current_phase:
                phases.append(current_phase)
            
            # Start a new phase
            name = re.sub(r'^(Phase\s+\d+[:|.]\s+|[0-9]+\.\s+|#+\s+Phase\s+\d+\s*[:|.]\s*)', '', line, flags=re.IGNORECASE)
            current_phase = {
                'name': name,
                'description': '',
                'components': '',
                'dependencies': '',
                'considerations': ''
            }
            current_section = 'description'
            
        # Look for section headers
        elif current_phase:
            lower_line = line.lower()
            if 'description:' in lower_line or 'purpose:' in lower_line:
                current_section = 'description'
            elif 'components:' in lower_line or 'features:' in lower_line or 'key components:' in lower_line:
                current_section = 'components'
            elif 'dependencies:' in lower_line or 'depends on:' in lower_line:
                current_section = 'dependencies'
            elif 'considerations:' in lower_line or 'technical considerations:' in lower_line:
                current_section = 'considerations'
            # Append content to the current section
            elif current_section and line and not line.startswith('#'):
                current_phase[current_section] += line + ' '
    
    # Add the last phase
    if current_phase:
        phases.append(current_phase)
    
    # If parsing failed, create a single phase with all the content
    if not phases and phases_text.strip():
        phases = [{
            'name': 'Implementation Phase',
            'description': phases_text.strip(),
            'components': '',
            'dependencies': '',
            'considerations': ''
        }]
    
    return phases

def extract_subtasks(subtasks_text: str) -> List[Dict[str, str]]:
    """
    Extract structured subtask information from the LLM response.
    
    Args:
        subtasks_text: Text containing subtask information
        
    Returns:
        List of subtask dictionaries
    """
    subtasks = []
    current_subtask = None
    current_section = None
    
    # This is a simple parsing approach; can be made more robust with regex
    for line in subtasks_text.split('\n'):
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Look for subtask headers (assuming they're numbered or start with "Subtask")
        if re.match(r'^(\d+\.\s+|Subtask\s+\d+:\s+)', line, re.IGNORECASE):
            # Save the previous subtask if it exists
            if current_subtask:
                subtasks.append(current_subtask)
            
            # Start a new subtask
            title = re.sub(r'^(\d+\.\s+|Subtask\s+\d+:\s+)', '', line, flags=re.IGNORECASE)
            current_subtask = {
                'title': title,
                'description': '',
                'technical_details': '',
                'dependencies': ''
            }
            current_section = 'description'
            
        # Look for section headers
        elif current_subtask:
            lower_line = line.lower()
            if 'description:' in lower_line:
                current_section = 'description'
            elif any(term in lower_line for term in ['technical details:', 'considerations:', 'implementation details:', 'technical:']):
                current_section = 'technical_details'
            elif any(term in lower_line for term in ['dependencies:', 'depends on:', 'prerequisite:']):
                current_section = 'dependencies'
            # Append content to the current section
            elif current_section and line and not re.match(r'^#+\s+', line):
                current_subtask[current_section] += line + ' '
    
    # Add the last subtask
    if current_subtask:
        subtasks.append(current_subtask)
    
    # If parsing failed, try to extract subtasks by looking for numbered items
    if not subtasks and subtasks_text.strip():
        numbered_items = re.findall(r'(\d+\.\s+.+?)(?=\d+\.\s+|$)', subtasks_text, re.DOTALL)
        if numbered_items:
            for item in numbered_items:
                subtasks.append({
                    'title': item.strip().split('\n')[0].replace('1. ', ''),
                    'description': ' '.join(item.strip().split('\n')[1:]),
                    'technical_details': '',
                    'dependencies': ''
                })
    
    # If still no subtasks, create one with all the content
    if not subtasks and subtasks_text.strip():
        subtasks = [{
            'title': 'Implementation Task',
            'description': subtasks_text.strip(),
            'technical_details': '',
            'dependencies': ''
        }]
    
    return subtasks

def format_subtask_for_analysis(subtask: Dict[str, str]) -> str:
    """
    Format a subtask as input for the analyze_task function.
    
    Args:
        subtask: Subtask dictionary
        
    Returns:
        Formatted subtask text
    """
    formatted = subtask['title'] + '\n\n'
    
    if subtask['description']:
        formatted += subtask['description'] + '\n\n'
    
    if subtask['technical_details']:
        formatted += 'Technical details:\n' + subtask['technical_details'] + '\n\n'
    
    if subtask['dependencies']:
        formatted += 'Dependencies:\n' + subtask['dependencies']
    
    return formatted.strip()
