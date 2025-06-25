"""
Generate-Tests command module for the SLIM CLI.

This module contains the implementation of the 'generate-tests' subcommand,
which generates unit test files for Python code in the repository.
"""

import logging
import os
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from jpl.slim.commands.common import get_ai_model_pairs
from jpl.slim.app import app, state, handle_dry_run_for_command

console = Console()

@app.command(name="generate-tests")
def generate_tests(
    repo_dir: Path = typer.Option(
        ...,
        "--repo-dir",
        help="Repository directory location on local machine",
        exists=True,
        file_okay=False,
        dir_okay=True
    ),
    output_dir: Path = typer.Option(
        ...,
        "--output-dir",
        help="Directory where test files should be generated"
    ),
    use_ai: Optional[str] = typer.Option(
        None,
        "--use-ai",
        help="Generate tests using AI model. Use 'slim models list' to see available models."
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run", "-d",
        help="Show what would be executed without making changes"
    )
):
    """
    Generate unit test files for Python code in the repository.
    
    This command analyzes Python files in the specified repository
    and generates corresponding unit test files.
    """
    # Handle dry-run mode
    if state.dry_run or dry_run:
        if handle_dry_run_for_command(
            "generate-tests",
            repo_dir=str(repo_dir),
            output_dir=str(output_dir),
            use_ai=use_ai,
            dry_run=True
        ):
            return
    
    # Call the existing handler function
    success = handle_generate_tests(
        repo_dir=str(repo_dir),
        output_dir=str(output_dir),
        use_ai=use_ai
    )
    
    if not success:
        raise typer.Exit(1)

def handle_generate_tests(repo_dir, output_dir, use_ai):
    """
    Handle the generate-tests command.
    
    Args:
        repo_dir: Repository directory path
        output_dir: Output directory path
        use_ai: AI model to use for test generation
        
    Returns:
        bool: True if test generation was successful, False otherwise
    """
    logging.debug(f"Generating tests for repository: {repo_dir}")
    
    # Validate repository directory
    if not os.path.isdir(repo_dir):
        console.print(f"[red]Repository directory does not exist: {repo_dir}[/red]")
        return False
        
    # Initialize and run test generator
    try:
        from jpl.slim.testgen import TestGenerator

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Generating unit tests...", total=None)
            
            generator = TestGenerator(
                repo_path=repo_dir,
                output_dir=output_dir,
                model=use_ai
            )
            
            if generator.generate_tests():
                progress.update(task, completed=100)
                
        console.print(f"[green]Successfully generated tests in {output_dir}[/green]")
        
        # Print next steps with rich formatting
        console.print("\n[bold green]Test files generated successfully![/bold green]")
        console.print("\n[bold]Next steps:[/bold]")
        console.print("1. Install pytest if you haven't already:")
        console.print("   [cyan]pip install pytest[/cyan]")
        console.print("\n2. Review the generated tests and modify as needed")
        console.print("\n3. Run the tests:")
        console.print("   [cyan]python -m pytest[/cyan]")
        
        return True
    except Exception as e:
        console.print(f"[red]Test generation failed: {str(e)}[/red]")
        return False