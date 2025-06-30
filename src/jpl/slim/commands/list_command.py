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

from jpl.slim.utils.io_utils import fetch_best_practices
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
    in a tree format organized by practice title, showing their 
    descriptions, guide URLs, and associated assets with aliases.
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
            
            progress.update(task, description=f"Found {len(practices)} best practices")

    # Create and configure the tree
    tree = Tree(
        "[bold]Available SLIM Best Practices (choose an asset)[/bold]",
        style="bold"
    )
    
    # Add practices to tree in alphabetical order by title
    logging.debug("Building tree structure for display")
    for practice in sorted(practices, key=lambda x: x.get('title', '')):
        title = practice.get('title', 'N/A')
        logging.debug(f"Adding practice: {title}")
        
        # Create the practice node with title
        practice_node = tree.add(f"[yellow]{title}[/yellow]")
        
        # Add description as a sub-node
        description = practice.get('description', 'N/A')
        description = textwrap.fill(description, width=80)
        practice_node.add(f"[yellow]Description:[/yellow] [white]{description}[/white]")
        
        # Add guide URL
        practice_uri = practice.get('uri', '')
        if practice_uri:
            guide_url = f"https://nasa-ammos.github.io{practice_uri}"
            practice_node.add(f"[yellow]Guide:[/yellow] [white]{guide_url}[/white]")
        
        # Add assets if available
        assets = practice.get('assets', [])
        if assets:
            assets_node = practice_node.add("[yellow]Assets:[/yellow]")
            for asset in assets:
                alias = asset.get('alias', '')
                name = asset.get('name', 'N/A')
                uri = asset.get('uri', '')
                
                if alias:
                    # Format: alias (cyan) - name (white)
                    asset_text = f"[cyan]{alias}[/cyan] - [white]{name}[/white]"
                    if uri:
                        asset_text += f" [white]({uri})[/white]"
                    assets_node.add(asset_text)
                else:
                    # No alias, just show name
                    asset_text = f"[white]{name}[/white]"
                    if uri:
                        asset_text += f" [white]({uri})[/white]"
                    assets_node.add(asset_text)

    logging.debug("Displaying practices tree")
    console.print(tree)
    console.print(f"\n[dim]Total practices: {len(practices)}[/dim]")
    logging.debug("List command completed successfully")
