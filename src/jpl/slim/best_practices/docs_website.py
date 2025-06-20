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

from jpl.slim.best_practices.base import BestPractice
from jpl.slim.best_practices.docs_website_impl.generator import SlimDocGenerator

# Check if we're in test mode
SLIM_TEST_MODE = os.environ.get('SLIM_TEST_MODE', 'False').lower() in ('true', '1', 't')


class DocsWebsiteBestPractice(BestPractice):
    """
    Best practice for documentation generation.

    This class handles generating comprehensive documentation sites for
    software projects using the integrated SLIM docsite template and optional AI enhancement.
    """

    def __init__(self):
        """Initialize the documentation generation best practice."""
        super().__init__(
            best_practice_id="docs-website",
            uri="https://github.com/NASA-AMMOS/slim-docsite-template.git",
            title="Documentation Generator",
            description="Generates comprehensive documentation sites for software projects using the SLIM docsite template and AI enhancement"
        )
        
    def apply(self, repo_path, use_ai=False, model=None, repo_url=None, 
              target_dir_to_clone_to=None, branch=None, no_prompt=False, **kwargs):
        """
        Apply the documentation generation best practice to a repository.
        
        Args:
            repo_path (str): Path to the repository
            use_ai (bool, optional): Whether to use AI assistance. Defaults to False.
            model (str, optional): AI model to use if use_ai is True. Defaults to None.
            repo_url (str, optional): Repository URL to apply to. Defaults to None.
            target_dir_to_clone_to (str, optional): Directory to clone repository to. Defaults to None.
            branch (str, optional): Git branch to use. Defaults to None.
            no_prompt (bool, optional): Skip user confirmation prompts. Defaults to False.
            
        Returns:
            str: Repository path if successful, None otherwise
        """
        logging.debug(f"Applying best practice {self.best_practice_id}")
        
        # Extract additional parameters that might be passed via the command line
        template_only = kwargs.get('template_only', False)
        revise_site = kwargs.get('revise_site', False)
        output_dir = kwargs.get('output_dir')
        
        if not output_dir:
            logging.error("Output directory (--output-dir) is required for documentation generation")
            return None
            
        # In test mode, simulate success without making actual changes
        if SLIM_TEST_MODE:
            logging.info(f"TEST MODE: Simulating applying best practice {self.best_practice_id}")
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
            
            # Generate documentation
            success = generator.generate()
            
            if success:
                if template_only:
                    logging.info(f"Template structure successfully generated at {output_dir}")
                    print(f"✅ Successfully generated documentation template at {output_dir}")
                else:
                    logging.info(f"Documentation successfully generated at {output_dir}")
                    print(f"✅ Successfully generated documentation at {output_dir}")
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
        logging.info(f"No deployment needed for {self.best_practice_id}. Documentation was generated in the specified output directory.")
        return True