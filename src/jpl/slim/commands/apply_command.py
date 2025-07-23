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
from rich.progress import Progress, SpinnerColumn, TextColumn
import git


from jpl.slim.utils.io_utils import (
    fetch_best_practices,
    repo_file_to_list
)
from jpl.slim.utils.git_utils import generate_git_branch_name, create_repo_temp_dir
from jpl.slim.manager.best_practices_manager import BestPracticeManager
from jpl.slim.commands.common import (
    SLIM_REGISTRY_URI,
    GIT_BRANCH_NAME_FOR_MULTIPLE_COMMITS,
    get_ai_model_pairs
)
from jpl.slim.app import app, state, handle_dry_run_for_command
from jpl.slim.utils.cli_utils import managed_progress

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
        "--repo-urls", "-r",
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
    ),
    logging_level: str = typer.Option(
        None,
        "--logging", "-l",
        help="Set the logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
):
    """
    Apply best practices to git repositories.
    
    This command applies one or more best practices to specified repositories,
    optionally using AI to customize the content.
    """
    # Configure logging
    from jpl.slim.commands.common import configure_logging
    configure_logging(logging_level, state)
    
    logging.debug("Starting apply command execution")
    logging.debug(f"Best practice IDs: {best_practice_ids}")
    logging.debug(f"Use AI: {use_ai}")
    
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
        
        # Apply each best practice with simple spinner
        for best_practice_id in best_practice_ids:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                with managed_progress(progress):
                    task = progress.add_task(f"Applying {best_practice_id}...", total=None)
                    
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
                    
                    progress.update(task, description=f"Completed {best_practice_id}")
    else:
        # Apply to repo URLs with simple spinners
        for repo_url in repo_urls:
            if len(best_practice_ids) > 1:
                if repo_url:
                    logging.debug(f"Using repository URL {repo_url} for group of best_practice_ids {best_practice_ids}")

                    parsed_url = urllib.parse.urlparse(repo_url)
                    repo_name = os.path.basename(parsed_url.path)
                    repo_name = repo_name[:-4] if repo_name.endswith('.git') else repo_name  # Remove '.git' from repo name if present
                    if target_dir_to_clone_to:
                        for best_practice_id in best_practice_ids:
                            with Progress(
                                SpinnerColumn(),
                                TextColumn("[progress.description]{task.description}"),
                                console=console,
                                transient=True
                            ) as progress:
                                with managed_progress(progress):
                                    task = progress.add_task(f"Applying {best_practice_id} to {repo_url}...", total=None)
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
                                    progress.update(task, description=f"Completed {best_practice_id}")
                    else:  # else make a temporary directory
                        repo_dir = create_repo_temp_dir(repo_name)
                        logging.debug(f"Generating temporary clone directory for group of best_practice_ids at {repo_dir}")
                        for best_practice_id in best_practice_ids:
                            with Progress(
                                SpinnerColumn(),
                                TextColumn("[progress.description]{task.description}"),
                                console=console,
                                transient=True
                            ) as progress:
                                with managed_progress(progress):
                                    task = progress.add_task(f"Applying {best_practice_id} to {repo_url}...", total=None)
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
                                    if result is None:
                                        return False
                                    progress.update(task, description=f"Completed {best_practice_id}")
                else:
                    for best_practice_id in best_practice_ids:
                        with Progress(
                            SpinnerColumn(),
                            TextColumn("[progress.description]{task.description}"),
                            console=console,
                            transient=True
                        ) as progress:
                            with managed_progress(progress):
                                task = progress.add_task(f"Applying {best_practice_id}...", total=None)
                                result = apply_best_practice(
                                    best_practice_id=best_practice_id,
                                    use_ai_flag=use_ai_flag,
                                    model=model,
                                    existing_repo_dir=existing_repo_dir,
                                    no_prompt=no_prompt,
                                    **kwargs
                                )
                                if result is None:
                                    return False
                                progress.update(task, description=f"Completed {best_practice_id}")
            elif len(best_practice_ids) == 1:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                    transient=True
                ) as progress:
                    with managed_progress(progress):
                        task = progress.add_task(f"Applying {best_practice_ids[0]} to {repo_url}...", total=None)
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
                        if result is None:
                            return False
                        progress.update(task, description=f"Completed {best_practice_ids[0]}")
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


    # Fetch best practices information
    practices = fetch_best_practices(SLIM_REGISTRY_URI)
    if not practices:
        console.print("[red]No practices found or failed to fetch practices.[/red]")
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
            repo_path = create_repo_temp_dir(repo_name)
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
