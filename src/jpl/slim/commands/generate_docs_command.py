"""
Generate-Docs command module for the SLIM CLI.

This module contains the implementation of the 'generate-docs' subcommand,
which generates Docusaurus documentation from repository content.
"""

import logging
import os
import yaml

def setup_parser(subparsers):
    """
    Set up the parser for the 'generate-docs' command.
    
    Args:
        subparsers: Subparsers object from argparse
        
    Returns:
        The parser for the 'generate-docs' command
    """
    from jpl.slim.commands.common import SUPPORTED_MODELS, get_ai_model_pairs
    
    parser = subparsers.add_parser('generate-docs', 
        help='Generates Docusaurus documentation from repository content')
    parser.add_argument('--repo-dir', required=True, 
        help='Repository directory location on local machine')
    parser.add_argument('--output-dir', required=True,
        help='Directory where documentation should be generated')
    parser.add_argument('--config', required=False,
        help='Optional YAML configuration file for documentation generation')
    parser.add_argument('--use-ai', metavar='MODEL',
        help=f"Enhance documentation using AI model. Supported models: {get_ai_model_pairs(SUPPORTED_MODELS)}")
    parser.set_defaults(func=handle_command)
    return parser

def handle_command(args):
    """
    Handle the 'generate-docs' command.
    
    Args:
        args: Arguments from argparse
        
    Returns:
        bool: True if documentation generation was successful, False otherwise
    """
    return handle_generate_docs(args)

def handle_generate_docs(args):
    """
    Handle the generate-docs command.
    
    Args:
        args: Arguments from argparse
        
    Returns:
        bool: True if documentation generation was successful, False otherwise
    """
    logging.debug(f"Generating documentation from repository: {args.repo_dir}")
    
    # Validate repository directory
    if not os.path.isdir(args.repo_dir):
        logging.error(f"Repository directory does not exist: {args.repo_dir}")
        return False
        
    # Load configuration if provided
    config = None
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            logging.warning(f"Failed to load configuration file: {str(e)}")
    
    # Log AI usage
    if args.use_ai:
        logging.info(f"AI enhancement enabled using model: {args.use_ai}")
    
    # Initialize and run documentation generator
    try:
        from jpl.slim.docgen import DocusaurusGenerator
        generator = DocusaurusGenerator(
            repo_path=args.repo_dir,
            output_dir=args.output_dir,
            config=config,
            use_ai=args.use_ai
        )
        
        if generator.generate():
            logging.info(f"Successfully generated documentation in {args.output_dir}")
            
            # Print next steps
            print("\nDocumentation generated successfully!")
            print("\nNext steps:")
            print("1. Install Docusaurus if you haven't already:")
            print("   npx create-docusaurus@latest my-docs classic")
            print("\n2. Copy the generated files to your Docusaurus docs directory:")
            print(f"   cp -r {args.output_dir}/*.md my-docs/docs/")
            print(f"   cp -r {args.output_dir}/docusaurus.config.js my-docs/")
            print(f"   cp -r {args.output_dir}/sidebars.js my-docs/")
            print(f"   cp -r {args.output_dir}/static/* my-docs/static/")
            print("\n3. Start the Docusaurus development server:")
            print("   cd my-docs")
            print("   npm start")
            
            return True
    except Exception as e:
        logging.error(f"Documentation generation failed: {str(e)}")
        return False
