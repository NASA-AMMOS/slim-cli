# File: src/jpl/slim/docgen/template/config_updater.py
"""
Updates configuration files for Docusaurus.
"""
import json
import logging
import os
import re
from typing import Dict, Set


class ConfigUpdater:
    """
    Updates configuration files for Docusaurus template.
    """
    
    def __init__(self, output_dir: str, logger: logging.Logger):
        """
        Initialize the configuration updater.
        
        Args:
            output_dir: Directory where the documentation is being generated
            logger: Logger instance
        """
        self.output_dir = output_dir
        self.logger = logger
    
    def _sanitize_package_name(self, name: str) -> str:
        """
        Sanitize package name to follow npm naming conventions.
        
        Args:
            name: Original package name
            
        Returns:
            Sanitized package name following npm rules
        """
        # Convert to lowercase
        sanitized = name.lower()
        
        # Replace spaces, colons, and other invalid characters with hyphens
        sanitized = re.sub(r'[^a-z0-9\-._~]', '-', sanitized)
        
        # Remove multiple consecutive hyphens
        sanitized = re.sub(r'-+', '-', sanitized)
        
        # Remove leading/trailing hyphens
        sanitized = sanitized.strip('-')
        
        # Ensure it doesn't start with a dot or underscore
        sanitized = re.sub(r'^[._]+', '', sanitized)
        
        # Ensure minimum length and doesn't exceed npm limits
        if len(sanitized) < 1:
            sanitized = 'documentation-site'
        elif len(sanitized) > 214:
            sanitized = sanitized[:214].rstrip('-')
        
        return sanitized
    
    def update_config(self, repo_info: Dict) -> bool:
        """
        Update Docusaurus configuration files with repository information.
        
        Args:
            repo_info: Repository information dictionary
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            self.logger.info("Updating Docusaurus configuration")
            
            # Fix common Docusaurus configuration issues first
            self._fix_common_config_issues()
            
            # Update docusaurus.config.js
            self._update_docusaurus_config(repo_info)
            
            # Update package.json
            self._update_package_json(repo_info)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating configuration: {str(e)}")
            return False
            
    def _fix_common_config_issues(self) -> None:
        """
        Fix common Docusaurus configuration issues.
        
        This method addresses known issues with the default SLIM docsite template configuration
        to ensure compatibility with our generated documentation.
        """
        config_path = os.path.join(self.output_dir, 'docusaurus.config.js')
        
        if not os.path.exists(config_path):
            return
            
        try:
            # Read current config
            with open(config_path, 'r') as f:
                config_content = f.read()
            
            changes_made = False
            
            # Fix 1: Ensure routeBasePath is set correctly
            if re.search(r'routeBasePath:\s*"docs"', config_content):
                config_content = re.sub(
                    r'routeBasePath:\s*"docs"',
                    'routeBasePath: "/"',
                    config_content
                )
                changes_made = True
                self.logger.info("Fixed routeBasePath in docusaurus.config.js")
            
            # Fix 2: Remove or update path in navbar that might cause issues
            if re.search(r'to:\s*"/docs"', config_content):
                config_content = re.sub(
                    r'to:\s*"/docs"',
                    'to: "/"',
                    config_content
                )
                changes_made = True
                self.logger.info("Fixed navbar paths in docusaurus.config.js")
                
            # Fix 3: Ensure the sidebar ID in the navbar matches our sidebar ID
            if re.search(r'sidebarId:\s*[\'"](?!tutorialSidebar)[^\'"]+[\'"]', config_content):
                config_content = re.sub(
                    r'sidebarId:\s*[\'"](?!tutorialSidebar)[^\'"]+[\'"]',
                    'sidebarId: "tutorialSidebar"',
                    config_content
                )
                changes_made = True
                self.logger.info("Fixed sidebar ID in docusaurus.config.js")
            
            # Only write if changes were made
            if changes_made:
                with open(config_path, 'w') as f:
                    f.write(config_content)
                
        except Exception as e:
            self.logger.warning(f"Error fixing common configuration issues: {str(e)}")
    
    def update_sidebars(self, sections: Set[str]) -> bool:
        """
        Update sidebar configuration with generated sections.
        
        Args:
            sections: Set of generated section IDs
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            self.logger.info("Updating sidebar configuration")
            
            # Define sidebar items
            sidebar_items = []
            
            # Add index as first item
            sidebar_items.append({
                'type': 'doc',
                'id': 'index',
                'label': 'Home'
            })
            
            # Add other sections in a specific order
            section_order = ['overview', 'installation', 'api', 'development', 'contributing']
            for section_id in section_order:
                if section_id in sections:
                    sidebar_items.append({
                        'type': 'doc',
                        'id': section_id,
                        'label': section_id.capitalize()
                    })
            
            # Generate JavaScript for sidebars.js
            sidebars_js_path = os.path.join(self.output_dir, 'sidebars.js')
            with open(sidebars_js_path, 'w') as f:
                f.write("/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */\n")
                f.write("const sidebars = {\n")
                # Using 'tutorialSidebar' as the sidebar ID to match the default navbar configuration
                f.write("  tutorialSidebar: [\n")
                
                for i, item in enumerate(sidebar_items):
                    f.write(f"    {{\n")
                    f.write(f"      type: '{item['type']}',\n")
                    f.write(f"      id: '{item['id']}',\n")
                    f.write(f"      label: '{item['label']}',\n")
                    f.write(f"    }}")
                    
                    if i < len(sidebar_items) - 1:
                        f.write(",\n")
                    else:
                        f.write("\n")
                
                f.write("  ],\n")
                f.write("};\n\n")
                f.write("module.exports = sidebars;\n")
            
            self.logger.info(f"Sidebar configuration updated with {len(sidebar_items)} items")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating sidebar configuration: {str(e)}")
            return False
    
    def _update_docusaurus_config(self, repo_info: Dict) -> None:
        """
        Update docusaurus.config.js with repository information.
        
        Args:
            repo_info: Repository information dictionary
        """
        config_path = os.path.join(self.output_dir, 'docusaurus.config.js')
        
        if not os.path.exists(config_path):
            self.logger.warning(f"docusaurus.config.js not found at {config_path}")
            return
        
        try:
            # Read current config
            with open(config_path, 'r') as f:
                config_content = f.read()
            
            # Update title
            project_name = repo_info.get("project_name", "Documentation Site")
            config_content = re.sub(
                r'title: .*?,',
                f'title: "{project_name}",',
                config_content
            )
            
            # Update tagline/description
            config_content = re.sub(
                r'tagline: .*?,',
                f'tagline: "{repo_info.get("description", "Documentation")}",',
                config_content
            )
            
            # Update routeBasePath if it exists (make sure the docs directory is at the root)
            config_content = re.sub(
                r'routeBasePath: .*?,',
                'routeBasePath: "/",',
                config_content
            )
            
            # Make sure the sidebar ID in the navbar item matches our sidebar
            # This is critical to fix the "Can't find any sidebar with id 'tutorialSidebar'" error
            if 'sidebarId: "docs"' in config_content:
                config_content = re.sub(
                    r'sidebarId: "docs"',
                    'sidebarId: "tutorialSidebar"',
                    config_content
                )
            
            # Update repository URL if available
            if repo_info.get("repo_url"):
                # Update organization name
                if repo_info.get("org_name"):
                    config_content = re.sub(
                        r'organizationName: .*?,',
                        f'organizationName: "{repo_info["org_name"]}",',
                        config_content
                    )
                
                # Update repository URL in navbar items
                config_content = re.sub(
                    r'href: "https://github.com/[^"]+",\s+label: "GitHub"',
                    f'href: "{repo_info["repo_url"]}",\n            label: "GitHub"',
                    config_content
                )
            
            # Write updated config
            with open(config_path, 'w') as f:
                f.write(config_content)
            
            self.logger.info("docusaurus.config.js updated successfully")
            
        except Exception as e:
            self.logger.error(f"Error updating docusaurus.config.js: {str(e)}")
            raise
    
    def _update_package_json(self, repo_info: Dict) -> None:
        """
        Update package.json with repository information.
        
        Args:
            repo_info: Repository information dictionary
        """
        package_path = os.path.join(self.output_dir, 'package.json')
        
        if not os.path.exists(package_path):
            self.logger.warning(f"package.json not found at {package_path}")
            return
        
        try:
            # Read current package.json
            with open(package_path, 'r') as f:
                package_data = json.load(f)
            
            # Update name with proper sanitization
            project_name = repo_info.get('project_name', 'documentation-site')
            sanitized_name = self._sanitize_package_name(project_name)
            package_data['name'] = sanitized_name
            self.logger.info(f"Sanitized package name from '{project_name}' to '{sanitized_name}'")
            
            # Update description
            if repo_info.get("description"):
                package_data['description'] = repo_info["description"]
            
            # Update repository
            if repo_info.get("repo_url"):
                if 'repository' not in package_data:
                    package_data['repository'] = {}
                
                if isinstance(package_data['repository'], str):
                    package_data['repository'] = {'url': repo_info["repo_url"]}
                else:
                    package_data['repository']['url'] = repo_info["repo_url"]
            
            # Write updated package.json
            with open(package_path, 'w') as f:
                json.dump(package_data, f, indent=2)
            
            self.logger.info("package.json updated successfully")
            
        except Exception as e:
            self.logger.error(f"Error updating package.json: {str(e)}")
            raise