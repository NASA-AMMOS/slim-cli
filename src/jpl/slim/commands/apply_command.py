"""
Apply command module for the SLIM CLI.

This module contains the implementation of the 'apply' subcommand,
which applies best practices to repositories.
"""

import logging
import os
import os
import tempfile
import urllib.parse
import uuid
import git

# Check if we're in test mode
SLIM_TEST_MODE = os.environ.get('SLIM_TEST_MODE', 'False').lower() in ('true', '1', 't')

from jpl.slim.utils.io_utils import (
    fetch_best_practices,
    repo_file_to_list
)
from jpl.slim.utils.git_utils import generate_git_branch_name
from jpl.slim.manager.best_practices_manager import BestPracticeManager
from jpl.slim.commands.common import (
    SLIM_REGISTRY_URI,
    GIT_BRANCH_NAME_FOR_MULTIPLE_COMMITS
)

def setup_parser(subparsers):
    """
    Set up the parser for the 'apply' command.

    Args:
        subparsers: Subparsers object from argparse

    Returns:
        The parser for the 'apply' command
    """
    from jpl.slim.commands.common import SUPPORTED_MODELS, get_ai_model_pairs

    parser = subparsers.add_parser('apply', help='Applies a best practice, i.e. places a best practice in a git repo in the right spot with appropriate content')
    parser.add_argument('--best-practice-ids', nargs='+', required=True, help='Best practice IDs to apply')
    parser.add_argument('--repo-urls', nargs='+', required=False, help='Repository URLs to apply to. Do not use if --repo-dir specified')
    parser.add_argument('--repo-urls-file', required=False, help='Path to a file containing repository URLs')
    parser.add_argument('--repo-dir', required=False, help='Repository directory location on local machine. Only one repository supported')
    parser.add_argument('--clone-to-dir', required=False, help='Local path to clone repository to. Compatible with --repo-urls')
    parser.add_argument('--use-ai', metavar='MODEL', help=f"Automatically customize the application of the best practice with an AI model. Support for: {get_ai_model_pairs(SUPPORTED_MODELS)}")
    parser.add_argument('--no-prompt', action='store_true', help='Skip user confirmation prompts when installing dependencies')
    
    # Document generator specific arguments
    parser.add_argument('--output-dir', required=False, help='Output directory for generated documentation (required for doc-gen)')
    parser.add_argument('--template-only', action='store_true', help='Generate only the documentation template without analyzing a repository (for doc-gen)')
    parser.add_argument('--revise-site', action='store_true', help='Revise an existing documentation site (for doc-gen)')
    
    parser.set_defaults(func=handle_command)
    return parser

def handle_command(args):
    """
    Handle the 'apply' command.

    Args:
        args: Arguments from argparse
    """
    # Create a dictionary from the args - handles missing attributes safely
    kwargs = vars(args).copy()
    
    # Extract the arguments we need
    best_practice_ids = kwargs.pop('best_practice_ids', [])
    
    # Handle use_ai safely
    use_ai = kwargs.pop('use_ai', None)
    use_ai_flag = bool(use_ai)
    model = use_ai  # The model name is the value of use_ai
    
    # Extract other arguments
    repo_urls_file = kwargs.pop('repo_urls_file', None)
    repo_urls = repo_file_to_list(repo_urls_file) if repo_urls_file else kwargs.pop('repo_urls', None)
    existing_repo_dir = kwargs.pop('repo_dir', None)
    target_dir_to_clone_to = kwargs.pop('clone_to_dir', None)
    no_prompt = kwargs.pop('no_prompt', False)
    
    # Remove command-specific arguments that shouldn't be passed to apply_best_practices
    kwargs.pop('func', None)
    kwargs.pop('command', None)
    kwargs.pop('logging', None)
    kwargs.pop('dry_run', None)
    
    # Call apply_best_practices with the extracted parameters
    apply_best_practices(
        best_practice_ids=best_practice_ids,
        use_ai_flag=use_ai_flag,
        model=model,
        repo_urls=repo_urls,
        existing_repo_dir=existing_repo_dir,
        target_dir_to_clone_to=target_dir_to_clone_to,
        no_prompt=no_prompt,
        **kwargs  # Pass remaining kwargs to the function
    )

def apply_best_practices(best_practice_ids, use_ai_flag, model, repo_urls=None, existing_repo_dir=None, 
                         target_dir_to_clone_to=None, no_prompt=False, **kwargs):
    """
    Apply best practices to repositories.

    Args:
        best_practice_ids: List of best practice IDs to apply
        use_ai_flag: Whether to use AI to customize the best practices
        model: AI model to use if use_ai_flag is True
        repo_urls: List of repository URLs to apply to
        existing_repo_dir: Existing repository directory to apply to
        target_dir_to_clone_to: Directory to clone repositories to
        no_prompt: Skip user confirmation prompts for dependencies installation
        **kwargs: Additional arguments to pass to the apply method
    """
    # Handle special case for doc-gen best practice
    if len(best_practice_ids) == 1 and best_practice_ids[0] == "doc-gen":
        apply_best_practice(
            best_practice_id=best_practice_ids[0],
            use_ai_flag=use_ai_flag,
            model=model,
            repo_url=repo_urls[0] if repo_urls else None,
            existing_repo_dir=existing_repo_dir,
            target_dir_to_clone_to=target_dir_to_clone_to,
            no_prompt=no_prompt,
            **kwargs
        )
        return

    # Handle normal case for other best practices
    if existing_repo_dir:
        branch = GIT_BRANCH_NAME_FOR_MULTIPLE_COMMITS if len(best_practice_ids) > 1 else best_practice_ids[0]
        for best_practice_id in best_practice_ids:
            apply_best_practice(
                best_practice_id=best_practice_id,
                use_ai_flag=use_ai_flag,
                model=model,
                existing_repo_dir=existing_repo_dir,
                branch=branch,
                no_prompt=no_prompt,
                **kwargs
            )
    else:
        for repo_url in repo_urls:
            if len(best_practice_ids) > 1:
                if repo_url:
                    logging.debug(f"Using repository URL {repo_url} for group of best_practice_ids {best_practice_ids}")

                    parsed_url = urllib.parse.urlparse(repo_url)
                    repo_name = os.path.basename(parsed_url.path)
                    repo_name = repo_name[:-4] if repo_name.endswith('.git') else repo_name  # Remove '.git' from repo name if present
                    if target_dir_to_clone_to:
                        for best_practice_id in best_practice_ids:
                            apply_best_practice(
                                best_practice_id=best_practice_id,
                                use_ai_flag=use_ai_flag,
                                model=model,
                                repo_url=repo_url,
                                target_dir_to_clone_to=target_dir_to_clone_to,
                                branch=GIT_BRANCH_NAME_FOR_MULTIPLE_COMMITS,
                                no_prompt=no_prompt,
                                **kwargs
                            )
                    else:  # else make a temporary directory
                        repo_dir = tempfile.mkdtemp(prefix=f"{repo_name}_" + str(uuid.uuid4()) + '_')
                        logging.debug(f"Generating temporary clone directory for group of best_practice_ids at {repo_dir}")
                        for best_practice_id in best_practice_ids:
                            apply_best_practice(
                                best_practice_id=best_practice_id,
                                use_ai_flag=use_ai_flag,
                                model=model,
                                repo_url=repo_url,
                                target_dir_to_clone_to=repo_dir,
                                branch=GIT_BRANCH_NAME_FOR_MULTIPLE_COMMITS,
                                no_prompt=no_prompt,
                                **kwargs
                            )
                else:
                    for best_practice_id in best_practice_ids:
                        apply_best_practice(
                            best_practice_id=best_practice_id,
                            use_ai_flag=use_ai_flag,
                            model=model,
                            existing_repo_dir=existing_repo_dir,
                            no_prompt=no_prompt,
                            **kwargs
                        )
            elif len(best_practice_ids) == 1:
                apply_best_practice(
                    best_practice_id=best_practice_ids[0],
                    use_ai_flag=use_ai_flag,
                    model=model,
                    repo_url=repo_url,
                    existing_repo_dir=existing_repo_dir,
                    target_dir_to_clone_to=target_dir_to_clone_to,
                    no_prompt=no_prompt,
                    **kwargs
                )
            else:
                logging.error(f"No best practice IDs specified.")

def apply_best_practice(best_practice_id, use_ai_flag, model, repo_url=None, existing_repo_dir=None, 
                        target_dir_to_clone_to=None, branch=None, no_prompt=False, **kwargs):
    """
    Apply a best practice to a repository.

    Args:
        best_practice_id: Best practice ID to apply
        use_ai_flag: Whether to use AI to customize the best practice
        model: AI model to use if use_ai_flag is True
        repo_url: Repository URL to apply to
        existing_repo_dir: Existing repository directory to apply to
        target_dir_to_clone_to: Directory to clone repository to
        branch: Git branch to use
        no_prompt: Skip user confirmation prompts for dependencies installation
        **kwargs: Additional arguments to pass to the apply method

    Returns:
        git.Repo: Git repository object if successful, None otherwise
    """
    logging.debug(f"AI features {'enabled' if use_ai_flag else 'disabled'} for applying best practices")
    logging.debug(f"Applying best practice ID: {best_practice_id} to repository: {repo_url or existing_repo_dir}")
    
    # Log any additional kwargs for debugging
    if kwargs:
        logging.debug(f"Additional parameters: {kwargs}")

    # In test mode, simulate success without making actual API calls
    if SLIM_TEST_MODE:
        logging.info(f"TEST MODE: Simulating applying best practice {best_practice_id}")
        # Create a mock repo object for testing
        mock_repo = git.Repo.init(target_dir_to_clone_to or tempfile.mkdtemp())
        # Create a mock branch
        branch_name = branch or best_practice_id
        if not hasattr(mock_repo.heads, branch_name):
            mock_repo.create_head(branch_name)
        mock_repo.head.reference = getattr(mock_repo.heads, branch_name)
        logging.info(f"TEST MODE: Successfully applied best practice {best_practice_id} to mock repository")
        return mock_repo

    # Fetch best practices information
    practices = fetch_best_practices(SLIM_REGISTRY_URI)
    if not practices:
        print("No practices found or failed to fetch practices.")
        return None

    # Create a best practices manager to handle the practice
    manager = BestPracticeManager(practices)

    # Get the best practice
    practice = manager.get_best_practice(best_practice_id)
    if not practice:
        logging.warning(f"Best practice with ID {best_practice_id} is not supported or not found.")
        return None

    # Determine the repository path
    repo_path = existing_repo_dir
    if repo_url:
        parsed_url = urllib.parse.urlparse(repo_url)
        repo_name = os.path.basename(parsed_url.path)
        repo_name = repo_name[:-4] if repo_name.endswith('.git') else repo_name  # Remove '.git' from repo name if present

        if target_dir_to_clone_to:
            # If target_dir_to_clone_to is specified, append repo name
            repo_path = os.path.join(target_dir_to_clone_to, repo_name)
            logging.debug(f"Set clone directory to {repo_path}")
        else:
            # Create a temporary directory
            repo_path = tempfile.mkdtemp(prefix=f"{repo_name}_" + str(uuid.uuid4()) + '_')
            logging.debug(f"Generating temporary clone directory at {repo_path}")

    # Apply the best practice
    return practice.apply(
        repo_path=repo_path,
        use_ai=use_ai_flag,
        model=model,
        repo_url=repo_url,
        target_dir_to_clone_to=target_dir_to_clone_to,
        branch=branch,
        no_prompt=no_prompt,
        **kwargs
    )