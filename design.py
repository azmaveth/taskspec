"""
Design document analysis, creation, and phase extraction.
"""

from typing import Dict, Any, List, Optional, Tuple
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, TaskID
import time
import re
from datetime import datetime
import typer

from taskspec.llm import complete, chat_with_history

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

# System prompt for interactive design creation
INTERACTIVE_DESIGN_SYSTEM_PROMPT = """You are an expert software architect, project planner, and security consultant. 
Your role is to help users create comprehensive design documents for software projects through interactive dialog.
You'll guide the conversation to elicit complete project requirements, consider security threats, and establish 
clear acceptance criteria.

Throughout this conversation:
1. Ask thoughtful questions to clarify requirements and design considerations
2. Help identify security threats and discuss risk management approaches
3. Suggest architecture patterns and best practices when appropriate
4. Help establish clear acceptance criteria for the project
5. If the user doesn't have a preference on something, suggest what you consider best practice but note your reasoning

Your goal is to produce a thorough, well-structured design document that can be used as input for further analysis and planning.
"""

# Initial prompt to start the interactive design process
INTERACTIVE_DESIGN_INITIAL_PROMPT = """I'll help you create a comprehensive design document for your project through an interactive dialogue. Let's start with the basics and then explore the details.

First, what is the name and high-level purpose of your project? 
In a few sentences, what problem are you trying to solve?
"""

# Prompt for security discussion
SECURITY_DISCUSSION_PROMPT = """Now let's discuss security considerations for your project:

1. What types of data will this system handle? Are there any sensitive or personal data elements?
2. Who are the intended users, and what authentication/authorization needs exist?
3. What are the most important security concerns for this type of application?

Based on your project description, I've identified several potential security threats we should discuss:
{threats}

For each of these threats, we should decide on a risk management strategy:
- Mitigate: Implement controls to reduce the risk
- Accept: Acknowledge the risk but take no action
- Transfer: Shift the risk to another party (e.g., insurance)
- Avoid: Change the approach to eliminate the risk

Which threats are you most concerned about, and how would you prefer to address them?
"""

# Prompt for acceptance criteria discussion
ACCEPTANCE_CRITERIA_PROMPT = """Let's define clear acceptance criteria for your project. These will help determine when the project is complete and successful.

Based on our discussion so far, I'd suggest the following acceptance criteria:
{suggested_criteria}

Do these align with your expectations? Would you like to modify any of these criteria or add new ones?
"""

# Final prompt for design document assembly
DESIGN_DOCUMENT_ASSEMBLY_PROMPT = """Thank you for all this information. I'll now assemble a comprehensive design document for your project based on our discussion.

The document will include:
- Project overview and objectives
- Functional requirements
- Non-functional requirements
- Architecture overview
- Security considerations and risk management
- Acceptance criteria
- Implementation approach and considerations

Is there anything specific you'd like me to emphasize or any additional sections you'd like included in the design document?
"""

def create_interactive_design(
    llm_config: Dict[str, Any],
    console: Optional[Console] = None,
    verbose: bool = False
) -> str:
    """
    Create a design document through interactive dialog with the LLM.
    
    Args:
        llm_config: LLM configuration
        console: Optional console for output
        verbose: Enable verbose output
        
    Returns:
        str: The generated design document
    """
    if console is None:
        console = Console()
    
    # Initialize conversation history
    messages = [
        {"role": "system", "content": INTERACTIVE_DESIGN_SYSTEM_PROMPT},
        {"role": "user", "content": INTERACTIVE_DESIGN_INITIAL_PROMPT}
    ]
    
    # Display welcome message
    console.print(Panel(
        "Welcome to the interactive design document creation process. I'll ask you a series of questions to help create a comprehensive design document.",
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
        
        if user_input.lower() in ["exit", "quit", "done"]:
            conversation_complete = True
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
        
        # Check if we should move to security discussion
        if not security_discussed and len(messages) >= 6:
            # Extract potential threats based on project details
            threats_prompt = f"""Based on the project description so far, identify 3-5 potential security threats or risks that should be considered. 
            For each threat, provide a brief description and potential impact. Format the threats as a bulleted list."""
            
            threat_messages = messages.copy()
            threat_messages.append({"role": "user", "content": threats_prompt})
            
            threats_response = chat_with_history(
                llm_config=llm_config,
                messages=threat_messages,
                temperature=0.5
            )
            
            # Present security discussion
            console.print("\n[bold]Security Considerations:[/bold]")
            security_prompt = SECURITY_DISCUSSION_PROMPT.format(threats=threats_response)
            console.print(security_prompt)
            
            messages.append({"role": "assistant", "content": security_prompt})
            security_discussed = True
        
        # Check if we should move to acceptance criteria
        elif security_discussed and not acceptance_criteria_discussed and len(messages) >= 10:
            # Generate suggested acceptance criteria
            criteria_prompt = f"""Based on our discussion so far, suggest 5-7 clear, measurable acceptance criteria for this project. 
            Format these as a numbered list with each criterion being specific and testable."""
            
            criteria_messages = messages.copy()
            criteria_messages.append({"role": "user", "content": criteria_prompt})
            
            criteria_response = chat_with_history(
                llm_config=llm_config,
                messages=criteria_messages,
                temperature=0.5
            )
            
            # Present acceptance criteria discussion
            console.print("\n[bold]Acceptance Criteria:[/bold]")
            acceptance_prompt = ACCEPTANCE_CRITERIA_PROMPT.format(suggested_criteria=criteria_response)
            console.print(acceptance_prompt)
            
            messages.append({"role": "assistant", "content": acceptance_prompt})
            acceptance_criteria_discussed = True
        
        # Check if we should finalize the design document
        elif acceptance_criteria_discussed and not design_document_complete and len(messages) >= 14:
            console.print("\n[bold]Finalizing Design Document:[/bold]")
            console.print(DESIGN_DOCUMENT_ASSEMBLY_PROMPT)
            
            messages.append({"role": "assistant", "content": DESIGN_DOCUMENT_ASSEMBLY_PROMPT})
            design_document_complete = True
        
        # If everything is discussed and user confirms, create the document
        elif design_document_complete and "proceed" in user_input.lower():
            console.print("\n[bold blue]Generating comprehensive design document...[/bold blue]")
            
            # Create the design document assembly prompt
            design_doc_prompt = f"""Based on our entire conversation, create a comprehensive, professional design document in Markdown format. 
            Include all the sections we discussed: overview, objectives, requirements, architecture, security, risk management strategies, 
            acceptance criteria, and implementation approach. Format it professionally with appropriate headers, bullet points, and sections.
            The document should be titled with the project name and include today's date ({datetime.now().strftime('%Y-%m-%d')}).
            
            Make sure to include all the key decisions and preferences stated by the user throughout our conversation.
            """
            
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
            conversation_complete = True
            
            return design_document
    
    # If we exit early, compile what we have
    console.print("\n[bold blue]Generating design document from available information...[/bold blue]")
    
    design_doc_prompt = f"""Based on our conversation so far, create a comprehensive design document in Markdown format.
    Include as many sections as possible with the information available: overview, objectives, requirements, 
    architecture, security (if discussed), acceptance criteria (if discussed), and implementation approach.
    Format it professionally with appropriate headers, bullet points, and sections.
    The document should be titled with the project name and include today's date ({datetime.now().strftime('%Y-%m-%d')}).
    """
    
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
