"""
Apply command module for the SLIM CLI.

This module contains the implementation of the 'apply' subcommand,
which applies best practices to repositories.
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
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
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
    GIT_BRANCH_NAME_FOR_MULTIPLE_COMMITS,
    SUPPORTED_MODELS,
    get_ai_model_pairs
)
from jpl.slim.app import app, state, handle_dry_run_for_command

console = Console()

@app.command()
def apply(
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
        help=f"Automatically customize the application of the best practice with an AI model. Support for: {get_ai_model_pairs(SUPPORTED_MODELS)}"
    ),
    no_prompt: bool = typer.Option(
        False,
        "--no-prompt",
        help="Skip user confirmation prompts when installing dependencies"
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        help="Output directory for generated documentation (required for docs-website)"
    ),
    template_only: bool = typer.Option(
        False,
        "--template-only",
        help="Generate only the documentation template without analyzing a repository (for docs-website)"
    ),
    revise_site: bool = typer.Option(
        False,
        "--revise-site",
        help="Revise an existing documentation site (for docs-website)"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run", "-d",
        help="Show what would be executed without making changes"
    )
):
    """
    Apply best practices to git repositories.
    
    This command applies one or more best practices to specified repositories,
    optionally using AI to customize the content.
    """
    # Handle dry-run mode (check both global state and local parameter)
    if state.dry_run or dry_run:
        if handle_dry_run_for_command(
            "apply", 
            best_practice_ids=best_practice_ids,
            repo_urls=repo_urls,
            repo_urls_file=str(repo_urls_file) if repo_urls_file else None,
            repo_dir=str(repo_dir) if repo_dir else None,
            clone_to_dir=str(clone_to_dir) if clone_to_dir else None,
            use_ai=use_ai,
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
    
    # Apply best practices with timing
    start_time = time.time()
    try:
        success = apply_best_practices(
            best_practice_ids=best_practice_ids,
            use_ai_flag=bool(use_ai),
            model=use_ai,
            repo_urls=urls_from_file if urls_from_file else repo_urls,
            existing_repo_dir=repo_dir_str,
            target_dir_to_clone_to=clone_to_dir_str,
            no_prompt=no_prompt,
            output_dir=output_dir_str,
            template_only=template_only,
            revise_site=revise_site
        )
        if success:
            end_time = time.time()
            duration = end_time - start_time
            console.print(f"\n✅ [green]Apply operation completed in {duration:.2f} seconds[/green]")
        else:
            raise typer.Exit(1)
    except Exception as e:
        console = Console()
        console.print(f"❌ [red]Error applying best practices: {str(e)}[/red]")
        raise typer.Exit(1)

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
        **kwargs: Additional arguments (output_dir, template_only, revise_site, etc.)
    """
    # Handle special case for docs-website best practice
    if len(best_practice_ids) == 1 and best_practice_ids[0] == "docs-website":
        result = apply_best_practice(
            best_practice_id=best_practice_ids[0],
            use_ai_flag=use_ai_flag,
            model=model,
            repo_url=repo_urls[0] if repo_urls else None,
            existing_repo_dir=existing_repo_dir,
            target_dir_to_clone_to=target_dir_to_clone_to,
            no_prompt=no_prompt,
            **kwargs
        )
        return result is not None

    # Handle normal case for other best practices
    if existing_repo_dir:
        branch = GIT_BRANCH_NAME_FOR_MULTIPLE_COMMITS if len(best_practice_ids) > 1 else best_practice_ids[0]
        for best_practice_id in best_practice_ids:
            result = apply_best_practice(
                best_practice_id=best_practice_id,
                use_ai_flag=use_ai_flag,
                model=model,
                existing_repo_dir=existing_repo_dir,
                branch=branch,
                no_prompt=no_prompt,
                **kwargs
            )
            if result is None:
                return False
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
                            result = apply_best_practice(
                                best_practice_id=best_practice_id,
                                use_ai_flag=use_ai_flag,
                                model=model,
                                repo_url=repo_url,
                                target_dir_to_clone_to=target_dir_to_clone_to,
                                branch=GIT_BRANCH_NAME_FOR_MULTIPLE_COMMITS,
                                no_prompt=no_prompt,
                                **kwargs
                            )
                            if result is None:
                                return False
                    else:  # else make a temporary directory
                        repo_dir = tempfile.mkdtemp(prefix=f"{repo_name}_" + str(uuid.uuid4()) + '_')
                        logging.debug(f"Generating temporary clone directory for group of best_practice_ids at {repo_dir}")
                        for best_practice_id in best_practice_ids:
                            result = apply_best_practice(
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
                        result = apply_best_practice(
                            best_practice_id=best_practice_id,
                            use_ai_flag=use_ai_flag,
                            model=model,
                            existing_repo_dir=existing_repo_dir,
                            no_prompt=no_prompt,
                            **kwargs
                        )
            elif len(best_practice_ids) == 1:
                result = apply_best_practice(
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
                return False
    
    # Return True if we get here (successful execution)
    return True

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

    # Use progress indicator for the apply operation
    with Progress(
        SpinnerColumn() if use_ai_flag else BarColumn(),
        TextColumn("[progress.description]{task.description}"),
        TaskProgressColumn() if not use_ai_flag else TextColumn(""),
        console=console,
        transient=True
    ) as progress:
        # Initialize progress task
        if use_ai_flag:
            task = progress.add_task(f"Applying {best_practice_id} with AI...", total=None)
        else:
            task = progress.add_task(f"Applying {best_practice_id}...", total=100)
            progress.update(task, completed=10)

        # Fetch best practices information
        progress.update(task, description=f"Fetching registry for {best_practice_id}...")
        practices = fetch_best_practices(SLIM_REGISTRY_URI)
        if not practices:
            console.print("[red]No practices found or failed to fetch practices.[/red]")
            return None
        
        if not use_ai_flag:
            progress.update(task, completed=20)

        # Create a best practices manager to handle the practice
        progress.update(task, description=f"Loading best practice {best_practice_id}...")
        manager = BestPracticeManager(practices)

        # Get the best practice
        practice = manager.get_best_practice(best_practice_id)
        if not practice:
            logging.warning(f"Best practice with ID {best_practice_id} is not supported or not found.")
            return None
        
        if not use_ai_flag:
            progress.update(task, completed=30)

        # Determine the repository path
        progress.update(task, description=f"Preparing repository for {best_practice_id}...")
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
        
        if not use_ai_flag:
            progress.update(task, completed=50)

        # Apply the best practice
        if use_ai_flag:
            progress.update(task, description=f"Analyzing repository with AI for {best_practice_id}...")
        else:
            progress.update(task, description=f"Executing {best_practice_id} application...")
            progress.update(task, completed=70)

        result = practice.apply(
            repo_path=repo_path,
            use_ai=use_ai_flag,
            model=model,
            repo_url=repo_url,
            target_dir_to_clone_to=target_dir_to_clone_to,
            branch=branch,
            no_prompt=no_prompt,
            **kwargs
        )
        
        if not use_ai_flag:
            progress.update(task, completed=100)
        
        if use_ai_flag:
            progress.update(task, description=f"Completed {best_practice_id} with AI assistance")
        
        return result
