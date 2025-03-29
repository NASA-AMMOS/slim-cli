"""
Standard best practice module.

This module contains the StandardPractice class for applying and deploying
standard best practices to repositories.
"""

import os
import logging
import urllib.parse
import tempfile
import uuid
import git

from jpl.slim.best_practices.base import BestPractice
from jpl.slim.utils.io_utils import download_and_place_file
from jpl.slim.utils.ai_utils import generate_with_ai
# Import the constant directly to avoid circular imports
GIT_BRANCH_NAME_FOR_MULTIPLE_COMMITS = 'slim-best-practices'

# Check if we're in test mode
SLIM_TEST_MODE = os.environ.get('SLIM_TEST_MODE', 'False').lower() in ('true', '1', 't')


class StandardPractice(BestPractice):
    """
    Best practice for standard best practices (README, CONTRIBUTING, etc).
    
    This class handles downloading and customizing documentation
    based on the SLIM best practices.
    """
    
    def apply(self, repo_path, use_ai=False, model=None, repo_url=None, 
              target_dir_to_clone_to=None, branch=None):
        """
        Apply the standard best practice to a repository.
        
        Args:
            repo_path (str): Path to the repository
            use_ai (bool, optional): Whether to use AI assistance. Defaults to False.
            model (str, optional): AI model to use if use_ai is True. Defaults to None.
            repo_url (str, optional): Repository URL. Defaults to None.
            target_dir_to_clone_to (str, optional): Directory to clone to. Defaults to None.
            branch (str, optional): Git branch to use. Defaults to None.
            
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
        
        applied_file_path = None  # default return value is invalid applied best practice
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
        if self.best_practice_id == 'SLIM-3.1':
            applied_file_path = download_and_place_file(git_repo, self.uri, 'README.md')
        elif self.best_practice_id == 'SLIM-4.1':
            applied_file_path = download_and_place_file(git_repo, self.uri, '.github/ISSUE_TEMPLATE/bug_report.md')
        elif self.best_practice_id == 'SLIM-4.2':
            applied_file_path = download_and_place_file(git_repo, self.uri, '.github/ISSUE_TEMPLATE/bug_report.yml')
        elif self.best_practice_id == 'SLIM-4.3':
            applied_file_path = download_and_place_file(git_repo, self.uri, '.github/ISSUE_TEMPLATE/new_feature.md')
        elif self.best_practice_id == 'SLIM-4.4':
            applied_file_path = download_and_place_file(git_repo, self.uri, '.github/ISSUE_TEMPLATE/new_feature.yml')
        elif self.best_practice_id == 'SLIM-5.1':
            applied_file_path = download_and_place_file(git_repo, self.uri, 'CHANGELOG.md')
        elif self.best_practice_id == 'SLIM-7.1':
            applied_file_path = download_and_place_file(git_repo, self.uri, '.github/PULL_REQUEST_TEMPLATE.md')
        elif self.best_practice_id == 'SLIM-8.1':
            applied_file_path = download_and_place_file(git_repo, self.uri, 'CODE_OF_CONDUCT.md')
        elif self.best_practice_id == 'SLIM-9.1':
            applied_file_path = download_and_place_file(git_repo, self.uri, 'CONTRIBUTING.md')
        elif self.best_practice_id == 'SLIM-13.1':
            applied_file_path = download_and_place_file(git_repo, self.uri, 'TESTING.md')
        else:
            applied_file_path = None  # nothing was modified 
            logging.warning(f"SLIM best practice {self.best_practice_id} not supported.")
        
        # Apply AI customization if requested
        if applied_file_path and use_ai and model:
            ai_content = generate_with_ai(self.best_practice_id, git_repo.working_tree_dir, applied_file_path, model)
            if ai_content:
                with open(applied_file_path, 'w') as f:
                    f.write(ai_content)
                logging.info(f"Applied AI-generated content to {applied_file_path}")
            else:
                logging.warning(f"AI generation failed for best practice {self.best_practice_id}")
        
        if applied_file_path:
            logging.info(f"Applied best practice {self.best_practice_id} to local repo {git_repo.working_tree_dir} and branch '{git_branch.name}'")
            return git_repo  # return the modified git repo object
        else:
            logging.error(f"Failed to apply best practice {self.best_practice_id}")
            return None
    
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
