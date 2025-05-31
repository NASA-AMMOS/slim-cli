# File: src/jpl/slim/docgen/content/overview_generator.py
"""
Overview content generator.
"""
import logging
import os
import re
from typing import Dict, Optional


class OverviewGenerator:
    """
    Generates overview documentation from repository information.
    """
    
    def __init__(self, repo_path: str, logger: logging.Logger):
        """
        Initialize the overview generator.
        
        Args:
            repo_path: Path to the repository
            logger: Logger instance
        """
        self.repo_path = repo_path
        self.logger = logger
    
    def generate(self, repo_info: Dict) -> str:
        """
        Generate overview content based on repository README and structure.
        
        Args:
            repo_info: Repository information dictionary
            
        Returns:
            Generated content as string
        """
        content = []
        content.append(f"# {repo_info['project_name']} Overview\n")
        
        # Add description
        if repo_info.get('description'):
            content.append(repo_info['description'] + "\n")
        
        # Extract content from README
        readme_path = repo_info.get("key_files", {}).get("readme")
        if readme_path:
            readme_content = self._extract_from_readme(os.path.join(self.repo_path, readme_path), repo_info)
            if readme_content:
                content.append(readme_content)
        
        # Add repository structure information
        content.append("\n## Repository Structure\n")
        content.append("This project contains the following key directories:\n")
        
        if repo_info.get("src_dirs"):
            content.append("\n### Source Code\n")
            for dir_path in repo_info["src_dirs"]:
                content.append(f"- `{dir_path}/`: Source code directory")
        
        if repo_info.get("doc_dirs"):
            content.append("\n### Documentation\n")
            for dir_path in repo_info["doc_dirs"]:
                content.append(f"- `{dir_path}/`: Documentation directory")
        
        if repo_info.get("test_dirs"):
            content.append("\n### Tests\n")
            for dir_path in repo_info["test_dirs"]:
                content.append(f"- `{dir_path}/`: Test directory")
        
        # Add programming languages information
        if repo_info.get("languages"):
            content.append("\n## Technologies\n")
            content.append("This project is implemented using the following languages and technologies:\n")
            for language in sorted(repo_info["languages"]):
                content.append(f"- {language}")
        
        return "\n".join(content)
    
    def _extract_from_readme(self, readme_path: str, repo_info: Dict) -> Optional[str]:
        """
        Extract content from README.md for the overview section.
        
        Args:
            readme_path: Path to README.md
            repo_info: Repository information dictionary
            
        Returns:
            Extracted content or None if extraction failed
        """
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                readme_content = f.read()
            
            # Remove the first heading if it's just the project name
            project_name_pattern = re.escape(repo_info['project_name'])
            readme_content = re.sub(r'^#\s+' + project_name_pattern + r'\s*\n', '', readme_content)
            
            # If there's a description that matches what we already have, remove it too
            if repo_info.get('description'):
                description_pattern = re.escape(repo_info['description'])
                readme_content = re.sub(description_pattern, '', readme_content)
            
            # Look for specific sections we want to include
            features_section = self._extract_section(readme_content, "Features", "")
            if features_section:
                return features_section
            
            # If no specific sections found, return the whole README content with the first heading removed
            return readme_content
        
        except Exception as e:
            self.logger.warning(f"Error extracting content from README: {str(e)}")
            return None
    
    def _extract_section(self, content: str, section_name: str, end_section_name: str = "") -> Optional[str]:
        """
        Extract a specific section from content.
        
        Args:
            content: Content to extract section from
            section_name: Name of the section to extract
            end_section_name: Name of the section that marks the end of extraction
            
        Returns:
            Extracted section or None if section not found
        """
        # Pattern to match the section heading
        pattern = rf"^##\s+{section_name}.*?$"
        match = re.search(pattern, content, re.MULTILINE)
        
        if match:
            start_pos = match.start()
            
            # Find the end of the section
            if end_section_name:
                end_pattern = rf"^##\s+{end_section_name}.*?$"
                end_match = re.search(end_pattern, content[start_pos:], re.MULTILINE)
                
                if end_match:
                    end_pos = start_pos + end_match.start()
                    return content[start_pos:end_pos].strip()
            
            # If no end section specified or not found, go until the next heading or end of file
            next_heading = re.search(r"^##\s+", content[start_pos+1:], re.MULTILINE)
            if next_heading:
                end_pos = start_pos + 1 + next_heading.start()
                return content[start_pos:end_pos].strip()
            else:
                return content[start_pos:].strip()
        
        return None
