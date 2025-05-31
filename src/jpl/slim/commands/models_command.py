"""
Models command module for the SLIM CLI.

This module contains the implementation of the 'models' subcommand,
which helps users discover and configure AI models.
"""

import logging
from jpl.slim.commands.common import (
    SUPPORTED_MODELS, MODEL_RECOMMENDATIONS,
    get_recommended_models, check_model_availability,
    get_provider_setup_instructions, print_model_recommendations,
    get_ai_model_pairs
)

def setup_parser(subparsers):
    """
    Set up the parser for the 'models' command.
    
    Args:
        subparsers: Subparsers object from argparse
        
    Returns:
        The parser for the 'models' command
    """
    parser = subparsers.add_parser('models', help='Discover and configure AI models')
    subcommands = parser.add_subparsers(dest='models_action', help='Models subcommands')
    
    # List models
    list_parser = subcommands.add_parser('list', help='List available models')
    list_parser.add_argument('--provider', help='Filter by provider')
    list_parser.add_argument('--tier', choices=['premium', 'balanced', 'fast', 'local'], 
                           help='Filter by quality tier')
    
    # Recommend models
    recommend_parser = subcommands.add_parser('recommend', help='Get model recommendations')
    recommend_parser.add_argument('--task', choices=['documentation', 'code_generation'],
                                default='documentation', help='Task type')
    recommend_parser.add_argument('--tier', choices=['premium', 'balanced', 'fast', 'local'],
                                default='balanced', help='Quality/cost tier')
    
    # Setup instructions
    setup_parser = subcommands.add_parser('setup', help='Get setup instructions for a provider')
    setup_parser.add_argument('provider', help='Provider name (e.g., anthropic, groq)')
    
    # Validate model
    validate_parser = subcommands.add_parser('validate', help='Validate model configuration')
    validate_parser.add_argument('model', help='Model in provider/model format')
    
    parser.set_defaults(func=handle_command)
    return parser

def handle_command(args):
    """
    Handle the 'models' command.
    
    Args:
        args: Arguments from argparse
    """
    if args.models_action == 'list':
        handle_list(args)
    elif args.models_action == 'recommend':
        handle_recommend(args)
    elif args.models_action == 'setup':
        handle_setup(args)
    elif args.models_action == 'validate':
        handle_validate(args)
    else:
        print_model_recommendations()

def handle_list(args):
    """Handle the list subcommand."""
    models = get_ai_model_pairs()
    
    if args.provider:
        models = [m for m in models if m.startswith(f"{args.provider}/")]
    
    if args.tier:
        # Filter by tier - this would need to be implemented
        pass
    
    print(f"\nFound {len(models)} models:")
    for model in sorted(models):
        print(f"  • {model}")

def handle_recommend(args):
    """Handle the recommend subcommand."""
    recommended = get_recommended_models(args.task, args.tier)
    print(f"\nRecommended {args.tier} models for {args.task}:")
    for model in recommended:
        print(f"  • {model}")

def handle_setup(args):
    """Handle the setup subcommand."""
    instructions = get_provider_setup_instructions(args.provider)
    print(instructions)

def handle_validate(args):
    """Handle the validate subcommand."""
    is_available, error_msg = check_model_availability(args.model)
    if is_available:
        print(f"✅ Model {args.model} is properly configured")
    else:
        print(f"❌ Model {args.model} configuration error: {error_msg}")