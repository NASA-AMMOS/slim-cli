import logging
import os
import sys
import tempfile
import urllib.parse
import uuid
from typing import Any, Dict, Optional
import typer
from rich.console import Console

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

# Try to import LiteLLM with graceful fallback
try:
    import litellm
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    logging.warning("LiteLLM not available. Install with: pip install litellm")

VERSION = open(os.path.join(os.path.dirname(__file__), 'VERSION.txt')).read().strip()

# Set up test mode detection
SLIM_TEST_MODE = os.environ.get('SLIM_TEST_MODE', 'False').lower() in ('true', '1', 't')

# CLI-level arguments that should never be passed to commands
CLI_ONLY_ARGS = {
    'version', 'dry_run', 'logging', 'command', 'func'
}

# Import command modules
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
    generate_git_branch_name
)
from jpl.slim.utils.ai_utils import (
    generate_with_ai,
    construct_prompt,
    generate_ai_content,
    get_model_recommendations,
    validate_model
)

# Import command functions for backward compatibility (keeping only what's needed)
from jpl.slim.commands.apply_command import apply_best_practices, apply_best_practice
from jpl.slim.commands.deploy_command import deploy_best_practices, deploy_best_practice
from jpl.slim.commands.apply_deploy_command import apply_and_deploy_best_practices, apply_and_deploy_best_practice
from jpl.slim.commands.generate_tests_command import handle_generate_tests




def check_litellm_availability():
    """Check if LiteLLM is available and warn if not."""
    if not LITELLM_AVAILABLE:
        print("⚠️  Warning: LiteLLM is not installed. Some AI model providers may not be available.")
        print("   For full AI model support, install with: pip install litellm")
        print()


def validate_ai_model(model: str) -> bool:
    """
    Validate AI model format and availability.
    
    Args:
        model: Model string in format "provider/model"
        
    Returns:
        bool: True if model is valid and available
    """
    if not model:
        return True  # No model specified is valid
    
    # Check model format
    is_valid, error_msg = validate_model(model)
    if not is_valid:
        print(f"❌ Error: {error_msg}")
        return False
    
    # Check LiteLLM availability for non-legacy providers
    provider = model.split('/')[0]
    legacy_providers = {'openai', 'azure', 'ollama'}
    
    if provider not in legacy_providers and not LITELLM_AVAILABLE:
        print(f"❌ Error: Provider '{provider}' requires LiteLLM. Install with: pip install litellm")
        return False
    
    return True


def show_model_help():
    """Show helpful information about available AI models."""
    print("\n🤖 AI Model Usage Examples:")
    print()
    
    print("Premium Quality (Recommended for Production):")
    print("  slim apply --best-practice-ids docs-website --use-ai anthropic/claude-3-5-sonnet-20241022 [...]")
    print("  slim apply --best-practice-ids docs-website --use-ai openai/gpt-4o [...]")
    print()
    
    print("Balanced Quality/Cost:")
    print("  slim apply --best-practice-ids docs-website --use-ai openai/gpt-4o-mini [...]")
    print("  slim apply --best-practice-ids docs-website --use-ai cohere/command-r [...]")
    print()
    
    print("Fast & Affordable:")
    print("  slim apply --best-practice-ids docs-website --use-ai groq/llama-3.1-70b-versatile [...]")
    print("  slim apply --best-practice-ids docs-website --use-ai together/meta-llama/Llama-3-8b-chat-hf [...]")
    print()
    
    print("Local/Offline:")
    print("  slim apply --best-practice-ids docs-website --use-ai ollama/llama3.1 [...]")
    print("  slim apply --best-practice-ids docs-website --use-ai vllm/meta-llama/Llama-3-8b-chat-hf [...]")
    print()
    
    print("For more models and setup instructions:")
    print("  slim models list")
    print("  slim models recommend --task documentation")
    print("  slim models setup <provider>")
    print()


def print_startup_banner():
    """Print a helpful startup banner with version and AI info."""
    print(f"🛠️  SLIM CLI v{VERSION}")
    
    if LITELLM_AVAILABLE:
        print("✅ LiteLLM integration enabled - 100+ AI models available")
    else:
        print("⚠️  LiteLLM not installed - limited AI model support")
    
    print("   Use 'slim models list' to see available AI models")
    print()




# Import app and state from the separate module to avoid circular imports
from jpl.slim.app import app, state

@app.callback()
def main_callback(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Show version and exit"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Generate a dry-run plan of activities to be performed"),
    logging_level: str = typer.Option("INFO", "--logging", "-l", help="Set the logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL")
):
    """
    SLIM CLI - Software Lifecycle Improvement & Modernization
    
    This tool automates the application of best practices to git repositories.
    """
    if version:
        console = Console()
        console.print(f"SLIM CLI v{VERSION}")
        raise typer.Exit()
    
    # Convert string to logging level
    log_level = getattr(logging, logging_level.upper(), None)
    if log_level is None:
        console = Console()
        console.print("❌ Invalid logging level provided. Choose from DEBUG, INFO, WARNING, ERROR, CRITICAL.", style="red")
        raise typer.Exit(1)
    
    # Store global options in state
    state.dry_run = dry_run
    state.logging_level = log_level
    
    # Set up logging
    setup_logging(log_level)
    
    # Print startup banner for interactive use (only if a command is being run)
    if not SLIM_TEST_MODE and len(sys.argv) > 1 and ctx.invoked_subcommand is not None:
        print_startup_banner()
    
    # Check LiteLLM availability if not in test mode
    if not SLIM_TEST_MODE and ctx.invoked_subcommand is not None:
        check_litellm_availability()


# Import and register commands after app is created
# We do this at module level to allow commands to access the state
from jpl.slim.commands import list_command
from jpl.slim.commands import models_command
from jpl.slim.commands import apply_command  
from jpl.slim.commands import deploy_command
from jpl.slim.commands import apply_deploy_command
from jpl.slim.commands import generate_tests_command


def main():
    """
    Main entry point for the SLIM CLI tool.
    """
    try:
        app()
    except KeyboardInterrupt:
        console = Console()
        console.print("\n⚠️  Operation cancelled by user", style="yellow")
        sys.exit(1)


if __name__ == "__main__":
    main()