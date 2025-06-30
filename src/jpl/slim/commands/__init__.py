"""
Command modules for the SLIM CLI.

This package contains modules for each subcommand of the SLIM CLI.
Each module defines a setup_parser function to configure the command's
arguments and a handle_command function to execute the command.
"""

from jpl.slim.commands import (
    list_command,
    apply_command,
    deploy_command,
    apply_deploy_command,
    # generate_tests_command  # Temporarily disabled - needs work
)

__all__ = [
    "list_command",
    "apply_command",
    "deploy_command",
    "apply_deploy_command",
    # "generate_tests_command"  # Temporarily disabled - needs work
]
