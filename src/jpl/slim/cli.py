import argparse
import logging
import os
import sys
import tempfile
import urllib.parse
import uuid
try:
    import yaml
except ImportError:
    print("Error: The 'pyyaml' package is required but not installed.")
    print("Please install it using: pip install pyyaml")
    sys.exit(1)
try:
    import git
except ImportError:
    print("Error: The 'gitpython' package is required but not installed.")
    print("Please install it using: pip install gitpython")
    sys.exit(1)
try:
    import requests
except ImportError:
    print("Error: The 'requests' package is required but not installed.")
    print("Please install it using: pip install requests")
    sys.exit(1)
from typing import Optional, Dict, Any
import os
VERSION = open(os.path.join(os.path.dirname(__file__), 'VERSION.txt')).read().strip()

# Set up test mode detection
SLIM_TEST_MODE = os.environ.get('SLIM_TEST_MODE', 'False').lower() in ('true', '1', 't')

# Import command modules
from jpl.slim.commands.list_command import setup_parser as setup_list_parser
from jpl.slim.commands.apply_command import setup_parser as setup_apply_parser
from jpl.slim.commands.deploy_command import setup_parser as setup_deploy_parser
from jpl.slim.commands.apply_deploy_command import setup_parser as setup_apply_deploy_parser
from jpl.slim.commands.generate_tests_command import setup_parser as setup_generate_tests_parser
from jpl.slim.commands.common import setup_logging

# Import utility modules for backward compatibility
from jpl.slim.utils.io_utils import (
    fetch_best_practices,
    fetch_best_practices_from_file,
    create_slim_registry_dictionary,
    repo_file_to_list,
    fetch_relative_file_paths,
    download_and_place_file,
    read_file_content,
    fetch_readme,
    fetch_code_base
)
from jpl.slim.utils.git_utils import (
    generate_git_branch_name,
    is_open_source
)
from jpl.slim.utils.ai_utils import (
    generate_with_ai,
    construct_prompt,
    generate_content,
    generate_with_openai,
    generate_with_azure,
    generate_with_ollama
)

# Import command functions for backward compatibility
from jpl.slim.commands.list_command import handle_command as list_practices
from jpl.slim.commands.apply_command import apply_best_practices, apply_best_practice
from jpl.slim.commands.deploy_command import deploy_best_practices, deploy_best_practice
from jpl.slim.commands.apply_deploy_command import apply_and_deploy_best_practices, apply_and_deploy_best_practice
from jpl.slim.commands.generate_tests_command import handle_generate_tests

# Global parser that hands off parsing to respective, supported sub-commands
def create_parser() -> argparse.ArgumentParser:
    """
    Creates a global argument parser for the SLIM tool.

    This function sets up the basic command-line interface and defines the available sub-commands.
    It also configures the logging system based on user input.

    Returns:
        The global argument parser instance.
    """

    # Create a basic argument parser
    parser = argparse.ArgumentParser(description='This tool automates the application of best practices to git repositories.')

    # Add version option
    parser.add_argument('--version', action='version', version=VERSION)
    parser.add_argument('-d', '--dry-run', action='store_true', help='Generate a dry-run plan of activities to be performed')
    parser.add_argument(
        '-l', '--logging',
        required=False,
        default='INFO',  # default is a string; we'll convert it to logging.INFO below
        type=lambda s: getattr(logging, s.upper(), None),
        help='Set the logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL'
    )

    subparsers = parser.add_subparsers(dest='command', required=True)

    # Set up parsers for each command
    setup_list_parser(subparsers)
    setup_apply_parser(subparsers)
    setup_deploy_parser(subparsers)
    setup_apply_deploy_parser(subparsers)
    setup_generate_tests_parser(subparsers)

    return parser


def main():
    """
    Main entry point for the SLIM CLI tool. Parses command-line arguments,
    sets up logging, and executes the appropriate command function.
    """
    parser = create_parser()
    args = parser.parse_args()

    if args.logging is None:
        print("Invalid logging level provided. Choose from DEBUG, INFO, WARNING, ERROR, CRITICAL.")
        sys.exit(1)
    else:
        setup_logging(args.logging)

    if args.dry_run:
        logging.debug("Dry run activated")

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
