"""
Documentation generator best practice module.

This module contains the DocGenPractice class for applying and deploying
documentation generation best practice to repositories.
"""

import os
import logging
import tempfile
import shutil
import sys
import subprocess
from pathlib import Path
import traceback
from typing import Optional, Dict, Any, List
import uuid

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from jpl.slim.best_practices.standard import StandardPractice
from jpl.slim.best_practices.docs_website_impl.generator import SlimDocGenerator

# Check if we're in test mode
SLIM_TEST_MODE = os.environ.get('SLIM_TEST_MODE', 'False').lower() in ('true', '1', 't')


class DocsWebsiteBestPractice(StandardPractice):
    """
    Best practice for documentation generation.

    This class handles generating comprehensive documentation sites for
    software projects using the integrated SLIM docsite template and optional AI enhancement.
    """

    def __init__(self):
        """Initialize the documentation generation best practice."""
        super().__init__(
            best_practice_id="docs-website",
            uri="/Users/rverma/Desktop/test/yunks/slim-cli/example_sites/slim-docsite-template/",
            title="Documentation Generator",
            description="Generates comprehensive documentation sites for software projects using the SLIM docsite template and AI enhancement"
        )
        
    def apply(self, repo_path, use_ai=False, model=None, repo_url=None, 
              target_dir_to_clone_to=None, branch=None, no_prompt=False, **kwargs):
        """
        Apply the documentation generation best practice to a repository.
        
        Args:
            repo_path (str): Path to the repository
            use_ai (bool, optional): Whether to use AI assistance. Required for docs-website.
            model (str, optional): AI model to use. Required for docs-website.
            repo_url (str, optional): Repository URL to apply to. Defaults to None.
            target_dir_to_clone_to (str, optional): Directory to clone repository to. Defaults to None.
            branch (str, optional): Git branch to use. Defaults to None.
            no_prompt (bool, optional): Skip user confirmation prompts. Defaults to False.
            
        Returns:
            str: Repository path if successful, None otherwise
        """
        logging.debug(f"Applying best practice {self.best_practice_id}")
        
        # Early validation - docs-website requires AI
        if not use_ai or not model:
            logging.error("The docs-website best practice requires --use-ai flag with a model specified")
            print("❌ Error: docs-website requires AI assistance. Please use: --use-ai <model>")
            return None
        
        # Validate AI model configuration before proceeding
        from jpl.slim.utils.ai_utils import validate_model, generate_ai_content
        is_valid, error_message = validate_model(model)
        if not is_valid:
            logging.error(f"AI model validation failed: {error_message}")
            print(f"❌ Error: {error_message}")
            return None
        
        # Test AI connectivity with a simple request
        print("🔍 Testing AI model connectivity...")
        test_prompt = "Reply with only the word 'OK' to confirm you are working."
        test_response = generate_ai_content(test_prompt, model)
        if not test_response:
            logging.error(f"AI model connectivity test failed for {model}")
            print(f"❌ Error: Cannot connect to AI model '{model}'. Please check your API keys and network connection.")
            return None
        
        print(f"✅ AI model '{model}' is working correctly")
        
        # Extract additional parameters that might be passed via the command line
        template_only = kwargs.get('template_only', False)
        revise_site = kwargs.get('revise_site', False)
        output_dir = kwargs.get('output_dir')
        
        if not output_dir:
            logging.error("Output directory (--output-dir) is required for documentation generation")
            return None
        
        # Set up repository (clone if needed, create branch, etc.)
        git_repo, git_branch, actual_repo_path = self.setup_repository(
            repo_path=repo_path,
            repo_url=repo_url,
            target_dir_to_clone_to=target_dir_to_clone_to,
            branch=branch
        )
        
        if not git_repo:
            logging.error("Failed to set up repository")
            return None
        
        # Use the actual repository path from setup_repository
        repo_path = actual_repo_path
            
        # In test mode, simulate success without making actual changes
        if SLIM_TEST_MODE:
            logging.debug(f"TEST MODE: Simulating applying best practice {self.best_practice_id}")
            return repo_path
        
        # Use the integrated documentation generator
        try:
            # Create the SlimDocGenerator instance
            generator = SlimDocGenerator(
                target_repo_path=repo_path,
                output_dir=output_dir,
                template_repo=self.uri,
                use_ai=model if use_ai else None,
                config_file=None,
                verbose=logging.getLogger().getEffectiveLevel() <= logging.DEBUG,
                template_only=template_only,
                revise_site=revise_site
            )
            
            # Generate documentation with progress updates
            print("🔄 Starting documentation generation...")
            
            # Show simple spinner during AI generation
            console = Console()
            with Progress(
                SpinnerColumn(),
                TextColumn(f"AI generation in progress ({model})"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("", total=None)
                success = generator.generate(progress_task=None, progress=None)
            
            if success:
                print("✅ Documentation generation completed")
            
            if success:
                if template_only:
                    logging.debug(f"Template structure successfully generated at {output_dir}")
                    print(f"✅ Successfully applied best practice '{self.best_practice_id}' - documentation template at {output_dir}")
                else:
                    logging.debug(f"Documentation successfully generated at {output_dir}")
                    print(f"✅ Successfully applied best practice '{self.best_practice_id}' - documentation generated at {output_dir}")
                print(f"   📁 Source repository: {repo_path}")
                return repo_path
            else:
                logging.error("Documentation generation failed")
                print(f"❌ Failed to generate documentation for best practice '{self.best_practice_id}'")
                return None
                
        except Exception as e:
            logging.error(f"Error generating documentation: {str(e)}")
            logging.debug(traceback.format_exc())
            print(f"❌ Error generating documentation: {str(e)}")
            return None
    
    def deploy(self, repo_path, remote=None, commit_message=None):
        """
        Deploy changes made by applying the documentation generation best practice.
        
        For documentation generation, this is a no-op as the documentation is
        generated in a specified output directory and does not modify the source repository.
        
        Args:
            repo_path (str): Path to the repository
            remote (str, optional): Remote repository to push changes to. Defaults to None.
            commit_message (str, optional): Commit message for the changes. Defaults to None.
            
        Returns:
            bool: True (always returns True as no deployment is needed)
        """
        logging.debug(f"No deployment needed for {self.best_practice_id}. Documentation was generated in the specified output directory.")
        return True