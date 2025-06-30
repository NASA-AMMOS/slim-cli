"""
List command module for the SLIM CLI.

This module contains the implementation of the 'list' subcommand,
which lists all available best practices from the SLIM registry.
"""

import logging
import textwrap
import typer
from rich.console import Console
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn

from jpl.slim.utils.io_utils import fetch_best_practices, create_slim_registry_dictionary
from jpl.slim.commands.common import SLIM_REGISTRY_URI
from jpl.slim.app import app, state, handle_dry_run_for_command
from jpl.slim.utils.cli_utils import managed_progress

console = Console()

@app.command()
def list(
    dry_run: bool = typer.Option(
        False,
        "--dry-run", "-d",
        help="Show what would be executed without making changes"
    ),
    logging_level: str = typer.Option(
        None,
        "--logging", "-l",
        help="Set the logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
):
    """
    Lists all available best practices from the SLIM registry.
    
    This command fetches and displays all registered best practices
    in a tree format organized by category, showing their aliases, 
    titles, descriptions, and associated assets.
    """
    # Configure logging
    from jpl.slim.commands.common import configure_logging
    configure_logging(logging_level, state)
    
    # Handle dry-run mode
    if handle_dry_run_for_command("list", dry_run=dry_run or state.dry_run):
        return
    
    logging.debug("Starting list command execution")
    logging.debug(f"Registry URI: {SLIM_REGISTRY_URI}")
    
    # Fetch practices with enhanced progress indicator
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        with managed_progress(progress):
            task = progress.add_task("Connecting to SLIM registry...", total=None)
            
            progress.update(task, description="Fetching best practices from registry...")
            logging.debug("Calling fetch_best_practices()")
            practices = fetch_best_practices(SLIM_REGISTRY_URI)

            if not practices:
                logging.error("No practices found or failed to fetch practices")
                console.print("[red]No practices found or failed to fetch practices.[/red]")
                raise typer.Exit(1)

            logging.debug(f"Successfully fetched {len(practices)} practices from registry")
            progress.update(task, description="Processing registry data...")
            
            logging.debug("Creating SLIM registry dictionary from practices")

            asset_mapping = create_slim_registry_dictionary(practices)
            logging.debug(f"Created mapping for {len(asset_mapping)} practices")
            
            progress.update(task, description=f"Found {len(asset_mapping)} best practices")

    # Create and configure the tree
    tree = Tree(
        "[bold]Available SLIM Best Practices[/bold]",
        style="bold magenta"
    )
    
    # Add practices to tree in alphabetical order (no categorization)
    logging.debug("Building tree structure for display")
    for alias, info in sorted(asset_mapping.items(), key=lambda x: x[0]):
        logging.debug(f"Adding practice: {alias} - {info['title']}")
        
        # Create the practice node with alias
        practice_node = tree.add(f"[cyan]{alias}[/cyan]")
        
        # Add title as a sub-node
        practice_node.add(f"[bold yellow]Title:[/bold yellow] [white]{info['title']}[/white]")
        
        # Add description, wrapped for readability
        description = textwrap.fill(info['description'], width=80)
        practice_node.add(f"[bold yellow]Description:[/bold yellow] [white]{description}[/white]")
        
        # Add asset information
        practice_node.add(f"[bold yellow]Asset:[/bold yellow] [white]{info['asset_name']}[/white]")

    logging.debug("Displaying practices tree")
    console.print(tree)
    console.print(f"\n[dim]Total practices: {len(asset_mapping)}[/dim]")
    logging.debug("List command completed successfully")
