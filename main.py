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

from taskspec.config import load_config
from taskspec.llm import setup_llm_client
from taskspec.analyzer import analyze_task
from taskspec.design import analyze_design_document, format_subtask_for_analysis
from taskspec.template import render_template
from taskspec.utils import sanitize_filename, format_design_results, generate_task_summary, split_phases_to_files
from taskspec.cache import get_cache_manager

# Initialize Typer app
app = typer.Typer(help="Task analysis and specification generator using LLMs")
console = Console()

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
        # Get task content
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
        
        # Load template if provided
        custom_template = None
        if template_path is not None:
            if not template_path.exists():
                console.print(f"[bold red]Error:[/bold red] Template file not found: {template_path}")
                return 1
            custom_template = template_path.read_text()
            if verbose:
                console.print(f"Template loaded from: [bold]{template_path}[/bold]")
        
        # Load configuration
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
            # Generate a summary of the task for the filename
            filename = generate_task_summary(task_content, llm_client)
            filename = sanitize_filename(filename)
            output_file = Path(f"{filename}_{timestamp}_spec.md")
            
            if verbose:
                console.print(f"Generated filename based on task summary: [bold]{filename}[/bold]")
        
        # Progress display setup
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}[/bold blue]"),
            BarColumn(bar_width=40),
            TextColumn("[bold]{task.percentage:.0f}%[/bold]"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),  # Use Rich's built-in remaining time column
            console=console,
            transient=not verbose,
            expand=True,
            refresh_per_second=10  # Increase refresh rate for smoother updates
        ) as progress:
            # Analyze task
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
        
        # Output results
        if not no_stdout:
            console.print(spec_content)
        
        # Save to file if requested
        if output_file:
            output_file.write_text(spec_content)
            if verbose or not no_stdout:
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
    """
    try:
        # Check if we're in interactive mode
        if interactive:
            # Generate output filename if none provided
            if output_file is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = Path(f"interactive_design_{timestamp}_design.md")
                if verbose:
                    console.print(f"Generated filename for interactive design: [bold]{output_file}[/bold]")
                    
            # Load configuration and setup LLM client for interactive session
            config = load_config(
                provider_override=llm_provider, 
                model_override=llm_model,
                cache_enabled_override=cache_enabled,
                cache_type_override=cache_type,
                cache_ttl_override=cache_ttl
            )
            
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
            design_content = design.create_interactive_design(llm_client, console, verbose)
            
            # Save the design document 
            output_file.write_text(design_content)
            if verbose:
                console.print(f"\nDesign document saved to: [bold green]{output_file}[/bold green]")
                
            # Proceed with analysis if needed
            if verbose:
                console.print("\n[bold]Proceeding to analyze the created design document...[/bold]")
            
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
            cache_ttl_override=cache_ttl
        )
        
        if verbose:
            console.print(f"Using LLM provider: [bold]{config.llm_provider}[/bold] with model: [bold]{config.llm_model}[/bold]")
            if config.cache_enabled:
                console.print(f"Caching enabled: [bold]{config.cache_type}[/bold] with TTL: [bold]{config.cache_ttl}s[/bold]")
        
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
            output_file = Path(f"{filename}_{timestamp}_phases.md")
            
            if verbose:
                console.print(f"Generated filename based on design summary: [bold]{filename}[/bold]")
        
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
                verbose=verbose
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
            
        # Split the phases file
        if verbose:
            console.print(f"Splitting phases from: [bold]{phases_file}[/bold]")
            
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
