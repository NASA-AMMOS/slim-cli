# File: src/jpl/slim/docgen/content/installation_generator.py
"""
Installation content generator.
"""
import logging
import os
import re
from typing import Dict, List


class InstallationGenerator:
    """
    Generates installation documentation from repository information.
    """
    
    def __init__(self, repo_path: str, logger: logging.Logger):
        """
        Initialize the installation generator.
        
        Args:
            repo_path: Path to the repository
            logger: Logger instance
        """
        self.repo_path = repo_path
        self.logger = logger
    
    def generate(self, repo_info: Dict) -> str:
        """
        Generate installation instructions based on repository contents.
        
        Args:
            repo_info: Repository information dictionary
            
        Returns:
            Generated content as string
        """
        content = []
        content.append("# Installation\n")
        content.append("This page provides instructions for installing and setting up the project.\n")
        
        # Determine installation methods based on repository structure
        has_npm = "package.json" in repo_info["files"]
        has_pip = "setup.py" in repo_info["files"] or "requirements.txt" in repo_info["files"]
        has_docker = "Dockerfile" in repo_info["files"] or "docker-compose.yml" in repo_info["files"]
        
        # Check for installation section in README
        installation_section = self._extract_installation_from_readme(repo_info)
        if installation_section:
            content.append(installation_section)
            return "\n".join(content)
        
        # If no installation section found, generate based on repo structure
        self._generate_installation_by_type(content, repo_info, has_npm, has_pip, has_docker)
        
        # Add prerequisites section
        self._add_prerequisites(content, has_npm, has_pip, has_docker)
        
        # Add configuration section
        self._add_configuration_section(content, repo_info)
        
        return "\n".join(content)
    
    def _extract_installation_from_readme(self, repo_info: Dict) -> str:
        """
        Extract installation section from README.
        
        Args:
            repo_info: Repository information dictionary
            
        Returns:
            Extracted installation section or empty string if not found
        """
        readme_path = repo_info.get("key_files", {}).get("readme")
        if not readme_path:
            return ""
        
        try:
            with open(os.path.join(self.repo_path, readme_path), 'r', encoding='utf-8') as f:
                readme_content = f.read()
            
            # Look for installation section
            for section_name in ["Installation", "Getting Started", "Setup", "Usage"]:
                pattern = rf"^##\s+{section_name}.*?$"
                match = re.search(pattern, readme_content, re.MULTILINE)
                
                if match:
                    start_pos = match.start()
                    
                    # Find the end of the section
                    next_heading = re.search(r"^##\s+", readme_content[start_pos+1:], re.MULTILINE)
                    if next_heading:
                        end_pos = start_pos + 1 + next_heading.start()
                        return readme_content[start_pos:end_pos].strip()
                    else:
                        return readme_content[start_pos:].strip()
        
        except Exception as e:
            self.logger.warning(f"Error extracting installation section from README: {str(e)}")
        
        return ""
    
    def _generate_installation_by_type(self, content: List[str], repo_info: Dict, 
                                      has_npm: bool, has_pip: bool, has_docker: bool) -> None:
        """
        Generate installation instructions based on repository type.
        """
        project_name = repo_info['project_name']
        repo_url = repo_info.get('repo_url', f"[REPO_URL]/{project_name}")
        
        if has_npm:
            content.append("\n## Installation with npm\n")
            content.append("```bash\n# Clone the repository\n")
            content.append(f"git clone {repo_url}\n")
            content.append(f"cd {os.path.basename(project_name)}\n\n")
            content.append("# Install dependencies\nnpm install\n```\n")
        
        if has_pip:
            content.append("\n## Installation with pip\n")
            
            if "requirements.txt" in repo_info["files"]:
                content.append("```bash\n# Clone the repository\n")
                content.append(f"git clone {repo_url}\n")
                content.append(f"cd {os.path.basename(project_name)}\n\n")
                content.append("# Create and activate a virtual environment\n")
                content.append("python -m venv venv\n")
                content.append("source venv/bin/activate  # On Windows: venv\\Scripts\\activate\n\n")
                content.append("# Install dependencies\npip install -r requirements.txt\n```\n")
            
            if "setup.py" in repo_info["files"]:
                content.append("```bash\n# Install in development mode\npip install -e .\n```\n")
        
        if has_docker:
            content.append("\n## Installation with Docker\n")
            content.append("```bash\n# Clone the repository\n")
            content.append(f"git clone {repo_url}\n")
            content.append(f"cd {os.path.basename(project_name)}\n\n")
            
            if "docker-compose.yml" in repo_info["files"]:
                content.append("# Build and run with Docker Compose\ndocker-compose up -d\n```\n")
            else:
                content.append(f"# Build and run with Docker\ndocker build -t {project_name.lower()} .\n")
                content.append(f"docker run -p 8000:8000 {project_name.lower()}\n```\n")
        
        if not any([has_npm, has_pip, has_docker]):
            content.append("\n## Manual Installation\n")
            content.append("```bash\n# Clone the repository\n")
            content.append(f"git clone {repo_url}\n")
            content.append(f"cd {os.path.basename(project_name)}\n```\n")
            content.append("\nRefer to the README for specific installation instructions.\n")
    
    def _add_prerequisites(self, content: List[str], has_npm: bool, has_pip: bool, has_docker: bool) -> None:
        """
        Add prerequisites section.
        """
        prerequisites = []
        
        if has_npm:
            prerequisites.extend([
                "- [Node.js](https://nodejs.org/) (>=12.x)",
                "- [npm](https://www.npmjs.com/) or [yarn](https://yarnpkg.com/)"
            ])
        
        if has_pip:
            prerequisites.extend([
                "- [Python](https://www.python.org/) (>=3.7)",
                "- [pip](https://pip.pypa.io/en/stable/)"
            ])
        
        if has_docker:
            prerequisites.extend([
                "- [Docker](https://www.docker.com/)",
                "- [Docker Compose](https://docs.docker.com/compose/) (for docker-compose.yml)" if "docker-compose.yml" in os.listdir(self.repo_path) else ""
            ])
        
        if prerequisites:
            content.append("\n## Prerequisites\n")
            content.extend([p for p in prerequisites if p])  # Filter out empty strings
            content.append("\n")
    
    def _add_configuration_section(self, content: List[str], repo_info: Dict) -> None:
        """
        Add configuration section.
        """
        content.append("\n## Configuration\n")
        content.append("After installation, you may need to configure the application. ")
        
        # Look for config files
        config_files = []
        for file in repo_info["files"]:
            if file.endswith(('.env.example', '.env.sample', 'config.example.json', 'config.example.yaml', 'config.example.yml')):
                config_files.append(file)
        
        if config_files:
            content.append("Check for the following configuration files:\n")
            
            for file in config_files:
                base_name = os.path.basename(file)
                target_name = base_name.replace('.example', '').replace('.sample', '')
                content.append(f"- Copy `{base_name}` to `{target_name}` and update the values as needed.")
        else:
            content.append("Refer to the project documentation for specific configuration options.")
