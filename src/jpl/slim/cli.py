import argparse
import logging
import os
import sys
import tempfile
import urllib.parse
import uuid
from typing import Any, Dict
from jpl.slim.commands.models_command import setup_parser as setup_models_parser

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
    generate_with_litellm,
    get_model_recommendations,
    validate_model_config,
    # Legacy functions for backward compatibility
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


def extract_command_args(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Extract only command-specific arguments, filtering out CLI-level arguments.
    
    Args:
        args: Parsed arguments from argparse
        
    Returns:
        Dictionary containing only command-specific arguments
    """
    command_args = {}
    
    for key, value in vars(args).items():
        if key not in CLI_ONLY_ARGS:
            command_args[key] = value
    
    return command_args


def handle_dry_run(args: argparse.Namespace) -> bool:
    """
    Handle dry-run mode at the CLI level.
    
    Args:
        args: Parsed arguments
        
    Returns:
        True if this is a dry-run and execution should stop
    """
    if args.dry_run:
        logging.info("🔍 DRY RUN MODE: Showing what would be executed")
        logging.info(f"Command: {args.command}")
        
        # Show command-specific arguments
        command_args = extract_command_args(args)
        for key, value in command_args.items():
            if value is not None:
                if isinstance(value, list):
                    logging.info(f"  --{key.replace('_', '-')}: {', '.join(str(v) for v in value)}")
                elif isinstance(value, bool):
                    if value:  # Only show True flags
                        logging.info(f"  --{key.replace('_', '-')}")
                else:
                    logging.info(f"  --{key.replace('_', '-')}: {value}")
        
        logging.info("✅ Dry run complete. No actions were taken.")
        return True
    
    return False


def validate_global_arguments(args: argparse.Namespace) -> None:
    """
    Validate CLI-level arguments before command execution.
    
    Args:
        args: Parsed arguments
    """
    # Validate logging level
    if args.logging is None:
        print("❌ Invalid logging level provided. Choose from DEBUG, INFO, WARNING, ERROR, CRITICAL.")
        sys.exit(1)


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
    is_valid, error_msg = validate_model_config(model)
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


def validate_ai_arguments(args):
    """
    Validate AI-related arguments across all commands.
    
    Args:
        args: Parsed command line arguments
    """
    # Check if any AI model is specified
    ai_model = getattr(args, 'use_ai', None)
    
    if ai_model:
        if not validate_ai_model(ai_model):
            print("\nFor help with AI models, run:")
            print("  slim models list")
            print("  slim models setup <provider>")
            sys.exit(1)
        
        # Show helpful message for first-time AI users
        provider = ai_model.split('/')[0]
        if provider not in {'openai', 'azure', 'ollama'}:  # Non-legacy providers
            print(f"🤖 Using AI model: {ai_model}")
            if not LITELLM_AVAILABLE:
                print("⚠️  Warning: This provider requires LiteLLM for optimal performance")
            print()


def handle_special_cases(args):
    """
    Handle special cases and provide helpful guidance.
    
    Args:
        args: Parsed command line arguments
    """
    # If user tries to use AI without specifying a model, show help
    if hasattr(args, 'use_ai') and args.use_ai == '':
        print("❌ Error: --use-ai requires a model specification")
        print()
        show_model_help()
        sys.exit(1)
    
    # If user is applying docs-website without output-dir
    if (hasattr(args, 'best_practice_ids') and 
        args.best_practice_ids and 
        'docs-website' in args.best_practice_ids and 
        not getattr(args, 'output_dir', None) and
        not getattr(args, 'template_only', False)):
        print("❌ Error: --output-dir is required for documentation generation")
        print()
        print("Example:")
        print("  slim apply --best-practice-ids docs-website --repo-dir ./my-project --output-dir ./docs")
        sys.exit(1)


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
    parser = argparse.ArgumentParser(
        description='This tool automates the application of best practices to git repositories.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
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

    # CLI-level arguments (handled at CLI level only)
    parser.add_argument('--version', action='version', version=f'SLIM CLI v{VERSION}')
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
    setup_models_parser(subparsers)
    
    return parser


def main():
    """
    Main entry point for the SLIM CLI tool. Parses command-line arguments,
    sets up logging, and executes the appropriate command function.
    """
    # Print startup banner for interactive use
    if not SLIM_TEST_MODE and len(sys.argv) > 1:
        print_startup_banner()
    
    parser = create_parser()
    args = parser.parse_args()

    # Handle CLI-level concerns first
    validate_global_arguments(args)
    setup_logging(args.logging)
    
    # Check LiteLLM availability if not in test mode
    if not SLIM_TEST_MODE:
        check_litellm_availability()

    # Validate AI arguments
    validate_ai_arguments(args)
    
    # Handle special cases
    handle_special_cases(args)

    # Handle dry-run mode at CLI level
    if handle_dry_run(args):
        return

    # Execute command with filtered arguments
    if hasattr(args, 'func'):
        try:
            # Create a new namespace with only command-specific arguments
            command_args = argparse.Namespace(**extract_command_args(args))
            args.func(command_args)
        except KeyboardInterrupt:
            print("\n⚠️  Operation cancelled by user")
            sys.exit(1)
        except Exception as e:
            if args.logging == logging.DEBUG:
                # In debug mode, show full traceback
                raise
            else:
                # In normal mode, show clean error message
                print(f"❌ Error: {str(e)}")
                print("\nFor detailed error information, run with --logging DEBUG")
                sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()