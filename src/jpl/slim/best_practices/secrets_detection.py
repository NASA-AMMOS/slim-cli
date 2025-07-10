"""
Secrets detection best practice module.

This module contains the SecretsDetection class for applying and deploying
secrets detection best practices to repositories.
"""

import os
import logging
import subprocess
import sys
import json
import git
from pathlib import Path
from jpl.slim.best_practices.standard import StandardPractice
from jpl.slim.utils.io_utils import download_and_place_file
from jpl.slim.utils.cli_utils import spinner_safe_input



class SecretsDetection(StandardPractice):
    """
    Best practice for secrets detection implementation (secrets-github and secrets-precommit).

    This class handles setting up secrets detection tools like detect-secrets
    and pre-commit hooks in repositories.
    """

    def apply(self, repo_path, use_ai=False, model=None, repo_url=None,
              target_dir_to_clone_to=None, branch=None, no_prompt=False, **kwargs):
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


        # Setup repository using the parent class method
        git_repo, git_branch, target_dir = self.setup_repository(repo_path, repo_url, target_dir_to_clone_to, branch)
        if not git_repo:
            return None

        # Process best practice by alias
        if self.best_practice_id == 'secrets-github':
            # Create .github/workflows directory if it doesn't exist
            workflows_dir = os.path.join(git_repo.working_dir, '.github', 'workflows')
            os.makedirs(workflows_dir, exist_ok=True)

            # Download and place the detect-secrets.yaml file
            applied_file_path = download_and_place_file(git_repo, self.uri, '.github/workflows/detect-secrets.yaml')

            if applied_file_path:
                logging.debug(f"Applied best practice {self.best_practice_id} to local repo {git_repo.working_tree_dir} and branch '{git_branch.name}'")

                # Install detect-secrets
                if no_prompt:
                    # Skip confirmation if --no-prompt flag is used
                    self._install_detect_secrets()
                    # Run scan and check for unverified secrets
                    if not self._run_detect_secrets_scan(git_repo):
                        logging.error("Detection of unverified secrets failed. Aborting application of best practice.")
                        return None
                else:
                    # Prompt for confirmation before installing
                    confirmation = spinner_safe_input("\nThe detect-secrets tool (https://github.com/Yelp/detect-secrets) is needed to support this best practice. Do you want me to install/re-install detect-secrets? (y/n): ")
                    if confirmation.lower() in ['y', 'yes']:
                        self._install_detect_secrets()
                    else:
                        logging.warning("Not installing detect-secrets. Assuming it is already installed.")

                    # Prompt for confirmation before installing
                    confirmation = spinner_safe_input("\nDo you want me to run an initial scan with detect-secrets (will overwrite an existing `.secrets-baseline` file)? (y/n): ")
                    if confirmation.lower() in ['y', 'yes']:
                        scan_result = self._run_detect_secrets_scan(git_repo)
                        if not scan_result:
                            logging.error("Detection of unverified secrets failed. Aborting application of best practice.")
                            return None
                    else:
                        logging.warning("Not running detect-secrets scan. Assuming you have a `.secrets-baseline` file present in your repo already.")

                print(f"✅ Successfully applied best practice '{self.best_practice_id}' to repository")
                print(f"   📁 Repository: {git_repo.working_dir}")
                print(f"   🌿 Branch: {git_branch.name}")
                return git_repo
            else:
                logging.error(f"Failed to apply best practice {self.best_practice_id}")
                print(f"❌ Failed to apply best practice '{self.best_practice_id}'")
                return None

        elif self.best_practice_id == 'secrets-precommit':
            # Install pre-commit
            if no_prompt:
                # Skip confirmation if --no-prompt flag is used
                self._install_detect_secrets()
                self._install_pre_commit()
            else:
                # Prompt for confirmation before installing
                confirmation = spinner_safe_input("\nThe detect-secrets tool (https://github.com/Yelp/detect-secrets) is needed to support this best practice. Do you want me to install/re-install detect-secrets? (y/n): ")
                if confirmation.lower() in ['y', 'yes']:
                    self._install_detect_secrets()
                else:
                    logging.warning("Not installing detect-secrets. Assuming it is already installed.")

                # Prompt for confirmation before installing
                confirmation = spinner_safe_input("\nThe pre-commit tool (https://pre-commit.com) is needed to support this best practice. Do you want to install/re-install pre-commit? (y/n): ")
                if confirmation.lower() in ['y', 'yes']:
                    self._install_pre_commit()
                else:
                    logging.warning("Not installing pre-commit tool. Assuming it is already installed.")

            # Download and place the pre-commit config file
            applied_file_path = download_and_place_file(git_repo, self.uri, '.pre-commit-config.yaml')

            if applied_file_path:
                logging.debug(f"Applied best practice {self.best_practice_id} to local repo {git_repo.working_tree_dir} and branch '{git_branch.name}'")

                # Initialize pre-commit hooks
                if no_prompt:
                    # Skip confirmation if --no-prompt flag is used
                    self._install_pre_commit_hooks(git_repo)
                    
                    # Check if .secrets.baseline file exists and run detect-secrets scan if it doesn't
                    baseline_file = os.path.join(git_repo.working_dir, '.secrets.baseline')
                    if not os.path.exists(baseline_file):
                        logging.debug("No existing .secrets.baseline file found. Running detect-secrets scan...")
                        if not self._run_detect_secrets_scan(git_repo):
                            logging.error("Detection of unverified secrets failed. Aborting application of best practice.")
                            return None
                else:
                    # Prompt for confirmation before installing hooks
                    confirmation = spinner_safe_input("\nInstallation of the new pre-commit hook is needed via `pre-commit install`. Do you want to install the pre-commit hook for you? (y/n): ")
                    if confirmation.lower() in ['y', 'yes']:
                        self._install_pre_commit_hooks(git_repo)
                    
                    # Check if .secrets.baseline file exists and prompt user
                    baseline_file = os.path.join(git_repo.working_dir, '.secrets.baseline')
                    if os.path.exists(baseline_file):
                        confirmation = spinner_safe_input("\nA .secrets.baseline file already exists. Do you want to run detect-secrets scan again (this will overwrite the existing file)? (y/n): ")
                    else:
                        confirmation = spinner_safe_input("\nDo you want to run an initial scan with detect-secrets to create a .secrets.baseline file? (y/n): ")
                    
                    if confirmation.lower() in ['y', 'yes']:
                        scan_result = self._run_detect_secrets_scan(git_repo)
                        if not scan_result:
                            logging.error("Detection of unverified secrets failed. Aborting application of best practice.")
                            return None
                    elif not os.path.exists(baseline_file):
                        logging.warning("Not running detect-secrets scan. No .secrets.baseline file is present in your repo.")

                print(f"✅ Successfully applied best practice '{self.best_practice_id}' to repository")
                print(f"   📁 Repository: {git_repo.working_dir}")
                print(f"   🌿 Branch: {git_branch.name}")
                return git_repo
            else:
                logging.error(f"Failed to apply best practice {self.best_practice_id}")
                print(f"❌ Failed to apply best practice '{self.best_practice_id}'")
                return None
        else:
            logging.warning(f"SLIM best practice {self.best_practice_id} not supported.")
            print(f"❌ Best practice '{self.best_practice_id}' is not supported by SecretsDetection")
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

        # Set custom commit message for secrets detection best practices
        if not commit_message:
            if self.best_practice_id == 'secrets-github':
                commit_message = "Add detect-secrets workflow"
            elif self.best_practice_id == 'secrets-precommit':
                commit_message = "Add pre-commit configuration"
            else:
                commit_message = f"Add secrets detection for {self.best_practice_id}"

        try:
            # Get the git repository object
            repo = git.Repo(repo_path)

            # Use parent class method to handle commit and push with special error handling for pre-commit hooks
            try:
                success, error_message = self._handle_commit_and_push(repo, remote, commit_message)
                
                if success:
                    logging.debug(f"Successfully deployed best practice {self.best_practice_id}")
                    return True
                else:
                    # Check if the error is related to pre-commit hooks
                    if "hook" in error_message or "pre-commit" in error_message:
                        logging.warning(f"Git commit failed due to pre-commit hooks: {error_message}")
                        logging.warning("Please fix the issues identified by pre-commit hooks before deploying.")
                        logging.warning("You may need to run 'git add' after fixing the issues and try the commit again.")
                        return False
                    else:
                        logging.error(error_message)
                        return False

            except Exception as commit_error:
                logging.error(f"Error during commit and push: {commit_error}")
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

    def _install_pre_commit_hooks(self, git_repo):
        """Initialize pre-commit hooks in the repository.
        
        Args:
            git_repo: Git repository object containing the working directory context
        """
        try:
            logging.debug("Installing pre-commit hooks...")
            subprocess.check_call(
                ["pre-commit", "install"],
                cwd=git_repo.working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logging.debug("Successfully installed pre-commit hooks")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to install pre-commit hooks: {e}")
            return False

    def _run_detect_secrets_scan(self, git_repo):
        """
        Run detect-secrets scan to generate a baseline file and check for unverified secrets.

        Args:
            git_repo: Git repository object containing the working directory context

        Returns:
            bool: True if scan was successful and no unverified secrets were found,
                 False if scan failed or unverified secrets were found
        """
        try:
            logging.debug("Running detect-secrets scan...")
            cmd = "detect-secrets scan --all-files --exclude-files '\\.secrets.*' --exclude-files '\\.git.*' > .secrets.baseline"
            # Using shell=True since we need shell features like redirection (>)
            # Run in the repository's working directory
            subprocess.check_call(
                cmd,
                shell=True,
                cwd=git_repo.working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logging.debug("Successfully created .secrets.baseline file")

            # Check the baseline file for unverified secrets
            return self._check_baseline_for_unverified_secrets(git_repo)

        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to run detect-secrets scan: {e}")
            return False

    def _check_baseline_for_unverified_secrets(self, git_repo):
        """
        Check the .secrets.baseline file for unverified secrets.

        Args:
            git_repo: Git repository object containing the working directory context

        Returns:
            bool: True if no unverified secrets were found, False otherwise
        """
        try:
            # Read the baseline file from the repository directory
            baseline_file = os.path.join(git_repo.working_dir, '.secrets.baseline')
            with open(baseline_file, 'r') as f:
                baseline = json.load(f)

            # Check the results for unverified secrets
            if 'results' in baseline:
                results = baseline['results']
                unverified_secrets = []

                # Iterate through files in results
                for filename, secrets in results.items():
                    for secret in secrets:
                        # Check if the secret is unverified
                        if secret.get('is_verified') is False:
                            unverified_secrets.append({
                                'filename': secret.get('filename', filename),
                                'type': secret.get('type', 'Unknown'),
                                'line_number': secret.get('line_number', 'Unknown')
                            })

                # If unverified secrets were found, report them and return False
                if unverified_secrets:
                    logging.error("Unverified secrets found in the repository:")
                    for secret in unverified_secrets:
                        logging.error(f"  - {secret['type']} in {secret['filename']} at line {secret['line_number']}")
                    logging.error("Secrets must be verified or removed before deployment.")
                    logging.error("To verify secrets, run 'detect-secrets audit .secrets.baseline'")
                    logging.error("To remove secrets, edit the files and remove the sensitive information.")
                    return False

                return True
            else:
                # No results found, which is strange but not necessarily an error
                logging.warning("No results found in .secrets.baseline file. This is unusual.")
                return True

        except Exception as e:
            logging.error(f"Error checking .secrets.baseline file: {e}")
            return False