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
    parser.add_argument('--best-practice-ids', nargs='+', required=True, help='Best practice IDs to apply')
    parser.add_argument('--repo-urls', nargs='+', required=False, help='Repository URLs to apply to. Do not use if --repo-dir specified')
    parser.add_argument('--repo-urls-file', required=False, help='Path to a file containing repository URLs')
    parser.add_argument('--repo-dir', required=False, help='Repository directory location on local machine. Only one repository supported')
    parser.add_argument('--clone-to-dir', required=False, help='Local path to clone repository to. Compatible with --repo-urls')
    parser.add_argument('--use-ai', metavar='MODEL', help=f'Automatically customize the application of the best practice with the specified AI model. Support for: {{get_ai_model_pairs(SUPPORTED_MODELS)}}')
    parser.add_argument('--remote', required=False, default=None, help=f"Push to a specified remote. If not specified, pushes to 'origin'. Format should be a GitHub-like URL base. For example `https://github.com/my_github_user`")
    parser.add_argument('--commit-message', required=False, default=GIT_DEFAULT_COMMIT_MESSAGE, help=f"Commit message to use for the deployment. Default '{GIT_DEFAULT_COMMIT_MESSAGE}")
    parser.set_defaults(func=handle_command)
    return parser

def handle_command(args):
    """
    Handle the 'apply-deploy' command.
    
    Args:
        args: Arguments from argparse
    """
    apply_and_deploy_best_practices(
        best_practice_ids=args.best_practice_ids,
        use_ai_flag=bool(args.use_ai),
        model=args.use_ai if args.use_ai else None,
        remote=args.remote,
        commit_message=args.commit_message,
        repo_urls=repo_file_to_list(args.repo_urls_file) if args.repo_urls_file else args.repo_urls,
        existing_repo_dir=args.repo_dir,
        target_dir_to_clone_to=args.clone_to_dir
    )

def apply_and_deploy_best_practices(best_practice_ids, use_ai_flag, model, remote=None, commit_message=GIT_DEFAULT_COMMIT_MESSAGE, repo_urls=None, existing_repo_dir=None, target_dir_to_clone_to=None):
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
    """
    branch_name = generate_git_branch_name(best_practice_ids)

    for repo_url in repo_urls:
        git_repo = None  # Ensure git_repo is reset for each iteration
        if len(best_practice_ids) > 1:
            if repo_url:
                parsed_url = urllib.parse.urlparse(repo_url)
                repo_name = os.path.basename(parsed_url.path)
                repo_name = repo_name[:-4] if repo_name.endswith('.git') else repo_name  # Remove '.git' from repo name if present
                if target_dir_to_clone_to:
                    for best_practice_id in best_practice_ids:
                        git_repo = apply_best_practice(
                            best_practice_id=best_practice_id, 
                            use_ai_flag=use_ai_flag, 
                            model=model,
                            repo_url=repo_url, 
                            target_dir_to_clone_to=target_dir_to_clone_to, 
                            branch=branch_name)
                    
                    # deploy just the last best practice, which deploys others as well
                    if git_repo:
                        deploy_best_practice(
                            best_practice_id=best_practice_id,
                            repo_dir=git_repo.working_tree_dir,
                            remote=remote,
                            commit_message=commit_message,
                            branch=branch_name)
                    else:
                        logging.error(f"Unable to deploy best practice '{best_practice_id}' because apply failed.")
                else: # else make a temporary directory
                    repo_dir = tempfile.mkdtemp(prefix=f"{repo_name}_" + str(uuid.uuid4()) + '_')
                    logging.debug(f"Generating temporary clone directory for group of best_practice_ids at {repo_dir}")
                    for best_practice_id in best_practice_ids:
                        git_repo = apply_best_practice(
                            best_practice_id=best_practice_id, 
                            use_ai_flag=use_ai_flag, 
                            model=model,
                            repo_url=repo_url, 
                            target_dir_to_clone_to=repo_dir, 
                            branch=branch_name)
                        
                    # deploy just the last best practice, which deploys others as well    
                    if git_repo:
                        deploy_best_practice(
                            best_practice_id=best_practice_id,
                            repo_dir=git_repo.working_tree_dir,
                            remote=remote,
                            commit_message=commit_message,
                            branch=branch_name)
                    else:
                        logging.error(f"Unable to deploy best practice '{best_practice_id}' because apply failed.")
            else:
                for best_practice_id in best_practice_ids:
                    git_repo = apply_best_practice(best_practice_id=best_practice_id, use_ai_flag=use_ai_flag, model=model, existing_repo_dir=existing_repo_dir)
                
                # deploy just the last best practice, which deploys others as well
                if git_repo:
                    deploy_best_practice(
                        best_practice_id=best_practice_id,
                        repo_dir=git_repo.working_tree_dir,
                        remote=remote,
                        commit_message=commit_message,
                        branch=branch_name)
                else:
                    logging.error(f"Unable to deploy best practice '{best_practice_id}' because apply failed.")
        elif len(best_practice_ids) == 1:
            git_repo = apply_best_practice(
                best_practice_id=best_practice_ids[0], 
                use_ai_flag=use_ai_flag, 
                model=model,
                repo_url=repo_url, 
                existing_repo_dir=existing_repo_dir, 
                target_dir_to_clone_to=target_dir_to_clone_to)
            
            # deploy just the last best practice, which deploys others as well
            if git_repo:
                deploy_best_practice(
                    best_practice_id=best_practice_ids[0],
                    repo_dir=git_repo.working_tree_dir,
                    remote=remote,
                    commit_message=commit_message,
                    branch=branch_name)
            else:
                logging.error(f"Unable to deploy best practice '{best_practice_ids[0]}' because apply failed.")
        else:
            logging.error(f"No best practice IDs specified.")

def apply_and_deploy_best_practice(best_practice_id, use_ai_flag, model, remote=None, commit_message=GIT_DEFAULT_COMMIT_MESSAGE, repo_url=None, existing_repo_dir=None, target_dir_to_clone_to=None, branch=None):
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
        
    Returns:
        bool: True if application and deployment were successful, False otherwise
    """
    logging.debug("AI customization enabled for applying and deploying best practices" if use_ai_flag else "AI customization disabled")
    logging.debug(f"Applying and deploying best practice ID: {best_practice_id}")

    # Apply the best practice
    git_repo = apply_best_practice(best_practice_id=best_practice_id, use_ai_flag=use_ai_flag, model=model, repo_url=repo_url, existing_repo_dir=existing_repo_dir, target_dir_to_clone_to=target_dir_to_clone_to, branch=branch)
    
    # Deploy the best practice if applied successfully 
    if git_repo:
        result = deploy_best_practice(best_practice_id=best_practice_id, repo_dir=git_repo.working_tree_dir, remote=remote, commit_message=commit_message, branch=branch)
        if result:
            logging.info(f"Successfully applied and deployed best practice ID: {best_practice_id}")
            return True
        else:
            logging.error(f"Unable to deploy best practice ID: {best_practice_id}")
            return False
    else:
        logging.error(f"Unable to apply and deploy best practice ID: {best_practice_id}")
        return False
