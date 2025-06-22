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

from jpl.slim.commands.common import (
    SUPPORTED_MODELS, MODEL_RECOMMENDATIONS,
    get_recommended_models, check_model_availability,
    get_provider_setup_instructions, print_model_recommendations,
    get_ai_model_pairs
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
        print_model_recommendations()

@models_app.command(name="list")
def models_list(
    provider: Optional[str] = typer.Option(None, help="Filter by provider"),
    tier: Optional[Tier] = typer.Option(None, help="Filter by quality tier"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Show what would be executed without making changes")
):
    """List all available AI models."""
    if state.dry_run or dry_run:
        if handle_dry_run_for_command("models list", provider=provider, tier=tier, dry_run=True):
            return
    
    models = get_ai_model_pairs()
    
    if provider:
        models = [m for m in models if m.startswith(f"{provider}/")]
    
    if tier:
        # Filter by tier - this would need to be implemented
        # For now, we'll show all models with tier info
        pass
    
    console.print(f"\n[bold]Found {len(models)} models:[/bold]")
    for model in sorted(models):
        console.print(f"  • [cyan]{model}[/cyan]")

@models_app.command(name="recommend")
def models_recommend(
    task: Task = typer.Option(Task.documentation, "--task", help="Task type"),
    tier: Tier = typer.Option(Tier.balanced, "--tier", help="Quality/cost tier"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Show what would be executed without making changes")
):
    """Get AI model recommendations for specific tasks."""
    if state.dry_run or dry_run:
        if handle_dry_run_for_command("models recommend", task=task.value, tier=tier.value, dry_run=True):
            return
    
    recommended = get_recommended_models(task.value, tier.value)
    console.print(f"\n[bold]Recommended {tier.value} models for {task.value}:[/bold]")
    for model in recommended:
        console.print(f"  • [cyan]{model}[/cyan]")

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
    
    is_available, error_msg = check_model_availability(model)
    if is_available:
        console.print(f"✅ Model [cyan]{model}[/cyan] is properly configured", style="green")
    else:
        console.print(f"❌ Model [cyan]{model}[/cyan] configuration error: {error_msg}", style="red")

# Register the models subcommand app with the main app
app.add_typer(models_app, name="models")