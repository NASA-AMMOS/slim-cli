"""
Governance best practice module.

This module contains the GovernancePractice class for applying and deploying
governance documentation to repositories.
"""

import os
import logging
from jpl.slim.best_practices.base import BestPractice
import git

# Import functions from utility modules
from jpl.slim.utils.io_utils import download_and_place_file
from jpl.slim.utils.ai_utils import generate_with_ai


class GovernancePractice(BestPractice):
    """
    Best practice for adding governance documentation to repositories.
    
    This class handles downloading and customizing governance documentation
    based on the SLIM-1.1, SLIM-1.2, and SLIM-1.3 best practices.
    """
    
    def apply(self, repo_path, use_ai=False, model=None, repo_url=None, 
              target_dir_to_clone_to=None, branch=None):
        """
        Apply the governance best practice to a repository.
        
        Args:
            repo_path (str): Path to the repository
            use_ai (bool, optional): Whether to use AI assistance. Defaults to False.
            model (str, optional): AI model to use if use_ai is True. Defaults to None.
            repo_url (str, optional): Repository URL. Defaults to None.
            target_dir_to_clone_to (str, optional): Directory to clone to. Defaults to None.
            branch (str, optional): Git branch to use. Defaults to None.
            
        Returns:
            str: Path to the applied file
        """
        logging.debug(f"Applying governance best practice {self.best_practice_id} to repository: {repo_path}")
        
        # Get the git repository object
        try:
            # If repo_url is provided, we need to clone the repository
            if repo_url:
                logging.debug(f"Using repository URL {repo_url}")
                if target_dir_to_clone_to:
                    logging.debug(f"Cloning to directory {target_dir_to_clone_to}")
                    git_repo = git.Repo.clone_from(repo_url, target_dir_to_clone_to)
                    repo_path = target_dir_to_clone_to
                else:
                    # Create a temporary directory for cloning
                    import tempfile
                    import os
                    temp_dir = tempfile.mkdtemp()
                    logging.debug(f"Cloning to temporary directory {temp_dir}")
                    git_repo = git.Repo.clone_from(repo_url, temp_dir)
                    repo_path = temp_dir
                
                # Create and checkout branch if specified
                if branch:
                    if branch in git_repo.heads:
                        git_repo.heads[branch].checkout()
                    else:
                        git_repo.git.checkout('-b', branch)
                    logging.debug(f"Checked out branch {branch}")
            else:
                git_repo = git.Repo(repo_path)
                
                # Create and checkout branch if specified
                if branch:
                    if branch in git_repo.heads:
                        git_repo.heads[branch].checkout()
                    else:
                        git_repo.git.checkout('-b', branch)
                    logging.debug(f"Checked out branch {branch}")
        except git.exc.InvalidGitRepositoryError:
            logging.error(f"Error: {repo_path} is not a valid Git repository.")
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return None
        
        # Determine which file to download based on best practice ID
        filename = None
        if self.best_practice_id == 'SLIM-1.1':
            filename = 'GOVERNANCE.md'
        elif self.best_practice_id == 'SLIM-1.2':
            filename = 'GOVERNANCE.md'
        elif self.best_practice_id == 'SLIM-1.3':
            filename = 'GOVERNANCE.md'
        else:
            logging.warning(f"Unsupported governance best practice ID: {self.best_practice_id}")
            return None
        
        # Download the governance file
        applied_file_path = download_and_place_file(git_repo, self.uri, filename)
        
        if not applied_file_path:
            logging.error(f"Failed to download governance file for best practice {self.best_practice_id}")
            return None
        
        # Apply AI customization if requested
        if use_ai and model:
            ai_content = generate_with_ai(self.best_practice_id, git_repo.working_tree_dir, applied_file_path, model)
            if ai_content:
                with open(applied_file_path, 'w') as f:
                    f.write(ai_content)
                logging.info(f"Applied AI-generated content to {applied_file_path}")
            else:
                logging.warning(f"AI generation failed for best practice {self.best_practice_id}")
        
        logging.info(f"Applied governance best practice {self.best_practice_id} to repository {repo_path}")
        return applied_file_path
    
    def deploy(self, repo_path, remote=None, commit_message=None):
        """
        Deploy changes made by applying the governance best practice.
        
        Args:
            repo_path (str): Path to the repository
            remote (str, optional): Remote repository to push changes to. Defaults to None.
            commit_message (str, optional): Commit message for the changes. Defaults to None.
            
        Returns:
            bool: True if deployment was successful, False otherwise
        """
        logging.debug(f"Deploying governance best practice {self.best_practice_id} to repository: {repo_path}")
        
        if not commit_message:
            commit_message = f"Add governance documentation ({self.best_practice_id})"
        
        try:
            # Get the git repository object
            repo = git.Repo(repo_path)
            
            # Add all changes
            repo.git.add(A=True)
            logging.debug("Added all changes to git index.")
            
            # Commit changes
            repo.git.commit('-m', commit_message)
            logging.debug("Committed changes.")
            
            # Push changes if remote is specified
            if remote:
                repo.git.push(remote, repo.active_branch.name)
                logging.debug(f"Pushed changes to remote {remote} on branch {repo.active_branch.name}")
            
            logging.info(f"Successfully deployed governance best practice {self.best_practice_id}")
            return True
            
        except git.exc.GitCommandError as e:
            logging.error(f"Git command failed: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"An error occurred during deployment: {str(e)}")
            return False
