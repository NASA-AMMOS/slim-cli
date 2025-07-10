"""
Apply-Deploy command module for the SLIM CLI.

This module contains the implementation of the 'apply-deploy' subcommand,
which applies and deploys best practices to repositories.
"""

import logging
import os
import tempfile
import time
import urllib.parse
import uuid
from typing import List, Optional
from pathlib import Path
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
import git

from jpl.slim.utils.io_utils import repo_file_to_list
from jpl.slim.utils.git_utils import generate_git_branch_name, create_repo_temp_dir
from jpl.slim.commands.apply_command import apply_best_practice
from jpl.slim.commands.deploy_command import deploy_best_practice
from jpl.slim.commands.common import (
    GIT_BRANCH_NAME_FOR_MULTIPLE_COMMITS,
    GIT_DEFAULT_COMMIT_MESSAGE,
    get_ai_model_pairs
)
from jpl.slim.app import app, state, handle_dry_run_for_command

console = Console()

# Log message constants
LOG_APPLY_FAILED = "Failed to apply best practice '{}'"
LOG_DEPLOY_FAILED_MULTIPLE = "Unable to deploy best practices because one or more apply steps failed."
LOG_DEPLOY_FAILED_SINGLE = "Unable to deploy best practice '{}' because apply failed."
LOG_NO_BEST_PRACTICE_IDS = "No best practice IDs specified."
LOG_SUCCESS_APPLY_DEPLOY = "Successfully applied and deployed best practice ID: {}"
LOG_UNABLE_TO_APPLY_DEPLOY = "Unable to apply and deploy best practice ID: {}"
LOG_UNABLE_TO_DEPLOY = "Unable to deploy best practice ID: {}"

@app.command(name="apply-deploy")
def apply_deploy(
    best_practice_ids: List[str] = typer.Option(
        ...,
        "--best-practice-ids", "-b",
        help="Best practice aliases to apply (e.g., readme, governance-small, secrets-github)"
    ),
    repo_urls: Optional[List[str]] = typer.Option(
        None,
        "--repo-urls",
        help="Repository URLs to apply to. Do not use if --repo-dir specified"
    ),
    repo_urls_file: Optional[Path] = typer.Option(
        None,
        "--repo-urls-file",
        help="Path to a file containing repository URLs",
        exists=True,
        file_okay=True,
        dir_okay=False
    ),
    repo_dir: Optional[Path] = typer.Option(
        None,
        "--repo-dir",
        help="Repository directory location on local machine. Only one repository supported",
        exists=True,
        file_okay=False,
        dir_okay=True
    ),
    clone_to_dir: Optional[Path] = typer.Option(
        None,
        "--clone-to-dir",
        help="Local path to clone repository to. Compatible with --repo-urls"
    ),
    use_ai: Optional[str] = typer.Option(
        None,
        "--use-ai",
        help="Automatically customize the application of the best practice with the specified AI model. Use 'slim models list' to see available models."
    ),
    remote: Optional[str] = typer.Option(
        None,
        "--remote",
        help="Push to a specified remote. If not specified, pushes to 'origin'. Format should be a GitHub-like URL base. For example `https://github.com/my_github_user`"
    ),
    commit_message: str = typer.Option(
        GIT_DEFAULT_COMMIT_MESSAGE,
        "--commit-message", "-m",
        help="Commit message to use for the deployment."
    ),
    no_prompt: bool = typer.Option(
        False,
        "--no-prompt",
        help="Skip user confirmation prompts when installing dependencies"
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        help="Output directory for generated documentation (required for doc-gen)"
    ),
    template_only: bool = typer.Option(
        False,
        "--template-only",
        help="Generate only the documentation template without analyzing a repository (for doc-gen)"
    ),
    revise_site: bool = typer.Option(
        False,
        "--revise-site",
        help="Revise an existing documentation site (for doc-gen)"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run", "-d",
        help="Show what would be executed without making changes"
    ),
    logging_level: str = typer.Option(
        None,
        "--logging", "-l",
        help="Set the logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
):
    """
    Apply and deploy best practices to repositories in one step.
    
    This command combines the functionality of 'apply' and 'deploy',
    applying best practices and then pushing them to a git remote.
    """
    # Configure logging
    from jpl.slim.commands.common import configure_logging
    configure_logging(logging_level, state)
    
    logging.debug("Starting apply-deploy command execution")
    logging.debug(f"Best practice IDs: {best_practice_ids}")
    logging.debug(f"Use AI: {use_ai}")
    
    # Handle dry-run mode
    if state.dry_run or dry_run:
        if handle_dry_run_for_command(
            "apply-deploy",
            best_practice_ids=best_practice_ids,
            repo_urls=repo_urls,
            repo_urls_file=str(repo_urls_file) if repo_urls_file else None,
            repo_dir=str(repo_dir) if repo_dir else None,
            clone_to_dir=str(clone_to_dir) if clone_to_dir else None,
            use_ai=use_ai,
            remote=remote,
            commit_message=commit_message,
            no_prompt=no_prompt,
            output_dir=str(output_dir) if output_dir else None,
            template_only=template_only,
            revise_site=revise_site,
            dry_run=True
        ):
            return
    
    # Convert paths to strings for backward compatibility
    repo_dir_str = str(repo_dir) if repo_dir else None
    clone_to_dir_str = str(clone_to_dir) if clone_to_dir else None
    output_dir_str = str(output_dir) if output_dir else None
    
    # Read URLs from file if provided
    urls_from_file = repo_file_to_list(str(repo_urls_file)) if repo_urls_file else None
    
    # Apply and deploy best practices with timing
    start_time = time.time()
    try:
        apply_and_deploy_best_practices(
            best_practice_ids=best_practice_ids,
            use_ai_flag=bool(use_ai),
            model=use_ai,
            remote=remote,
            commit_message=commit_message,
            repo_urls=urls_from_file if urls_from_file else repo_urls,
            existing_repo_dir=repo_dir_str,
            target_dir_to_clone_to=clone_to_dir_str,
            no_prompt=no_prompt,
            output_dir=output_dir_str,
            template_only=template_only,
            revise_site=revise_site
        )
        end_time = time.time()
        duration = end_time - start_time
        console.print(f"\n✅ [green]Apply-deploy operation completed in {duration:.2f} seconds[/green]")
    except Exception as e:
        console.print(f"❌ [red]Error in apply-deploy operation: {str(e)}[/red]")
        raise typer.Exit(1)

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
                        repo_dir = create_repo_temp_dir(repo_name)
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

    # Apply the best practice with simple spinner
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task(f"Applying {best_practice_id}...", total=None)
        
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
        
        progress.update(task, description=f"Completed applying {best_practice_id}")
    
    # Deploy the best practice if applied successfully
    if git_repo:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task(f"Deploying {best_practice_id}...", total=None)
            
            result = deploy_best_practice(
                best_practice_id=best_practice_id,
                repo_dir=git_repo.working_tree_dir,
                remote=remote,
                commit_message=commit_message,
                branch=branch
            )
            
            progress.update(task, description=f"Completed deploying {best_practice_id}")
        
        if result:
            logging.debug(LOG_SUCCESS_APPLY_DEPLOY.format(best_practice_id))
            
            # Print success message to user  
            console.print(f"✅ Successfully applied and deployed best practice '{best_practice_id}' to repository")
            console.print(f"   📁 Repository: {git_repo.working_dir}")
            console.print(f"   🌿 Branch: {branch if branch else best_practice_id}")
            console.print(f"   💬 Commit: {commit_message}")
            if remote:
                console.print(f"   🚀 Deployed to: {remote}")
            
            return True
        else:
            logging.error(LOG_UNABLE_TO_DEPLOY.format(best_practice_id))
            return False
    else:
        logging.error(LOG_UNABLE_TO_APPLY_DEPLOY.format(best_practice_id))
        return False