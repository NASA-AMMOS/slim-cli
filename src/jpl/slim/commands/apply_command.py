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
        help="Enable AI customization via MCP. Specify 'mcp' to generate AI coordination prompts for MCP clients (Claude Code, Aider, etc.)."
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

def handle_mcp_integration(best_practice_ids, repo_urls=None, existing_repo_dir=None, 
                          target_dir_to_clone_to=None, no_prompt=False, **kwargs):
    """
    Handle MCP integration by generating AI coordination prompts for MCP clients.
    
    Args:
        best_practice_ids: List of best practice IDs to apply
        repo_urls: List of repository URLs to apply to
        existing_repo_dir: Existing repository directory to apply to
        target_dir_to_clone_to: Directory to clone repositories to
        no_prompt: Skip user confirmation prompts
        **kwargs: Additional arguments (output_dir, template_only, revise_site, etc.)
    
    Returns:
        bool: True if coordination prompts generated successfully
    """
    console.print("🚀 [green]Generating MCP AI coordination prompts...[/green]")
    
    # Determine repository context
    repo_context = existing_repo_dir or "."
    if repo_urls:
        repo_context = repo_urls[0] if len(repo_urls) == 1 else f"{len(repo_urls)} repositories"
    
    # Generate coordination prompts for each best practice
    coordination_prompts = []
    for practice_id in best_practice_ids:
        prompts = generate_practice_coordination_prompts(
            practice_id=practice_id,
            repo_context=repo_context,
            existing_repo_dir=existing_repo_dir,
            repo_urls=repo_urls,
            target_dir_to_clone_to=target_dir_to_clone_to,
            **kwargs
        )
        coordination_prompts.extend(prompts)
    
    # Display coordination prompts for MCP clients
    console.print("\n📋 [bold blue]AI Coordination Prompts for MCP Clients:[/bold blue]")
    console.print("Copy these prompts to your MCP-enabled AI client (Claude Code, Aider, etc.):\n")
    
    for i, prompt in enumerate(coordination_prompts, 1):
        console.print(f"[bold cyan]Step {i}:[/bold cyan] {prompt['title']}")
        console.print(f"[dim]{prompt['description']}[/dim]")
        console.print(f"[green]Prompt:[/green] {prompt['prompt']}\n")
    
    # Generate summary
    console.print(f"✅ [green]Generated {len(coordination_prompts)} coordination prompts for {len(best_practice_ids)} best practices[/green]")
    console.print("💡 [blue]These prompts will guide your MCP-enabled AI client through the complete SLIM workflow[/blue]")
    
    return True

def generate_practice_coordination_prompts(practice_id, repo_context, existing_repo_dir=None, 
                                         repo_urls=None, target_dir_to_clone_to=None, **kwargs):
    """
    Generate AI coordination prompts for a specific SLIM best practice.
    
    Args:
        practice_id: Best practice ID to generate prompts for
        repo_context: Context about the target repository
        existing_repo_dir: Existing repository directory
        repo_urls: Repository URLs 
        target_dir_to_clone_to: Directory to clone to
        **kwargs: Additional practice-specific arguments
    
    Returns:
        List[Dict]: List of coordination prompts
    """
    prompts = []
    
    # Base repository analysis prompt
    repo_analysis_prompt = f"Using SLIM MCP tools, analyze the repository context for applying the '{practice_id}' best practice. "
    if existing_repo_dir:
        repo_analysis_prompt += f"Repository location: {existing_repo_dir}. "
    elif repo_urls:
        repo_analysis_prompt += f"Repository URL(s): {', '.join(repo_urls)}. "
    repo_analysis_prompt += "Use slim_analyze_repository_context_tool to gather project-specific context for customization."
    
    prompts.append({
        "title": f"Analyze Repository for {practice_id}",
        "description": f"Gather repository context and project information for {practice_id} customization",
        "prompt": repo_analysis_prompt
    })
    
    # Practice-specific coordination prompts
    if practice_id in ["governance", "governance-small", "governance-medium"]:
        prompts.append({
            "title": f"Git Committer Analysis for {practice_id}",
            "description": "Analyze Git commit history to identify project committers and maintainers",
            "prompt": f"Use SLIM MCP tools to analyze Git commit history in the repository. Extract real committer data including names, email domains, and contribution patterns. This data will be used to populate the {practice_id} template with actual project maintainers."
        })
    
    elif practice_id == "docs-website":
        prompts.extend([
            {
                "title": "DocuSaurus Website Template Generation",
                "description": "Generate base DocuSaurus website structure",
                "prompt": f"Use SLIM MCP tools to generate the DocuSaurus website template for the repository. Set output_dir parameter if specified: {kwargs.get('output_dir', 'docs')}. Use template_only={kwargs.get('template_only', False)} mode."
            },
            {
                "title": "Content Population and Validation", 
                "description": "Populate website content and validate structure",
                "prompt": "Use SLIM MCP tools to populate the DocuSaurus website with repository-specific content. Validate the generated structure and ensure all links and navigation work correctly."
            }
        ])
    
    # Core application prompt
    application_prompt = f"Use SLIM MCP tools to apply the '{practice_id}' best practice. "
    if existing_repo_dir:
        application_prompt += f"Apply to repository at: {existing_repo_dir}. "
    elif repo_urls:
        application_prompt += f"Apply to repository URL(s): {', '.join(repo_urls)}. "
        if target_dir_to_clone_to:
            application_prompt += f"Clone to: {target_dir_to_clone_to}. "
    
    # Add practice-specific parameters
    if kwargs.get('output_dir'):
        application_prompt += f"Use output directory: {kwargs['output_dir']}. "
    if kwargs.get('template_only'):
        application_prompt += "Use template-only mode. "
    if kwargs.get('revise_site'):
        application_prompt += "Revise existing site. "
    
    application_prompt += "Use AI customization based on the repository analysis from previous steps."
    
    prompts.append({
        "title": f"Apply {practice_id} with AI Customization",
        "description": f"Apply the {practice_id} template with AI-generated customizations",
        "prompt": application_prompt
    })
    
    # Validation and deployment prompt
    prompts.append({
        "title": f"Validate and Deploy {practice_id}",
        "description": "Validate the applied changes and optionally deploy to Git",
        "prompt": f"Use SLIM MCP tools to validate the applied {practice_id} changes. Review generated files for accuracy and completeness. If everything looks good, optionally use slim_deploy_tool to commit and push changes to the repository."
    })
    
    return prompts

def apply_best_practices(best_practice_ids, use_ai_flag, model, repo_urls=None, existing_repo_dir=None, 
                         target_dir_to_clone_to=None, no_prompt=False, **kwargs):
    """
    Apply best practices to repositories.

    Args:
        best_practice_ids: List of best practice IDs to apply
        use_ai_flag: [DEPRECATED] Legacy AI flag - functionality disabled
        model: [DEPRECATED] Legacy AI model parameter - functionality disabled
        repo_urls: List of repository URLs to apply to
        existing_repo_dir: Existing repository directory to apply to
        target_dir_to_clone_to: Directory to clone repositories to
        no_prompt: Skip user confirmation prompts for dependencies installation
        **kwargs: Additional arguments (output_dir, template_only, revise_site, etc.)
    """
    
    # Handle MCP integration for --use-ai flag
    if use_ai_flag and model == "mcp":
        return handle_mcp_integration(
            best_practice_ids=best_practice_ids,
            repo_urls=repo_urls,
            existing_repo_dir=existing_repo_dir,
            target_dir_to_clone_to=target_dir_to_clone_to,
            no_prompt=no_prompt,
            **kwargs
        )
    
    # Disable legacy AI functionality to avoid conflicts with MCP
    if use_ai_flag and model and model != "none" and model != "mcp":
        console.print("⚠️  [yellow]Legacy AI support is disabled. Use MCP plugin via Claude Code for AI functionality.[/yellow]")
        console.print("💡 [blue]Use --use-ai mcp to generate AI coordination prompts for MCP clients[/blue]")
        use_ai_flag = False
        model = "none"
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
