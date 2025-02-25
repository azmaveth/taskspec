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
# ]
# ///

import os
import sys
import typer
from datetime import datetime
from pathlib import Path
from typing import Optional, Union
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn

from config import load_config
from llm import setup_llm_client
from analyzer import analyze_task
from design import analyze_design_document, format_subtask_for_analysis
from template import render_template
from utils import sanitize_filename, format_design_results
from cache import get_cache_manager

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
            # Use first 30 chars of task for filename
            first_line = task_content.splitlines()[0] if task_content else "task"
            filename = sanitize_filename(first_line[:30])
            output_file = Path(f"{filename}_{timestamp}.spec.md")
        
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
            expand=True
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
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """
    Analyze a design document, break it into implementation phases and subtasks.
    
    The design document can be provided directly as an argument or read from a file.
    """
    try:
        # Get design document content
        if design_doc is None and input_file is None:
            console.print("[bold red]Error:[/bold red] Either design document or input file must be provided.")
            return 1
            
        if input_file is not None:
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
            # Use first 30 chars of design doc for filename
            first_line = design_content.splitlines()[0] if design_content else "design"
            filename = sanitize_filename(first_line[:30])
            output_file = Path(f"{filename}_{timestamp}_phases.md")
        
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
            expand=True
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
                        if verbose:
                            console.print(f"Analyzing subtask {task_idx+1}/{len(phase['subtasks'])} of phase {phase_idx+1}/{len(result['phases'])}")
                        
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
            
            return 0
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        return 1

if __name__ == "__main__":
    app()
