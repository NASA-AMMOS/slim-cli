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
    )
):
    """
    Lists all available best practices from the SLIM registry.
    
    This command fetches and displays all registered best practices
    in a formatted table showing their aliases, titles, descriptions,
    and associated assets.
    """
    # Handle dry-run mode
    if handle_dry_run_for_command("list", dry_run=dry_run or state.dry_run):
        return
    
    logging.debug("Listing all best practices...")
    
    # Fetch practices with progress indicator
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        progress.add_task("Fetching best practices from registry...", total=None)
        practices = fetch_best_practices(SLIM_REGISTRY_URI)

    if not practices:
        console.print("[red]No practices found or failed to fetch practices.[/red]")
        raise typer.Exit(1)

    asset_mapping = create_slim_registry_dictionary(practices)

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
    for alias, info in asset_mapping.items():
        table.add_row(
            alias, 
            textwrap.fill(info['title'], width=30), 
            textwrap.fill(info['description'], width=50), 
            textwrap.fill(info['asset_name'], width=20)
        )

    console.print(table)
    console.print(f"\n[dim]Total practices: {len(asset_mapping)}[/dim]")
