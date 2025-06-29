"""
Git utility functions for SLIM.

This module contains utility functions for Git operations, including branch management,
deployment, and repository information.
"""

import os
import logging
import git
import requests
import urllib.parse
import tempfile
import uuid
import re
from typing import Dict, List, Optional, Union

# Constants (these should be moved to a constants module later)
GIT_BRANCH_NAME_FOR_MULTIPLE_COMMITS = 'slim-best-practices'
GIT_DEFAULT_REMOTE_NAME = 'origin'
GIT_CUSTOM_REMOTE_NAME = 'slim-custom'
GIT_DEFAULT_COMMIT_MESSAGE = 'SLIM-CLI Best Practices Bot Commit'

__all__ = [
    "generate_git_branch_name",
    "clone_repository",
    "create_branch",
    "extract_git_info",
    "is_git_repository",
    "get_git_info_summary",
    "get_contributor_stats"
]


def generate_git_branch_name(best_practice_ids):
    """
    Generate a Git branch name based on best practice IDs.
    
    Args:
        best_practice_ids: List of best practice IDs
        
    Returns:
        str: Branch name, or None if no best practice IDs are provided
    """
    logging.debug(f"Generating git branch name for best_practice_ids: {best_practice_ids}")
    # Use shared branch name if multiple best_practice_ids else use default branch name
    if len(best_practice_ids) > 1:
        branch_name = GIT_BRANCH_NAME_FOR_MULTIPLE_COMMITS
        logging.debug(f"Multiple best practices detected, using shared branch: {branch_name}")
        return branch_name
    elif len(best_practice_ids) == 1:
        branch_name = best_practice_ids[0]
        logging.debug(f"Single best practice, using branch: {branch_name}")
        return branch_name
    else:
        logging.debug("No best practice IDs provided, returning None")
        return None



def clone_repository(repo_url, target_dir=None):
    """
    Clone a repository.
    
    Args:
        repo_url: URL of the repository to clone
        target_dir: Directory to clone the repository to
        
    Returns:
        git.Repo: Cloned repository object, or None if cloning failed
    """
    logging.debug(f"Cloning repository from URL: {repo_url}")
    try:
        # Parse the repository URL to get the repository name
        parsed_url = urllib.parse.urlparse(repo_url)
        repo_name = os.path.basename(parsed_url.path)
        repo_name = repo_name[:-4] if repo_name.endswith('.git') else repo_name  # Remove '.git' from repo name if present
        logging.debug(f"Parsed repository name: {repo_name}")
        
        # Determine the target directory
        if target_dir:
            target_dir = os.path.join(target_dir, repo_name)
            logging.debug(f"Set clone directory to {target_dir}")
        else:
            target_dir = tempfile.mkdtemp(prefix=f"{repo_name}_" + str(uuid.uuid4()) + '_')
            logging.debug(f"Generating temporary clone directory at {target_dir}")
        
        # Clone the repository
        repo = git.Repo.clone_from(repo_url, target_dir)
        logging.debug(f"Repository {repo_url} cloned to {target_dir}")
        
        return repo
    except git.exc.GitCommandError as e:
        logging.error(f"Git command error: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return None


def create_branch(repo, branch_name):
    """
    Create a branch in a repository.
    
    Args:
        repo: Git repository object
        branch_name: Name of the branch to create
        
    Returns:
        git.Head: Branch object, or None if creation failed
    """
    logging.debug(f"Creating branch: {branch_name}")
    try:
        if repo.head.is_valid():
            if branch_name in repo.heads:
                # Check out the existing branch
                git_branch = repo.heads[branch_name]
                git_branch.checkout()
                logging.warning(f"Git branch '{git_branch.name}' already exists. Checking out existing branch.")
            else:
                # Create and check out the new branch
                git_branch = repo.create_head(branch_name)
                git_branch.checkout()
                logging.debug(f"Branch '{git_branch.name}' created and checked out successfully.")
        else:
            # Create an initial commit
            with open(os.path.join(repo.working_dir, 'README.md'), 'w') as file:
                file.write("Empty README for now.")
            repo.index.add(['README.md'])  # Add files to the index
            repo.index.commit('Initial commit')  # Commit the changes
            logging.debug("Initial commit created in the empty repository.")

            # Empty repo, so only now create and check out the fresh branch
            git_branch = repo.create_head(branch_name)
            git_branch.checkout()
            logging.debug(f"Empty repository. Creating new branch '{git_branch.name}' and checked it out successfully.")
        
        return git_branch
    except git.exc.GitCommandError as e:
        logging.error(f"Git command error: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return None


def extract_git_info(repo_path: str, repo_info: Dict) -> None:
    """
    Extract git repository information including organization, URL, and default branch.
    
    Extracts the following information from a git repository:
    - org_name: Organization/user name from the remote URL
    - repo_url: HTTPS URL of the repository
    - default_branch: Name of the default branch (main, master, etc.)
    
    Supports multiple git hosting platforms including GitHub, GitHub Enterprise,
    GitLab, and other common git hosts.
    
    Args:
        repo_path: Path to the git repository
        repo_info: Dictionary to update with extracted information
    """
    try:
        repo = git.Repo(repo_path)
        
        # Extract URL from remotes
        for remote in repo.remotes:
            for url in remote.urls:
                # Extract org and repo from common git URL formats
                # Support GitHub, GitHub Enterprise, GitLab, and other common hosts
                patterns = [
                    r'([^/:]+\.github\.com)[:/]([^/]+)/([^/.]+)',  # GitHub Enterprise
                    r'(github\.com)[:/]([^/]+)/([^/.]+)',          # GitHub.com
                    r'([^/:]+\.gitlab\.com)[:/]([^/]+)/([^/.]+)',  # GitLab instances
                    r'(gitlab\.com)[:/]([^/]+)/([^/.]+)',          # GitLab.com
                    r'([^/:]+\.[^/:]+)[:/]([^/]+)/([^/.]+)'        # Generic git hosts
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, url)
                    if match:
                        host = match.group(1)
                        org = match.group(2)
                        repo_name = match.group(3)
                        
                        # Remove .git suffix if present
                        repo_name = repo_name[:-4] if repo_name.endswith('.git') else repo_name
                        
                        repo_info['org_name'] = org
                        repo_info['repo_url'] = f"https://{host}/{org}/{repo_name}"
                        break
                if 'repo_url' in repo_info:
                    break
        
        # Get default branch
        try:
            default_branch = repo.active_branch.name
            repo_info['default_branch'] = default_branch
        except (TypeError, git.exc.GitCommandError):
            # Head might be detached, try to get from remote
            try:
                ref = repo.git.symbolic_ref('refs/remotes/origin/HEAD')
                default_branch = ref.replace('refs/remotes/origin/', '')
                repo_info['default_branch'] = default_branch
            except git.exc.GitCommandError:
                # Try common branch names
                for branch in ['main', 'master']:
                    try:
                        repo.git.rev_parse('--verify', branch)
                        repo_info['default_branch'] = branch
                        break
                    except git.exc.GitCommandError:
                        continue
    
    except Exception as e:
        logging.warning(f"Error extracting git information: {str(e)}")


def is_git_repository(repo_path: str) -> bool:
    """
    Check if a directory is a git repository.
    
    Args:
        repo_path: Path to check
        
    Returns:
        True if the path is a git repository
    """
    try:
        git.Repo(repo_path)
        return True
    except (git.exc.InvalidGitRepositoryError, git.exc.NoSuchPathError):
        return False


def get_git_info_summary(repo_path: str) -> Optional[Dict[str, str]]:
    """
    Get a summary of git repository information.
    
    Returns a dictionary containing:
    - org_name: Organization/user name from the remote URL
    - repo_url: HTTPS URL of the repository  
    - default_branch: Name of the default branch (main, master, etc.)
    
    Args:
        repo_path: Path to the git repository
        
    Returns:
        Dictionary with git info summary containing org_name, repo_url, and default_branch,
        or None if the path is not a valid git repository
    """
    if not is_git_repository(repo_path):
        return None
        
    git_info = {}
    extract_git_info(repo_path, git_info)
    
    return {
        'org_name': git_info.get('org_name', ''),
        'repo_url': git_info.get('repo_url', ''),
        'default_branch': git_info.get('default_branch', '')
    }


def get_contributor_stats(repo_path: str) -> List[Dict[str, Union[int, str]]]:
    """
    Get contributor statistics from a git repository.
    
    Returns a list of contributors sorted by commit count (highest first).
    Each contributor is a dictionary with 'commits', 'name', and 'email' keys.
    
    Args:
        repo_path: Path to the git repository
        
    Returns:
        List of contributor dictionaries, empty list if error occurs
    """
    try:
        repo = git.Repo(repo_path)
        contributors = {}
        
        for commit in repo.iter_commits('--all'):
            email = commit.author.email
            
            # Initialize contributor if not seen before
            if email not in contributors:
                contributors[email] = {
                    'commits': 0, 
                    'name': commit.author.name, 
                    'email': email
                }
            
            # Increment commit count and update name (in case it changed)
            contributors[email]['commits'] += 1
            contributors[email]['name'] = commit.author.name
        
        # Convert to list and sort by commit count (highest first)
        contributor_list = list(contributors.values())
        contributor_list.sort(key=lambda x: x['commits'], reverse=True)
        
        return contributor_list
        
    except Exception as e:
        logging.error(f"Error getting contributor stats: {e}")
        return []
