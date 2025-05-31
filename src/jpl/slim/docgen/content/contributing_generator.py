# File: src/jpl/slim/docgen/content/contributing_generator.py
"""
Contributing documentation generator.
"""
import logging
import os
import re
from typing import Dict, List, Optional


class ContributingGenerator:
    """
    Generates contributing documentation from repository information.
    """
    
    def __init__(self, repo_path: str, logger: logging.Logger):
        """
        Initialize the contributing generator.
        
        Args:
            repo_path: Path to the repository
            logger: Logger instance
        """
        self.repo_path = repo_path
        self.logger = logger
    
    def generate(self, repo_info: Dict) -> str:
        """
        Generate contributing documentation based on repository content.
        
        Args:
            repo_info: Repository information dictionary
            
        Returns:
            Generated content as string
        """
        content = []
        content.append("# Contributing\n")
        content.append("This page provides guidelines for contributing to this project.\n")
        
        # Check for existing CONTRIBUTING.md file
        contributing_path = repo_info.get("key_files", {}).get("contributing")
        if contributing_path:
            contributing_content = self._extract_from_contributing(os.path.join(self.repo_path, contributing_path))
            if contributing_content:
                return contributing_content
        
        # Check for contributing section in README
        readme_path = repo_info.get("key_files", {}).get("readme")
        if readme_path:
            contributing_section = self._extract_contributing_from_readme(os.path.join(self.repo_path, readme_path))
            if contributing_section:
                content.append(contributing_section)
                return "\n".join(content)
        
        # If no contributing information found, generate default content
        self._generate_default_contributing(content, repo_info)
        
        return "\n".join(content)
    
    def _extract_from_contributing(self, file_path: str) -> Optional[str]:
        """
        Extract content from CONTRIBUTING.md file.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Remove heading if it's just "Contributing" to avoid duplication
                content = re.sub(r'^#\s+Contributing\s*\n', '', content)
                
                return "# Contributing\n\n" + content
        
        except Exception as e:
            self.logger.warning(f"Error extracting content from CONTRIBUTING.md: {str(e)}")
            return None
    
    def _extract_contributing_from_readme(self, file_path: str) -> Optional[str]:
        """
        Extract contributing section from README.md.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                readme_content = f.read()
            
            # Look for contributing section
            section_names = ["Contributing", "Contribution", "How to Contribute"]
            for section_name in section_names:
                pattern = rf"^##\s+{section_name}.*?$"
                match = re.search(pattern, readme_content, re.MULTILINE)
                
                if match:
                    start_pos = match.start()
                    
                    # Find the end of the section
                    next_heading = re.search(r"^##\s+", readme_content[start_pos+1:], re.MULTILINE)
                    if next_heading:
                        end_pos = start_pos + 1 + next_heading.start()
                        section = readme_content[start_pos:end_pos].strip()
                    else:
                        section = readme_content[start_pos:].strip()
                    
                    # Remove the heading to avoid duplication
                    section = re.sub(rf"^##\s+{section_name}.*?\n", '', section)
                    
                    return section
        
        except Exception as e:
            self.logger.warning(f"Error extracting contributing section from README: {str(e)}")
        
        return None
    
    def _generate_default_contributing(self, content: List[str], repo_info: Dict) -> None:
        """
        Generate default contributing guidelines.
        """
        project_name = repo_info['project_name']
        repo_url = repo_info.get('repo_url', f"[REPO_URL]/{project_name}")
        
        content.append("\nThank you for considering contributing to this project! Here's how you can help:\n")
        
        # Add basic workflow
        content.append("## Getting Started\n")
        content.append("1. Fork the repository")
        content.append("2. Clone your fork locally")
        content.append("3. Create a new branch for your work")
        content.append("4. Make your changes")
        content.append("5. Test your changes")
        content.append("6. Submit a pull request\n")
        
        # Add contact information
        content.append("## Contact\n")
        content.append(f"If you have any questions, please open an issue on the [repository]({repo_url}/issues).\n")