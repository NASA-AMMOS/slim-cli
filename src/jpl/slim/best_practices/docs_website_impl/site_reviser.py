# File: src/jpl/slim/docgen/site_reviser.py
"""
Site revision module for updating landing page content based on docs/overview.md using AI enhancement.
"""
import logging
import os
import re
from typing import Dict, Optional, Tuple

from jpl.slim.best_practices.docs_website_impl.helpers import extract_frontmatter
from jpl.slim.utils.prompt_utils import get_prompt


class SiteReviser:
    """
    Updates site landing page content based on docs/overview.md using AI enhancement.
    """
    
    def __init__(self, output_dir: str, logger: logging.Logger, ai_enhancer=None):
        """
        Initialize the site reviser.
        
        Args:
            output_dir: Directory where the documentation site is generated
            logger: Logger instance
            ai_enhancer: Optional AI enhancer for content improvement
        """
        self.output_dir = output_dir
        self.logger = logger
        self.ai_enhancer = ai_enhancer
        self.docs_dir = os.path.join(output_dir, 'docs')
        self.src_dir = os.path.join(output_dir, 'src')
        self.pages_dir = os.path.join(self.src_dir, 'pages')
        self.components_dir = os.path.join(self.src_dir, 'components')
        self.static_dir = os.path.join(output_dir, 'static')
        self.img_dir = os.path.join(self.static_dir, 'img')
        
    def revise_site(self) -> bool:
        """
        Revise the site landing page content based on docs/overview.md using AI enhancement.
        
        Returns:
            True if revision was successful, False otherwise
        """
        try:
            self.logger.debug("Revising site landing page content based on docs/overview.md")
            
            # Check if necessary directories exist
            if not os.path.exists(self.docs_dir):
                self.logger.warning(f"Docs directory not found at {self.docs_dir}")
                return False
                
            if not os.path.exists(self.pages_dir):
                self.logger.warning(f"Pages directory not found at {self.pages_dir}")
                return False
            
            # Check if AI enhancer is available
            if not self.ai_enhancer:
                self.logger.warning("AI enhancer is not available. Please specify '--use-ai' option.")
                return False
            
            # Check if overview.md exists
            overview_path = os.path.join(self.docs_dir, 'overview.md')
            if not os.path.exists(overview_path):
                self.logger.warning(f"overview.md not found at {overview_path}")
                return False
            
            # Read overview.md content to use as context
            overview_content = self._read_overview_content(overview_path)
            if not overview_content:
                self.logger.warning("Could not read content from overview.md")
                return False
            
            # Update landing page files using AI with overview.md as context
            # Track overall success but continue even if some files fail
            overall_success = True
            
            # Try updating each file independently to avoid one failure stopping the whole process
            try:
                if not self._update_index_js_with_ai(overview_content):
                    overall_success = False
            except Exception as e:
                self.logger.error(f"Error updating index.js: {str(e)}")
                overall_success = False
            
            try:
                if not self._update_homepage_features_with_ai(overview_content):
                    overall_success = False
            except Exception as e:
                self.logger.error(f"Error updating HomepageFeatures: {str(e)}")
                overall_success = False
            
            try:
                if not self._update_docusaurus_config_with_ai(overview_content):
                    overall_success = False
            except Exception as e:
                self.logger.error(f"Error updating docusaurus.config.js: {str(e)}")
                overall_success = False
            
            if overall_success:
                self.logger.debug("Successfully revised site landing page content using AI with overview.md context")
                return True
            else:
                self.logger.warning("Some files could not be updated, but the process completed")
                # Return True since we still successfully updated some files
                return True
                
        except Exception as e:
            self.logger.error(f"Error revising site landing page: {str(e)}")
            return False
    
    def _read_overview_content(self, overview_path: str) -> Optional[str]:
        """
        Read content from overview.md.
        
        Args:
            overview_path: Path to overview.md
            
        Returns:
            Content of overview.md or None if reading failed
        """
        try:
            with open(overview_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract frontmatter and content
            frontmatter, content_text = extract_frontmatter(content)
            
            # Return full content including frontmatter for AI context
            return content
            
        except Exception as e:
            self.logger.error(f"Error reading content from overview.md: {str(e)}")
            return None
    
    def _update_index_js_with_ai(self, overview_content: str) -> bool:
        """
        Update index.js using AI with overview.md as context.
        
        Args:
            overview_content: Content of overview.md
            
        Returns:
            True if update was successful, False otherwise
        """
        index_js_path = os.path.join(self.pages_dir, 'index.js')
        if not os.path.exists(index_js_path):
            self.logger.warning(f"index.js not found at {index_js_path}")
            return False
            
        try:
            # Read current index.js
            with open(index_js_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
            
            # Get the prompt from centralized prompts.yaml
            base_prompt = get_prompt('docgen', 'index_js_update')
            if not base_prompt:
                self.logger.warning("Could not load index_js_update prompt from prompts.yaml, using fallback")
                base_prompt = "Using the provided overview.md content as context, update ONLY the text content in this React component (index.js) while preserving its existing structure completely."
            
            # Create full prompt with context
            prompt = f"""
{base_prompt}

OVERVIEW.MD CONTENT (Use this as the source of information):
```
{overview_content}
```

CURRENT INDEX.JS:
```
{current_content}
```

Return ONLY the complete, updated index.js code.
"""
            
            # Use AI to update the content
            self.logger.debug("Enhancing index_js_update content with AI")
            updated_content = self.ai_enhancer.enhance(prompt, "index_js_update")
            
            if updated_content:
                self.logger.debug(f"AI-generated content for index.js:\n{updated_content}")
                # Remove any markdown code blocks
                updated_content = self._extract_code_block(updated_content, "javascript")
                
                # Only write if the content changed
                if updated_content != current_content:
                    with open(index_js_path, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                    
                    self.logger.debug("Updated index.js content using AI with overview.md context")
                else:
                    self.logger.debug("No changes needed for index.js")
                
                return True
            else:
                self.logger.warning("AI failed to generate updated index.js content")
                return False
            
        except Exception as e:
            self.logger.error(f"Error updating index.js: {str(e)}")
            return False
    
    def _update_homepage_features_with_ai(self, overview_content: str) -> bool:
        """
        Update HomepageFeatures component using AI with overview.md as context.
        
        Args:
            overview_content: Content of overview.md
            
        Returns:
            True if update was successful, False otherwise
        """
        # Find the HomepageFeatures directory
        homepage_features_dir = os.path.join(self.components_dir, 'HomepageFeatures')
        if not os.path.exists(homepage_features_dir):
            self.logger.warning("HomepageFeatures component not found")
            return False
        
        # Find the index.js file
        index_js_path = os.path.join(homepage_features_dir, 'index.js')
        if not os.path.exists(index_js_path):
            self.logger.warning("HomepageFeatures/index.js not found")
            return False
        
        try:
            # Read current HomepageFeatures component
            with open(index_js_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
            
            # Get the prompt from centralized prompts.yaml
            base_prompt = get_prompt('docgen', 'homepage_features_update')
            if not base_prompt:
                self.logger.warning("Could not load homepage_features_update prompt from prompts.yaml, using fallback")
                base_prompt = "Using the provided overview.md content as context, update ONLY the feature descriptions in this React component while preserving its structure."
            
            # Create full prompt with context
            prompt = f"""
{base_prompt}

OVERVIEW.MD CONTENT (Use this as the source of information):
```
{overview_content}
```

CURRENT COMPONENT:
```
{current_content}
```

Return ONLY the updated component code.
"""
            
            # Use AI to update the content
            self.logger.debug("Enhancing homepage_features_update content with AI")
            updated_content = self.ai_enhancer.enhance(prompt, "homepage_features_update")
            
            if updated_content:
                self.logger.debug(f"AI-generated content for HomepageFeatures:\n{updated_content}")
                # Remove any markdown code blocks
                updated_content = self._extract_code_block(updated_content, "javascript")
                
                # Only write if the content changed
                if updated_content != current_content:
                    with open(index_js_path, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                    
                    self.logger.debug("Updated HomepageFeatures content using AI with overview.md context")
                else:
                    self.logger.debug("No changes needed for HomepageFeatures")
                
                return True
            else:
                self.logger.warning("AI failed to generate updated HomepageFeatures content")
                return False
            
        except Exception as e:
            self.logger.error(f"Error updating HomepageFeatures: {str(e)}")
            return False
    
    def _update_docusaurus_config_with_ai(self, overview_content: str) -> bool:
        """
        Update docusaurus.config.js using AI with overview.md as context.
        
        Args:
            overview_content: Content of overview.md
            
        Returns:
            True if update was successful, False otherwise
        """
        config_path = os.path.join(self.output_dir, 'docusaurus.config.js')
        if not os.path.exists(config_path):
            self.logger.warning(f"docusaurus.config.js not found at {config_path}")
            return False
        
        try:
            # Read current config
            with open(config_path, 'r', encoding='utf-8') as f:
                current_config = f.read()
            
            # Get the prompt from centralized prompts.yaml
            base_prompt = get_prompt('docgen', 'docusaurus_config_update')
            if not base_prompt:
                self.logger.warning("Could not load docusaurus_config_update prompt from prompts.yaml, using fallback")
                base_prompt = "Using the provided overview.md content as context, update ONLY the title and tagline in this docusaurus.config.js file."
            
            # Create full prompt with context
            prompt = f"""
{base_prompt}

OVERVIEW.MD CONTENT (Use this as the source of information):
```
{overview_content}
```

CURRENT CONFIG:
```
{current_config}
```

Return ONLY the updated configuration code.
"""
            
            # Use AI to update the content
            self.logger.debug("Enhancing docusaurus_config_update content with AI")
            updated_config = self.ai_enhancer.enhance(prompt, "docusaurus_config_update")
            
            if updated_config:
                self.logger.debug(f"AI-generated content for docusaurus.config.js:\n{updated_config}")
                # Remove any markdown code blocks
                updated_config = self._extract_code_block(updated_config, "javascript")
                
                # Only write if the content changed
                if updated_config != current_config:
                    with open(config_path, 'w', encoding='utf-8') as f:
                        f.write(updated_config)
                    
                    self.logger.debug("Updated docusaurus.config.js content using AI with overview.md context")
                else:
                    self.logger.debug("No changes needed for docusaurus.config.js")
                
                return True
            else:
                self.logger.warning("AI failed to generate updated docusaurus.config.js content")
                return False
            
        except Exception as e:
            self.logger.error(f"Error updating docusaurus.config.js: {str(e)}")
            return False
    
    def _extract_code_block(self, content: str, language: str) -> str:
        """
        Extract code from content, removing markdown code blocks and explanations.
        
        Args:
            content: Content possibly containing code blocks
            language: Language of the code for markdown block detection
            
        Returns:
            Clean code without markdown formatting
        """
        # Check if the content is already wrapped in a markdown code block
        code_block_pattern = rf"```(?:{language})?\n(.*?)```"
        code_match = re.search(code_block_pattern, content, re.DOTALL)
        
        if code_match:
            # Extract just the code from the markdown code block
            return code_match.group(1).strip()
        
        # If not in a code block, try to identify and remove any explanatory text
        # This is a heuristic approach to find where the code starts
        
        # Look for common import statements at the start of JS files
        if language == "javascript":
            import_match = re.search(r'^(?:import|const|let|var|function|class|\/\*\*)', content, re.MULTILINE)
            if import_match:
                return content[import_match.start():].strip()
        
        # If we couldn't identify a clear pattern, just return the content as is
        return content.strip()
