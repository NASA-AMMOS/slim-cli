"""
Standard best practice module.

This module contains the StandardPractice class for applying and deploying
standard best practices to repositories. It provides common functionality
that can be inherited by other best practice classes.
"""

import os
import logging
import urllib.parse
import tempfile
import uuid
import git

from jpl.slim.best_practices.base import BestPractice
from jpl.slim.best_practices.practice_mapping import get_file_path
from jpl.slim.utils.io_utils import download_and_place_file
from jpl.slim.utils.ai_utils import generate_with_ai
from jpl.slim.utils.prompt_utils import get_prompt_with_context, get_repository_context
from jpl.slim.utils.io_utils import read_file_content, fetch_repository_context
from jpl.slim.utils.git_utils import create_repo_temp_dir
# Import the constant directly to avoid circular imports
GIT_BRANCH_NAME_FOR_MULTIPLE_COMMITS = 'slim-best-practices'



class StandardPractice(BestPractice):
    """
    Best practice for standard best practices (README, CONTRIBUTING, etc).

    This class handles downloading and customizing documentation
    based on the SLIM best practices. It also provides common functionality
    that can be inherited by other best practice classes.
    """

    def setup_repository(self, repo_path, repo_url=None, target_dir_to_clone_to=None, branch=None):
        """
        Set up the repository for applying best practices.

        Args:
            repo_path (str): Path to the repository
            repo_url (str, optional): Repository URL. Defaults to None.
            target_dir_to_clone_to (str, optional): Directory to clone to. Defaults to None.
            branch (str, optional): Git branch to use. Defaults to None.

        Returns:
            tuple: (git_repo, git_branch, target_dir) if successful, (None, None, None) otherwise
        """
        git_repo = None
        git_branch = None


        try:
            # Handle repository setup
            if repo_url:
                logging.debug(f"Using repository URL {repo_url}. URI: {self.uri}")

                parsed_url = urllib.parse.urlparse(repo_url)
                repo_name = os.path.basename(parsed_url.path)
                repo_name = repo_name[:-4] if repo_name.endswith('.git') else repo_name  # Remove '.git' from repo name if present
                if target_dir_to_clone_to:  # If target_dir_to_clone_to is specified, append repo name to target_dir_to_clone_to
                    target_dir_to_clone_to = os.path.join(target_dir_to_clone_to, repo_name)
                    logging.debug(f"Set clone directory to {target_dir_to_clone_to}")
                else:  # else make a temporary directory
                    target_dir_to_clone_to = create_repo_temp_dir(repo_name)
                    logging.debug(f"Generating temporary clone directory at {target_dir_to_clone_to}")
            else:
                target_dir_to_clone_to = repo_path
                logging.debug(f"Using existing repository directory {repo_path}")

            try:
                git_repo = git.Repo(target_dir_to_clone_to)
                logging.debug(f"Repository folder ({target_dir_to_clone_to}) exists already. Using existing directory.")
            except Exception as e:
                logging.debug(f"Repository folder ({target_dir_to_clone_to}) not a git repository yet already. Cloning repo {repo_url} contents into folder.")
                git_repo = git.Repo.clone_from(repo_url, target_dir_to_clone_to)

            # Note: We don't change the working directory to avoid global state issues
            # Git operations work with absolute paths from git_repo object

            if git_repo.head.is_valid():
                if self.best_practice_id in git_repo.heads:
                    # Check out the existing branch
                    git_branch = git_repo.heads[self.best_practice_id] if not branch else git_repo.create_head(branch)
                    git_branch.checkout()
                    logging.warning(f"Git branch '{git_branch.name}' already exists in clone_to_dir '{target_dir_to_clone_to}'. Checking out existing branch.")
                else:
                    # Create and check out the new branch
                    git_branch = git_repo.create_head(self.best_practice_id) if not branch else git_repo.create_head(branch)
                    git_branch.checkout()
                    logging.debug(f"Branch '{git_branch.name}' created and checked out successfully.")
            else:
                # Create an initial commit
                with open(os.path.join(git_repo.working_dir, 'README.md'), 'w') as file:
                    file.write("Initial commit")
                git_repo.index.add(['README.md'])  # Add files to the index
                git_repo.index.commit('Initial commit')  # Commit the changes
                logging.debug("Initial commit created in the empty repository.")

                # Empty repo, so only now create and check out the fresh branch
                git_branch = git_repo.create_head(self.best_practice_id) if not branch else git_repo.create_head(branch)
                git_branch.checkout()
                logging.debug(f"Empty repository. Creating new branch '{git_branch.name}' and checked it out successfully.")

            return git_repo, git_branch, target_dir_to_clone_to

        except git.exc.InvalidGitRepositoryError:
            logging.error(f"Error: {target_dir_to_clone_to} is not a valid Git repository.")
            print(f"❌ Error: {target_dir_to_clone_to} is not a valid Git repository.")
            return None, None, None
        except git.exc.GitCommandError as e:
            logging.error(f"Git command error: {e}")
            # Extract user-friendly error message from Git command error
            error_msg = str(e)
            if "Could not resolve host" in error_msg:
                print(f"❌ Error: Unable to access repository. Could not resolve host.")
            elif "Repository not found" in error_msg or "not found" in error_msg:
                print(f"❌ Error: Repository not found. Please check the URL and try again.")
            elif "could not read Username" in error_msg or "Authentication failed" in error_msg:
                print(f"❌ Error: Repository not found or access denied. Please check the URL and your permissions.")
            elif "Permission denied" in error_msg or "access denied" in error_msg:
                print(f"❌ Error: Permission denied. Please check your access credentials.")
            elif "Connection refused" in error_msg or "Connection timed out" in error_msg:
                print(f"❌ Error: Connection failed. Please check your network connection and try again.")
            else:
                print(f"❌ Error: Failed to clone repository. Please check the repository URL and try again.")
            return None, None, None
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            print(f"❌ Error: An unexpected error occurred while setting up repository: {str(e)}")
            return None, None, None
            
    def apply(self, repo_path, use_ai=False, model=None, repo_url=None,
              target_dir_to_clone_to=None, branch=None, no_prompt=False, **kwargs):
        """
        Apply the standard best practice to a repository.

        Args:
            repo_path (str): Path to the repository
            use_ai (bool, optional): Whether to use AI assistance. Defaults to False.
            model (str, optional): AI model to use if use_ai is True. Defaults to None.
            repo_url (str, optional): Repository URL. Defaults to None.
            target_dir_to_clone_to (str, optional): Directory to clone to. Defaults to None.
            branch (str, optional): Git branch to use. Defaults to None.
            no_prompt (bool, optional): Skip user confirmation prompts for dependencies installation. Defaults to False.

        Returns:
            git.Repo: Git repository object if successful, None otherwise
        """
        logging.debug(f"Applying best practice {self.best_practice_id} to repository: {repo_path}")


        applied_file_path = None  # default return value is invalid applied best practice
        
        # Setup repository
        git_repo, git_branch, target_dir = self.setup_repository(repo_path, repo_url, target_dir_to_clone_to, branch)
        if not git_repo:
            return None

        # Process best practice by alias
        file_path = get_file_path(self.best_practice_id)
        if file_path:
            applied_file_path = download_and_place_file(git_repo, self.uri, file_path)
        else:
            applied_file_path = None  # nothing was modified
            logging.warning(f"Best practice {self.best_practice_id} not supported or no file mapping found.")

        # Apply AI customization if requested
        if applied_file_path and use_ai and model:
            self._apply_ai_customization(git_repo, applied_file_path, model)

        if applied_file_path:
            logging.debug(f"Applied best practice {self.best_practice_id} to local repo {git_repo.working_tree_dir} and branch '{git_branch.name}'")
            print(f"✅ Successfully applied best practice '{self.best_practice_id}' to repository")
            print(f"   📁 Repository: {git_repo.working_tree_dir}")
            print(f"   🌿 Branch: {git_branch.name}")
            return git_repo  # return the modified git repo object
        else:
            logging.error(f"Failed to apply best practice {self.best_practice_id}")
            print(f"❌ Failed to apply best practice '{self.best_practice_id}'")
            return None

    def _apply_ai_customization(self, git_repo, file_path, model):
        """
        Apply AI customization to a file using centralized prompt system.

        Args:
            git_repo (git.Repo): Git repository object
            file_path (str): Path to the file to customize
            model (str): AI model to use

        Returns:
            bool: True if AI customization was successful, False otherwise
        """
        try:
            # Read current file content
            current_content = read_file_content(file_path)
            if not current_content:
                logging.warning(f"Could not read content from {file_path}")
                return False
            
            # Get AI prompt with context from centralized system
            prompt_with_context = get_prompt_with_context('standard_practices', self.best_practice_id)
            
            if not prompt_with_context:
                logging.warning(f"No AI prompt found for best practice {self.best_practice_id}, falling back to original method")
                # Fall back to original AI generation method
                ai_content = generate_with_ai(self.best_practice_id, git_repo.working_tree_dir, file_path, model)
            else:
                # Use centralized prompt system with repository context
                logging.debug(f"Fetching repository context from: {git_repo.working_tree_dir}")
                
                # Get repository context configuration for this specific best practice
                repo_context_config = get_repository_context('standard_practices', self.best_practice_id)
                logging.debug(f"Repository context config: {repo_context_config}")
                
                # Fetch repository context using the new system
                repo_context = fetch_repository_context(git_repo.working_tree_dir, repo_context_config)
                context_info = f"REPOSITORY CONTEXT:\n{repo_context}" if repo_context else "No repository context found."
                logging.debug(f"Fetched repository context, length: {len(repo_context) if repo_context else 0}")
                
                # Construct full prompt
                full_prompt = f"{prompt_with_context}\n\nTEMPLATE TO ENHANCE:\n{current_content}\n\nCONTEXT INFORMATION:\n{context_info}"
                
                # Generate AI content using the centralized AI utilities
                from jpl.slim.utils.ai_utils import generate_ai_content
                ai_content = generate_ai_content(full_prompt, model)
            
            if ai_content:
                logging.debug(f"AI-generated content for {file_path}:\n{ai_content}")
                with open(file_path, 'w') as f:
                    f.write(ai_content)
                logging.debug(f"Applied AI-generated content to {file_path}")
                return True
            else:
                logging.warning(f"AI generation failed for best practice {self.best_practice_id}")
                return False
        except Exception as e:
            logging.error(f"Error applying AI customization: {e}")
            return False
            
    def _handle_commit_and_push(self, repo, remote=None, commit_message=None):
        """
        Common method to handle git commit and push operations.

        Args:
            repo (git.Repo): Git repository object
            remote (str, optional): Remote repository to push changes to. Defaults to None.
            commit_message (str, optional): Commit message for the changes. Defaults to None.

        Returns:
            bool: True if commit and push were successful, False otherwise
            str: Error message if there was a failure, None otherwise
        """
        try:
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

            return True, None
        except git.exc.GitCommandError as e:
            return False, f"Git command failed: {str(e)}"
        except Exception as e:
            return False, f"An error occurred: {str(e)}"

    def deploy(self, repo_path, remote=None, commit_message=None):
        """
        Deploy changes made by applying the best practice.

        Args:
            repo_path (str): Path to the repository
            remote (str, optional): Remote repository to push changes to. Defaults to None.
            commit_message (str, optional): Commit message for the changes. Defaults to None.

        Returns:
            bool: True if deployment was successful, False otherwise
        """
        logging.debug(f"Deploying best practice {self.best_practice_id} to repository: {repo_path}")

        if not commit_message:
            commit_message = f"Add documentation for {self.best_practice_id}"

        try:
            # Get the git repository object
            repo = git.Repo(repo_path)

            # Use common method to handle commit and push
            success, error_message = self._handle_commit_and_push(repo, remote, commit_message)
            
            if success:
                logging.debug(f"Successfully deployed best practice {self.best_practice_id}")
                return True
            else:
                logging.error(error_message)
                return False

        except Exception as e:
            logging.error(f"An error occurred during deployment: {str(e)}")
            return False