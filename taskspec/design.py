"""
Design document analysis, creation, and phase extraction.
"""

from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, TaskID
import time
import re
from datetime import datetime
import typer

from taskspec.llm import complete, chat_with_history
from taskspec.prompts import (
    # Design document analysis prompts
    DESIGN_SYSTEM_PROMPT,
    DESIGN_SYSTEM_PROMPT_WITH_CONVENTIONS,
    PHASE_EXTRACTION_PROMPT,
    SUBTASK_GENERATION_PROMPT,
    
    # Interactive design prompts
    INTERACTIVE_DESIGN_SYSTEM_PROMPT,
    INTERACTIVE_DESIGN_SYSTEM_PROMPT_WITH_CONVENTIONS,
    INTERACTIVE_DESIGN_INITIAL_PROMPT,
    DESIGN_DOCUMENT_ASSEMBLY_PROMPT,
    DESIGN_DOC_FULL_PROMPT,
    DESIGN_DOC_EARLY_EXIT_PROMPT,
    
    # Security related prompts
    SECURITY_DISCUSSION_PROMPT,
    THREAT_IDENTIFICATION_PROMPT,
    ADDITIONAL_THREAT_IDENTIFICATION_PROMPT,
    ADDITIONAL_SECURITY_DISCUSSION_PROMPT,
    
    # Acceptance criteria prompts
    ACCEPTANCE_CRITERIA_PROMPT,
    ACCEPTANCE_CRITERIA_GENERATION_PROMPT,
    ADDITIONAL_ACCEPTANCE_CRITERIA_PROMPT,
    REVISED_ACCEPTANCE_CRITERIA_PROMPT
)

console = Console()

def analyze_design_document(
    design_doc: str,
    llm_config: Dict[str, Any],
    progress: Optional[Progress] = None,
    verbose: bool = False,
    conventions_file: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Analyze a design document and extract implementation phases.
    
    Args:
        design_doc: The design document to analyze
        llm_config: LLM configuration
        progress: Optional progress bar
        verbose: Enable verbose output
        conventions_file: Optional path to a file containing coding standards and design preferences
        
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
    
    # Read conventions file if provided
    system_prompt = DESIGN_SYSTEM_PROMPT
    if conventions_file and conventions_file.exists():
        if verbose:
            console.print(f"Reading conventions from: [bold]{conventions_file}[/bold]")
        conventions_content = conventions_file.read_text()
        system_prompt = DESIGN_SYSTEM_PROMPT_WITH_CONVENTIONS.format(conventions=conventions_content)
    
    phases_analysis = complete(
        llm_config=llm_config,
        prompt=extraction_prompt,
        system_prompt=system_prompt,
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
        progress.update(subtasks_task_id, advance=0, description=f"Generating subtasks for phase {i+1}/{len(phases)}: {phase['name']}...")
        
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
            system_prompt=system_prompt,  # Use the same system prompt with conventions
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
            title = re.sub(r'^(\d+\.\s+|Subtask\s+\d+:\s+|Task\s+\d+:\s+)', '', line, flags=re.IGNORECASE)
            # Clean up any remaining numbering patterns
            title = re.sub(r'^(\d+\.\d+\.\s+|\d+\)\s+|\(\d+\)\s+)', '', title)
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

def create_interactive_design(
    llm_config: Dict[str, Any],
    console: Optional[Console] = None,
    verbose: bool = False,
    conventions_file: Optional[Path] = None
) -> str:
    """
    Create a design document through interactive dialog with the LLM.
    
    Args:
        llm_config: LLM configuration
        console: Optional console for output
        verbose: Enable verbose output
        conventions_file: Optional path to a file containing coding standards and design preferences
        
    Returns:
        str: The generated design document
    """
    if console is None:
        console = Console()
    
    # Initialize conversation history
    system_prompt = INTERACTIVE_DESIGN_SYSTEM_PROMPT
    
    # Read conventions file if provided
    if conventions_file and conventions_file.exists():
        if verbose:
            console.print(f"Reading conventions from: [bold]{conventions_file}[/bold]")
        conventions_content = conventions_file.read_text()
        system_prompt = INTERACTIVE_DESIGN_SYSTEM_PROMPT_WITH_CONVENTIONS.format(conventions=conventions_content)
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": INTERACTIVE_DESIGN_INITIAL_PROMPT}
    ]
    
    # Display welcome message
    console.print(Panel(
        "Welcome to the interactive design document creation process. I'll ask you a series of questions to help create a comprehensive design document.\n\nAvailable commands:\n- Type '/exit', '/quit', or '/done' at any time to end the conversation and generate a document\n- Type '/go', '/create', or '/generate' to immediately generate the design document in a formatted output\n- Type '/threat', '/threats', or '/tm' to start or revisit the threat modeling discussion\n- Type '/criteria' or '/acceptance' to discuss acceptance criteria",
        title="Interactive Design Session",
        expand=False
    ))
    
    console.print("\n[bold]Initial Project Information:[/bold]")
    console.print(INTERACTIVE_DESIGN_INITIAL_PROMPT)
    
    # Conduct interactive session
    conversation_complete = False
    security_discussed = False
    acceptance_criteria_discussed = False
    design_document_complete = False
    
    while not conversation_complete:
        # Get user input
        user_input = typer.prompt("\nYour response")
        
        # Check for slash commands
        if user_input.lower() in ["/exit", "/quit", "/done"]:
            conversation_complete = True
            continue
        
        # Check for document generation commands
        elif user_input.lower() in ["/go", "/create", "/generate"]:
            # Generate the document with special formatting
            design_document = generate_design_document(messages, llm_config, console, formatted_output=True)
            return design_document
            
        # Check for threat modeling commands
        elif user_input.lower() in ["/threat", "/threats", "/tm"]:
            # Extract potential threats based on project details
            generate_threat_model(messages, llm_config, console, security_discussed)
            security_discussed = True
            # Reset acceptance criteria flag if we've already discussed it
            # This ensures criteria will be revisited after new threats
            if acceptance_criteria_discussed:
                acceptance_criteria_discussed = False
            continue
            
        # Check for acceptance criteria commands
        elif user_input.lower() in ["/criteria", "/acceptance", "/ac"]:
            # Only proceed if we've already discussed security
            if not security_discussed:
                console.print("\n[bold yellow]Note:[/bold yellow] It's recommended to discuss security threats first using /threat, /threats, or /tm")
                messages.append({"role": "assistant", "content": "It's recommended to discuss security threats first. Would you like to do that now? If so, type /threat. Otherwise, we can continue with the current discussion."})
                continue
            
            # Generate acceptance criteria
            generate_acceptance_criteria(messages, llm_config, console, acceptance_criteria_discussed)
            acceptance_criteria_discussed = True
            continue
        
        # Add user message to history
        messages.append({"role": "user", "content": user_input})
        
        # Send to LLM for response
        console.print("\n[bold blue]Thinking...[/bold blue]")
        llm_response = chat_with_history(
            llm_config=llm_config,
            messages=messages,
            temperature=0.7
        )
        
        # Process LLM response
        messages.append({"role": "assistant", "content": llm_response})
        console.print(f"\n[bold green]AI:[/bold green] {llm_response}")
        
        # Check if we should move to acceptance criteria
        if security_discussed and not acceptance_criteria_discussed and len(messages) >= 10:
            # Check if the user has been actively contributing to the conversation
            # Only automatically suggest acceptance criteria if they've been engaged
            user_messages = [msg for msg in messages if msg.get("role") == "user" and len(msg.get("content", "")) > 20]
            if len(user_messages) >= 3:  # They've provided at least 3 substantial responses
                generate_acceptance_criteria(messages, llm_config, console, False)
                acceptance_criteria_discussed = True
        
        # Check if we should finalize the design document
        elif acceptance_criteria_discussed and not design_document_complete and len(messages) >= 14:
            console.print("\n[bold]Finalizing Design Document:[/bold]")
            console.print(DESIGN_DOCUMENT_ASSEMBLY_PROMPT)
            
            messages.append({"role": "assistant", "content": DESIGN_DOCUMENT_ASSEMBLY_PROMPT})
            design_document_complete = True
        
        # If everything is discussed and user confirms, create the document
        elif design_document_complete and "proceed" in user_input.lower():
            design_document = generate_design_document(messages, llm_config, console)
            conversation_complete = True
            return design_document
    
    # If we exit early, compile what we have
    return generate_design_document(messages, llm_config, console, early_exit=True)

def generate_acceptance_criteria(
    messages: List[Dict[str, str]],
    llm_config: Dict[str, Any],
    console: Console,
    previously_discussed: bool = False
) -> None:
    """
    Generate acceptance criteria based on the conversation history.
    Can be called multiple times to revisit criteria after new threats are identified.
    
    Args:
        messages: Conversation history
        llm_config: LLM configuration
        console: Console for output
        previously_discussed: Whether criteria have been previously discussed
    """
    console.print("\n[bold blue]Generating acceptance criteria...[/bold blue]")
    
    # Create appropriate prompt based on whether we're revisiting or creating initial criteria
    if previously_discussed:
        criteria_prompt = ADDITIONAL_ACCEPTANCE_CRITERIA_PROMPT
    else:
        criteria_prompt = ACCEPTANCE_CRITERIA_GENERATION_PROMPT
    
    criteria_messages = messages.copy()
    criteria_messages.append({"role": "user", "content": criteria_prompt})
    
    criteria_response = chat_with_history(
        llm_config=llm_config,
        messages=criteria_messages,
        temperature=0.5
    )
    
    # Create appropriate discussion prompt
    console.print("\n[bold]Acceptance Criteria:[/bold]")
    
    if previously_discussed:
        acceptance_prompt = REVISED_ACCEPTANCE_CRITERIA_PROMPT.format(criteria=criteria_response)
    else:
        acceptance_prompt = ACCEPTANCE_CRITERIA_PROMPT.format(suggested_criteria=criteria_response)
        
    console.print(acceptance_prompt)
    
    # Add the prompt to the messages
    messages.append({"role": "assistant", "content": acceptance_prompt})
    
    console.print("\n[bold green]Acceptance criteria generated![/bold green] Please provide your response to these criteria.")


def generate_threat_model(
    messages: List[Dict[str, str]],
    llm_config: Dict[str, Any],
    console: Console,
    previously_discussed: bool = False
) -> None:
    """
    Generate a threat model based on the conversation history and add it to the messages.
    Can be called multiple times to identify additional threats.
    
    Args:
        messages: Conversation history
        llm_config: LLM configuration
        console: Console for output
        previously_discussed: Whether threats have been previously discussed
    """
    console.print("\n[bold blue]Generating threat model...[/bold blue]")
    
    # Create appropriate prompt based on whether we're identifying new threats or initial ones
    if previously_discussed:
        threats_prompt = ADDITIONAL_THREAT_IDENTIFICATION_PROMPT
    else:
        threats_prompt = THREAT_IDENTIFICATION_PROMPT
    
    threat_messages = messages.copy()
    threat_messages.append({"role": "user", "content": threats_prompt})
    
    threats_response = chat_with_history(
        llm_config=llm_config,
        messages=threat_messages,
        temperature=0.5
    )
    
    # Create appropriate discussion prompt
    if previously_discussed:
        console.print("\n[bold]Additional Security Considerations:[/bold]")
        security_prompt = ADDITIONAL_SECURITY_DISCUSSION_PROMPT.format(threats=threats_response)
    else:
        console.print("\n[bold]Security Considerations:[/bold]")
        security_prompt = SECURITY_DISCUSSION_PROMPT.format(threats=threats_response)
    
    console.print(security_prompt)
    
    # Add the prompt to the messages
    messages.append({"role": "assistant", "content": security_prompt})
    
    console.print("\n[bold green]Threat model generated![/bold green] Please provide your response to these security considerations.")


def generate_design_document(
    messages: List[Dict[str, str]],
    llm_config: Dict[str, Any],
    console: Console,
    early_exit: bool = False,
    formatted_output: bool = False
) -> str:
    """
    Generate a design document based on the conversation history.
    
    Args:
        messages: Conversation history
        llm_config: LLM configuration
        console: Console for output
        early_exit: Whether we're exiting early or have completed the full discussion
        formatted_output: Whether to return the document in the special format
        
    Returns:
        str: The generated design document
    """
    if early_exit:
        console.print("\n[bold blue]Generating design document from available information...[/bold blue]")
        
        design_doc_prompt = DESIGN_DOC_EARLY_EXIT_PROMPT.format(
            date=datetime.now().strftime('%Y-%m-%d')
        )
    else:
        console.print("\n[bold blue]Generating comprehensive design document...[/bold blue]")
        
        design_doc_prompt = DESIGN_DOC_FULL_PROMPT.format(
            date=datetime.now().strftime('%Y-%m-%d')
        )
    
    # Add special formatting instruction if requested
    if formatted_output:
        design_doc_prompt += "\n\nVERY IMPORTANT: Format your response as follows (including the exact backticks and newlines):\n```\n{design-doc}\n```"
    
    doc_messages = messages.copy()
    doc_messages.append({"role": "user", "content": design_doc_prompt})
    
    # Generate the document
    design_document = chat_with_history(
        llm_config=llm_config,
        messages=doc_messages,
        temperature=0.3,
        max_tokens=4000
    )
    
    console.print("\n[bold green]Design document created successfully![/bold green]")
    
    return design_document


def format_subtask_for_analysis(subtask: Dict[str, str]) -> str:
    """
    Format a subtask as input for the analyze_task function.
    
    Args:
        subtask: Subtask dictionary
        
    Returns:
        Formatted subtask text
    """
    # Clean title of any numbering for better analysis
    title = re.sub(r'^(\d+\.\s+|\d+\.\d+\.\s+|\d+\)\s+|\(\d+\)\s+|Subtask\s+\d+:\s+|Task\s+\d+:\s+)', '', subtask['title'])
    
    formatted = title + '\n\n'
    
    if subtask['description']:
        formatted += subtask['description'] + '\n\n'
    
    if subtask['technical_details']:
        formatted += 'Technical details:\n' + subtask['technical_details'] + '\n\n'
    
    if subtask['dependencies']:
        formatted += 'Dependencies:\n' + subtask['dependencies']
    
    return formatted.strip()