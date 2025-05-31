### src/jpl/slim/docgen/analyzer/repo_analyzer.py
"""
Repository analyzer for extracting structure and metadata from repositories.
"""
import logging
import os
import re
from typing import Dict, List, Set

import git

from jpl.slim.docgen.analyzer.content_extractor import (
    extract_from_package_json,
    extract_from_readme,
    extract_from_setup_py,
    extract_git_info
)


class RepoAnalyzer:
    """
    Analyzes a repository structure and extracts relevant information.
    """
    
    def __init__(self, repo_path: str, logger: logging.Logger):
        """
        Initialize the repository analyzer.
        
        Args:
            repo_path: Path to the repository
            logger: Logger instance
        """
        self.repo_path = repo_path
        self.logger = logger
        
        # Check if the repo is a git repository
        self.is_git_repo = os.path.exists(os.path.join(repo_path, '.git'))
    
    def analyze(self) -> Dict:
        """
        Analyze the repository and return extracted information.
        
        Returns:
            Dictionary containing repository information
        """
        self.logger.info(f"Analyzing repository: {self.repo_path}")
        
        repo_info = {
            "project_name": os.path.basename(self.repo_path),
            "description": "",
            "repo_url": "",
            "org_name": "",
            "files": [],
            "directories": [],
            "key_files": {},
            "src_dirs": [],
            "doc_dirs": [],
            "test_dirs": [],
            "languages": set()
        }
        
        # Extract basic project info
        self._extract_project_info(repo_info)
        
        # Scan filesystem
        self._scan_filesystem(repo_info)
        
        # Convert sets to lists for serialization
        repo_info["languages"] = list(repo_info["languages"])
        
        self.logger.debug(f"Completed repository analysis")
        return repo_info
    
    def _extract_project_info(self, repo_info: Dict) -> None:
        """
        Extract project information from various sources.
        
        Args:
            repo_info: Repository information dictionary to update
        """
        # Try extracting from package.json
        package_json_path = os.path.join(self.repo_path, 'package.json')
        if os.path.exists(package_json_path):
            extract_from_package_json(package_json_path, repo_info)
        
        # Try extracting from setup.py
        setup_py_path = os.path.join(self.repo_path, 'setup.py')
        if os.path.exists(setup_py_path):
            extract_from_setup_py(setup_py_path, repo_info)
        
        # Try extracting from README.md
        readme_path = os.path.join(self.repo_path, 'README.md')
        if os.path.exists(readme_path):
            extract_from_readme(readme_path, repo_info)
        
        # Try extracting from git
        if self.is_git_repo:
            extract_git_info(self.repo_path, repo_info)
    
    def _scan_filesystem(self, repo_info: Dict) -> None:
        """
        Scan the filesystem and update repository information.
        
        Args:
            repo_info: Repository information dictionary to update
        """
        # File extensions to programming languages mapping
        ext_to_lang = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.jsx': 'React',
            '.ts': 'TypeScript',
            '.tsx': 'React',
            '.java': 'Java',
            '.c': 'C',
            '.cpp': 'C++',
            '.h': 'C/C++',
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
            '.html': 'HTML',
            '.css': 'CSS',
            '.md': 'Markdown'
        }
        
        # Key files to look for
        key_file_patterns = {
            'readme': [r'readme\.md', r'README\.md'],
            'license': [r'license(\.md|\.txt)?', r'LICENSE(\.md|\.txt)?'],
            'contributing': [r'contributing\.md', r'CONTRIBUTING\.md'],
            'code_of_conduct': [r'code[-_]of[-_]conduct\.md', r'CODE[-_]OF[-_]CONDUCT\.md'],
            'changelog': [r'changelog\.md', r'CHANGELOG\.md'],
        }
        
        # Directories to exclude from analysis
        exclude_dirs = {'.git', 'node_modules', 'venv', 'env', '__pycache__', 'build', 'dist'}
        
        # Scan repository
        for root, dirs, files in os.walk(self.repo_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            # Process relative path
            rel_path = os.path.relpath(root, self.repo_path)
            if rel_path != '.':
                repo_info["directories"].append(rel_path)
                
                # Categorize directories
                dir_name = os.path.basename(rel_path).lower()
                if dir_name in {'src', 'lib', 'app', 'core'} or any(f.endswith(tuple(ext_to_lang.keys())) for f in files):
                    repo_info["src_dirs"].append(rel_path)
                if dir_name in {'docs', 'doc', 'documentation', 'wiki'}:
                    repo_info["doc_dirs"].append(rel_path)
                if dir_name in {'test', 'tests', 'testing', 'specs'}:
                    repo_info["test_dirs"].append(rel_path)
            
            # Process files
            for file in files:
                file_path = os.path.join(rel_path, file)
                if rel_path == '.':
                    file_path = file
                
                repo_info["files"].append(file_path)
                
                # Identify key files
                for key, patterns in key_file_patterns.items():
                    if any(re.match(pattern, file, re.IGNORECASE) for pattern in patterns):
                        repo_info["key_files"][key] = file_path
                
                # Identify programming languages
                _, ext = os.path.splitext(file)
                if ext.lower() in ext_to_lang:
                    repo_info["languages"].add(ext_to_lang[ext.lower()])
        
        self.logger.debug(f"Found {len(repo_info['files'])} files and {len(repo_info['directories'])} directories")