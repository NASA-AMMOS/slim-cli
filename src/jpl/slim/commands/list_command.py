"""
List command module for the SLIM CLI.

This module contains the implementation of the 'list' subcommand,
which lists all available best practices from the SLIM registry.
"""

import logging
import textwrap
from rich.console import Console
from rich.table import Table

from jpl.slim.utils.io_utils import fetch_best_practices, create_slim_registry_dictionary
from jpl.slim.commands.common import SLIM_REGISTRY_URI

def setup_parser(subparsers):
    """
    Set up the parser for the 'list' command.
    
    Args:
        subparsers: Subparsers object from argparse
        
    Returns:
        The parser for the 'list' command
    """
    parser = subparsers.add_parser('list', help='Lists all available best practice from the SLIM')
    parser.set_defaults(func=handle_command)
    return parser

def handle_command(args):
    """
    Handle the 'list' command.
    
    Args:
        args: Arguments from argparse
    """
    logging.debug("Listing all best practices...")
    practices = fetch_best_practices(SLIM_REGISTRY_URI)

    if not practices:
        print("No practices found or failed to fetch practices.")
        return

    asset_mapping = create_slim_registry_dictionary(practices)

    console = Console()
    table = Table(show_header=True, header_style="bold magenta", show_lines=True)
    headers = ["Alias", "Title", "Description", "Asset"]
    for header in headers:
        table.add_column(header)

    for alias, info in asset_mapping.items():
        table.add_row(
            alias, 
            textwrap.fill(info['title'], width=30), 
            textwrap.fill(info['description'], width=50), 
            textwrap.fill(info['asset_name'], width=20)
        )

    console.print(table)
