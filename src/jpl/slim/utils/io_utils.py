"""
I/O utility functions for SLIM.

This module contains utility functions for file I/O operations, HTTP requests, and JSON handling.
"""

import os
import json
import logging
import requests
import fnmatch
from pathlib import Path


def download_and_place_file(repo, url, filename, target_relative_path_in_repo=''):
    """
    Download a file from a URL and place it in a repository.
    
    Args:
        repo: Git repository object
        url: URL to download the file from
        filename: Name of the file to save
        target_relative_path_in_repo: Relative path in the repository to save the file
        
    Returns:
        str: Path to the downloaded file, or None if download failed
    """
    # Create the full path where the file will be saved. By default write to root.
    target_directory = os.path.join(repo.working_tree_dir, target_relative_path_in_repo)
    file_path = os.path.join(target_directory, filename)

    # Ensure that the target directory exists, create if not
    os.makedirs(target_directory, exist_ok=True)

    # Fetch the file from the URL
    response = requests.get(url)
    if response.status_code == 200:
        # Ensure the parent directories exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write the content to the file in the repository
        with open(file_path, 'wb') as file:
            file.write(response.content)
        logging.debug(f"File {filename} downloaded and placed at {file_path}.")
    else:
        logging.error(f"Failed to download the file. HTTP status code: {response.status_code}")
        file_path = None
    
    return file_path


def read_file_content(file_path):
    """
    Read the content of a file.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        str: Content of the file, or None if reading failed
    """
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except IOError as e:
        logging.error(f"Error reading file {file_path}: {e}")
        return None


def fetch_best_practices(url):
    """
    Fetch best practices from a URL.
    
    Args:
        url: URL to fetch best practices from
        
    Returns:
        list: List of best practices
    """
    logging.debug(f"Fetching best practices from URL: {url}")
    try:
        response = requests.get(url)
        logging.debug(f"HTTP response status: {response.status_code}")
        response.raise_for_status()
        
        data = response.json()
        logging.debug(f"Successfully parsed JSON data with {len(data)} practices")
        return data
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch best practices: {e}")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON response: {e}")
        return []


def fetch_best_practices_from_file(file_path):
    """
    Fetch best practices from a file.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        list: List of best practices
    """
    with open(file_path, 'r') as file:
        practices = json.load(file)
    return practices


def create_slim_registry_dictionary(practices):
    """
    Create a dictionary of best practices from the SLIM registry using aliases as keys.
    
    Args:
        practices: List of best practices
        
    Returns:
        dict: Dictionary of best practices keyed by alias
    """
    logging.debug(f"Creating SLIM registry dictionary from {len(practices)} practices")
    asset_mapping = {}
    
    for i, practice in enumerate(practices, start=1):
        title = practice.get('title', 'N/A')
        description = practice.get('description', 'N/A')
        logging.debug(f"Processing practice {i}: {title}")
        
        if 'assets' in practice and practice['assets']:
            assets = practice['assets']
            logging.debug(f"Practice has {len(assets)} assets")
            for j, asset in enumerate(assets, start=1):
                # Use alias as the key instead of SLIM-X.X format
                alias = asset.get('alias')
                if not alias:
                    # Skip assets without aliases for now
                    logging.debug(f"Skipping asset {j} without alias in practice: {title}")
                    continue
                
                asset_name = asset.get('name', 'N/A')
                asset_uri = asset.get('uri', '')
                logging.debug(f"Adding asset: {alias} - {asset_name}")
                asset_mapping[alias] = {
                    'title': title, 
                    'description': description, 
                    'asset_name': asset_name,
                    'asset_uri': asset_uri
                }
        else:
            logging.debug(f"Skipping practice without assets: {title}")
    
    logging.debug(f"Created registry dictionary with {len(asset_mapping)} mapped assets")
    return asset_mapping


def repo_file_to_list(file_path):
    """
    Convert a repository file to a list.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        list: List of lines in the file
    """
    # open the file at the given path
    with open(file_path, 'r') as file:
        # read all lines and strip any leading/trailing whitespace
        repos = [line.strip() for line in file.readlines()]
    # return the list of lines
    return repos


def fetch_relative_file_paths(directory):
    """
    Fetch relative file paths in a directory.
    
    Args:
        directory: Directory to fetch file paths from
        
    Returns:
        list: List of relative file paths
    """
    relative_paths = []
    for root, _, files in os.walk(directory):
        for file in files:
            # Get the relative file path and add it to the list
            relative_path = os.path.relpath(os.path.join(root, file), directory)
            relative_paths.append(relative_path)
    return relative_paths


def fetch_readme(repo_path):
    """
    Fetch the README file from a repository.
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        str: Content of the README file, or None if not found
    """
    readme_files = ['README.md', 'README.txt', 'README.rst']  # Add more variations as needed
    
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file in readme_files:
                file_path = os.path.join(root, file)
                return read_file_content(file_path)
    
    return None


def fetch_repository_context(repo_path, repository_context_config):
    """
    Fetch repository context based on configuration categories and patterns.
    
    Args:
        repo_path: Path to the repository
        repository_context_config: Dictionary with categories, include_patterns, exclude_patterns, max_characters
        
    Returns:
        str: Combined context content, or None if not found
    """
    categories = repository_context_config.get('categories', None)
    max_characters = repository_context_config.get('max_characters', 10000)
    include_patterns = repository_context_config.get('include_patterns', [])
    exclude_patterns = repository_context_config.get('exclude_patterns', ['*.log', '.git/'])
    
    # Build the final set of patterns
    all_patterns = set()
    
    # Step 1: If categories specified, add their default patterns
    if categories:
        for category in categories:
            if category == "documentation":
                # Get default doc patterns
                doc_patterns = ['README*', '*.md', '*.rst', '*.txt', 'CHANGELOG*', 'LICENSE*', 'CONTRIBUTING*']
                all_patterns.update(doc_patterns)
            elif category == "code":
                # Get default code patterns
                code_patterns = ['*.py', '*.js', '*.ts', '*.java', '*.go', '*.rs', '*.cpp', '*.c', '*.h', '*.cs', '*.php', '*.rb']
                all_patterns.update(code_patterns)
            elif category == "config":
                # Get default config patterns
                config_patterns = ['package.json', 'setup.py', 'pyproject.toml', 'Cargo.toml', 'pom.xml', '*.yaml', '*.yml', '*.ini', '*.cfg', 'Makefile', 'Dockerfile']
                all_patterns.update(config_patterns)
            elif category == "tests":
                # Get default test patterns
                test_patterns = ['test_*.py', '*_test.py', '*.test.js', '*.spec.js', 'tests/**', 'test/**']
                all_patterns.update(test_patterns)
    
    # Step 2: Add include_patterns if specified
    if include_patterns:
        all_patterns.update(include_patterns)
    
    # Step 3: If no patterns collected, return None (no context)
    if not all_patterns:
        return None
    
    # Convert set back to list for processing
    final_patterns = list(all_patterns)
    
    # Fetch files using the final pattern list
    # exclude_patterns are handled at the file level in _fetch_files_by_patterns
    content = _fetch_files_by_patterns(repo_path, final_patterns, exclude_patterns)
    
    # Handle max_characters limit
    if content and len(content) > max_characters:
        content = content[:max_characters] + "... [truncated]"
    
    # For structure category, handle separately as it doesn't use patterns
    if categories and "structure" in categories:
        structure_content = fetch_directory_structure(repo_path, exclude_patterns)
        if structure_content:
            if content:
                content = f"{content}\n\n=== STRUCTURE ===\n{structure_content}"
            else:
                content = f"=== STRUCTURE ===\n{structure_content}"
    
    return content


def fetch_documentation_files(repo_path, include_patterns, exclude_patterns):
    """Fetch documentation files content."""
    doc_patterns = ['README*', '*.md', '*.rst', '*.txt', 'CHANGELOG*', 'LICENSE*', 'CONTRIBUTING*']
    # Combine with user patterns, prioritizing documentation patterns
    combined_patterns = doc_patterns + [p for p in include_patterns if p not in doc_patterns]
    return _fetch_files_by_patterns(repo_path, combined_patterns, exclude_patterns)


def fetch_code_files(repo_path, include_patterns, exclude_patterns):
    """Fetch code files content."""
    code_patterns = ['*.py', '*.js', '*.ts', '*.java', '*.go', '*.rs', '*.cpp', '*.c', '*.h', '*.cs', '*.php', '*.rb']
    # Filter include_patterns to only code-related patterns
    code_include = [p for p in include_patterns if any(fnmatch.fnmatch(p, cp) for cp in code_patterns)]
    if not code_include:
        code_include = code_patterns
    return _fetch_files_by_patterns(repo_path, code_include, exclude_patterns, max_files=10)


def fetch_config_files(repo_path, include_patterns, exclude_patterns):
    """Fetch configuration files content."""
    config_patterns = ['package.json', 'setup.py', 'pyproject.toml', 'Cargo.toml', 'pom.xml', '*.yaml', '*.yml', '*.ini', '*.cfg', 'Makefile', 'Dockerfile']
    # Combine with user patterns
    combined_patterns = config_patterns + [p for p in include_patterns if p not in config_patterns]
    return _fetch_files_by_patterns(repo_path, combined_patterns, exclude_patterns)


def fetch_test_files(repo_path, include_patterns, exclude_patterns):
    """Fetch test files content."""
    test_patterns = ['test_*.py', '*_test.py', '*.test.js', '*.spec.js', 'tests/**', 'test/**']
    # Filter include_patterns to only test-related patterns
    test_include = [p for p in include_patterns if 'test' in p.lower()]
    if not test_include:
        test_include = test_patterns
    return _fetch_files_by_patterns(repo_path, test_include, exclude_patterns, max_files=5)


def fetch_directory_structure(repo_path, exclude_patterns):
    """Fetch directory structure as a tree listing."""
    structure_lines = []
    
    def add_to_structure(root, dirs, files, level=0):
        indent = "  " * level
        rel_root = os.path.relpath(root, repo_path)
        if rel_root != ".":
            structure_lines.append(f"{indent}{os.path.basename(root)}/")
        
        # Filter directories by exclude patterns
        dirs_filtered = [d for d in dirs if not _matches_exclude_patterns(os.path.join(rel_root, d), exclude_patterns)]
        files_filtered = [f for f in files if not _matches_exclude_patterns(os.path.join(rel_root, f), exclude_patterns)]
        
        # Add files
        for file in sorted(files_filtered)[:20]:  # Limit to first 20 files per directory
            structure_lines.append(f"{indent}  {file}")
        
        return dirs_filtered
    
    # Walk directory tree
    for root, dirs, files in os.walk(repo_path):
        if len(structure_lines) > 100:  # Limit total lines
            structure_lines.append("... [truncated]")
            break
            
        level = root[len(repo_path):].count(os.sep)
        dirs[:] = add_to_structure(root, dirs, files, level)
    
    return "\n".join(structure_lines) if structure_lines else None


def _fetch_files_by_patterns(repo_path, include_patterns, exclude_patterns, max_files=None):
    """Helper function to fetch files matching include patterns but not exclude patterns."""
    content_parts = []
    file_count = 0
    
    for root, dirs, files in os.walk(repo_path):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if not _matches_exclude_patterns(os.path.join(root, d), exclude_patterns)]
        
        for file in files:
            if max_files and file_count >= max_files:
                break
                
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, repo_path)
            
            # Check if file matches exclude patterns
            if _matches_exclude_patterns(rel_path, exclude_patterns):
                continue
                
            # Check if file matches include patterns
            if _matches_include_patterns(rel_path, include_patterns):
                content = read_file_content(file_path)
                if content:
                    content_parts.append(f"--- {rel_path} ---\n{content}")
                    file_count += 1
        
        if max_files and file_count >= max_files:
            break
    
    return "\n\n".join(content_parts) if content_parts else None


def _matches_include_patterns(file_path, patterns):
    """Check if file path matches any include pattern."""
    return any(fnmatch.fnmatch(file_path, pattern) or fnmatch.fnmatch(os.path.basename(file_path), pattern) for pattern in patterns)


def _matches_exclude_patterns(file_path, patterns):
    """Check if file path matches any exclude pattern."""
    return any(fnmatch.fnmatch(file_path, pattern) or pattern in file_path for pattern in patterns)


def fetch_code_base(repo_path):
    """
    Legacy function - fetch code base from repository.
    
    This function is maintained for backwards compatibility.
    Use fetch_repository_context() for new implementations.
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        str: Content of the code base, or None if not found
    """
    # Use default configuration for backwards compatibility
    default_config = {
        'categories': ['code'],
        'max_characters': 50000,
        'include_patterns': ['*.py', '*.js', '*.java', '*.cpp', '*.cs', '*.go', '*.rs'],
        'exclude_patterns': ['*.log', '.git/', '__pycache__/', 'node_modules/']
    }
    return fetch_repository_context(repo_path, default_config)
