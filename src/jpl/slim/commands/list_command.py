"""
List command module for the SLIM CLI.

This module contains the implementation of the 'list' subcommand,
which lists all available best practices from the SLIM registry.
"""

import logging
import textwrap
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from jpl.slim.utils.io_utils import fetch_best_practices, create_slim_registry_dictionary
from jpl.slim.commands.common import SLIM_REGISTRY_URI
from jpl.slim.app import app, state, handle_dry_run_for_command

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
    in a formatted table showing their aliases, titles, descriptions,
    and associated assets.
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

    # Create and configure the table
    table = Table(
        show_header=True, 
        header_style="bold magenta", 
        show_lines=True,
        title="[bold]Available SLIM Best Practices[/bold]"
    )
    
    # Add columns with specific widths
    table.add_column("Alias", style="cyan", no_wrap=True)
    table.add_column("Title", width=30)
    table.add_column("Description", width=50)
    table.add_column("Asset", width=20)

    # Add rows
    logging.debug("Building table rows for display")
    for alias, info in asset_mapping.items():
        logging.debug(f"Adding practice: {alias} - {info['title']}")
        table.add_row(
            alias, 
            textwrap.fill(info['title'], width=30), 
            textwrap.fill(info['description'], width=50), 
            textwrap.fill(info['asset_name'], width=20)
        )

    logging.debug("Displaying practices table")
    console.print(table)
    console.print(f"\n[dim]Total practices: {len(asset_mapping)}[/dim]")
    logging.debug("List command completed successfully")
