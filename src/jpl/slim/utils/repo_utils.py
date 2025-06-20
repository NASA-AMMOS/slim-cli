"""
Repository analysis and metadata extraction utilities for SLIM CLI.

This module provides reusable functionality for analyzing repository structure,
extracting project metadata from various sources, and categorizing repository
contents. It leverages third-party libraries for robust file parsing.
"""

import json
import logging
import os
import re
import tomllib
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any, Union
import yaml

__all__ = [
    "scan_repository",
    "extract_project_metadata", 
    "categorize_directories",
    "detect_languages",
    "extract_from_package_json",
    "extract_from_setup_py", 
    "extract_from_pyproject_toml",
    "extract_from_readme",
    "find_key_files",
    "get_file_language",
    "is_source_directory",
    "is_test_directory",
    "is_documentation_directory"
]


# File extensions to programming languages mapping
LANGUAGE_EXTENSIONS = {
    '.py': 'Python',
    '.js': 'JavaScript', 
    '.jsx': 'React',
    '.ts': 'TypeScript',
    '.tsx': 'React',
    '.java': 'Java',
    '.c': 'C',
    '.cpp': 'C++',
    '.cxx': 'C++',
    '.cc': 'C++',
    '.h': 'C/C++',
    '.hpp': 'C++',
    '.go': 'Go',
    '.rs': 'Rust',
    '.rb': 'Ruby',
    '.php': 'PHP',
    '.swift': 'Swift',
    '.kt': 'Kotlin',
    '.scala': 'Scala',
    '.cs': 'C#',
    '.r': 'R',
    '.sh': 'Shell',
    '.bash': 'Shell',
    '.zsh': 'Shell',
    '.fish': 'Shell',
    '.html': 'HTML',
    '.htm': 'HTML',
    '.css': 'CSS',
    '.scss': 'SCSS',
    '.sass': 'Sass',
    '.less': 'Less',
    '.md': 'Markdown',
    '.markdown': 'Markdown',
    '.json': 'JSON',
    '.xml': 'XML',
    '.yaml': 'YAML',
    '.yml': 'YAML',
    '.toml': 'TOML',
    '.sql': 'SQL',
    '.dockerfile': 'Docker',
    '.docker': 'Docker'
}

# Key files to look for in repositories
KEY_FILE_PATTERNS = {
    'readme': [r'readme\.md$', r'README\.md$', r'readme\.txt$', r'README\.txt$', r'readme$', r'README$'],
    'license': [r'license(\.md|\.txt)?$', r'LICENSE(\.md|\.txt)?$', r'COPYING$', r'COPYRIGHT$'],
    'contributing': [r'contributing\.md$', r'CONTRIBUTING\.md$', r'CONTRIBUTE\.md$'],
    'code_of_conduct': [r'code[-_]of[-_]conduct\.md$', r'CODE[-_]OF[-_]CONDUCT\.md$'],
    'changelog': [r'changelog\.md$', r'CHANGELOG\.md$', r'HISTORY\.md$', r'RELEASES\.md$'],
    'security': [r'security\.md$', r'SECURITY\.md$'],
    'support': [r'support\.md$', r'SUPPORT\.md$'],
    'authors': [r'authors\.md$', r'AUTHORS\.md$', r'CONTRIBUTORS\.md$'],
    'citation': [r'citation\.cff$', r'CITATION\.cff$', r'citation\.bib$'],
    'dockerfile': [r'dockerfile$', r'Dockerfile$', r'docker-compose\.ya?ml$'],
    'gitignore': [r'\.gitignore$'],
    'github_workflows': [r'\.github/workflows/.*\.ya?ml$']
}

# Directories to exclude from analysis
EXCLUDE_DIRECTORIES = {
    '.git', '.svn', '.hg', '.bzr',  # Version control
    'node_modules', '__pycache__', '.pytest_cache',  # Dependencies/cache
    'venv', 'env', '.venv', '.env', 'virtualenv',  # Virtual environments
    'build', 'dist', 'target', 'out', 'bin',  # Build outputs
    '.idea', '.vscode', '.vs',  # IDEs
    '.nyc_output', 'coverage'  # Coverage reports
}


def scan_repository(repo_path: Union[str, Path], 
                   exclude_dirs: Optional[Set[str]] = None,
                   include_hidden: bool = False) -> Dict[str, Any]:
    """
    Scan a repository and extract comprehensive information about its structure.
    
    Args:
        repo_path: Path to the repository
        exclude_dirs: Additional directories to exclude (merges with defaults)
        include_hidden: Whether to include hidden files/directories
        
    Returns:
        Dictionary containing repository analysis results
    """
    repo_path = Path(repo_path)
    
    if not repo_path.exists():
        raise FileNotFoundError(f"Repository path does not exist: {repo_path}")
    
    # Merge exclude directories
    exclude_set = EXCLUDE_DIRECTORIES.copy()
    if exclude_dirs:
        exclude_set.update(exclude_dirs)
    
    repo_info = {
        "project_name": repo_path.name,
        "description": "",
        "repo_url": "",
        "org_name": "",
        "files": [],
        "directories": [],
        "key_files": {},
        "src_dirs": [],
        "doc_dirs": [],
        "test_dirs": [],
        "languages": set(),
        "file_count": 0,
        "size_bytes": 0
    }
    
    logging.debug(f"Scanning repository: {repo_path}")
    
    # Extract project metadata from various sources
    _extract_all_metadata(repo_path, repo_info)
    
    # Scan filesystem
    _scan_filesystem(repo_path, repo_info, exclude_set, include_hidden)
    
    # Convert sets to lists for serialization
    repo_info["languages"] = list(repo_info["languages"])
    
    logging.debug(f"Repository scan complete: {len(repo_info['files'])} files, "
                 f"{len(repo_info['directories'])} directories")
    
    return repo_info


def extract_project_metadata(repo_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Extract project metadata from various configuration files.
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        Dictionary containing extracted metadata
    """
    repo_path = Path(repo_path)
    metadata = {
        "project_name": repo_path.name,
        "description": "",
        "version": "",
        "author": "",
        "repo_url": "",
        "license": "",
        "dependencies": [],
        "dev_dependencies": []
    }
    
    _extract_all_metadata(repo_path, metadata)
    return metadata


def categorize_directories(repo_path: Union[str, Path]) -> Dict[str, List[str]]:
    """
    Categorize directories in a repository by their likely purpose.
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        Dictionary with categorized directory lists
    """
    repo_path = Path(repo_path)
    categories = {
        "source": [],
        "test": [], 
        "documentation": [],
        "build": [],
        "config": [],
        "other": []
    }
    
    for item in repo_path.rglob("*"):
        if item.is_dir() and item.name not in EXCLUDE_DIRECTORIES:
            rel_path = item.relative_to(repo_path)
            
            if is_source_directory(item):
                categories["source"].append(str(rel_path))
            elif is_test_directory(item):
                categories["test"].append(str(rel_path))
            elif is_documentation_directory(item):
                categories["documentation"].append(str(rel_path))
            elif _is_build_directory(item):
                categories["build"].append(str(rel_path))
            elif _is_config_directory(item):
                categories["config"].append(str(rel_path))
            else:
                categories["other"].append(str(rel_path))
    
    return categories


def detect_languages(repo_path: Union[str, Path]) -> Dict[str, int]:
    """
    Detect programming languages used in the repository.
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        Dictionary mapping language names to file counts
    """
    repo_path = Path(repo_path)
    language_counts = {}
    
    for file_path in repo_path.rglob("*"):
        if file_path.is_file():
            # Skip files in excluded directories
            if any(excl in file_path.parts for excl in EXCLUDE_DIRECTORIES):
                continue
                
            language = get_file_language(file_path)
            if language:
                language_counts[language] = language_counts.get(language, 0) + 1
    
    # Sort by count descending
    return dict(sorted(language_counts.items(), key=lambda x: x[1], reverse=True))


def extract_from_package_json(file_path: Union[str, Path], metadata: Dict[str, Any]) -> None:
    """
    Extract information from package.json file.
    
    Args:
        file_path: Path to package.json
        metadata: Dictionary to update with extracted information
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if 'name' in data:
            metadata['project_name'] = data['name']
        
        if 'description' in data:
            metadata['description'] = data['description']
            
        if 'version' in data:
            metadata['version'] = data['version']
            
        if 'author' in data:
            if isinstance(data['author'], str):
                metadata['author'] = data['author']
            elif isinstance(data['author'], dict):
                metadata['author'] = data['author'].get('name', '')
                
        if 'license' in data:
            metadata['license'] = data['license']
            
        if 'repository' in data:
            if isinstance(data['repository'], str):
                metadata['repo_url'] = data['repository']
            elif isinstance(data['repository'], dict):
                metadata['repo_url'] = data['repository'].get('url', '')
                
        if 'dependencies' in data:
            metadata['dependencies'] = list(data['dependencies'].keys())
            
        if 'devDependencies' in data:
            metadata['dev_dependencies'] = list(data['devDependencies'].keys())
            
    except Exception as e:
        logging.warning(f"Error extracting info from package.json: {str(e)}")


def extract_from_setup_py(file_path: Union[str, Path], metadata: Dict[str, Any]) -> None:
    """
    Extract information from setup.py file.
    
    Args:
        file_path: Path to setup.py
        metadata: Dictionary to update with extracted information
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract common setup() parameters using regex
        patterns = {
            'project_name': r'name\s*=\s*[\'"]([^\'"]+)[\'"]',
            'description': r'description\s*=\s*[\'"]([^\'"]+)[\'"]',
            'version': r'version\s*=\s*[\'"]([^\'"]+)[\'"]',
            'author': r'author\s*=\s*[\'"]([^\'"]+)[\'"]',
            'license': r'license\s*=\s*[\'"]([^\'"]+)[\'"]',
            'repo_url': r'url\s*=\s*[\'"]([^\'"]+)[\'"]'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                metadata[key] = match.group(1)
                
        # Extract install_requires
        install_requires_match = re.search(
            r'install_requires\s*=\s*\[(.*?)\]', content, re.DOTALL
        )
        if install_requires_match:
            deps_str = install_requires_match.group(1)
            deps = re.findall(r'[\'"]([^\'"]+)[\'"]', deps_str)
            metadata['dependencies'] = deps
            
    except Exception as e:
        logging.warning(f"Error extracting info from setup.py: {str(e)}")


def extract_from_pyproject_toml(file_path: Union[str, Path], metadata: Dict[str, Any]) -> None:
    """
    Extract information from pyproject.toml file.
    
    Args:
        file_path: Path to pyproject.toml
        metadata: Dictionary to update with extracted information
    """
    try:
        with open(file_path, 'rb') as f:
            data = tomllib.load(f)
            
        # Check for Poetry configuration
        if 'tool' in data and 'poetry' in data['tool']:
            poetry_config = data['tool']['poetry']
            _extract_from_dict(poetry_config, metadata)
            
        # Check for setuptools configuration
        elif 'project' in data:
            project_config = data['project']
            _extract_from_dict(project_config, metadata)
            
        # Check for build-system
        if 'build-system' in data:
            build_deps = data['build-system'].get('requires', [])
            if build_deps:
                metadata['dev_dependencies'] = build_deps
                
    except Exception as e:
        logging.warning(f"Error extracting info from pyproject.toml: {str(e)}")


def extract_from_readme(file_path: Union[str, Path], metadata: Dict[str, Any]) -> None:
    """
    Extract information from README file.
    
    Args:
        file_path: Path to README file
        metadata: Dictionary to update with extracted information
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Try to extract the first heading as the project name
        title_match = re.search(r'^#\s+(.+)', content, re.MULTILINE)
        if title_match and not metadata.get('project_name'):
            metadata['project_name'] = title_match.group(1).strip()
            
        # Try to extract the first paragraph as the description
        desc_match = re.search(r'#.+\n+(.+?)(\n\n|\n#|$)', content, re.DOTALL)
        if desc_match and not metadata.get('description'):
            description = desc_match.group(1).strip()
            # Clean up common README formatting
            description = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', description)  # Remove links
            description = re.sub(r'[*_`]', '', description)  # Remove formatting
            metadata['description'] = description
            
    except Exception as e:
        logging.warning(f"Error extracting info from README: {str(e)}")


def find_key_files(repo_path: Union[str, Path]) -> Dict[str, str]:
    """
    Find key files in the repository (README, LICENSE, etc.).
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        Dictionary mapping file types to their paths
    """
    repo_path = Path(repo_path)
    key_files = {}
    
    for file_type, patterns in KEY_FILE_PATTERNS.items():
        for pattern in patterns:
            matches = list(repo_path.glob(pattern))
            if matches:
                # Take the first match, prefer files in root directory
                matches.sort(key=lambda x: (len(x.parts), x.name))
                rel_path = matches[0].relative_to(repo_path)
                key_files[file_type] = str(rel_path)
                break
    
    return key_files


def get_file_language(file_path: Union[str, Path]) -> Optional[str]:
    """
    Determine the programming language of a file based on its extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Language name or None if not recognized
    """
    file_path = Path(file_path)
    extension = file_path.suffix.lower()
    
    # Special cases
    if file_path.name.lower() in ['dockerfile', 'dockerfile.dev', 'dockerfile.prod']:
        return 'Docker'
    
    return LANGUAGE_EXTENSIONS.get(extension)


def is_source_directory(dir_path: Union[str, Path]) -> bool:
    """
    Check if a directory likely contains source code.
    
    Args:
        dir_path: Path to the directory
        
    Returns:
        True if likely a source directory
    """
    dir_name = Path(dir_path).name.lower()
    source_patterns = {'src', 'lib', 'app', 'core', 'source', 'code', 'pkg', 'internal'}
    return dir_name in source_patterns


def is_test_directory(dir_path: Union[str, Path]) -> bool:
    """
    Check if a directory likely contains tests.
    
    Args:
        dir_path: Path to the directory
        
    Returns:
        True if likely a test directory
    """
    dir_name = Path(dir_path).name.lower()
    test_patterns = {'test', 'tests', 'testing', 'spec', 'specs', '__tests__', 'e2e'}
    return dir_name in test_patterns


def is_documentation_directory(dir_path: Union[str, Path]) -> bool:
    """
    Check if a directory likely contains documentation.
    
    Args:
        dir_path: Path to the directory
        
    Returns:
        True if likely a documentation directory
    """
    dir_name = Path(dir_path).name.lower()
    doc_patterns = {'docs', 'doc', 'documentation', 'wiki', 'manual', 'guide'}
    return dir_name in doc_patterns


# Private helper functions

def _extract_all_metadata(repo_path: Path, metadata: Dict[str, Any]) -> None:
    """Extract metadata from all available sources."""
    # Try package.json
    package_json = repo_path / 'package.json'
    if package_json.exists():
        extract_from_package_json(package_json, metadata)
    
    # Try setup.py
    setup_py = repo_path / 'setup.py'
    if setup_py.exists():
        extract_from_setup_py(setup_py, metadata)
        
    # Try pyproject.toml
    pyproject_toml = repo_path / 'pyproject.toml'
    if pyproject_toml.exists():
        extract_from_pyproject_toml(pyproject_toml, metadata)
    
    # Try README files
    for readme_pattern in KEY_FILE_PATTERNS['readme']:
        readme_files = list(repo_path.glob(readme_pattern))
        if readme_files:
            extract_from_readme(readme_files[0], metadata)
            break


def _extract_from_dict(config_dict: Dict[str, Any], metadata: Dict[str, Any]) -> None:
    """Extract metadata from a configuration dictionary."""
    mapping = {
        'name': 'project_name',
        'description': 'description',
        'version': 'version',
        'author': 'author',
        'license': 'license',
        'repository': 'repo_url',
        'homepage': 'repo_url'
    }
    
    for src_key, dst_key in mapping.items():
        if src_key in config_dict:
            value = config_dict[src_key]
            if isinstance(value, dict) and 'url' in value:
                metadata[dst_key] = value['url']
            else:
                metadata[dst_key] = str(value)
    
    # Handle dependencies
    if 'dependencies' in config_dict:
        deps = config_dict['dependencies']
        if isinstance(deps, dict):
            metadata['dependencies'] = list(deps.keys())
        elif isinstance(deps, list):
            metadata['dependencies'] = deps


def _scan_filesystem(repo_path: Path, repo_info: Dict[str, Any], 
                    exclude_dirs: Set[str], include_hidden: bool) -> None:
    """Scan the filesystem and update repository information."""
    for root, dirs, files in os.walk(repo_path):
        root_path = Path(root)
        
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        # Filter out hidden directories if not including them
        if not include_hidden:
            dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        # Process relative path
        try:
            rel_path = root_path.relative_to(repo_path)
            if str(rel_path) != '.':
                repo_info["directories"].append(str(rel_path))
                
                # Categorize directories
                if is_source_directory(root_path):
                    repo_info["src_dirs"].append(str(rel_path))
                elif is_test_directory(root_path):
                    repo_info["test_dirs"].append(str(rel_path))
                elif is_documentation_directory(root_path):
                    repo_info["doc_dirs"].append(str(rel_path))
        except ValueError:
            # Path is not relative to repo_path, skip
            continue
        
        # Process files
        for file_name in files:
            # Filter out hidden files if not including them
            if not include_hidden and file_name.startswith('.'):
                continue
                
            file_path = root_path / file_name
            try:
                rel_file_path = file_path.relative_to(repo_path)
                repo_info["files"].append(str(rel_file_path))
                repo_info["file_count"] += 1
                
                # Add file size
                try:
                    repo_info["size_bytes"] += file_path.stat().st_size
                except OSError:
                    pass  # File might be a symlink or have permission issues
                
                # Identify programming languages
                language = get_file_language(file_path)
                if language:
                    repo_info["languages"].add(language)
                    
            except ValueError:
                # File path is not relative to repo_path, skip
                continue
    
    # Find key files
    repo_info["key_files"] = find_key_files(repo_path)


def _is_build_directory(dir_path: Path) -> bool:
    """Check if directory is for build outputs."""
    dir_name = dir_path.name.lower()
    build_patterns = {'build', 'dist', 'target', 'out', 'bin', 'release', 'debug'}
    return dir_name in build_patterns


def _is_config_directory(dir_path: Path) -> bool:
    """Check if directory contains configuration files."""
    dir_name = dir_path.name.lower()
    config_patterns = {'config', 'conf', 'cfg', 'settings', '.github', '.vscode', '.idea'}
    return dir_name in config_patterns