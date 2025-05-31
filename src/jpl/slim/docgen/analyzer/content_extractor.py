### src/jpl/slim/docgen/analyzer/content_extractor.py
"""
Content extraction functions for repository files.
"""
import json
import logging
import os
import re
from typing import Dict

import git


def extract_from_package_json(file_path: str, repo_info: Dict) -> None:
    """
    Extract information from package.json.
    
    Args:
        file_path: Path to package.json
        repo_info: Dictionary to update with extracted information
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            if 'name' in data:
                repo_info['project_name'] = data['name']
            
            if 'description' in data:
                repo_info['description'] = data['description']
            
            if 'repository' in data:
                if isinstance(data['repository'], str):
                    repo_info['repo_url'] = data['repository']
                elif isinstance(data['repository'], dict) and 'url' in data['repository']:
                    repo_info['repo_url'] = data['repository']['url']
    
    except Exception as e:
        logging.warning(f"Error extracting info from package.json: {str(e)}")


def extract_from_setup_py(file_path: str, repo_info: Dict) -> None:
    """
    Extract information from setup.py.
    
    Args:
        file_path: Path to setup.py
        repo_info: Dictionary to update with extracted information
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Extract name
            name_match = re.search(r'name\s*=\s*[\'"]([^\'"]+)[\'"]', content)
            if name_match:
                repo_info['project_name'] = name_match.group(1)
            
            # Extract description
            desc_match = re.search(r'description\s*=\s*[\'"]([^\'"]+)[\'"]', content)
            if desc_match:
                repo_info['description'] = desc_match.group(1)
            
            # Extract URL
            url_match = re.search(r'url\s*=\s*[\'"]([^\'"]+)[\'"]', content)
            if url_match:
                repo_info['repo_url'] = url_match.group(1)
    
    except Exception as e:
        logging.warning(f"Error extracting info from setup.py: {str(e)}")


def extract_from_readme(file_path: str, repo_info: Dict) -> None:
    """
    Extract information from README.md.
    
    Args:
        file_path: Path to README.md
        repo_info: Dictionary to update with extracted information
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Try to extract the first heading as the project name
            title_match = re.search(r'#\s+(.+)', content, re.MULTILINE)
            if title_match:
                repo_info['project_name'] = title_match.group(1).strip()
            
            # Try to extract the first paragraph as the description
            desc_match = re.search(r'#.+\n+(.+?)(\n\n|\n#|$)', content, re.DOTALL)
            if desc_match and not repo_info.get('description'):
                repo_info['description'] = desc_match.group(1).strip()
    
    except Exception as e:
        logging.warning(f"Error extracting info from README.md: {str(e)}")


def extract_git_info(repo_path: str, repo_info: Dict) -> None:
    """
    Extract information from git repository.
    
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
                match = re.search(r'github\.com[:/]([^/]+)/([^/.]+)', url)
                if match:
                    repo_info['org_name'] = match.group(1)
                    repo_info['repo_url'] = f"https://github.com/{match.group(1)}/{match.group(2)}"
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