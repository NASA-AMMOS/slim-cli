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
import xml.etree.ElementTree as ET

__all__ = [
    "scan_repository",
    "extract_project_metadata", 
    "categorize_directories",
    "detect_languages",
    "extract_from_package_json",
    "extract_from_setup_py", 
    "extract_from_pyproject_toml",
    "extract_from_readme",
    "extract_from_pom_xml",
    "extract_from_build_gradle",
    "extract_from_cargo_toml",
    "extract_from_go_mod",
    "extract_from_composer_json",
    "extract_from_gemfile",
    "extract_from_csproj",
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
    '.docker': 'Docker',
    '.txt': 'Text',
    '.text': 'Text',
    '.rst': 'reStructuredText',
    '.adoc': 'AsciiDoc',
    '.asciidoc': 'AsciiDoc',
    '.pod': 'Pod',
    '.tex': 'LaTeX',
    '.latex': 'LaTeX',
    '.properties': 'Properties',
    '.ini': 'INI',
    '.cfg': 'Config',
    '.conf': 'Config',
    '.env': 'Environment'
}

# Key files to look for in repositories
KEY_FILE_PATTERNS = {
    'readme': [
        r'(?i)readme\.md$', r'(?i)readme\.txt$', r'(?i)readme\.rst$', 
        r'(?i)readme\.adoc$', r'(?i)readme$', r'(?i)readme\.markdown$'
    ],
    'license': [
        r'(?i)license(\.md|\.txt)?$', r'(?i)licence(\.md|\.txt)?$', 
        r'(?i)copying(\.md|\.txt)?$', r'(?i)copyright(\.md|\.txt)?$'
    ],
    'contributing': [r'(?i)contributing\.md$', r'(?i)contribute\.md$'],
    'code_of_conduct': [r'(?i)code[-_]of[-_]conduct\.md$'],
    'changelog': [
        r'(?i)changelog\.md$', r'(?i)changelog\.txt$', r'(?i)history\.md$', 
        r'(?i)history\.txt$', r'(?i)releases\.md$', r'(?i)news\.md$', 
        r'(?i)changes\.md$', r'(?i)changes\.txt$'
    ],
    'security': [r'(?i)security\.md$'],
    'support': [r'(?i)support\.md$'],
    'authors': [r'(?i)authors\.md$', r'(?i)contributors\.md$', r'(?i)credits\.md$'],
    'citation': [r'(?i)citation\.cff$', r'(?i)citation\.bib$'],
    'dockerfile': [r'(?i)dockerfile$', r'(?i)dockerfile\..*$', r'docker-compose\.ya?ml$'],
    'gitignore': [r'\.gitignore$'],
    'github_workflows': [r'\.github/workflows/.*\.ya?ml$']
}

# Directories to exclude from analysis
EXCLUDE_DIRECTORIES = {
    '.git', '.svn', '.hg', '.bzr',  # Version control
    'node_modules', '__pycache__', '.pytest_cache',  # Dependencies/cache
    'venv', 'env', '.venv', 'virtualenv',  # Virtual environments (removed .env as it's usually a file)
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
    logging.debug(f"Scanning repository: {repo_path}")
    
    if not repo_path.exists():
        raise FileNotFoundError(f"Repository path does not exist: {repo_path}")
    
    # Merge exclude directories
    exclude_set = EXCLUDE_DIRECTORIES.copy()
    if exclude_dirs:
        exclude_set.update(exclude_dirs)
    logging.debug(f"Excluding directories: {exclude_set}")
    
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
    
    # For categorization, we only exclude version control and cache directories
    categorization_excludes = {'.git', '.svn', '.hg', '.bzr', '__pycache__', '.pytest_cache', 'node_modules'}
    
    for item in repo_path.rglob("*"):
        if item.is_dir() and item.name not in categorization_excludes:
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
        if title_match:
            # Only override if the current project_name is the default (directory name)
            current_name = metadata.get('project_name', '')
            if not current_name or current_name == Path(file_path).parent.name:
                metadata['project_name'] = title_match.group(1).strip()
            
        # Try to extract the first paragraph as the description
        # Handle multiple README formats: with/without blank lines after title
        desc_patterns = [
            r'#[^\n]*\n\s*\n(.+?)(?:\n\s*\n|\n\s*#|$)',  # Title with blank line
            r'#[^\n]*\n(.+?)(?:\n\s*\n|\n\s*#|$)',        # Title without blank line
        ]
        
        for pattern in desc_patterns:
            desc_match = re.search(pattern, content, re.DOTALL)
            if desc_match and not metadata.get('description'):
                description = desc_match.group(1).strip()
                # Clean up common README formatting
                description = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', description)  # Remove links
                description = re.sub(r'[*_`]', '', description)  # Remove formatting
                # Take only the first sentence or line
                first_line = description.split('\n')[0].strip()
                if first_line:
                    metadata['description'] = first_line
                    break
            
    except Exception as e:
        logging.warning(f"Error extracting info from README: {str(e)}")


def extract_from_pom_xml(file_path: Union[str, Path], metadata: Dict[str, Any]) -> None:
    """
    Extract information from Maven pom.xml file.
    
    Args:
        file_path: Path to pom.xml
        metadata: Dictionary to update with extracted information
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Handle namespace - try with and without namespace
        ns = {}
        if root.tag.startswith('{'):
            ns_uri = root.tag.split('}')[0][1:]
            ns = {'maven': ns_uri}
            
        # Try with namespace first, then without
        for prefix in ['maven:', '']:
            artifact_id = root.find(f'.//{prefix}artifactId', ns if prefix else None)
            if artifact_id is not None and artifact_id.text:
                metadata['project_name'] = artifact_id.text
                break
                
        for prefix in ['maven:', '']:
            group_id = root.find(f'.//{prefix}groupId', ns if prefix else None)
            if group_id is not None and group_id.text:
                metadata['org_name'] = group_id.text
                break
                
        for prefix in ['maven:', '']:
            version = root.find(f'.//{prefix}version', ns if prefix else None)
            if version is not None and version.text:
                metadata['version'] = version.text
                break
                
        for prefix in ['maven:', '']:
            description = root.find(f'.//{prefix}description', ns if prefix else None)
            if description is not None and description.text:
                metadata['description'] = description.text.strip()
                break
                
        for prefix in ['maven:', '']:
            url = root.find(f'.//{prefix}url', ns if prefix else None)
            if url is not None and url.text:
                metadata['repo_url'] = url.text
                break
                
        # Extract license
        for prefix in ['maven:', '']:
            license_elem = root.find(f'.//{prefix}licenses/{prefix}license/{prefix}name', ns if prefix else None)
            if license_elem is not None and license_elem.text:
                metadata['license'] = license_elem.text
                break
                
        # Extract dependencies
        for prefix in ['maven:', '']:
            dependencies = root.findall(f'.//{prefix}dependencies/{prefix}dependency/{prefix}artifactId', ns if prefix else None)
            if dependencies:
                metadata['dependencies'] = [dep.text for dep in dependencies if dep.text]
                break
            
    except Exception as e:
        logging.warning(f"Error extracting info from pom.xml: {str(e)}")


def extract_from_build_gradle(file_path: Union[str, Path], metadata: Dict[str, Any]) -> None:
    """
    Extract information from Gradle build file (build.gradle or build.gradle.kts).
    
    Args:
        file_path: Path to build.gradle
        metadata: Dictionary to update with extracted information
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract common Gradle properties using regex
        patterns = {
            'project_name': r'rootProject\.name\s*=\s*[\'"]([^"\']+)["\']',
            'version': r'version\s*=?\s*[\'"]([^"\']+)["\']',
            'group': r'group\s*=?\s*[\'"]([^"\']+)["\']'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, content)
            if match:
                if key == 'project_name':
                    metadata['project_name'] = match.group(1)
                elif key == 'version':
                    metadata['version'] = match.group(1)
                elif key == 'group':
                    metadata['org_name'] = match.group(1)
                    
        # Extract dependencies
        deps_match = re.findall(r'(?:implementation|compile|api)\s*[\'"]([^:]+:[^:]+):[^"\']+["\']', content)
        if deps_match:
            metadata['dependencies'] = list(set(deps_match))
            
    except Exception as e:
        logging.warning(f"Error extracting info from build.gradle: {str(e)}")


def extract_from_cargo_toml(file_path: Union[str, Path], metadata: Dict[str, Any]) -> None:
    """
    Extract information from Rust's Cargo.toml file.
    
    Args:
        file_path: Path to Cargo.toml
        metadata: Dictionary to update with extracted information
    """
    try:
        with open(file_path, 'rb') as f:
            data = tomllib.load(f)
            
        if 'package' in data:
            package = data['package']
            
            if 'name' in package:
                metadata['project_name'] = package['name']
                
            if 'version' in package:
                metadata['version'] = package['version']
                
            if 'description' in package:
                metadata['description'] = package['description']
                
            if 'authors' in package and package['authors']:
                metadata['author'] = package['authors'][0]
                
            if 'license' in package:
                metadata['license'] = package['license']
                
            if 'repository' in package:
                metadata['repo_url'] = package['repository']
                
        # Extract dependencies
        if 'dependencies' in data:
            metadata['dependencies'] = list(data['dependencies'].keys())
            
        if 'dev-dependencies' in data:
            metadata['dev_dependencies'] = list(data['dev-dependencies'].keys())
            
    except Exception as e:
        logging.warning(f"Error extracting info from Cargo.toml: {str(e)}")


def extract_from_go_mod(file_path: Union[str, Path], metadata: Dict[str, Any]) -> None:
    """
    Extract information from Go's go.mod file.
    
    Args:
        file_path: Path to go.mod
        metadata: Dictionary to update with extracted information
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract module name
        module_match = re.search(r'^module\s+(.+)$', content, re.MULTILINE)
        if module_match:
            module_name = module_match.group(1).strip()
            metadata['project_name'] = module_name.split('/')[-1]
            
            # Full module path might be the repo URL
            if module_name.startswith('github.com/'):
                metadata['repo_url'] = f"https://{module_name}"
                
        # Extract Go version
        go_match = re.search(r'^go\s+([\d.]+)$', content, re.MULTILINE)
        if go_match:
            metadata['go_version'] = go_match.group(1)
            
        # Extract dependencies
        require_block = re.search(r'require\s*\((.*?)\)', content, re.DOTALL)
        if require_block:
            deps = re.findall(r'^\s*([^\s]+)\s+v[\d.]+', require_block.group(1), re.MULTILINE)
            metadata['dependencies'] = deps
        else:
            # Single line requires
            deps = re.findall(r'^require\s+([^\s]+)\s+v[\d.]+', content, re.MULTILINE)
            if deps:
                metadata['dependencies'] = deps
                
    except Exception as e:
        logging.warning(f"Error extracting info from go.mod: {str(e)}")


def extract_from_composer_json(file_path: Union[str, Path], metadata: Dict[str, Any]) -> None:
    """
    Extract information from PHP's composer.json file.
    
    Args:
        file_path: Path to composer.json
        metadata: Dictionary to update with extracted information
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if 'name' in data:
            metadata['project_name'] = data['name'].split('/')[-1]
            
        if 'description' in data:
            metadata['description'] = data['description']
            
        if 'version' in data:
            metadata['version'] = data['version']
            
        if 'authors' in data and data['authors']:
            author = data['authors'][0]
            if 'name' in author:
                metadata['author'] = author['name']
                
        if 'license' in data:
            metadata['license'] = data['license']
            
        if 'homepage' in data:
            metadata['repo_url'] = data['homepage']
            
        if 'require' in data:
            # Filter out PHP version requirement
            deps = [dep for dep in data['require'].keys() if not dep.startswith('php')]
            metadata['dependencies'] = deps
            
        if 'require-dev' in data:
            metadata['dev_dependencies'] = list(data['require-dev'].keys())
            
    except Exception as e:
        logging.warning(f"Error extracting info from composer.json: {str(e)}")


def extract_from_gemfile(file_path: Union[str, Path], metadata: Dict[str, Any]) -> None:
    """
    Extract information from Ruby's Gemfile.
    
    Args:
        file_path: Path to Gemfile
        metadata: Dictionary to update with extracted information
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract gem dependencies
        gems = re.findall(r'^\s*gem\s+[\'"]([^"\']+)["\']', content, re.MULTILINE)
        if gems:
            metadata['dependencies'] = gems
            
        # Try to find gemspec reference
        gemspec_match = re.search(r'gemspec\s*(?:path:\s*[\'"]([^"\']+)["\'])?', content)
        if gemspec_match:
            # Look for .gemspec file
            gemfile_dir = Path(file_path).parent
            gemspec_files = list(gemfile_dir.glob('*.gemspec'))
            if gemspec_files:
                _extract_from_gemspec(gemspec_files[0], metadata)
                
    except Exception as e:
        logging.warning(f"Error extracting info from Gemfile: {str(e)}")


def _extract_from_gemspec(file_path: Path, metadata: Dict[str, Any]) -> None:
    """Helper to extract info from .gemspec file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract gem name
        name_match = re.search(r'\.name\s*=\s*[\'"]([^"\']+)["\']', content)
        if name_match:
            metadata['project_name'] = name_match.group(1)
            
        # Extract version
        version_match = re.search(r'\.version\s*=\s*[\'"]([^"\']+)["\']', content)
        if version_match:
            metadata['version'] = version_match.group(1)
            
        # Extract description (prefer description over summary)
        desc_match = re.search(r'\.description\s*=\s*[\'"]([^"\']+)["\']', content)
        if desc_match:
            metadata['description'] = desc_match.group(1)
        else:
            # Fallback to summary if description not found
            summary_match = re.search(r'\.summary\s*=\s*[\'"]([^"\']+)["\']', content)
            if summary_match:
                metadata['description'] = summary_match.group(1)
            
    except Exception as e:
        logging.debug(f"Error extracting from gemspec: {str(e)}")


def extract_from_csproj(file_path: Union[str, Path], metadata: Dict[str, Any]) -> None:
    """
    Extract information from .NET project file (.csproj, .vbproj, .fsproj).
    
    Args:
        file_path: Path to .csproj file
        metadata: Dictionary to update with extracted information
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Extract from PropertyGroup elements
        for prop_group in root.findall('.//PropertyGroup'):
            # Project name (AssemblyName or fallback to filename)
            assembly_name = prop_group.find('AssemblyName')
            if assembly_name is not None and assembly_name.text:
                metadata['project_name'] = assembly_name.text
            elif not metadata.get('project_name'):
                metadata['project_name'] = Path(file_path).stem
                
            # Version
            for version_tag in ['Version', 'AssemblyVersion', 'FileVersion']:
                version = prop_group.find(version_tag)
                if version is not None and version.text:
                    metadata['version'] = version.text
                    break
                    
            # Description
            description = prop_group.find('Description')
            if description is not None and description.text:
                metadata['description'] = description.text
                
            # Authors
            authors = prop_group.find('Authors')
            if authors is not None and authors.text:
                metadata['author'] = authors.text
                
            # License
            license_elem = prop_group.find('PackageLicenseExpression')
            if license_elem is not None and license_elem.text:
                metadata['license'] = license_elem.text
                
            # Repository URL
            repo_url = prop_group.find('RepositoryUrl')
            if repo_url is not None and repo_url.text:
                metadata['repo_url'] = repo_url.text
                
        # Extract package references
        package_refs = root.findall('.//PackageReference')
        if package_refs:
            deps = []
            for ref in package_refs:
                if 'Include' in ref.attrib:
                    deps.append(ref.attrib['Include'])
            if deps:
                metadata['dependencies'] = deps
                
    except Exception as e:
        logging.warning(f"Error extracting info from .csproj: {str(e)}")


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
        found_files = []
        
        # Walk through repository to find matching files
        for root, dirs, files in os.walk(repo_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            root_path = Path(root)
            for file_name in files:
                file_path = root_path / file_name
                rel_path = file_path.relative_to(repo_path)
                
                # Check if file matches any of the patterns
                for pattern in patterns:
                    if re.search(pattern, str(rel_path)):
                        found_files.append(rel_path)
                        break
        
        if found_files:
            # Sort by depth (prefer root directory) and then by name
            found_files.sort(key=lambda x: (len(x.parts), str(x).lower()))
            key_files[file_type] = str(found_files[0])
    
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
    filename = file_path.name.lower()
    
    # Special cases for files without extensions or special names
    special_files = {
        'dockerfile': 'Docker',
        'dockerfile.dev': 'Docker',
        'dockerfile.prod': 'Docker',
        'dockerfile.test': 'Docker',
        'makefile': 'Makefile',
        'gnumakefile': 'Makefile',
        'rakefile': 'Ruby',
        'gemfile': 'Ruby',
        'guardfile': 'Ruby',
        'podfile': 'Ruby',
        'thorfile': 'Ruby',
        'vagrantfile': 'Ruby',
        'berksfile': 'Ruby',
        'cheffile': 'Ruby',
        'puppetfile': 'Ruby',
        'fastfile': 'Ruby',
        'appfile': 'Ruby',
        'deliverfile': 'Ruby',
        'snapfile': 'Ruby',
        'scanfile': 'Ruby',
        'gymfile': 'Ruby',
        'matchfile': 'Ruby',
        'jenkinsfile': 'Groovy',
        'gulpfile.js': 'JavaScript',
        'gruntfile.js': 'JavaScript',
        'webpack.config.js': 'JavaScript',
        'cmakelists.txt': 'CMake',
        'build.gradle': 'Gradle',
        'build.gradle.kts': 'Kotlin',
        'settings.gradle': 'Gradle',
        'settings.gradle.kts': 'Kotlin',
        '.env': 'Environment'
    }
    
    if filename in special_files:
        return special_files[filename]
    
    # Check shebang for shell scripts without extension
    if not extension and file_path.exists():
        try:
            with open(file_path, 'rb') as f:
                first_line = f.readline()
                if first_line.startswith(b'#!'):
                    shebang = first_line.decode('utf-8', errors='ignore').strip()
                    if 'python' in shebang:
                        return 'Python'
                    elif 'ruby' in shebang:
                        return 'Ruby'
                    elif 'node' in shebang:
                        return 'JavaScript'
                    elif 'sh' in shebang or 'bash' in shebang or 'zsh' in shebang:
                        return 'Shell'
                    elif 'perl' in shebang:
                        return 'Perl'
        except:
            pass
    
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
    source_patterns = {
        # Common patterns
        'src', 'lib', 'app', 'core', 'source', 'code', 'pkg', 'internal',
        # Java/JVM
        'java', 'kotlin', 'scala', 'groovy', 'clojure',
        # .NET
        'controllers', 'models', 'views', 'services',
        # Go
        'cmd', 'pkg', 'internal', 'api',
        # Ruby
        'app', 'lib',
        # PHP
        'src', 'app', 'classes',
        # JavaScript/TypeScript
        'src', 'lib', 'components', 'pages', 'utils'
    }
    
    # Also check for path patterns like src/main/java
    dir_path_str = str(Path(dir_path)).lower()
    if 'src/main' in dir_path_str or 'src\\main' in dir_path_str:
        return True
        
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
    test_patterns = {
        'test', 'tests', 'testing', 'spec', 'specs', '__tests__', 'e2e',
        'integration', 'unit', 'functional', 'acceptance', 'cypress',
        'jest', 'mocha', 'karma', 'jasmine', 'qunit', 'testcases',
        'test_cases', 'test-cases', 'fixtures', 'features', 'scenarios'
    }
    
    # Check for path patterns like src/test/java
    dir_path_str = str(Path(dir_path)).lower()
    if 'src/test' in dir_path_str or 'src\\test' in dir_path_str:
        return True
        
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
    # Try package.json (Node.js)
    package_json = repo_path / 'package.json'
    if package_json.exists():
        extract_from_package_json(package_json, metadata)
    
    # Try setup.py (Python)
    setup_py = repo_path / 'setup.py'
    if setup_py.exists():
        extract_from_setup_py(setup_py, metadata)
        
    # Try pyproject.toml (Python)
    pyproject_toml = repo_path / 'pyproject.toml'
    if pyproject_toml.exists():
        extract_from_pyproject_toml(pyproject_toml, metadata)
        
    # Try pom.xml (Java/Maven)
    pom_xml = repo_path / 'pom.xml'
    if pom_xml.exists():
        extract_from_pom_xml(pom_xml, metadata)
        
    # Try build.gradle or build.gradle.kts (Java/Gradle)
    for gradle_file in ['build.gradle', 'build.gradle.kts']:
        gradle_path = repo_path / gradle_file
        if gradle_path.exists():
            extract_from_build_gradle(gradle_path, metadata)
            break
    
    # Try settings.gradle for project name (prioritize over directory name)
    settings_gradle = repo_path / 'settings.gradle'
    if settings_gradle.exists():
        try:
            with open(settings_gradle, 'r', encoding='utf-8') as f:
                content = f.read()
            name_match = re.search(r'rootProject\.name\s*=\s*[\'"]([^"\']+)["\']', content)
            if name_match:
                current_name = metadata.get('project_name', '')
                # Only override if current name is the directory name or empty
                if not current_name or current_name == repo_path.name:
                    metadata['project_name'] = name_match.group(1)
        except Exception:
            pass
            
    # Try Cargo.toml (Rust)
    cargo_toml = repo_path / 'Cargo.toml'
    if cargo_toml.exists():
        extract_from_cargo_toml(cargo_toml, metadata)
        
    # Try go.mod (Go)
    go_mod = repo_path / 'go.mod'
    if go_mod.exists():
        extract_from_go_mod(go_mod, metadata)
        
    # Try composer.json (PHP)
    composer_json = repo_path / 'composer.json'
    if composer_json.exists():
        extract_from_composer_json(composer_json, metadata)
        
    # Try Gemfile (Ruby)
    gemfile = repo_path / 'Gemfile'
    if gemfile.exists():
        extract_from_gemfile(gemfile, metadata)
        
    # Try .csproj, .vbproj, .fsproj files (.NET)
    for proj_pattern in ['*.csproj', '*.vbproj', '*.fsproj']:
        proj_files = list(repo_path.glob(proj_pattern))
        if proj_files:
            extract_from_csproj(proj_files[0], metadata)
            break
    
    # Try README files (last to not override more specific metadata)
    key_files = find_key_files(repo_path)
    if 'readme' in key_files:
        readme_path = repo_path / key_files['readme']
        extract_from_readme(readme_path, metadata)


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
            # Filter out hidden files if not including them, but allow important dotfiles
            important_dotfiles = {'.env', '.gitignore', '.dockerignore', '.editorconfig', '.eslintrc', '.babelrc', '.prettierrc'}
            if not include_hidden and file_name.startswith('.') and file_name not in important_dotfiles:
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
    build_patterns = {'build', 'dist', 'target', 'out', 'bin', 'obj', 'release', 'debug'}
    return dir_name in build_patterns


def _is_config_directory(dir_path: Path) -> bool:
    """Check if directory contains configuration files."""
    dir_name = dir_path.name.lower()
    config_patterns = {'config', 'conf', 'cfg', 'settings', '.github', '.vscode', '.idea'}
    return dir_name in config_patterns