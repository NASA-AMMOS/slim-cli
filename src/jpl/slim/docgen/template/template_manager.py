# File: src/jpl/slim/docgen/template/template_manager.py
"""
Template management for documentation generation.
"""
import logging
import os
import shutil
from typing import Dict


class TemplateManager:
    """
    Manages the SLIM documentation template.
    """
    
    def __init__(self, template_repo: str, output_dir: str, logger: logging.Logger):
        """
        Initialize the template manager.
        
        Args:
            template_repo: URL or path to the template repository
            output_dir: Directory where the documentation should be generated
            logger: Logger instance
        """
        self.template_repo = template_repo
        self.output_dir = output_dir
        self.logger = logger
    
    def clone_template(self) -> bool:
        """
        Clone the template repository to the output directory.
        
        Returns:
            True if cloning was successful, False otherwise
        """
        try:
            self.logger.info(f"Cloning template from {self.template_repo}")
            
            # Ensure output directory exists
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Check if the template is a local path or a URL
            if os.path.exists(self.template_repo):
                return self._copy_local_template()
            else:
                return self._clone_git_template()
            
        except Exception as e:
            self.logger.error(f"Error cloning template: {str(e)}")
            return False
    
    def _copy_local_template(self) -> bool:
        """
        Copy template from a local directory.
        
        Returns:
            True if copying was successful, False otherwise
        """
        try:
            # Copy files from template to output directory
            for item in os.listdir(self.template_repo):
                source = os.path.join(self.template_repo, item)
                target = os.path.join(self.output_dir, item)
                
                # Skip .git directory
                if item == '.git':
                    continue
                
                # Copy files and directories
                if os.path.isdir(source):
                    shutil.copytree(source, target, dirs_exist_ok=True)
                else:
                    shutil.copy2(source, target)
            
            self.logger.info(f"Local template copied to {self.output_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error copying local template: {str(e)}")
            return False
    
    def _clone_git_template(self) -> bool:
        """
        Clone template from a git repository.
        
        Returns:
            True if cloning was successful, False otherwise
        """
        try:
            # Import git here to avoid dependency if not needed
            import git
            
            # Clone the repository
            repo = git.Repo.clone_from(self.template_repo, self.output_dir)
            
            # Remove .git directory to start fresh
            git_dir = os.path.join(self.output_dir, '.git')
            if os.path.exists(git_dir):
                shutil.rmtree(git_dir)
            
            self.logger.info(f"Git template cloned to {self.output_dir}")
            return True
            
        except ImportError:
            self.logger.error("GitPython package not installed. Install with: pip install gitpython")
            return False
        except Exception as e:
            self.logger.error(f"Error cloning git template: {str(e)}")
            return False
