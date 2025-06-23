"""
Simplified documentation generator using SLIM utils.

This module provides a lightweight orchestrator that leverages the utils layer
for repository analysis, AI enhancement, and template management.
"""

import logging
import os
import shutil
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from jpl.slim.utils.repo_utils import scan_repository, extract_project_metadata
from jpl.slim.utils.ai_utils import enhance_content
from jpl.slim.utils.git_utils import extract_git_info, is_git_repository
from jpl.slim.best_practices.docs_website_impl.template_manager import TemplateManager
from jpl.slim.best_practices.docs_website_impl.config_updater import ConfigUpdater
from jpl.slim.best_practices.docs_website_impl.helpers import load_config, escape_mdx_special_characters, clean_api_doc, escape_yaml_value

__all__ = ["SlimDocGenerator"]


class SlimDocGenerator:
    """
    Simplified documentation generator that uses the utils layer.
    """
    
    def __init__(
        self, 
        target_repo_path: Optional[str],
        output_dir: str,
        template_repo: str = "https://github.com/NASA-AMMOS/slim-docsite-template.git",
        use_ai: Optional[str] = None,
        config_file: Optional[str] = None,
        verbose: bool = False,
        template_only: bool = False,
        revise_site: bool = False
    ):
        """
        Initialize the SLIM documentation generator.
        
        Args:
            target_repo_path: Path to the target repository to document
            output_dir: Directory where the documentation site will be generated
            template_repo: URL or path to the template repository
            use_ai: Optional AI model to use for content enhancement
            config_file: Optional path to configuration file
            verbose: Whether to enable verbose logging
            template_only: Whether to generate only the template structure
            revise_site: Whether to revise the site landing page
        """
        self.logger = logging.getLogger("slim-doc-generator")
        
        self.output_dir = Path(output_dir).resolve()
        self.template_repo = template_repo
        self.use_ai = use_ai
        self.config = load_config(config_file) if config_file else {}
        self.verbose = verbose
        self.template_only = template_only
        self.revise_site = revise_site
        
        # Initialize template manager and config updater
        self.template_manager = TemplateManager(template_repo, str(self.output_dir), self.logger)
        self.config_updater = ConfigUpdater(str(self.output_dir), self.logger)
        
        # Initialize target repo analysis if provided
        if target_repo_path:
            self.target_repo_path = Path(target_repo_path).resolve()
            
            if not self.target_repo_path.exists():
                raise ValueError(f"Target repository path does not exist: {target_repo_path}")
            
            self.logger.info(f"Initialized SLIM Doc Generator for {self.target_repo_path.name}")
        else:
            self.target_repo_path = None
            self.logger.info("Initialized SLIM Doc Generator in template-only mode")
    
    def generate(self) -> bool:
        """
        Generate the documentation site.
        
        Returns:
            True if generation was successful, False otherwise
        """
        try:
            self.logger.info("Starting documentation generation")
            
            # Step 1: Setup template
            if not self._setup_template():
                return False
            
            # Step 2: Analyze repository (if not template-only)
            repo_info = {}
            if not self.template_only and self.target_repo_path:
                repo_info = self._analyze_repository()
                if not repo_info:
                    return False
            
            # Step 3: Generate content
            if not self.template_only:
                if not self._generate_content(repo_info):
                    return False
            
            # Step 4: Update configuration
            if not self._update_configuration(repo_info):
                return False
            
            # Step 5: Revise site if requested
            if self.revise_site and not self.template_only:
                if not self._revise_site():
                    return False
            
            self.logger.info("Documentation generation completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during documentation generation: {str(e)}")
            return False
    
    def _setup_template(self) -> bool:
        """Setup the documentation template."""
        try:
            self.logger.info("Setting up documentation template")
            return self.template_manager.clone_template()
        except Exception as e:
            self.logger.error(f"Error setting up template: {str(e)}")
            return False
    
    def _analyze_repository(self) -> Dict:
        """Analyze the target repository using utils."""
        try:
            self.logger.info(f"Analyzing repository: {self.target_repo_path}")
            
            # Use repo_utils for comprehensive analysis
            repo_info = scan_repository(self.target_repo_path)
            
            # Add git-specific information if it's a git repo
            if is_git_repository(str(self.target_repo_path)):
                extract_git_info(str(self.target_repo_path), repo_info)
            
            self.logger.info(f"Repository analysis complete: {len(repo_info.get('files', []))} files, "
                           f"{len(repo_info.get('languages', []))} languages detected")
            
            return repo_info
            
        except Exception as e:
            self.logger.error(f"Error analyzing repository: {str(e)}")
            return {}
    
    def _generate_content(self, repo_info: Dict) -> bool:
        """Generate documentation content."""
        try:
            self.logger.info("Generating documentation content")
            
            # Define content sections to generate
            sections = [
                ("overview", "Overview"),
                ("installation", "Installation"),
                ("api", "API Reference"),
                ("development", "Development"),
                ("contributing", "Contributing")
            ]
            
            for section_key, section_name in sections:
                self.logger.debug(f"Generating {section_name} content")
                
                # Generate base content using repository information
                base_content = self._generate_section_content(section_key, repo_info)
                
                # Enhance with AI if enabled
                if self.use_ai and base_content:
                    enhanced_content = enhance_content(
                        content=base_content,
                        practice_type="docgen",
                        section_name=section_key,
                        model=self.use_ai
                    )
                    base_content = enhanced_content
                
                # Save content to appropriate file
                if base_content:
                    self._save_section_content(section_key, base_content)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error generating content: {str(e)}")
            return False
    
    def _generate_section_content(self, section_key: str, repo_info: Dict) -> str:
        """Generate base content for a specific section."""
        # This is a simplified implementation
        # In the full version, this would use the content generators
        
        if section_key == "overview":
            return self._generate_overview_content(repo_info)
        elif section_key == "installation":
            return self._generate_installation_content(repo_info)
        elif section_key == "api":
            return self._generate_api_content(repo_info)
        elif section_key == "development":
            return self._generate_development_content(repo_info)
        elif section_key == "contributing":
            return self._generate_contributing_content(repo_info)
        
        return ""
    
    def _generate_overview_content(self, repo_info: Dict) -> str:
        """Generate overview content."""
        project_name = repo_info.get('project_name', 'Project')
        description = repo_info.get('description', 'A software project')
        languages = repo_info.get('languages', [])
        
        content = f"""---
title: {escape_yaml_value(f"{project_name} Overview")}
---

# {project_name}

{description}

## Key Features

- Built with {', '.join(languages[:3]) if languages else 'modern technologies'}
- Comprehensive documentation
- Easy to use and extend

## Getting Started

To get started with {project_name}, see the [Installation Guide](./installation.md).

## Project Structure

This project is organized as follows:

"""
        
        # Add directory structure if available
        src_dirs = repo_info.get('src_dirs', [])
        test_dirs = repo_info.get('test_dirs', [])
        doc_dirs = repo_info.get('doc_dirs', [])
        
        if src_dirs:
            content += f"- **Source Code**: {', '.join(src_dirs[:3])}\n"
        if test_dirs:
            content += f"- **Tests**: {', '.join(test_dirs[:3])}\n"
        if doc_dirs:
            content += f"- **Documentation**: {', '.join(doc_dirs[:3])}\n"
        
        return content
    
    def _generate_installation_content(self, repo_info: Dict) -> str:
        """Generate installation content."""
        project_name = repo_info.get('project_name', 'Project')
        languages = repo_info.get('languages', [])
        
        content = f"""---
title: {escape_yaml_value("Installation Guide")}
---

# Installation

This guide will help you install and set up {project_name}.

## Prerequisites

"""
        
        if 'Python' in languages:
            content += "- Python 3.7 or higher\n"
        if 'JavaScript' in languages or 'TypeScript' in languages:
            content += "- Node.js 14 or higher\n- npm or yarn\n"
        if 'Java' in languages:
            content += "- Java 8 or higher\n- Maven or Gradle\n"
        
        content += """
## Installation Steps

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd """ + project_name.lower().replace(' ', '-') + """
   ```

2. Install dependencies:
"""
        
        if 'Python' in languages:
            content += """   ```bash
   pip install -r requirements.txt
   ```
"""
        if 'JavaScript' in languages or 'TypeScript' in languages:
            content += """   ```bash
   npm install
   # or
   yarn install
   ```
"""
        
        content += """
3. Run the application:
   ```bash
   # Add specific run commands here
   ```

## Verification

To verify the installation was successful:

```bash
# Add verification commands here
```
"""
        
        return content
    
    def _generate_api_content(self, repo_info: Dict) -> str:
        """Generate API documentation content."""
        project_name = repo_info.get('project_name', 'Project')
        
        content = f"""---
title: {escape_yaml_value("API Reference")}
---

# API Reference

This document provides a comprehensive reference for the {project_name} API.

## Overview

The {project_name} API provides programmatic access to core functionality.

## Authentication

<!-- Add authentication details here -->

## Endpoints

<!-- Add API endpoints documentation here -->

## Examples

<!-- Add usage examples here -->

## Error Handling

<!-- Add error handling information here -->
"""
        
        return content
    
    def _generate_development_content(self, repo_info: Dict) -> str:
        """Generate development guide content."""
        project_name = repo_info.get('project_name', 'Project')
        languages = repo_info.get('languages', [])
        
        content = f"""---
title: {escape_yaml_value("Development Guide")}
---

# Development Guide

This guide covers the development workflow for {project_name}.

## Development Environment

### Requirements

"""
        
        if 'Python' in languages:
            content += "- Python development environment\n"
        if 'JavaScript' in languages or 'TypeScript' in languages:
            content += "- Node.js development environment\n"
        
        content += """
### Setup

1. Clone the repository
2. Install development dependencies
3. Set up pre-commit hooks (if available)

## Code Structure

<!-- Add information about code organization -->

## Development Workflow

1. Create a feature branch
2. Make your changes
3. Run tests
4. Submit a pull request

## Testing

<!-- Add testing guidelines -->

## Code Style

<!-- Add code style guidelines -->
"""
        
        return content
    
    def _generate_contributing_content(self, repo_info: Dict) -> str:
        """Generate contributing guidelines content."""
        project_name = repo_info.get('project_name', 'Project')
        
        content = f"""---
title: {escape_yaml_value("Contributing Guide")}
---

# Contributing to {project_name}

We welcome contributions to {project_name}! This guide will help you get started.

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a feature branch
4. Make your changes
5. Submit a pull request

## Development Setup

See the [Development Guide](./development.md) for detailed setup instructions.

## Guidelines

### Code Quality

- Write clean, readable code
- Add tests for new functionality
- Follow existing code style
- Update documentation as needed

### Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Add a clear description of changes
4. Request review from maintainers

## Code of Conduct

<!-- Add code of conduct information -->

## Getting Help

<!-- Add information about getting help -->
"""
        
        return content
    
    def _save_section_content(self, section_key: str, content: str) -> None:
        """Save section content to the appropriate file."""
        # Determine output file path based on section
        docs_dir = self.output_dir / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        filename_map = {
            "overview": "overview.md",
            "installation": "installation.md", 
            "api": "api.md",
            "development": "development.md",
            "contributing": "contributing.md"
        }
        
        filename = filename_map.get(section_key, f"{section_key}.md")
        file_path = docs_dir / filename
        
        # Apply MDX escaping
        escaped_content = escape_mdx_special_characters(content)
        
        # Save content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(escaped_content)
        
        self.logger.debug(f"Saved {section_key} content to {file_path}")
        
        # Clean API documentation if needed
        if section_key == "api":
            clean_api_doc(str(file_path))
    
    def _update_configuration(self, repo_info: Dict) -> bool:
        """Update site configuration."""
        try:
            self.logger.info("Updating site configuration")
            
            config_data = {
                'title': repo_info.get('project_name', 'Documentation'),
                'tagline': repo_info.get('description', 'Project documentation'),
                'url': repo_info.get('repo_url', ''),
                'organizationName': repo_info.get('org_name', ''),
                'projectName': repo_info.get('project_name', '')
            }
            
            return self.config_updater.update_config(config_data)
            
        except Exception as e:
            self.logger.error(f"Error updating configuration: {str(e)}")
            return False
    
    def _revise_site(self) -> bool:
        """Revise the site landing page."""
        try:
            self.logger.info("Revising site landing page")
            
            # Import and use site reviser
            from jpl.slim.best_practices.docs_website_impl.site_reviser import SiteReviser
            from jpl.slim.utils.ai_utils import enhance_content
            
            # Create AI enhancer if available
            ai_enhancer = None
            if self.use_ai:
                class SimpleAIEnhancer:
                    def __init__(self, model):
                        self.model = model
                    
                    def enhance(self, content, section_name):
                        return enhance_content(content, "docgen", section_name, self.model)
                
                ai_enhancer = SimpleAIEnhancer(self.use_ai)
            
            site_reviser = SiteReviser(str(self.output_dir), self.logger, ai_enhancer)
            return site_reviser.revise_site()
            
        except Exception as e:
            self.logger.error(f"Error revising site: {str(e)}")
            return False