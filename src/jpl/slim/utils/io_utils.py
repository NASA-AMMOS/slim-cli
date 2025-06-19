"""
I/O utility functions for SLIM.

This module contains utility functions for file I/O operations, HTTP requests, and JSON handling.
"""

import os
import json
import logging
import requests


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

    # In test mode, simulate successful download without making actual HTTP requests
    if os.environ.get('SLIM_TEST_MODE', 'False').lower() in ('true', '1', 't'):
        logging.info(f"TEST MODE: Simulating download of {url} to {filename}")
        
        # Create an empty file to simulate the download
        with open(file_path, 'w') as f:
            f.write(f"Mock content for {filename} downloaded from {url}")
        return file_path
    
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
    # In test mode, return mock data
    if os.environ.get('SLIM_TEST_MODE', 'False').lower() in ('true', '1', 't'):
        logging.info(f"TEST MODE: Returning mock best practices data")
        # Return a simple mock structure that matches what the tests expect
        return [
            {
                "title": "Test Practice",
                "description": "Test Description",
                "assets": [
                    {
                        "name": "Test Asset",
                        "uri": "https://example.com/test.md"
                    }
                ]
            }
        ]
    
    # Normal implementation for non-test mode
    response = requests.get(url)
    response.raise_for_status()

    return response.json()


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
    asset_mapping = {}
    
    for i, practice in enumerate(practices, start=1):
        title = practice.get('title', 'N/A')
        description = practice.get('description', 'N/A')
        
        if 'assets' in practice and practice['assets']:
            for j, asset in enumerate(practice['assets'], start=1):
                # Use alias as the key instead of SLIM-X.X format
                alias = asset.get('alias')
                if not alias:
                    # Skip assets without aliases for now
                    continue
                
                asset_name = asset.get('name', 'N/A')
                asset_uri = asset.get('uri', '')
                asset_mapping[alias] = {
                    'title': title, 
                    'description': description, 
                    'asset_name': asset_name,
                    'asset_uri': asset_uri
                }
        # Skip practices without assets - they don't have implementations yet
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


def fetch_code_base(repo_path):
    """
    Fetch the code base from a repository.
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        str: Content of the code base, or None if not found
    """
    code_base = ""
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(('.py', '.js', '.java', '.cpp', '.cs')):  # Add more extensions as needed
                file_path = os.path.join(root, file)
                code_base += read_file_content(file_path) or ""
    return code_base if code_base else None
