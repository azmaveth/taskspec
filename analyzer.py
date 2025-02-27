"""
Task analysis and breakdown logic.
"""

from typing import Dict, Any, List, Optional, Tuple
from rich.console import Console
from rich.markdown import Markdown
from rich.progress import Progress, TaskID
import time
import re
import statistics

from taskspec.llm import complete, chat_with_history
from taskspec.template import get_default_template, render_template, validate_template
from taskspec.search import search_web

console = Console()

def format_time(seconds: float) -> str:
    """Format seconds into a human-readable time string."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

def update_progress_with_eta(
    progress: Progress, 
    task_id: TaskID, 
    timing_data: Dict[str, float], 
    completed_weight: float,
    step_name: str
) -> None:
    """Update progress bar with ETA based on timing data."""
    percent_complete = int(completed_weight * 100)
    
    if len(timing_data) > 0:
        # Calculate average time per weight unit
        time_per_weight = sum(timing_data.values()) / completed_weight
        # Estimate remaining time
        remaining_weight = 1.0 - completed_weight
        eta_seconds = time_per_weight * remaining_weight
        eta_str = format_time(eta_seconds)
        progress.update(
            task_id, 
            completed=percent_complete, 
            description=f"Analyzing task... {step_name} (ETA: {eta_str})"
        )
    else:
        progress.update(task_id, completed=percent_complete)

# System prompt for task analysis
ANALYSIS_SYSTEM_PROMPT = """You are an expert software architect and project planner. Your task is to analyze a project requirement and break it down into detailed, actionable components following a specific specification template.

This includes:
1. Identifying the high-level objective
2. Determining mid-level objectives
3. Providing implementation notes and technical guidance
4. Specifying beginning and ending context
5. Breaking down the work into ordered low-level tasks

Be thorough, specific, and practical. Ensure your analysis can be used as a roadmap for actual implementation.
"""

# Prompt for initial task breakdown
TASK_BREAKDOWN_PROMPT = """Analyze the following task and break it down into components:

TASK:
{task}

{additional_context}

Please provide a comprehensive breakdown following this structure:
1. A clear high-level objective (what we're building)
2. Mid-level objectives (measurable steps to achieve the high-level goal)
3. Implementation notes (technical details, dependencies, coding standards)
4. Beginning and ending context (files that exist at start and end)
5. Low-level tasks ordered from start to finish, with each task including:
   - A clear task description
   - What file to create or update
   - What function to create or update
   - Details to drive code changes
   - Commands to test changes

Be precise and actionable. Your analysis will be used to implement this project.
"""

# Prompt for refinement
REFINEMENT_PROMPT = """You've created an initial task breakdown. Now, please review and refine your analysis to ensure:

1. All tasks are clear, specific, and actionable
2. The implementation notes cover all necessary technical details
3. The beginning and ending context are complete
4. Low-level tasks build on each other in a logical sequence
5. Each task includes specific files and functions to create or update
6. Test commands are practical and adequate

Here's your initial analysis:

{initial_analysis}

Please provide a refined version that addresses any gaps or improvements needed.
"""

# Prompt for formatting into template
TEMPLATE_FORMAT_PROMPT = """
Format your refined analysis precisely into this specification template:

```markdown
{template}
```

For each task in the Low-Level Tasks section, include the `aider` code block with prompts for:
- What prompt would you run to complete this task?
- What file do you want to CREATE or UPDATE?
- What function do you want to CREATE or UPDATE?
- What are details you want to add to drive the code changes?
- What command should be run to test that the changes are correct?

Make sure to follow the exact template format, filling in all sections with appropriate content.
"""

# Prompt for validation
VALIDATION_PROMPT = """
Review this specification document to ensure it is complete, actionable, and follows best practices:

{spec_document}

Validation criteria:
1. High-level objective clearly states what is being built
2. Mid-level objectives cover all necessary steps to achieve the high-level goal
3. Implementation notes provide sufficient technical details and dependencies
4. Beginning and ending contexts are clearly specified
5. Low-level tasks are ordered logically and build on each other
6. Each task includes specific files, functions, and test commands
7. All tasks are actionable and specific

If you find any issues, please identify them and suggest specific improvements. If the specification meets all criteria, confirm it is valid.
"""

def analyze_task(
    task: str, 
    llm_config: Dict[str, str], 
    progress: Optional[Progress] = None,
    custom_template: Optional[str] = None,
    search_enabled: bool = False,
    validate: bool = True,
    verbose: bool = False
) -> str:
    """
    Analyze a task and generate a specification document using a multi-step process.
    
    Args:
        task: The task to analyze
        llm_config: LLM configuration
        progress: Optional progress bar
        custom_template: Optional custom template string
        search_enabled: Whether to enable web search for additional context
        validate: Whether to validate the final document
        verbose: Enable verbose output
        
    Returns:
        str: The generated specification document
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
    
    # Define steps and their estimated weights (relative time complexity)
    steps = [
        {"name": "search", "weight": 0.1, "enabled": search_enabled},
        {"name": "initial_analysis", "weight": 0.35, "enabled": True},
        {"name": "refinement", "weight": 0.25, "enabled": True},
        {"name": "formatting", "weight": 0.15, "enabled": True},
        {"name": "validation", "weight": 0.15, "enabled": validate}
    ]
    
    # Filter out disabled steps and recalculate weights
    enabled_steps = [step for step in steps if step["enabled"]]
    total_weight = sum(step["weight"] for step in enabled_steps)
    for step in enabled_steps:
        step["weight"] = step["weight"] / total_weight
    
    # Storage for timing data
    timing_data = {}
    step_starts = {}
    completed_weight = 0.0
    
    # Track overall progress with finer granularity
    overall_task_id = progress.add_task("Analyzing task...", total=1000)
    progress.update(overall_task_id, advance=0)
    
    # Template setup
    template_str = custom_template if custom_template else get_default_template()
    if not validate_template(template_str):
        raise ValueError("Invalid template: missing required placeholders")
    
    # Step 1: Search for additional context
    additional_context = ""
    if search_enabled:
        current_step = next(s for s in enabled_steps if s["name"] == "search")
        step_weight = current_step["weight"]
        step_starts["search"] = time.time()
        
        # Create a progress task for this step with higher granularity
        search_task_id = progress.add_task("Searching for context (Step 1/5)...", total=100)
        progress.update(overall_task_id, advance=0, description="Searching for context...")
        
        # Start the search and update progress incrementally (simulate progress updates)
        for i in range(10):
            if i > 0:  # Skip the first iteration to avoid zero timing
                # Update the search progress
                progress.update(search_task_id, completed=i*10)
                # Also update the main progress incrementally
                increment = (step_weight * 1000) / 10
                progress.update(overall_task_id, advance=increment/2)
                time.sleep(0.05)  # Small delay to show progress
        
        search_results = search_web(task, max_results=3)
        search_time = time.time() - step_starts["search"]
        timing_data["search"] = search_time
        
        progress.update(search_task_id, completed=100)
        
        # Update overall progress based on completed weight
        completed_weight += step_weight
        progress.update(overall_task_id, completed=int(completed_weight * 1000))
        
        if search_results:
            additional_context = "ADDITIONAL CONTEXT FROM WEB SEARCH:\n\n"
            for result in search_results:
                additional_context += f"- {result['title']}: {result['description']}\n"
    
    # Step 2: Initial task breakdown
    current_step = next(s for s in enabled_steps if s["name"] == "initial_analysis")
    step_weight = current_step["weight"]
    step_starts["initial_analysis"] = time.time()
    
    initial_task_id = progress.add_task("Creating initial analysis (Step 2/5)...", total=100)
    progress.update(overall_task_id, description="Creating initial analysis...")
    
    # Simulate progress updates before the actual API call
    for i in range(5):
        progress.update(initial_task_id, completed=i*10)
        increment = (step_weight * 1000) / 10
        progress.update(overall_task_id, advance=increment/2)
        time.sleep(0.05)
    
    breakdown_prompt = TASK_BREAKDOWN_PROMPT.format(
        task=task,
        additional_context=additional_context
    )
    
    # Update progress before the potentially long call
    progress.update(initial_task_id, completed=50)
    progress.update(overall_task_id, advance=increment)
    
    initial_analysis = complete(
        llm_config=llm_config,
        prompt=breakdown_prompt,
        system_prompt=ANALYSIS_SYSTEM_PROMPT,
        temperature=0.3,
    )
    
    # Update progress after the call
    for i in range(5, 10):
        progress.update(initial_task_id, completed=i*10)
        progress.update(overall_task_id, advance=increment/2)
        time.sleep(0.02)
    
    initial_time = time.time() - step_starts["initial_analysis"]
    timing_data["initial_analysis"] = initial_time
    
    progress.update(initial_task_id, completed=100)
    
    # Update overall progress
    completed_weight += step_weight
    progress.update(overall_task_id, completed=int(completed_weight * 1000), description="Refining analysis...")
    
    # Step 3: Refinement
    current_step = next(s for s in enabled_steps if s["name"] == "refinement")
    step_weight = current_step["weight"]
    step_starts["refinement"] = time.time()
    
    refinement_task_id = progress.add_task("Refining analysis (Step 3/5)...", total=100)
    
    # Simulate progress updates before the actual API call
    for i in range(5):
        progress.update(refinement_task_id, completed=i*10)
        increment = (step_weight * 1000) / 10
        progress.update(overall_task_id, advance=increment/2)
        time.sleep(0.03)
    
    refinement_prompt = REFINEMENT_PROMPT.format(
        initial_analysis=initial_analysis
    )
    
    messages = [
        {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
        {"role": "user", "content": breakdown_prompt},
        {"role": "assistant", "content": initial_analysis},
        {"role": "user", "content": refinement_prompt}
    ]
    
    # Update progress before potentially long call
    progress.update(refinement_task_id, completed=50)
    progress.update(overall_task_id, advance=increment)
    
    refined_analysis = chat_with_history(
        llm_config=llm_config,
        messages=messages,
        temperature=0.2,
    )
    
    # Update progress after the call
    for i in range(5, 10):
        progress.update(refinement_task_id, completed=i*10)
        progress.update(overall_task_id, advance=increment/2)
        time.sleep(0.02)
    
    refinement_time = time.time() - step_starts["refinement"]
    timing_data["refinement"] = refinement_time
    
    progress.update(refinement_task_id, completed=100)
    
    # Update overall progress
    completed_weight += step_weight
    progress.update(overall_task_id, completed=int(completed_weight * 1000), description="Formatting specification...")
    
    # Step 4: Format into template
    current_step = next(s for s in enabled_steps if s["name"] == "formatting")
    step_weight = current_step["weight"]
    step_starts["formatting"] = time.time()
    
    template_task_id = progress.add_task("Formatting specification (Step 4/5)...", total=100)
    
    # Simulate progress updates before the actual API call
    for i in range(5):
        progress.update(template_task_id, completed=i*10)
        increment = (step_weight * 1000) / 10
        progress.update(overall_task_id, advance=increment/2)
        time.sleep(0.03)
    
    format_prompt = TEMPLATE_FORMAT_PROMPT.format(
        template=template_str
    )
    
    messages.append({"role": "assistant", "content": refined_analysis})
    messages.append({"role": "user", "content": format_prompt})
    
    # Update progress before potentially long call
    progress.update(template_task_id, completed=50)
    progress.update(overall_task_id, advance=increment)
    
    formatted_spec = chat_with_history(
        llm_config=llm_config,
        messages=messages,
        temperature=0.2,
    )
    
    # Update progress after the call
    for i in range(5, 10):
        progress.update(template_task_id, completed=i*10)
        progress.update(overall_task_id, advance=increment/2)
        time.sleep(0.02)
    
    formatting_time = time.time() - step_starts["formatting"]
    timing_data["formatting"] = formatting_time
    
    progress.update(template_task_id, completed=100)
    
    # Update overall progress
    completed_weight += step_weight
    progress.update(overall_task_id, completed=int(completed_weight * 1000), 
                   description="Validating specification..." if validate else "Completing analysis...")
    
    # Step 5: Validation
    if validate:
        current_step = next(s for s in enabled_steps if s["name"] == "validation")
        step_weight = current_step["weight"]
        step_starts["validation"] = time.time()
        
        validation_task_id = progress.add_task("Validating specification (Step 5/5)...", total=100)
        
        # Simulate incremental progress
        increment = (step_weight * 1000) / 20  # More granular for validation
        
        formatted_spec = validate_specification(
            formatted_spec, 
            llm_config, 
            progress, 
            validation_task_id,
            timing_data,
            step_starts,
            overall_task_id,
            increment
        )
        
        validation_time = time.time() - step_starts["validation"]
        timing_data["validation"] = validation_time
        
        progress.update(validation_task_id, completed=100)
        
        # Update overall progress
        completed_weight += step_weight
        progress.update(overall_task_id, completed=int(completed_weight * 1000), description="Analysis completed!")
    
    # Complete the overall task
    progress.update(overall_task_id, completed=100, description="Analysis completed!")
    
    # Print timing stats if verbose
    if verbose:
        console.print("\n[bold]Timing statistics:[/bold]")
        for step, duration in timing_data.items():
            console.print(f"  {step}: {format_time(duration)}")
        console.print(f"  Total: {format_time(sum(timing_data.values()))}")
    
    return formatted_spec

def validate_specification(
    spec_document: str,
    llm_config: Dict[str, str],
    progress: Progress,
    task_id: TaskID,
    timing_data: Dict[str, float] = None,
    step_starts: Dict[str, float] = None,
    overall_task_id: Optional[TaskID] = None,
    increment: float = 0,
    max_iterations: int = 3
) -> str:
    """
    Validate and improve a specification document.
    
    Args:
        spec_document: The specification document to validate
        llm_config: LLM configuration
        progress: Progress bar
        task_id: Task ID in the progress bar
        timing_data: Optional dictionary to store timing data
        step_starts: Optional dictionary to store step start times
        max_iterations: Maximum number of validation iterations
        
    Returns:
        str: The validated and potentially improved specification document
    """
    current_spec = spec_document
    iterations_timing = []
    
    for i in range(max_iterations):
        iter_start_time = time.time()
        progress.update(task_id, description=f"Validation iteration {i+1}/{max_iterations}...")
        
        # Simulate progress for validation prep
        for j in range(3):
            progress.update(task_id, advance=5)
            if overall_task_id and increment:
                progress.update(overall_task_id, advance=increment/4)
            time.sleep(0.02)
        
        validation_prompt = VALIDATION_PROMPT.format(
            spec_document=current_spec
        )
        
        # Update progress before LLM call
        progress.update(task_id, advance=10)
        if overall_task_id and increment:
            progress.update(overall_task_id, advance=increment/4)
        
        validation_result = complete(
            llm_config=llm_config,
            prompt=validation_prompt,
            system_prompt=ANALYSIS_SYSTEM_PROMPT,
            temperature=0.2,
        )
        
        # Update progress after LLM call
        progress.update(task_id, advance=10)
        if overall_task_id and increment:
            progress.update(overall_task_id, advance=increment/4)
        
        # Check if the validation indicates issues or if it's already valid
        if any(term in validation_result.lower() for term in ["valid", "meets all criteria", "no issues"]):
            # Specification is valid, no changes needed
            progress.update(task_id, completed=100 / max_iterations * (i+1))
            if overall_task_id and increment:
                progress.update(overall_task_id, advance=increment/4)
            if timing_data is not None and step_starts is not None:
                iterations_timing.append(time.time() - iter_start_time)
            break
        
        # Extract suggestions for improvement
        improvement_prompt = f"""
Based on the validation issues identified:

{validation_result}

Please improve the specification document to address these issues:

{current_spec}

Provide the complete improved specification document.
"""
        
        # Simulate progress before LLM call
        for j in range(2):
            progress.update(task_id, advance=5)
            if overall_task_id and increment:
                progress.update(overall_task_id, advance=increment/8)
            time.sleep(0.02)
        
        # Get improved specification
        improved_spec = complete(
            llm_config=llm_config,
            prompt=improvement_prompt,
            system_prompt=ANALYSIS_SYSTEM_PROMPT,
            temperature=0.2,
        )
        
        # Update progress after LLM call
        for j in range(2):
            progress.update(task_id, advance=5)
            if overall_task_id and increment:
                progress.update(overall_task_id, advance=increment/8)
            time.sleep(0.02)
        
        # Update the current specification
        current_spec = improved_spec
        
        # Update progress
        progress.update(task_id, completed=100 / max_iterations * (i+1))
        if overall_task_id and increment:
            progress.update(overall_task_id, advance=increment/4)
        
        # Track timing for this iteration
        if timing_data is not None and step_starts is not None:
            iterations_timing.append(time.time() - iter_start_time)
    
    return current_spec

def extract_components(spec_document: str) -> Dict[str, Any]:
    """
    Extract components from a specification document.
    
    Args:
        spec_document: The specification document
        
    Returns:
        Dict containing the extracted components
    """
    components = {
        "high_level_objective": "",
        "mid_level_objectives": "",
        "implementation_notes": "",
        "beginning_context": "",
        "ending_context": "",
        "low_level_tasks": ""
    }
    
    # Extract high-level objective
    high_level_match = re.search(r'## High-Level Objective\s+(.*?)(?=##|\Z)', spec_document, re.DOTALL)
    if high_level_match:
        components["high_level_objective"] = high_level_match.group(1).strip()
    
    # Extract mid-level objectives
    mid_level_match = re.search(r'## Mid-Level Objective\s+(.*?)(?=##|\Z)', spec_document, re.DOTALL)
    if mid_level_match:
        components["mid_level_objectives"] = mid_level_match.group(1).strip()
    
    # Extract implementation notes
    impl_notes_match = re.search(r'## Implementation Notes\s+(.*?)(?=##|\Z)', spec_document, re.DOTALL)
    if impl_notes_match:
        components["implementation_notes"] = impl_notes_match.group(1).strip()
    
    # Extract beginning context
    beginning_context_match = re.search(r'### Beginning context\s+(.*?)(?=###|\Z)', spec_document, re.DOTALL)
    if beginning_context_match:
        components["beginning_context"] = beginning_context_match.group(1).strip()
    
    # Extract ending context
    ending_context_match = re.search(r'### Ending context\s+(.*?)(?=##|\Z)', spec_document, re.DOTALL)
    if ending_context_match:
        components["ending_context"] = ending_context_match.group(1).strip()
    
    # Extract low-level tasks
    low_level_match = re.search(r'## Low-Level Tasks.*?\n(.*?)(?=##|\Z)', spec_document, re.DOTALL)
    if low_level_match:
        components["low_level_tasks"] = low_level_match.group(1).strip()
    
    return components
