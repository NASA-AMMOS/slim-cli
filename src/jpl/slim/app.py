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
    help="🛠️  SLIM CLI - Modernizing software through the automated infusion of best practices.",
    add_completion=False,
    no_args_is_help=True,
    invoke_without_command=True,
    rich_markup_mode="rich",
    epilog="""
  [bold]Examples:[/bold]

  [u]List available best practices:[/u]\n\n 
  slim list\n
  
  [u]Apply a README template by cloning and patching a repo in a temp folder:[/u]\n\n
  slim apply --best-practice-ids readme --repo-urls <YOUR_GITHUB_REPO_URL>\n
  
  [u]Apply a README template by cloning and patching a repo in a temp folder, then pushing to GitHub as a new branch:[/u]\n\n
  slim apply-deploy --best-practice-ids readme --repo-urls <YOUR_GITHUB_REPO_URL>\n
  
  [u]Apply Secrets Detection support (two assets):[/u]\n\n
  slim apply --best-practice-ids secrets-github --best-practice-ids secrets-precommit --repo-urls <YOUR_GITHUB_REPO_URL>\n

  [u]See available AI models:[/u]\n\n
  slim models list\n
  
  [u]Get model recommendations:[/u]\n\n
  slim models recommend\n

  [u]Create a docs website from scanning source code with local AI:[/u]\n\n
  slim apply --best-practice-ids docs-website --repo-urls <YOUR_GITHUB_REPO_URL> --output-dir /path/to/new/docs-website-folder-to-create --use-ai ollama/llama3.1\n
  
  [u]Apply to multiple repositories:[/u]\n\n
  slim apply --best-practice-ids readme --repo-urls https://github.com/org/repo1 --repo-urls https://github.com/org/repo2 --repo-urls https://github.com/org/repo3\n
  
  [u]Apply using a list of repositories from a file:[/u]\n\n
  slim apply --best-practice-ids governance-small --repo-urls-file repos.txt\n
  
  [u]Apply docs-website using a cloud AI model:[/u]\n\n
  slim apply --best-practice-ids docs-website --repo-urls <YOUR_GITHUB_REPO_URL> --output-dir /path/to/new/docs-website-folder-to-create --use-ai anthropic/claude-3-5-sonnet-20241022\n\n


[blue]Visit the SLIM website: https://github.com/NASA-AMMOS/slim[/blue]
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
