"""
Main generator class for the integrated SLIM Documentation Generator.
"""
import logging
import os
import shutil
import re
from typing import Dict, List, Optional, Tuple, Union

from jpl.slim.docgen.analyzer.repo_analyzer import RepoAnalyzer
from jpl.slim.docgen.content.overview_generator import OverviewGenerator
from jpl.slim.docgen.content.installation_generator import InstallationGenerator
from jpl.slim.docgen.content.api_generator import ApiGenerator
from jpl.slim.docgen.content.development_generator import DevelopmentGenerator
from jpl.slim.docgen.content.contributing_generator import ContributingGenerator
from jpl.slim.docgen.enhancer.ai_enhancer import AIEnhancer
from jpl.slim.docgen.template.template_manager import TemplateManager
from jpl.slim.docgen.template.config_updater import ConfigUpdater
from jpl.slim.docgen.site_reviser import SiteReviser
from jpl.slim.docgen.utils.helpers import load_config, escape_mdx_special_characters, clean_api_doc


class SlimDocGenerator:
    """
    Main class for generating documentation sites based on the SLIM template.
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
            target_repo_path: Path to the target repository to document (optional if template_only is True)
            output_dir: Directory where the documentation site will be generated
            template_repo: URL or path to the template repository
            use_ai: Optional AI model to use for content enhancement (format: provider/model)
            config_file: Optional path to configuration file
            verbose: Whether to enable verbose logging
            template_only: Whether to generate only the template structure without analyzing a repository
            revise_site: Whether to revise the site landing page based on documentation content
        """
        # Set up logging
        self.logger = logging.getLogger("slim-doc-generator")
        
        # Set properties
        self.output_dir = os.path.abspath(output_dir)
        self.template_repo = template_repo
        self.use_ai = use_ai
        self.config = load_config(config_file) if config_file else {}
        self.verbose = verbose
        self.template_only = template_only
        self.revise_site = revise_site
        
        # Initialize the template manager first 
        # since it's needed regardless of whether we're analyzing a repo
        self.template_manager = TemplateManager(template_repo, output_dir, self.logger)
        self.config_updater = ConfigUpdater(output_dir, self.logger)
        
        # Initialize site reviser if needed
        if revise_site:
            # Pass the AI enhancer to the site reviser if available
            ai_enhancer = AIEnhancer(use_ai, self.logger) if use_ai else None
            self.site_reviser = SiteReviser(output_dir, self.logger, ai_enhancer)
        else:
            self.site_reviser = None
        
        # Initialize AI enhancer if enabled
        self.ai_enhancer = AIEnhancer(use_ai, self.logger) if use_ai else None
        
        # Only initialize repo-specific components if we have a target repo
        if target_repo_path:
            self.target_repo_path = os.path.abspath(target_repo_path)
            
            # Validate target repository
            if not os.path.exists(target_repo_path):
                raise ValueError(f"Target repository path does not exist: {target_repo_path}")
            
            # Initialize analyzer and content generators
            self.analyzer = RepoAnalyzer(target_repo_path, self.logger)
            
            # Initialize content generators
            self.content_generators = {
                "overview": OverviewGenerator(self.target_repo_path, self.logger),
                "installation": InstallationGenerator(self.target_repo_path, self.logger),
                "api": ApiGenerator(self.target_repo_path, self.logger),
                "development": DevelopmentGenerator(self.target_repo_path, self.logger),
                "contributing": ContributingGenerator(self.target_repo_path, self.logger)
            }
            
            self.logger.info(f"Initialized SLIM Doc Generator for {os.path.basename(target_repo_path)}")
        else:
            # Template-only mode
            if not template_only:
                raise ValueError("Target repository path is required unless template_only is True")
                
            self.target_repo_path = None
            self.analyzer = None
            self.content_generators = None
            
            self.logger.info(f"Initialized SLIM Doc Generator in template-only mode")
    
    def generate(self) -> bool:
        """
        Generate the documentation site.
        
        Returns:
            True if generation was successful, False otherwise
        """
        try:
            # Step 1: Clone the template repository
            if not self.template_manager.clone_template():
                return False
            
            # For template-only mode, we're done after applying AI enhancement
            if self.template_only:
                self._generate_template_only()
                
                # Apply site revision if requested
                if self.revise_site and self.site_reviser:
                    self.site_reviser.revise()
                    
                return True
            
            # If we're here, we're not in template-only mode, so proceed with content generation
                
            # Step 2: Analyze the target repository
            repo_info = self.analyzer.analyze()
            
            # Step 3: Create the docs directory
            docs_dir = os.path.join(self.output_dir, 'docs')
            os.makedirs(docs_dir, exist_ok=True)
            
            # Step 4: Generate content for each section
            sections = {
                "overview": "Overview",
                "installation": "Installation",
                "api": "API Reference",
                "development": "Development",
                "contributing": "Contributing"
            }
            
            api_doc_path = None  # Track the API doc path for special cleaning
            
            for section_id, section_title in sections.items():
                # Generate content
                generator = self.content_generators[section_id]
                content = generator.generate(repo_info)
                
                # Enhance with AI if enabled
                if self.ai_enhancer and content:
                    content = self.ai_enhancer.enhance(content, section_id)
                
                # Write to file if content was generated
                if content:
                    # Escape special characters that might cause MDX parsing issues
                    content = escape_mdx_special_characters(content)
                    
                    file_path = os.path.join(docs_dir, f"{section_id}.md")
                    with open(file_path, 'w') as f:
                        # Add frontmatter
                        f.write("---\n")
                        f.write(f"id: {section_id}\n")
                        f.write(f"title: {section_title}\n")
                        f.write("---\n\n")
                        f.write(content)
                    self.logger.info(f"Generated {section_id} content")
                    
                    # Special handling for API doc - save path for additional cleaning
                    if section_id == "api":
                        api_doc_path = file_path
            
            # Apply additional cleaning to the API documentation
            if api_doc_path:
                clean_api_doc(api_doc_path)
                self.logger.info("Applied additional cleaning to API documentation")
            
            # Step 5: Generate index.md
            self._generate_index(repo_info, docs_dir)
            
            # Step 6: Update configuration files - must come after content generation
            # so we know which sections were actually created
            self.config_updater.update_config(repo_info)
            
            # Step 7: Generate or update sidebars.js
            sections_with_content = {section_id for section_id in sections if 
                                    os.path.exists(os.path.join(docs_dir, f"{section_id}.md"))}
            sections_with_content.add("index")  # Make sure index is always included
            self.config_updater.update_sidebars(sections_with_content)
            
            # Step 8: Verify the structure is correct for Docusaurus
            self._verify_docusaurus_structure()
            
            # Step 9: Revise the site landing page if requested
            if self.revise_site and self.site_reviser:
                self.site_reviser.revise()
            
            self.logger.info(f"Documentation successfully generated at {self.output_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error generating documentation: {str(e)}")
            if self.verbose:
                import traceback
                self.logger.debug(traceback.format_exc())
            return False

    def _generate_template_only(self) -> None:
        """
        Generate the template structure and apply AI enhancement if requested.
        In template-only mode, we preserve the exact template structure as provided
        and only modify content if AI enhancement is enabled.
        """
        self.logger.info("Generating template structure")
        
        # No AI enhancement, just return without modifying the template
        if not self.ai_enhancer:
            self.logger.info(f"Template structure generated at {self.output_dir}")
            self.logger.info("The template has been generated without any modifications.")
            return
            
        # Apply AI enhancement to existing content in the template
        self.logger.info("Applying AI enhancement to template content")
        
        # Look for markdown files in the docs directory
        docs_dir = os.path.join(self.output_dir, 'docs')
        if not os.path.exists(docs_dir):
            self.logger.warning("Docs directory not found in template")
            return
            
        # Find all markdown files in the docs directory
        md_files = []
        for root, _, files in os.walk(docs_dir):
            for file in files:
                if file.endswith('.md') or file.endswith('.mdx'):
                    md_files.append(os.path.join(root, file))
        
        if not md_files:
            self.logger.warning("No markdown files found in template docs directory")
            return
            
        # Enhance each markdown file with AI
        for md_file in md_files:
            try:
                file_name = os.path.basename(md_file)
                rel_path = os.path.relpath(md_file, self.output_dir)
                self.logger.info(f"Enhancing content in {rel_path}")
                
                # Read the file content
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract frontmatter if present
                frontmatter = {}
                if content.startswith('---'):
                    frontmatter_end = content.find('---', 3)
                    if frontmatter_end > 0:
                        frontmatter_content = content[3:frontmatter_end].strip()
                        # Parse frontmatter (simplified)
                        for line in frontmatter_content.split('\n'):
                            if ':' in line:
                                key, value = line.split(':', 1)
                                frontmatter[key.strip()] = value.strip()
                        
                        # Extract the main content after frontmatter
                        main_content = content[frontmatter_end + 3:].strip()
                else:
                    main_content = content
                
                # Enhance the content with AI
                section_id = frontmatter.get('id', os.path.splitext(file_name)[0])
                enhanced_content = self.ai_enhancer.enhance(main_content, section_id)
                
                # Reconstruct the file with frontmatter
                if frontmatter:
                    output_content = "---\n"
                    for key, value in frontmatter.items():
                        output_content += f"{key}: {value}\n"
                    output_content += "---\n\n" + enhanced_content
                else:
                    output_content = enhanced_content
                
                # Write the enhanced content back
                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(output_content)
                    
                self.logger.info(f"Enhanced content in {rel_path}")
                
            except Exception as e:
                self.logger.error(f"Error enhancing content in {os.path.basename(md_file)}: {str(e)}")
        
        self.logger.info(f"Template structure generated and enhanced at {self.output_dir}")

    def _generate_index(self, repo_info: Dict, docs_dir: str) -> None:
        """
        Generate the index.md file.
        
        Args:
            repo_info: Repository information dictionary
            docs_dir: Directory where docs are being generated
        """
        project_name = repo_info.get("project_name", os.path.basename(self.target_repo_path))
        description = repo_info.get("description", f"{project_name} documentation")
        
        content = [
            f"# {project_name} Documentation",
            "",
            description,
            "",
            "## Getting Started",
            ""
        ]
        
        # Add links to generated sections
        if os.path.exists(os.path.join(docs_dir, "overview.md")):
            content.append("- [Overview](overview.md)")
        if os.path.exists(os.path.join(docs_dir, "installation.md")):
            content.append("- [Installation](installation.md)")
        
        content.extend([
            "",
            "## Reference",
            ""
        ])
        
        if os.path.exists(os.path.join(docs_dir, "api.md")):
            content.append("- [API Reference](api.md)")
        if os.path.exists(os.path.join(docs_dir, "development.md")):
            content.append("- [Development](development.md)")
        if os.path.exists(os.path.join(docs_dir, "contributing.md")):
            content.append("- [Contributing](contributing.md)")
        
        # Join content and escape special characters
        index_content = "\n".join(content)
        index_content = escape_mdx_special_characters(index_content)
        
        # Write to file
        with open(os.path.join(docs_dir, 'index.md'), 'w') as f:
            f.write("---\n")
            f.write("slug: /\n")
            f.write("id: index\n")
            f.write(f"title: {project_name} Documentation\n")
            f.write("---\n\n")
            f.write(index_content)
        
        self.logger.info("Generated index.md")
        
    def _verify_docusaurus_structure(self) -> None:
        """
        Verify and fix the Docusaurus structure to prevent common errors.
        
        This method checks for common issues in the Docusaurus structure
        and attempts to fix them to prevent errors during build/runtime.
        """
        # Skip verification in template-only mode to avoid modifying the template
        if self.template_only:
            return
            
        # Check 1: Ensure the docs directory contains an index.md file
        docs_dir = os.path.join(self.output_dir, 'docs')
        index_path = os.path.join(docs_dir, 'index.md')
        if not os.path.exists(index_path):
            self.logger.warning("index.md not found in docs directory. Generating a basic one.")
            with open(index_path, 'w') as f:
                f.write("---\n")
                f.write("slug: /\n")
                f.write("id: index\n")
                f.write("title: Documentation\n")
                f.write("---\n\n")
                f.write("# Documentation\n\n")
                f.write("Welcome to the documentation.\n")
        
        # Check 2: Ensure the sidebars.js file exists and is properly formatted
        sidebars_path = os.path.join(self.output_dir, 'sidebars.js')
        if not os.path.exists(sidebars_path):
            self.logger.warning("sidebars.js not found. Generating a basic one.")
            with open(sidebars_path, 'w') as f:
                f.write("/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */\n")
                f.write("const sidebars = {\n")
                f.write("  tutorialSidebar: [\n")
                f.write("    {\n")
                f.write("      type: 'doc',\n")
                f.write("      id: 'index',\n")
                f.write("      label: 'Home',\n")
                f.write("    },\n")
                f.write("  ],\n")
                f.write("};\n\n")
                f.write("module.exports = sidebars;\n")
        
        # Check 3: Verify the docusaurus.config.js has the right sidebar ID
        config_path = os.path.join(self.output_dir, 'docusaurus.config.js')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config_content = f.read()
                
                # Make sure there's a reference to 'tutorialSidebar' in the navbar items
                if 'sidebarId: "tutorialSidebar"' not in config_content:
                    self.logger.warning("tutorialSidebar not found in docusaurus.config.js. Attempting to fix.")
                    if re.search(r'sidebarId:\s*"[^"]+"', config_content):
                        # Replace the existing sidebarId
                        config_content = re.sub(
                            r'sidebarId:\s*"[^"]+"',
                            'sidebarId: "tutorialSidebar"',
                            config_content
                        )
                        
                        with open(config_path, 'w') as f:
                            f.write(config_content)
            except Exception as e:
                self.logger.warning(f"Error checking docusaurus.config.js: {str(e)}")
        
        # Check 4: Make sure static directories exist
        static_dir = os.path.join(self.output_dir, 'static')
        if not os.path.exists(static_dir):
            os.makedirs(static_dir, exist_ok=True)
            
        img_dir = os.path.join(static_dir, 'img')
        if not os.path.exists(img_dir):
            os.makedirs(img_dir, exist_ok=True)
            
        self.logger.info("Verified Docusaurus structure")