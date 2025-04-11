"""
Secrets detection best practice module.

This module contains the SecretsDetection class for applying and deploying
secrets detection best practices to repositories.
"""

import os
import logging
import subprocess
import urllib.parse
import tempfile
import uuid
import git
import sys
from pathlib import Path
from jpl.slim.best_practices.base import BestPractice
from jpl.slim.utils.io_utils import download_and_place_file

# Check if we're in test mode
SLIM_TEST_MODE = os.environ.get('SLIM_TEST_MODE', 'False').lower() in ('true', '1', 't')


class SecretsDetection(BestPractice):
    """
    Best practice for secrets detection implementation (SLIM-2.1 and SLIM-2.2).

    This class handles setting up secrets detection tools like detect-secrets
    and pre-commit hooks in repositories.
    """

    def apply(self, repo_path, use_ai=False, model=None, repo_url=None,
              target_dir_to_clone_to=None, branch=None, no_prompt=False):
        """
        Apply the secrets detection best practice to a repository.

        Args:
            repo_path (str): Path to the repository
            use_ai (bool, optional): Whether to use AI assistance. Defaults to False.
            model (str, optional): AI model to use if use_ai is True. Defaults to None.
            repo_url (str, optional): Repository URL. Defaults to None.
            target_dir_to_clone_to (str, optional): Directory to clone to. Defaults to None.
            branch (str, optional): Git branch to use. Defaults to None.
            no_prompt (bool, optional): Skip user confirmation prompts. Defaults to False.

        Returns:
            git.Repo: Git repository object if successful, None otherwise
        """
        logging.debug(f"Applying best practice {self.best_practice_id} to repository: {repo_path}")

        # In test mode, simulate success without making actual API calls
        if SLIM_TEST_MODE:
            logging.info(f"TEST MODE: Simulating applying best practice {self.best_practice_id}")
            # Create a mock repo object for testing
            mock_repo = git.Repo.init(target_dir_to_clone_to or tempfile.mkdtemp())
            # Create a mock branch
            branch_name = branch or self.best_practice_id
            if not hasattr(mock_repo.heads, branch_name):
                mock_repo.create_head(branch_name)
            mock_repo.head.reference = getattr(mock_repo.heads, branch_name)
            logging.info(f"TEST MODE: Successfully applied best practice {self.best_practice_id} to mock repository")
            return mock_repo

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
                    target_dir_to_clone_to = tempfile.mkdtemp(prefix=f"{repo_name}_" + str(uuid.uuid4()) + '_')
                    logging.debug(f"Generating temporary clone directory at {target_dir_to_clone_to}")
            else:
                target_dir_to_clone_to = repo_path
                logging.debug(f"Using existing repository directory {repo_path}")

            try:
                git_repo = git.Repo(target_dir_to_clone_to)
                logging.debug(f"Repository folder ({target_dir_to_clone_to}) exists already. Using existing directory.")
            except Exception as e:
                logging.debug(f"Repository folder ({target_dir_to_clone_to}) not a git repository yet already. Cloning repo {repo_url} contents into folder.")
                if SLIM_TEST_MODE:
                    # In test mode, just initialize a new repo instead of cloning
                    git_repo = git.Repo.init(target_dir_to_clone_to)
                    logging.debug(f"TEST MODE: Initialized new git repository at {target_dir_to_clone_to}")
                else:
                    git_repo = git.Repo.clone_from(repo_url, target_dir_to_clone_to)

            # Change directory to the cloned repository
            os.chdir(target_dir_to_clone_to)

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

        except git.exc.InvalidGitRepositoryError:
            logging.error(f"Error: {target_dir_to_clone_to} is not a valid Git repository.")
            return None
        except git.exc.GitCommandError as e:
            logging.error(f"Git command error: {e}")
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return None

        # Process best practice by ID
        if self.best_practice_id == 'SLIM-2.1':
            # Create .github/workflows directory if it doesn't exist
            workflows_dir = os.path.join(git_repo.working_dir, '.github', 'workflows')
            os.makedirs(workflows_dir, exist_ok=True)
            
            # Download and place the detect-secrets.yaml file
            applied_file_path = download_and_place_file(git_repo, self.uri, '.github/workflows/detect-secrets.yaml')
            
            if applied_file_path:
                logging.info(f"Applied best practice {self.best_practice_id} to local repo {git_repo.working_tree_dir} and branch '{git_branch.name}'")
                
                # Install detect-secrets if not in test mode
                if not SLIM_TEST_MODE:
                    if no_prompt:
                        # Skip confirmation if --no-prompt flag is used
                        self._install_detect_secrets()
                        self._run_detect_secrets_scan()
                    else:
                        # Prompt for confirmation before installing
                        confirmation = input("The detect-secrets tool (https://github.com/Yelp/detect-secrets) is needed to support this best practice. Do you want me to install/re-install detect-secrets? (y/n): ")
                        if confirmation.lower() in ['y', 'yes']:
                            self._install_detect_secrets()
                        else:
                            logging.warning("Not installing detect-secrets. Assuming it is already installed.")
                
                        # Prompt for confirmation before installing
                        confirmation = input("Do you want me to run an initial scan with detect-secrets (will overwrite an existing `.secrets-baseline` file)? (y/n): ")
                        if confirmation.lower() in ['y', 'yes']:
                            self._run_detect_secrets_scan()
                        else:
                            logging.warning("Not running detect-secrets scan. Assuming you have a `.secrets-baseline` file present in your repo already.")
                
                return git_repo
            else:
                logging.error(f"Failed to apply best practice {self.best_practice_id}")
                return None
                
        elif self.best_practice_id == 'SLIM-2.2':
            # Install pre-commit if not in test mode
            if not SLIM_TEST_MODE:
                if no_prompt:
                    # Skip confirmation if --no-prompt flag is used
                    self._install_pre_commit()
                else:
                    # Prompt for confirmation before installing
                    confirmation = input("The pre-commit tool (https://pre-commit.com) is needed to support this best practice. Do you want to install/re-install pre-commit? (y/n): ")
                    if confirmation.lower() in ['y', 'yes']:
                        self._install_pre_commit()
                    else:
                        logging.warning("Not installing pre-commit tool. Assuming it is already installed.")
            
            # Download and place the pre-commit config file
            applied_file_path = download_and_place_file(git_repo, self.uri, '.pre-commit-config.yaml')
            
            if applied_file_path:
                logging.info(f"Applied best practice {self.best_practice_id} to local repo {git_repo.working_tree_dir} and branch '{git_branch.name}'")
                
                # Initialize pre-commit hooks if not in test mode
                if not SLIM_TEST_MODE:
                    if no_prompt:
                        # Skip confirmation if --no-prompt flag is used
                        self._install_pre_commit_hooks()
                    else:
                        # Prompt for confirmation before installing hooks
                        confirmation = input("Installation of the new pre-commit hook is needed via `pre-commit install`. Do you want to install the pre-commit hook for you? (y/n): ")
                        if confirmation.lower() in ['y', 'yes']:
                            self._install_pre_commit_hooks()
                
                return git_repo
            else:
                logging.error(f"Failed to apply best practice {self.best_practice_id}")
                return None
        else:
            logging.warning(f"SLIM best practice {self.best_practice_id} not supported.")
            return None

    def deploy(self, repo_path, remote=None, commit_message=None):
        """
        Deploy changes made by applying the secrets detection best practice.

        Args:
            repo_path (str): Path to the repository
            remote (str, optional): Remote repository to push changes to. Defaults to None.
            commit_message (str, optional): Commit message for the changes. Defaults to None.

        Returns:
            bool: True if deployment was successful, False otherwise
        """
        logging.debug(f"Deploying best practice {self.best_practice_id} to repository: {repo_path}")

        if not commit_message:
            if self.best_practice_id == 'SLIM-2.1':
                commit_message = "Add detect-secrets workflow"
            elif self.best_practice_id == 'SLIM-2.2':
                commit_message = "Add pre-commit configuration"
            else:
                commit_message = f"Add secrets detection for {self.best_practice_id}"

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

            logging.info(f"Successfully deployed best practice {self.best_practice_id}")
            return True

        except git.exc.GitCommandError as e:
            logging.error(f"Git command failed: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"An error occurred during deployment: {str(e)}")
            return False

    def _install_detect_secrets(self):
        """Install detect-secrets using pip."""
        try:
            logging.debug("Installing detect-secrets...")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "git+https://github.com/Yelp/detect-secrets.git"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logging.debug("Successfully installed detect-secrets")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to install detect-secrets: {e}")
            return False

    def _install_pre_commit(self):
        """Install pre-commit using pip."""
        try:
            logging.debug("Installing pre-commit...")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "pre-commit"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logging.debug("Successfully installed pre-commit")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to install pre-commit: {e}")
            return False

    def _install_pre_commit_hooks(self):
        """Initialize pre-commit hooks in the repository."""
        try:
            logging.debug("Installing pre-commit hooks...")
            subprocess.check_call(
                ["pre-commit", "install"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logging.info("Successfully installed pre-commit hooks")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to install pre-commit hooks: {e}")
            return False
            
    def _run_detect_secrets_scan(self):
        """Run detect-secrets scan to generate a baseline file."""
        try:
            logging.debug("Running detect-secrets scan...")
            cmd = "detect-secrets scan --all-files --exclude-files '\\.secrets.*' --exclude-files '\\.git.*' > .secrets.baseline"
            # Using shell=True since we need shell features like redirection (>)
            subprocess.check_call(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logging.info("Successfully ran detect-secrets and created .secrets.baseline file")
            logging.warning("Make sure to double-check if you have flagged secrets in .secrets.baseline file")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to run detect-secrets scan: {e}")
            return False
