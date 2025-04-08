#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "typer>=0.9.0",
#     "rich>=13.6.0",
#     "litellm>=1.16.0", 
#     "python-dotenv>=1.0.0",
#     "pydantic>=2.5.0",
#     "requests>=2.31.0",
#     "pyyaml>=6.0.0",
#     "statistics>=1.0.3.5",
# ]
# ///

import os
import sys
import typer
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Union
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn

# Make direct invocation of main.py work by adding parent directory to path
# to ensure the taskspec package can be found
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))

# Save to file if requested
from taskspec.config import load_config
# Save to file if requested
from taskspec.cache import get_cache_manager
from taskspec.llm import setup_llm_client
from taskspec.design import analyze_design_document, format_subtask_for_analysis
from taskspec.utils import generate_task_summary, split_phases_to_files, format_design_results, sanitize_filename
from taskspec.analyzer import analyze_task

console = Console()
app = typer.Typer()
@app.command()
def analyze(
    task: Optional[str] = typer.Argument(None, help="The task to analyze"),
    input_file: Optional[Path] = typer.Option(
        None, "--input", "-i", help="Input file containing task description"
    ),
    output_file: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output file path (default: auto-generated)"
    ),
    llm_provider: Optional[str] = typer.Option(
        None, "--provider", "-p", help="LLM provider to use (default: from config)"
    ),
    llm_model: Optional[str] = typer.Option(
        None, "--model", "-m", help="LLM model to use (default: from config)"
    ),
    no_stdout: bool = typer.Option(
        False, "--no-stdout", help="Disable printing to stdout"
    ),
    search: bool = typer.Option(
        False, "--search", help="Enable web search for additional context"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
    template_path: Optional[Path] = typer.Option(
        None, "--template", "-t", help="Custom template file path"
    ),
    validate: bool = typer.Option(
        True, "--validate/--no-validate", help="Enable task validation"
    ),
    cache_enabled: bool = typer.Option(
        True, "--cache/--no-cache", help="Enable response caching"
    ),
    cache_type: str = typer.Option(
        "disk", "--cache-type", help="Cache type (memory, disk)"
    ),
    cache_ttl: int = typer.Option(
        86400, "--cache-ttl", help="Cache TTL in seconds"
    ),
    clear_cache: bool = typer.Option(
        False, "--clear-cache", help="Clear the cache before running"
    ),
):
    """
    Analyze a task, break it down into subtasks, and generate a specification document.

    The task can be provided directly as an argument or read from a file.
    """
    try:
        if task is None and input_file is None:
            console.print("[bold red]Error:[/bold red] Either task or input file must be provided.")
            return 1

        if input_file is not None:
            if not input_file.exists():
                console.print(f"[bold red]Error:[/bold red] Input file not found: {input_file}")
                return 1
            task_content = input_file.read_text()
            if verbose:
                console.print(f"Task loaded from: [bold]{input_file}[/bold]")
        else:
            task_content = task

        custom_template = None
        if template_path is not None:
            if not template_path.exists():
                console.print(f"[bold red]Error:[/bold red] Template file not found: {template_path}")
                return 1
            custom_template = template_path.read_text()
            if verbose:
                console.print(f"Template loaded from: [bold]{template_path}[/bold]")

        config = load_config(
            provider_override=llm_provider,
            model_override=llm_model,
            cache_enabled_override=cache_enabled,
            cache_type_override=cache_type,
            cache_ttl_override=cache_ttl
        )

        if verbose:
            console.print(f"Using LLM provider: [bold]{config.llm_provider}[/bold] with model: [bold]{config.llm_model}[/bold]")
            if config.cache_enabled:
                console.print(f"Caching enabled: [bold]{config.cache_type}[/bold] with TTL: [bold]{config.cache_ttl}s[/bold]")

        cache_manager = None
        if config.cache_enabled:
            cache_manager = get_cache_manager(
                cache_type=config.cache_type,
                cache_path=config.cache_path,
                ttl=config.cache_ttl
            )

            if clear_cache:
                if verbose:
                    console.print("[bold yellow]Clearing cache...[/bold yellow]")
                cache_manager.clear()

            if verbose:
                stats = cache_manager.get_stats()
                console.print(f"Cache statistics: {stats['entries']} entries, {stats['hits']} hits, {stats['misses']} misses")

        llm_client = setup_llm_client(config, cache_manager)

        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = generate_task_summary(task_content, llm_client)
            filename = sanitize_filename(filename)

            if 'pytest' in sys.modules:
                output_dir = Path("test_output")
                os.makedirs(output_dir, exist_ok=True)
                output_file = output_dir / f"{filename}_{timestamp}_spec.md"
            else:
                output_dir = config.output_directory
                os.makedirs(output_dir, exist_ok=True)
                output_file = output_dir / f"{filename}_{timestamp}_spec.md"

            if verbose:
                console.print(f"Generated filename based on task summary: [bold]{filename}[/bold]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}[/bold blue]"),
            BarColumn(bar_width=40),
            TextColumn("[bold]{task.percentage:.0f}%[/bold]"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
            transient=not verbose,
            expand=True,
            refresh_per_second=10
        ) as progress:
            if verbose:
                console.print(Panel(task_content[:200] + "..." if len(task_content) > 200 else task_content,
                                    title="Task Description"))

            spec_content = analyze_task(
                task_content,
                llm_client,
                progress=progress,
                custom_template=custom_template,
                search_enabled=search,
                validate=validate,
                verbose=verbose
            )

        if not no_stdout:
            console.print(spec_content)

        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(spec_content)
            if verbose:
                console.print(f"[debug] Writing output to: {output_file}")
                console.print(f"\nSpecification saved to: [bold green]{output_file}[/bold green]")

        return 0

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        return 1
@app.command()
def design(
    design_doc: Optional[str] = typer.Argument(None, help="The design document text"),
    input_file: Optional[Path] = typer.Option(
        None, "--input", "-i", help="Input file containing design document"
    ),
    output_file: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output file path (default: auto-generated)"
    ),
    output_format: str = typer.Option(
        "markdown", "--format", "-f", help="Output format (markdown, json, yaml)"
    ),
    conventions_file: Optional[Path] = typer.Option(
        None, "--conventions", "-c", help="Conventions file containing coding standards and design preferences"
    ),
    llm_provider: Optional[str] = typer.Option(
        None, "--provider", "-p", help="LLM provider to use (default: from config)"
    ),
    llm_model: Optional[str] = typer.Option(
        None, "--model", "-m", help="LLM model to use (default: from config)"
    ),
    no_stdout: bool = typer.Option(
        False, "--no-stdout", help="Disable printing to stdout"
    ),
    cache_enabled: bool = typer.Option(
        True, "--cache/--no-cache", help="Enable response caching"
    ),
    cache_type: str = typer.Option(
        "disk", "--cache-type", help="Cache type (memory, disk)"
    ),
    cache_ttl: int = typer.Option(
        86400, "--cache-ttl", help="Cache TTL in seconds"
    ),
    clear_cache: bool = typer.Option(
        False, "--clear-cache", help="Clear the cache before running"
    ),
    analyze_subtasks: bool = typer.Option(
        False, "--analyze-subtasks", help="Analyze each subtask and generate specifications"
    ),
    split_phases: bool = typer.Option(
        False, "--split-phases", help="Split phases into separate files"
    ),
    output_dir: Optional[Path] = typer.Option(
        None, "--output-dir", "-d", help="Directory for split phase files (default: same as output file)"
    ),
    interactive: bool = typer.Option(
        False, "--interactive", help="Create a design document through guided interactive dialog with the LLM (includes security threat analysis and risk management)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """
    Analyze a design document, break it into implementation phases and subtasks.
    
    The design document can be provided directly as an argument or read from a file.
    Alternatively, use --interactive to create a design document through a guided dialog with the LLM.
    The interactive mode will guide you through requirements elicitation, security threat analysis,
    risk management strategy selection, and acceptance criteria definition.
    
    Use the --conventions option to provide a file with coding standards and design preferences
    that will be used as context for the design process.
    """
    try:
        # Check if we're in interactive mode
        if interactive:
            # Generate output filename if none provided
            if output_file is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # If we're running in a test environment, use test_output directory
                if 'pytest' in sys.modules:
                    output_dir = Path("test_output")
                    os.makedirs(output_dir, exist_ok=True)
                    output_file = output_dir / f"interactive_design_{timestamp}_design.md"
                else:
                    # Use the configured output directory
                    config = load_config(
                        provider_override=llm_provider,
                        model_override=llm_model,
                        conventions_file_override=conventions_file
                    )
                    output_dir = config.output_directory
                    os.makedirs(output_dir, exist_ok=True)
                    output_file = output_dir / f"interactive_design_{timestamp}_design.md"
                
                if verbose:
                    console.print(f"Generated filename for interactive design: [bold]{output_file}[/bold]")
                    
            # Load configuration and setup LLM client for interactive session
            config = load_config(
                provider_override=llm_provider, 
                model_override=llm_model,
                cache_enabled_override=cache_enabled,
                cache_type_override=cache_type,
                cache_ttl_override=cache_ttl,
                conventions_file_override=conventions_file
            )
            
            if verbose:
                console.print(f"Using LLM provider: [bold]{config.llm_provider}[/bold] with model: [bold]{config.llm_model}[/bold]")
                if config.cache_enabled:
                    console.print(f"Caching enabled: [bold]{config.cache_type}[/bold] with TTL: [bold]{config.cache_ttl}s[/bold]")
                if config.conventions_file:
                    console.print(f"Using conventions file: [bold]{config.conventions_file}[/bold]")
            
            cache_manager = None
            if config.cache_enabled:
                cache_manager = get_cache_manager(
                    cache_type=config.cache_type,
                    cache_path=config.cache_path,
                    ttl=config.cache_ttl
                )
                
                if clear_cache:
                    if verbose:
                        console.print("[bold yellow]Clearing cache...[/bold yellow]")
                    cache_manager.clear()
            
            # Setup LLM client
            llm_client = setup_llm_client(config, cache_manager)
            
            # Run interactive design session
            design_content = create_interactive_design(llm_client, console, verbose, config.conventions_file)
            
            # Save the design document 
            output_file.write_text(design_content)
            if verbose:
                console.print(f"\nDesign document saved to: [bold green]{output_file}[/bold green]")
                
            # Also save the original document before analysis
            original_output_file = output_file.with_name(f"{output_file.stem}_original{output_file.suffix}")
            original_output_file.write_text(design_content)
            if verbose:
                console.print(f"Original design document saved to: [bold green]{original_output_file}[/bold green]")
                
            # Ask if the user wants to continue with phase extraction
            continue_prompt = typer.confirm("\nDo you want to continue and extract implementation phases?", default=True)
            if not continue_prompt:
                console.print("\n[bold green]Interactive session completed.[/bold green] The design document has been saved.")
                return 0
                
            # Proceed with analysis if user confirmed
            if verbose:
                console.print("\n[bold]Proceeding to extract implementation phases...[/bold]")
            
        # Get design document content from file or argument
        elif design_doc is None and input_file is None:
            console.print("[bold red]Error:[/bold red] Either design document or input file must be provided, or use --interactive mode.")
            return 1
            
        elif input_file is not None:
            if not input_file.exists():
                console.print(f"[bold red]Error:[/bold red] Input file not found: {input_file}")
                return 1
            design_content = input_file.read_text()
            if verbose:
                console.print(f"Design document loaded from: [bold]{input_file}[/bold]")
        else:
            design_content = design_doc
        
        # Load configuration
        config = load_config(
            provider_override=llm_provider, 
            model_override=llm_model,
            cache_enabled_override=cache_enabled,
            cache_type_override=cache_type,
            cache_ttl_override=cache_ttl,
            conventions_file_override=conventions_file
        )
        
        if verbose:
            console.print(f"Using LLM provider: [bold]{config.llm_provider}[/bold] with model: [bold]{config.llm_model}[/bold]")
            if config.cache_enabled:
                console.print(f"Caching enabled: [bold]{config.cache_type}[/bold] with TTL: [bold]{config.cache_ttl}s[/bold]")
            if config.conventions_file:
                console.print(f"Using conventions file: [bold]{config.conventions_file}[/bold]")
        
        # Setup cache if enabled
        cache_manager = None
        if config.cache_enabled:
            cache_manager = get_cache_manager(
                cache_type=config.cache_type,
                cache_path=config.cache_path,
                ttl=config.cache_ttl
            )
            
            if clear_cache:
                if verbose:
                    console.print("[bold yellow]Clearing cache...[/bold yellow]")
                cache_manager.clear()
            
            if verbose:
                stats = cache_manager.get_stats()
                console.print(f"Cache statistics: {stats['entries']} entries, {stats['hits']} hits, {stats['misses']} misses")
        
        # Setup LLM client
        llm_client = setup_llm_client(config, cache_manager)
        
        # Generate auto filename if none provided
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Generate a summary of the design document for the filename
            filename = generate_task_summary(design_content, llm_client)
            filename = sanitize_filename(filename)
            
            # If we're running in a test environment, use test_output directory
            if 'pytest' in sys.modules:
                output_dir = Path("test_output")
                os.makedirs(output_dir, exist_ok=True)
                output_file = output_dir / f"{filename}_{timestamp}_phases.md"
            else:
                # Use the configured output directory
                output_dir = config.output_directory
                os.makedirs(output_dir, exist_ok=True)
                output_file = output_dir / f"{filename}_{timestamp}_phases.md"
            
            if verbose:
                console.print(f"Generated filename based on design summary: [bold]{filename}[/bold]")
        
        # Save the original design document before analysis
        original_output_file = output_file.with_name(f"{output_file.stem}_original{output_file.suffix}")
        original_output_file.write_text(design_content)
        if verbose:
            console.print(f"\nOriginal design document saved to: [bold green]{original_output_file}[/bold green]")
        
        # Progress display setup
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}[/bold blue]"),
            BarColumn(bar_width=40),
            TextColumn("[bold]{task.percentage:.0f}%[/bold]"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
            transient=not verbose,
            expand=True,
            refresh_per_second=10  # Increase refresh rate for smoother updates
        ) as progress:
            # Analyze design document
            if verbose:
                console.print(Panel(design_content[:200] + "..." if len(design_content) > 200 else design_content, 
                                  title="Design Document"))
            
            result = analyze_design_document(
                design_content, 
                llm_client, 
                progress=progress,
                verbose=verbose,
                conventions_file=config.conventions_file
            )
            
            # Process subtasks if requested
            if analyze_subtasks:
                if verbose:
                    console.print("\n[bold]Analyzing individual subtasks...[/bold]")
                
                specifications = []
                
                for phase_idx, phase in enumerate(result['phases']):
                    phase_specs = []
                    
                    for task_idx, task in enumerate(phase['subtasks']):
                        # Clean up any remaining numbering in the title for display
                        clean_title = re.sub(r'^(\d+\.\s+|\d+\.\d+\.\s+|\d+\)\s+|\(\d+\)\s+|Subtask\s+\d+:\s+|Task\s+\d+:\s+)', '', task['title'])
                        if verbose:
                            console.print(f"Analyzing subtask {task_idx+1}/{len(phase['subtasks'])} of phase {phase_idx+1}/{len(result['phases'])}: {clean_title}")
                        
                        task_content = format_subtask_for_analysis(task)
                        
                        spec = analyze_task(
                            task_content,
                            llm_client,
                            progress=progress,
                            validate=False,
                            verbose=verbose
                        )
                        
                        phase_specs.append({
                            'task': task,
                            'specification': spec
                        })
                    
                    phase['specifications'] = phase_specs
            
            # Format output based on requested format
            output_content = format_design_results(result, output_format, analyze_subtasks)
            
            # Output results
            if not no_stdout:
                console.print(output_content)
            
            # Save to file if requested
            if output_file:
                output_file.write_text(output_content)
                if verbose or not no_stdout:
                    console.print(f"\nResults saved to: [bold green]{output_file}[/bold green]")
                
                # Split phases if requested
                if split_phases:
                    if verbose:
                        console.print("\n[bold]Splitting phases into separate files...[/bold]")
                    
                    created_files = split_phases_to_files(
                        phases_file=output_file,
                        output_dir=output_dir,
                        prefix=None  # Use default prefix based on filename
                    )
                    
                    if verbose:
                        console.print(f"\n[bold green]Successfully split into {len(created_files)} files:[/bold green]")
                        for file_path in created_files:
                            console.print(f"  - {file_path}")
            
            return 0
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        return 1

@app.command()
def split(
    phases_file: Path = typer.Argument(..., help="Path to the phases markdown file"),
    output_dir: Optional[Path] = typer.Option(
        None, "--output-dir", "-d", help="Directory for output files (default: same directory as input)"
    ),
    prefix: Optional[str] = typer.Option(
        None, "--prefix", "-p", help="Prefix for output filenames (default: derived from input filename)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """
    Split a phases markdown file into separate files for each phase.
    """
    try:
        if not phases_file.exists():
            console.print(f"[bold red]Error:[/bold red] Phases file not found: {phases_file}")
            return 1
        
        # Load configuration to get default output directory if none provided
        config = load_config()
        if output_dir is None:
            # Use either the same directory as input file or the configured output directory
            output_dir = config.output_directory
            os.makedirs(output_dir, exist_ok=True)
            
        # Split the phases file
        if verbose:
            console.print(f"Splitting phases from: [bold]{phases_file}[/bold]")
            console.print(f"Output directory: [bold]{output_dir}[/bold]")
            
        created_files = split_phases_to_files(
            phases_file=phases_file,
            output_dir=output_dir,
            prefix=prefix
        )
        
        if verbose:
            console.print(f"\n[bold green]Successfully split into {len(created_files)} files:[/bold green]")
            for file_path in created_files:
                console.print(f"  - {file_path}")
                
        return 0
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        return 1

if __name__ == "__main__":
    app()