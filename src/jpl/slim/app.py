"""
Core Typer app instance and global state for SLIM CLI.

This module contains the main Typer app instance and global state management
to avoid circular imports.
"""

import logging
import typer
from rich.console import Console

# Create the main Typer app
app = typer.Typer(
    name="slim",
    help="🛠️ SLIM CLI - Automates the application of best practices to git repositories.",
    add_completion=True,
    no_args_is_help=True,
    invoke_without_command=True,
    rich_markup_mode="rich",
    epilog="""
[bold]Examples:[/bold]
  # List available best practices
  slim list

  # Apply documentation generation with AI
  slim apply --best-practice-ids docs-website --repo-dir ./my-project --output-dir ./docs --use-ai openai/gpt-4o-mini

  # See available AI models
  slim models list

  # Get model recommendations
  slim models recommend --task documentation --tier balanced

For more information: https://github.com/NASA-AMMOS/slim
    """
)

# Global state for CLI-level options
class State:
    def __init__(self):
        self.dry_run = False
        self.logging_level = logging.INFO

state = State()

def handle_dry_run_for_command(command_name: str, **kwargs) -> bool:
    """
    Handle dry-run mode at the command level.
    
    Args:
        command_name: Name of the command being executed
        **kwargs: Command-specific arguments (should include dry_run=True if this is a dry run)
        
    Returns:
        True if this is a dry-run and execution should stop
    """
    # Check if dry_run is explicitly passed or if global state indicates dry run
    is_dry_run = kwargs.get('dry_run', False) or state.dry_run
    
    if is_dry_run:
        console = Console()
        console.print("🔍 [bold cyan]DRY RUN MODE:[/bold cyan] Showing what would be executed")
        console.print(f"Command: [bold]{command_name}[/bold]")
        
        # Show command-specific arguments (exclude the dry_run flag itself)
        for key, value in kwargs.items():
            if key == 'dry_run':
                continue
            if value is not None:
                if isinstance(value, list):
                    console.print(f"  --{key.replace('_', '-')}: {', '.join(str(v) for v in value)}")
                elif isinstance(value, bool):
                    if value:  # Only show True flags
                        console.print(f"  --{key.replace('_', '-')}")
                else:
                    console.print(f"  --{key.replace('_', '-')}: {value}")
        
        console.print("✅ [green]Dry run complete. No actions were taken.[/green]")
        return True
    
    return False