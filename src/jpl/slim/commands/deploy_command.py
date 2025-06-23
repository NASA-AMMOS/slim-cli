"""
Deploy command module for the SLIM CLI.

This module contains the implementation of the 'deploy' subcommand,
which deploys best practices to repositories.
"""

import os
import logging
import time
from typing import List, Optional
from pathlib import Path
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
import git

from jpl.slim.utils.git_utils import generate_git_branch_name
from jpl.slim.commands.common import (
    GIT_DEFAULT_REMOTE_NAME,
    GIT_CUSTOM_REMOTE_NAME,
    GIT_DEFAULT_COMMIT_MESSAGE
)
from jpl.slim.app import app, state, handle_dry_run_for_command

console = Console()

@app.command()
def deploy(
    best_practice_ids: List[str] = typer.Option(
        ...,
        "--best-practice-ids", "-b",
        help="Best practice aliases to deploy (e.g., readme, governance-small, secrets-github)"
    ),
    repo_dir: Optional[Path] = typer.Option(
        None,
        "--repo-dir",
        help="Repository directory location on local machine",
        exists=True,
        file_okay=False,
        dir_okay=True
    ),
    remote: Optional[str] = typer.Option(
        None,
        "--remote",
        help=f"Push to a specified remote name. If not specified, pushes to '{GIT_DEFAULT_REMOTE_NAME}'."
    ),
    commit_message: str = typer.Option(
        GIT_DEFAULT_COMMIT_MESSAGE,
        "--commit-message", "-m",
        help=f"Commit message to use for the deployment."
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run", "-d",
        help="Show what would be executed without making changes"
    )
):
    """
    Deploy best practices to a git repository.
    
    This command adds, commits, and pushes best practice files to a git remote.
    """
    # Handle dry-run mode
    if state.dry_run or dry_run:
        if handle_dry_run_for_command(
            "deploy",
            best_practice_ids=best_practice_ids,
            repo_dir=str(repo_dir) if repo_dir else None,
            remote=remote,
            commit_message=commit_message,
            dry_run=True
        ):
            return
    
    # Convert path to string for backward compatibility
    repo_dir_str = str(repo_dir) if repo_dir else None
    
    # Deploy best practices with timing
    start_time = time.time()
    try:
        success = deploy_best_practices(
            best_practice_ids=best_practice_ids,
            repo_dir=repo_dir_str,
            remote=remote,
            commit_message=commit_message
        )
        if success:
            end_time = time.time()
            duration = end_time - start_time
            console.print(f"\n✅ [green]Deploy operation completed in {duration:.2f} seconds[/green]")
        else:
            raise typer.Exit(1)
    except Exception as e:
        console = Console()
        console.print(f"❌ [red]Error deploying best practices: {str(e)}[/red]")
        raise typer.Exit(1)

def deploy_best_practices(best_practice_ids, repo_dir, remote=None, commit_message=GIT_DEFAULT_COMMIT_MESSAGE):
    """
    Deploy best practices to a repository.

    Args:
        best_practice_ids: List of best practice IDs to deploy
        repo_dir: Repository directory to deploy to
        remote: Remote repository to push to
        commit_message: Commit message to use
    """
    # Use shared branch if multiple best_practice_ids else use default branch name
    branch_name = generate_git_branch_name(best_practice_ids)

    with Progress(
        BarColumn(),
        TextColumn("[progress.description]{task.description}"),
        TaskProgressColumn(),
        console=console,
        transient=True
    ) as progress:
        total_practices = len(best_practice_ids)
        task = progress.add_task(f"Deploying {total_practices} best practice(s)...", total=total_practices)
        
        success = True
        for i, best_practice_id in enumerate(best_practice_ids):
            progress.update(task, description=f"Deploying {best_practice_id}...")
            result = deploy_best_practice(
                best_practice_id=best_practice_id,
                repo_dir=repo_dir,
                remote=remote,
                commit_message=commit_message,
                branch=branch_name
            )
            if not result:
                success = False
                break
            progress.update(task, completed=i + 1)
    
    return success

def deploy_best_practice(best_practice_id, repo_dir, remote=None, commit_message='Default commit message', branch=None):
    """
    Deploy a best practice to a repository.

    Args:
        best_practice_id: Best practice ID to deploy
        repo_dir: Repository directory to deploy to
        remote: Remote repository to push to
        commit_message: Commit message to use
        branch: Git branch to use

    Returns:
        bool: True if deployment was successful, False otherwise
    """
    # In test mode, simulate success without making actual changes
    if os.environ.get('SLIM_TEST_MODE', 'False').lower() in ('true', '1', 't'):
        logging.info(f"TEST MODE: Simulating deployment of best practice {best_practice_id}")
        return True

    branch_name = branch if branch else best_practice_id
    logging.debug(f"Deploying branch: {branch_name}")

    with Progress(
        BarColumn(),
        TextColumn("[progress.description]{task.description}"),
        TaskProgressColumn(),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task(f"Deploying {best_practice_id}...", total=100)
        
        try:
            # Assuming repo_dir points to a local git repository directory
            progress.update(task, description=f"Initializing repository for {best_practice_id}...", completed=5)
            repo = git.Repo(repo_dir)

            # Checkout the branch or create it if it doesn't exist
            progress.update(task, description=f"Setting up branch {branch_name}...", completed=15)
            try:
                repo.git.checkout(branch_name)
                logging.debug(f"Checked out to branch {branch_name}")
            except git.exc.GitCommandError:
                # Branch doesn't exist, create it
                logging.debug(f"Branch {branch_name} doesn't exist, creating it")
                repo.git.checkout('-b', branch_name)
                logging.debug(f"Created and checked out branch {branch_name}")

            progress.update(task, completed=25)
            
            # Handle remote setup
            progress.update(task, description=f"Configuring remote for {best_practice_id}...", completed=35)
            if remote:
                # Check if the remote name already exists in the repository
                remote_exists = remote in [r.name for r in repo.remotes]
                if remote_exists:
                    # Use the existing remote with the provided name
                    remote_name = remote
                    logging.debug(f"Using existing remote '{remote_name}'")
                else:
                    # Assume remote is a valid Git URL - use it with the custom remote name
                    remote_name = GIT_CUSTOM_REMOTE_NAME
                    logging.debug(f"Creating new remote '{remote_name}' with URL '{remote}'")
                    
                    # Check if the custom remote name already exists
                    if remote_name in [r.name for r in repo.remotes]:
                        # Update the existing remote's URL
                        repo.git.remote('set-url', remote_name, remote)
                        logging.debug(f"Updated URL for existing remote '{remote_name}'")
                    else:
                        # Create a new remote
                        repo.create_remote(remote_name, remote)
                        logging.debug(f"Created new remote '{remote_name}'")
                
                # Fetch from the remote to ensure we have the latest
                progress.update(task, description=f"Fetching from remote {remote_name}...", completed=45)
                try:
                    repo.git.fetch(remote_name)
                    logging.debug(f"Fetched latest from remote '{remote_name}'")
                except git.exc.GitCommandError as e:
                    logging.warning(f"Failed to fetch from remote '{remote_name}': {str(e)}")
            else:
                # Default to using the 'origin' remote
                remote_name = GIT_DEFAULT_REMOTE_NAME
                progress.update(task, description=f"Fetching from remote {remote_name}...", completed=45)
                try:
                    repo.git.fetch(remote_name)
                    logging.debug(f"Fetched latest from remote '{remote_name}'")
                except git.exc.GitCommandError as e:
                    logging.warning(f"Failed to fetch from remote '{remote_name}': {str(e)}")

            # Check if the branch exists on the remote
            progress.update(task, description=f"Syncing with remote branch {branch_name}...", completed=55)
            try:
                remote_refs = repo.git.ls_remote('--heads', remote_name, branch_name)
                if remote_refs:
                    # Get the last commit on the remote branch
                    remote_commit = remote_refs.split()[0]
                    # Get the last commit on the local branch
                    local_commit = repo.heads[branch_name].commit.hexsha

                    if remote_commit != local_commit:
                        try:
                            # Pull changes from the remote to make sure the local branch is up-to-date
                            repo.git.pull(remote_name, branch_name, '--rebase=false')
                            logging.debug(f"Pulled latest changes for branch {branch_name} from remote {remote_name}")
                        except git.exc.GitCommandError as pull_error:
                            logging.warning(f"Could not pull from remote '{remote_name}': {str(pull_error)}")
                            logging.warning("Continuing with local changes only.")
                    else:
                        logging.debug(f"Local branch {branch_name} is up-to-date with remote {remote_name}. No pull needed.")
                else:
                    logging.info(f"Branch {branch_name} does not exist on remote {remote_name}. No pull performed.")
            except git.exc.GitCommandError as ls_error:
                logging.warning(f"Failed to check if branch exists on remote: {str(ls_error)}")
                logging.warning("Continuing with local changes only.")

            # Add / Commit changes
            progress.update(task, description=f"Staging changes for {best_practice_id}...", completed=70)
            repo.git.add(A=True)  # Adds all untracked files
            logging.debug("Added all changes to git index.")

            progress.update(task, description=f"Committing changes for {best_practice_id}...", completed=80)
            repo.git.commit('-m', commit_message)
            logging.debug("Committed changes.")

            # Push changes to the remote
            progress.update(task, description=f"Pushing {best_practice_id} to remote...", completed=90)
            try:
                repo.git.push(remote_name, branch_name)
                logging.debug(f"Pushed changes to remote {remote_name} on branch {branch_name}")
                logging.info(f"Deployed best practice id '{best_practice_id}' to remote '{remote_name}' on branch '{branch_name}'")
                
                progress.update(task, completed=100)
                
                # Print success message to user
                console.print(f"✅ Successfully deployed best practice '{best_practice_id}' to repository")
                console.print(f"   📁 Repository: {repo.working_dir}")
                console.print(f"   🌿 Branch: {branch_name}")
                console.print(f"   💬 Commit: {commit_message}")
                console.print(f"   🚀 Deployed to: {remote_name}")
                
            except git.exc.GitCommandError as push_error:
                logging.error(f"Failed to push to remote '{remote_name}': {str(push_error)}")
                raise  # Re-raise to be caught by the outer exception handler

            return True
        except git.exc.GitCommandError as e:
            # Initialize remote_name to a default value if it's not defined yet
            if 'remote_name' not in locals():
                remote_name = remote or GIT_DEFAULT_REMOTE_NAME
            logging.error(f"Unable to deploy best practice id '{best_practice_id}' to remote '{remote_name}' on branch '{branch_name}'")
            logging.error(f"Git command failed: {str(e)}")
            logging.error(f"An error occurred: {str(e)}")
            return False