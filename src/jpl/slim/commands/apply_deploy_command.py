"""
Apply-Deploy command module for the SLIM CLI.

This module contains the implementation of the 'apply-deploy' subcommand,
which applies and deploys best practices to repositories.
"""

import logging
import os
import tempfile
import urllib.parse
import uuid
import git

from jpl.slim.utils.io_utils import repo_file_to_list
from jpl.slim.utils.git_utils import generate_git_branch_name
from jpl.slim.commands.apply_command import apply_best_practice
from jpl.slim.commands.deploy_command import deploy_best_practice
from jpl.slim.commands.common import (
    GIT_BRANCH_NAME_FOR_MULTIPLE_COMMITS,
    GIT_DEFAULT_COMMIT_MESSAGE
)

# Log message constants
LOG_APPLY_FAILED = "Failed to apply best practice '{}'"
LOG_DEPLOY_FAILED_MULTIPLE = "Unable to deploy best practices because one or more apply steps failed."
LOG_DEPLOY_FAILED_SINGLE = "Unable to deploy best practice '{}' because apply failed."
LOG_NO_BEST_PRACTICE_IDS = "No best practice IDs specified."
LOG_SUCCESS_APPLY_DEPLOY = "Successfully applied and deployed best practice ID: {}"
LOG_UNABLE_TO_APPLY_DEPLOY = "Unable to apply and deploy best practice ID: {}"
LOG_UNABLE_TO_DEPLOY = "Unable to deploy best practice ID: {}"

def setup_parser(subparsers):
    """
    Set up the parser for the 'apply-deploy' command.

    Args:
        subparsers: Subparsers object from argparse

    Returns:
        The parser for the 'apply-deploy' command
    """
    from jpl.slim.commands.common import SUPPORTED_MODELS, get_ai_model_pairs

    parser = subparsers.add_parser('apply-deploy', help='Applies and deploys a best practice')
    parser.add_argument('--best-practices', nargs='+', required=True, help='Best practice aliases to apply (e.g., readme, governance-small, secrets-github)')
    parser.add_argument('--repo-urls', nargs='+', required=False, help='Repository URLs to apply to. Do not use if --repo-dir specified')
    parser.add_argument('--repo-urls-file', required=False, help='Path to a file containing repository URLs')
    parser.add_argument('--repo-dir', required=False, help='Repository directory location on local machine. Only one repository supported')
    parser.add_argument('--clone-to-dir', required=False, help='Local path to clone repository to. Compatible with --repo-urls')
    parser.add_argument('--use-ai', metavar='MODEL', help=f'Automatically customize the application of the best practice with the specified AI model. Support for: {get_ai_model_pairs(SUPPORTED_MODELS)}')
    parser.add_argument('--remote', required=False, default=None, help=f"Push to a specified remote. If not specified, pushes to 'origin'. Format should be a GitHub-like URL base. For example `https://github.com/my_github_user`")
    parser.add_argument('--commit-message', required=False, default=GIT_DEFAULT_COMMIT_MESSAGE, help=f"Commit message to use for the deployment. Default '{GIT_DEFAULT_COMMIT_MESSAGE}")
    parser.add_argument('--no-prompt', action='store_true', help='Skip user confirmation prompts when installing dependencies')
    
    # Doc-gen specific arguments
    parser.add_argument('--output-dir', required=False, help='Output directory for generated documentation (required for doc-gen)')
    parser.add_argument('--template-only', action='store_true', help='Generate only the documentation template without analyzing a repository (for doc-gen)')
    parser.add_argument('--revise-site', action='store_true', help='Revise an existing documentation site (for doc-gen)')
    
    parser.set_defaults(func=handle_command)
    return parser

def handle_command(args):
    """
    Handle the 'apply-deploy' command.
    
    Note: This function now receives only command-specific arguments.
    CLI-level arguments are handled at the CLI level.

    Args:
        args: Command-specific arguments from argparse
    """
    # Clean argument extraction - no more brittle popping!
    apply_and_deploy_best_practices(
        best_practice_ids=args.best_practices,
        use_ai_flag=bool(args.use_ai),
        model=args.use_ai if args.use_ai else None,
        remote=args.remote,
        commit_message=args.commit_message,
        repo_urls=repo_file_to_list(args.repo_urls_file) if args.repo_urls_file else args.repo_urls,
        existing_repo_dir=args.repo_dir,
        target_dir_to_clone_to=args.clone_to_dir,
        no_prompt=args.no_prompt,
        # Doc-gen specific arguments
        output_dir=getattr(args, 'output_dir', None),
        template_only=getattr(args, 'template_only', False),
        revise_site=getattr(args, 'revise_site', False)
    )

def _apply_multiple_best_practices(best_practice_ids, use_ai_flag, model, remote=None, 
                                 commit_message=GIT_DEFAULT_COMMIT_MESSAGE, repo_url=None, 
                                 existing_repo_dir=None, target_dir_to_clone_to=None, 
                                 branch_name=None, no_prompt=False, **kwargs):
    """
    Apply multiple best practices to a repository and deploy them.
    
    Args:
        best_practice_ids (list): List of best practice IDs to apply
        use_ai_flag (bool): Whether to use AI to customize the best practices
        model (str): AI model to use if use_ai_flag is True
        remote (str, optional): Remote repository to push to. Defaults to None.
        commit_message (str, optional): Commit message to use. Defaults to GIT_DEFAULT_COMMIT_MESSAGE.
        repo_url (str, optional): Repository URL to apply to. Defaults to None.
        existing_repo_dir (str, optional): Existing repository directory to apply to. Defaults to None.
        target_dir_to_clone_to (str, optional): Directory to clone repository to. Defaults to None.
        branch_name (str, optional): Git branch to use. Defaults to None.
        no_prompt (bool, optional): Skip user confirmation prompts. Defaults to False.
        **kwargs: Additional arguments for doc-gen and other features
        
    Returns:
        bool: True if all best practices were successfully applied and deployed, False otherwise
    """
    # Track whether all applies succeeded
    all_applies_successful = True
    repos_results = []

    for best_practice_id in best_practice_ids:
        git_repo = apply_best_practice(
            best_practice_id=best_practice_id,
            use_ai_flag=use_ai_flag,
            model=model,
            repo_url=repo_url,
            existing_repo_dir=existing_repo_dir,
            target_dir_to_clone_to=target_dir_to_clone_to,
            branch=branch_name,
            no_prompt=no_prompt,
            **kwargs
        )

        # Keep track of the result and repo
        if git_repo:
            repos_results.append(git_repo)
        else:
            all_applies_successful = False
            logging.error(LOG_APPLY_FAILED.format(best_practice_id))
            break  # Stop processing best practices if one fails

    # Deploy only if all best practices were successfully applied
    if all_applies_successful and repos_results:
        last_repo = repos_results[-1]  # Use the last repo for deployment
        deployed = deploy_best_practice(
            best_practice_id=best_practice_ids[-1],  # Use the last best practice ID
            repo_dir=last_repo.working_tree_dir,
            remote=remote,
            commit_message=commit_message,
            branch=branch_name
        )
        return deployed
    else:
        logging.error(LOG_DEPLOY_FAILED_MULTIPLE)
        return False

def apply_and_deploy_best_practices(best_practice_ids, use_ai_flag, model, remote=None, commit_message=GIT_DEFAULT_COMMIT_MESSAGE,
                                    repo_urls=None, existing_repo_dir=None, target_dir_to_clone_to=None, no_prompt=False, **kwargs):
    """
    Apply and deploy best practices to repositories.

    Args:
        best_practice_ids: List of best practice IDs to apply and deploy
        use_ai_flag: Whether to use AI to customize the best practices
        model: AI model to use if use_ai_flag is True
        remote: Remote repository to push to
        commit_message: Commit message to use
        repo_urls: List of repository URLs to apply to
        existing_repo_dir: Existing repository directory to apply to
        target_dir_to_clone_to: Directory to clone repositories to
        no_prompt: Skip user confirmation prompts for dependencies installation
        **kwargs: Additional arguments for doc-gen and other features
    """
    branch_name = generate_git_branch_name(best_practice_ids)

    if existing_repo_dir:
        # Apply to existing repo directory
        if len(best_practice_ids) > 1:
            # For multiple best practices
            _apply_multiple_best_practices(
                best_practice_ids=best_practice_ids,
                use_ai_flag=use_ai_flag,
                model=model,
                remote=remote,
                commit_message=commit_message,
                existing_repo_dir=existing_repo_dir,
                branch_name=branch_name,
                no_prompt=no_prompt,
                **kwargs
            )
        elif len(best_practice_ids) == 1:
            # For a single best practice
            apply_and_deploy_best_practice(
                best_practice_id=best_practice_ids[0],
                use_ai_flag=use_ai_flag,
                model=model,
                remote=remote,
                commit_message=commit_message,
                existing_repo_dir=existing_repo_dir,
                branch=branch_name,
                no_prompt=no_prompt,
                **kwargs
            )
        else:
            logging.error(LOG_NO_BEST_PRACTICE_IDS)

    # Apply to repo URLs
    elif repo_urls:
        for repo_url in repo_urls:
            if len(best_practice_ids) > 1:
                if repo_url:
                    logging.debug(f"Using repository URL {repo_url} for group of best_practice_ids {best_practice_ids}")

                    parsed_url = urllib.parse.urlparse(repo_url)
                    repo_name = os.path.basename(parsed_url.path)
                    repo_name = repo_name[:-4] if repo_name.endswith('.git') else repo_name  # Remove '.git' from repo name if present

                    if target_dir_to_clone_to:
                        # Apply and deploy with specific target directory
                        _apply_multiple_best_practices(
                            best_practice_ids=best_practice_ids,
                            use_ai_flag=use_ai_flag,
                            model=model,
                            remote=remote,
                            commit_message=commit_message,
                            repo_url=repo_url,
                            target_dir_to_clone_to=target_dir_to_clone_to,
                            branch_name=branch_name,
                            no_prompt=no_prompt,
                            **kwargs
                        )

                    else:  # Make a temporary directory
                        repo_dir = tempfile.mkdtemp(prefix=f"{repo_name}_" + str(uuid.uuid4()) + '_')
                        logging.debug(f"Generating temporary clone directory for group of best_practice_ids at {repo_dir}")
                        
                        # Apply and deploy with temporary directory
                        _apply_multiple_best_practices(
                            best_practice_ids=best_practice_ids,
                            use_ai_flag=use_ai_flag,
                            model=model,
                            remote=remote,
                            commit_message=commit_message,
                            repo_url=repo_url,
                            target_dir_to_clone_to=repo_dir,
                            branch_name=branch_name,
                            no_prompt=no_prompt,
                            **kwargs
                        )

            elif len(best_practice_ids) == 1:
                # For a single best practice
                apply_and_deploy_best_practice(
                    best_practice_id=best_practice_ids[0],
                    use_ai_flag=use_ai_flag,
                    model=model,
                    remote=remote,
                    commit_message=commit_message,
                    repo_url=repo_url,
                    target_dir_to_clone_to=target_dir_to_clone_to,
                    branch=branch_name,
                    no_prompt=no_prompt,
                    **kwargs
                )
            else:
                logging.error(LOG_NO_BEST_PRACTICE_IDS)

def apply_and_deploy_best_practice(best_practice_id, use_ai_flag, model, remote=None, commit_message=GIT_DEFAULT_COMMIT_MESSAGE,
                                   repo_url=None, existing_repo_dir=None, target_dir_to_clone_to=None, branch=None, no_prompt=False, **kwargs):
    """
    Apply and deploy a best practice to a repository.

    Args:
        best_practice_id: Best practice ID to apply and deploy
        use_ai_flag: Whether to use AI to customize the best practice
        model: AI model to use if use_ai_flag is True
        remote: Remote repository to push to
        commit_message: Commit message to use
        repo_url: Repository URL to apply to
        existing_repo_dir: Existing repository directory to apply to
        target_dir_to_clone_to: Directory to clone repository to
        branch: Git branch to use
        no_prompt: Skip user confirmation prompts for dependencies installation
        **kwargs: Additional arguments for doc-gen and other features

    Returns:
        bool: True if application and deployment were successful, False otherwise
    """
    logging.debug("AI customization enabled for applying and deploying best practices" if use_ai_flag else "AI customization disabled")
    logging.debug(f"Applying and deploying best practice ID: {best_practice_id}")

    # Apply the best practice
    git_repo = apply_best_practice(
        best_practice_id=best_practice_id,
        use_ai_flag=use_ai_flag,
        model=model,
        repo_url=repo_url,
        existing_repo_dir=existing_repo_dir,
        target_dir_to_clone_to=target_dir_to_clone_to,
        branch=branch,
        no_prompt=no_prompt,
        **kwargs
    )

    # Deploy the best practice if applied successfully
    if git_repo:
        result = deploy_best_practice(
            best_practice_id=best_practice_id,
            repo_dir=git_repo.working_tree_dir,
            remote=remote,
            commit_message=commit_message,
            branch=branch
        )
        if result:
            logging.info(LOG_SUCCESS_APPLY_DEPLOY.format(best_practice_id))
            return True
        else:
            logging.error(LOG_UNABLE_TO_DEPLOY.format(best_practice_id))
            return False
    else:
        logging.error(LOG_UNABLE_TO_APPLY_DEPLOY.format(best_practice_id))
        return False