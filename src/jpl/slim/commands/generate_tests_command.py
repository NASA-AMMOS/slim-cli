"""
Generate-Tests command module for the SLIM CLI.

This module contains the implementation of the 'generate-tests' subcommand,
which generates unit test files for Python code in the repository.
"""

import logging
import os

def setup_parser(subparsers):
    """
    Set up the parser for the 'generate-tests' command.
    
    Args:
        subparsers: Subparsers object from argparse
        
    Returns:
        The parser for the 'generate-tests' command
    """
    from jpl.slim.commands.common import SUPPORTED_MODELS, get_ai_model_pairs
    
    parser = subparsers.add_parser('generate-tests',
        help='Generates unit test files for Python code in the repository')
    parser.add_argument('--repo-dir', required=True,
        help='Repository directory location on local machine')
    parser.add_argument('--output-dir', required=True,
        help='Directory where test files should be generated')
    parser.add_argument('--use-ai', metavar='MODEL',
        help=f"Generate tests using AI model. Supported models: {get_ai_model_pairs(SUPPORTED_MODELS)}")
    parser.set_defaults(func=handle_command)
    return parser

def handle_command(args):
    """
    Handle the 'generate-tests' command.
    
    Args:
        args: Arguments from argparse
        
    Returns:
        bool: True if test generation was successful, False otherwise
    """
    return handle_generate_tests(args)

def handle_generate_tests(args):
    """
    Handle the generate-tests command.
    
    Args:
        args: Arguments from argparse
        
    Returns:
        bool: True if test generation was successful, False otherwise
    """
    logging.debug(f"Generating tests for repository: {args.repo_dir}")
    
    # Validate repository directory
    if not os.path.isdir(args.repo_dir):
        logging.error(f"Repository directory does not exist: {args.repo_dir}")
        return False
        
    # Initialize and run test generator
    try:
        from jpl.slim.testgen import TestGenerator

        generator = TestGenerator(
            repo_path=args.repo_dir,
            output_dir=args.output_dir,
            model=args.use_ai
        )
        
        if generator.generate_tests():
            logging.info(f"Successfully generated tests in {args.output_dir}")
            
            # Print next steps
            print("\nTest files generated successfully!")
            print("\nNext steps:")
            print("1. Install pytest if you haven't already:")
            print("   pip install pytest")
            print("\n2. Review the generated tests and modify as needed")
            print("\n3. Run the tests:")
            print("   python -m pytest")
            
            return True
        else:
            logging.error("Test generation failed")
            return False
            
    except Exception as e:
        logging.error(f"Test generation failed: {str(e)}")
        return False
