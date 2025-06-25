"""
Models command module for the SLIM CLI.

This module contains the implementation of the 'models' subcommand,
which helps users discover and configure AI models.
"""

import logging
from typing import Optional
from enum import Enum
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from jpl.slim.commands.common import (
    check_model_availability,
    get_provider_setup_instructions,
    get_ai_model_pairs, get_dynamic_ai_model_pairs, get_dynamic_recommended_models
)
from jpl.slim.app import app, state, handle_dry_run_for_command

console = Console()

# Create models subcommand app
models_app = typer.Typer(help="Discover and configure AI models")

# Define enums for better type safety
class Tier(str, Enum):
    premium = "premium"
    balanced = "balanced"
    fast = "fast"
    local = "local"

class Task(str, Enum):
    documentation = "documentation"
    code_generation = "code_generation"

@models_app.callback(invoke_without_command=True)
def models_main(ctx: typer.Context):
    """
    AI model discovery and configuration utilities.
    
    Use subcommands to list, recommend, setup, or validate AI models.
    """
    if ctx.invoked_subcommand is None:
        # No subcommand provided, show recommendations
        models_recommend(task=Task.documentation, tier=Tier.balanced, dry_run=False, logging_level=None)

@models_app.command(name="list")
def models_list(
    provider: Optional[str] = typer.Option(None, help="Filter by provider"),
    tier: Optional[Tier] = typer.Option(None, help="Filter by quality tier"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Show what would be executed without making changes"),
    logging_level: str = typer.Option(None, "--logging", "-l", help="Set the logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL")
):
    """List all available AI models."""
    # Configure logging
    from jpl.slim.commands.common import configure_logging
    configure_logging(logging_level, state)
    
    logging.debug("Starting models list command")
    logging.debug(f"Filters: provider={provider}, tier={tier}")
    
    if state.dry_run or dry_run:
        if handle_dry_run_for_command("models list", provider=provider, tier=tier, dry_run=True):
            return
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("Loading model registry...", total=None)
        
        progress.update(task, description="Fetching available models from LiteLLM...")
        logging.debug("Fetching AI model pairs from LiteLLM registry")
        models = get_dynamic_ai_model_pairs()
        
        if not models:
            logging.error("Unable to fetch models from LiteLLM")
            progress.update(task, description="Failed to fetch models")
            console.print("[red]Unable to fetch models due to network issues.[/red]")
            console.print("[yellow]For local models, try: `ollama list`[/yellow]")
            raise typer.Exit(1)
            
        logging.debug(f"Found {len(models)} total models")
        
        if provider:
            progress.update(task, description=f"Filtering by provider: {provider}...")
            logging.debug(f"Applying provider filter: {provider}")
            models = [m for m in models if m.startswith(f"{provider}/")]
            logging.debug(f"After provider filter: {len(models)} models")
        
        if tier:
            progress.update(task, description=f"Filtering by tier: {tier}...")
            logging.debug(f"Tier filtering requested for: {tier}")
            # Filter by tier - this would need to be implemented
            # For now, we'll show all models with tier info
            pass
        
        progress.update(task, description=f"Found {len(models)} models")
    
    console.print(f"\n[bold]Found {len(models)} models:[/bold]")
    for model in sorted(models):
        console.print(f"  • [cyan]{model}[/cyan]")

@models_app.command(name="recommend")
def models_recommend(
    task: Task = typer.Option(Task.documentation, "--task", help="Task type"),
    tier: Tier = typer.Option(Tier.balanced, "--tier", help="Quality/cost tier"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Show what would be executed without making changes"),
    logging_level: str = typer.Option(None, "--logging", "-l", help="Set the logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL")
):
    """Get AI model recommendations for specific tasks."""
    # Configure logging
    from jpl.slim.commands.common import configure_logging
    configure_logging(logging_level, state)
    
    logging.debug(f"Getting recommendations for task={task.value}, tier={tier.value}")
    
    if state.dry_run or dry_run:
        if handle_dry_run_for_command("models recommend", task=task.value, tier=tier.value, dry_run=True):
            return
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task_id = progress.add_task("Fetching current model recommendations...", total=None)
        
        progress.update(task_id, description="Getting dynamic model recommendations...")
        recommendations = get_dynamic_recommended_models()
        
        progress.update(task_id, description="Building recommendation list...")
    
    console.print("\n[bold]🏆 Premium Cloud Models:[/bold]")
    for model in recommendations["premium"][:6]:  # Limit to top 6
        console.print(f"  • [cyan]{model}[/cyan]")
    
    console.print("\n[bold]🦙 Local Models:[/bold]")
    for model in recommendations["local"]:
        console.print(f"  • [green]{model}[/green]")
    
    console.print("\n[yellow]💡 Tip: For laptops, use models with 6B - 12B parameters for a balance of speed and performance[/yellow]")
    
    console.print("\n[bold]💡 Usage Examples:[/bold]")
    console.print("  [dim]# Premium documentation generation[/dim]")
    console.print(f"  slim apply --best-practices docs-website --use-ai {recommendations['premium'][0] if recommendations['premium'] else 'anthropic/claude-3-5-sonnet-20241022'}")
    console.print("\n  [dim]# Fast local development[/dim]")
    console.print(f"  slim apply --best-practices docs-website --use-ai {recommendations['local'][0] if recommendations['local'] else 'ollama/llama3.1:8b'}")

@models_app.command(name="setup")
def models_setup(
    provider: str = typer.Argument(..., help="Provider name (e.g., anthropic, groq)"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Show what would be executed without making changes")
):
    """Get setup instructions for a specific AI provider."""
    if state.dry_run or dry_run:
        if handle_dry_run_for_command("models setup", provider=provider, dry_run=True):
            return
    
    instructions = get_provider_setup_instructions(provider)
    console.print(instructions)

@models_app.command(name="validate")
def models_validate(
    model: str = typer.Argument(..., help="Model in provider/model format"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Show what would be executed without making changes")
):
    """Validate if an AI model is properly configured."""
    if state.dry_run or dry_run:
        if handle_dry_run_for_command("models validate", model=model, dry_run=True):
            return
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task(f"Validating model {model}...", total=None)
        
        progress.update(task, description="Checking model format...")
        progress.update(task, description="Verifying environment configuration...")
        progress.update(task, description="Testing model availability...")
        
        is_available, error_msg = check_model_availability(model)
        
        progress.update(task, description="Validation complete")
    
    if is_available:
        console.print(f"✅ Model [cyan]{model}[/cyan] is properly configured", style="green")
    else:
        console.print(f"❌ Model [cyan]{model}[/cyan] configuration error: {error_msg}", style="red")
        raise typer.Exit(1)

# Register the models subcommand app with the main app
app.add_typer(models_app, name="models")