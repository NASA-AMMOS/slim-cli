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
from jpl.slim.best_practices.docs_website_impl.content_validator import ContentValidator
from jpl.slim.best_practices.docs_website_impl.markdown_linter import MarkdownLinter

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
        revise_site: bool = False,
        strict_ai: bool = True
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
            strict_ai: Whether to fail if AI enhancement fails (default True)
        """
        self.logger = logging.getLogger("slim-doc-generator")
        
        self.output_dir = Path(output_dir).resolve()
        self.template_repo = template_repo
        self.use_ai = use_ai
        self.config = load_config(config_file) if config_file else {}
        self.verbose = verbose
        self.template_only = template_only
        self.revise_site = revise_site
        self.strict_ai = strict_ai
        
        # Initialize template manager and config updater
        self.template_manager = TemplateManager(template_repo, str(self.output_dir), self.logger)
        self.config_updater = ConfigUpdater(str(self.output_dir), self.logger)
        
        # Initialize target repo analysis if provided
        if target_repo_path:
            self.target_repo_path = Path(target_repo_path).resolve()
            
            if not self.target_repo_path.exists():
                raise ValueError(f"Target repository path does not exist: {target_repo_path}")
            
            self.logger.debug(f"Initialized SLIM Doc Generator for {self.target_repo_path.name}")
        else:
            self.target_repo_path = None
            self.logger.debug("Initialized SLIM Doc Generator in template-only mode")
    
    def generate(self, progress_task=None, progress=None) -> bool:
        """
        Generate the documentation site using simplified AI-driven flow.
        
        Args:
            progress_task: Optional progress task to update
            progress: Optional progress instance
        
        Returns:
            True if generation was successful, False otherwise
        """
        try:
            self.logger.debug("Starting documentation generation")
            
            # Step 1: Clone template to output directory
            print("📁 Setting up template...")
            if not self._setup_template():
                print("❌ Template setup failed")
                return False
            
            # Step 2: Analyze repository to extract basic information
            print("🔍 Analyzing repository...")
            repo_info = self._analyze_repository() if self.target_repo_path else {}
            
            # Step 3: Replace universal placeholders (PROJECT_NAME, etc.)
            print("🔄 Replacing placeholders...")
            if not self._replace_basic_placeholders(repo_info):
                print("❌ Placeholder replacement failed")
                return False
            
            # Step 4: Use AI to fill [INSERT_CONTENT] markers in all markdown files
            if self.use_ai:
                print("🤖 Starting AI content enhancement...")
                if not self._ai_enhance_content(repo_info, progress, progress_task):
                    print("❌ AI enhancement failed")
                    return False
            
            # Step 5: Validate content and fix issues
            print("✅ Validating and fixing content...")
            if not self._validate_and_fix_content(repo_info):
                return False
            self.logger.debug("Documentation generation completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during documentation generation: {str(e)}")
            return False
    
    def _setup_template(self) -> bool:
        """Setup the documentation template."""
        try:
            self.logger.debug("Setting up documentation template")
            return self.template_manager.clone_template()
        except Exception as e:
            self.logger.error(f"Error setting up template: {str(e)}")
            return False
    
    def _analyze_repository(self) -> Dict:
        """Analyze the target repository using utils."""
        try:
            self.logger.debug(f"Analyzing repository: {self.target_repo_path}")
            
            # Use repo_utils for comprehensive analysis
            repo_info = scan_repository(self.target_repo_path)
            
            # Add git-specific information if it's a git repo
            if is_git_repository(str(self.target_repo_path)):
                extract_git_info(str(self.target_repo_path), repo_info)
            
            self.logger.debug(f"Repository analysis complete: {len(repo_info.get('files', []))} files, "
                           f"{len(repo_info.get('languages', []))} languages detected")
            
            return repo_info
            
        except Exception as e:
            self.logger.error(f"Error analyzing repository: {str(e)}")
            return {}
    
    def _replace_basic_placeholders(self, repo_info: Dict) -> bool:
        """Replace universal placeholders in template files."""
        try:
            self.logger.debug("Replacing basic placeholders")
            
            # Extract basic project information
            project_name = repo_info.get('project_name', 'Documentation Site')
            project_description = repo_info.get('description', 'A software project documentation site')
            project_overview = repo_info.get('overview', project_description)
            github_org = repo_info.get('github_org', 'your-org')
            github_repo = repo_info.get('github_repo', 'your-repo')
            
            print(f"  🔧 Replacing PROJECT_NAME with: {project_name}")
            
            # Define placeholder mappings (simplified set)
            placeholders = {
                '{{PROJECT_NAME}}': project_name,
                '{{PROJECT_DESCRIPTION}}': project_description,
                '{{PROJECT_OVERVIEW}}': project_overview,
                '{{GITHUB_ORG}}': github_org,
                '{{GITHUB_REPO}}': github_repo,
            }
            
            # Extract and add feature placeholders
            features = self._extract_features(repo_info)
            for i, feature in enumerate(features[:6], 1):  # Limit to 6 features
                placeholders[f'{{{{FEATURE_{i}_TITLE}}}}'] = feature.get('title', f'Feature {i}')
                placeholders[f'{{{{FEATURE_{i}_DESCRIPTION}}}}'] = feature.get('description', f'Description for feature {i}')
            
            # Fill remaining feature slots if needed
            for i in range(len(features) + 1, 7):
                placeholders[f'{{{{FEATURE_{i}_TITLE}}}}'] = f'Feature {i}'
                placeholders[f'{{{{FEATURE_{i}_DESCRIPTION}}}}'] = f'Description for feature {i}'
            
            # Replace placeholders in all files
            return self._replace_placeholders_in_files(placeholders)
            
        except Exception as e:
            self.logger.error(f"Error replacing basic placeholders: {str(e)}")
            return False
    
    def _extract_features(self, repo_info: Dict) -> List[Dict]:
        """Extract key features from repository analysis."""
        features = []
        
        # Extract features from README if available
        readme_content = repo_info.get('readme_content', '')
        if readme_content:
            # Simple feature extraction logic
            lines = readme_content.split('\n')
            current_feature = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('- ') or line.startswith('* '):
                    # Found a bullet point - potential feature
                    feature_text = line[2:].strip()
                    if len(feature_text) > 10:  # Only consider substantial bullet points
                        features.append({
                            'title': feature_text[:50] + ('...' if len(feature_text) > 50 else ''),
                            'description': feature_text
                        })
        
        # If no features found, generate generic ones based on project type
        if not features:
            languages = repo_info.get('languages', [])
            if 'Python' in languages:
                features.extend([
                    {'title': 'Python-Based', 'description': 'Built with Python for reliability and ease of use'},
                    {'title': 'Easy Installation', 'description': 'Simple pip install process'},
                ])
            if 'JavaScript' in languages:
                features.extend([
                    {'title': 'Modern JavaScript', 'description': 'Built with modern JavaScript frameworks'},
                    {'title': 'NPM Package', 'description': 'Easy installation via npm'},
                ])
            
            # Add generic features
            features.extend([
                {'title': 'Open Source', 'description': 'Open source project with community contributions'},
                {'title': 'Well Documented', 'description': 'Comprehensive documentation and examples'},
                {'title': 'Actively Maintained', 'description': 'Regular updates and bug fixes'},
                {'title': 'Cross Platform', 'description': 'Works on multiple operating systems'},
            ])
        
        return features[:6]  # Return max 6 features
    
    def _replace_placeholders_in_files(self, placeholders: Dict[str, str]) -> bool:
        """Replace placeholders in all template files."""
        try:
            # Find all files that might contain placeholders
            files_to_process = []
            for root, dirs, files in os.walk(self.output_dir):
                for file in files:
                    if file.endswith(('.js', '.md', '.json', '.tsx', '.jsx')):
                        files_to_process.append(os.path.join(root, file))
            
            for file_path in files_to_process:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Replace all placeholders
                    modified = False
                    for placeholder, replacement in placeholders.items():
                        if placeholder in content:
                            print(f"    🔍 Found {placeholder} in {os.path.basename(file_path)}, replacing with: {replacement}")
                            content = content.replace(placeholder, replacement)
                            modified = True
                    
                    # Write back if modified
                    if modified:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"    ✅ Updated placeholders in {os.path.basename(file_path)}")
                        self.logger.debug(f"Updated placeholders in {file_path}")
                
                except Exception as e:
                    self.logger.warning(f"Error processing file {file_path}: {str(e)}")
                    continue
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error replacing placeholders in files: {str(e)}")
            return False
    
    def _ai_enhance_content(self, repo_info: Dict, progress=None, progress_task=None) -> bool:
        """Use AI to enhance each markdown file with linting and retry loop."""
        try:
            self.logger.debug("AI enhancing content one file at a time")
            
            # Find all markdown files in docs directory
            docs_dir = self.output_dir / "docs"
            if not docs_dir.exists():
                self.logger.warning("No docs directory found")
                return True
            
            markdown_files = []
            for root, dirs, files in os.walk(docs_dir):
                for file in files:
                    if file.endswith('.md'):
                        markdown_files.append(os.path.join(root, file))
            
            print(f"  📚 Found {len(markdown_files)} markdown files to enhance")
            
            # Sort files by priority (core files first)
            priority_files = []
            regular_files = []
            
            for file_path in markdown_files:
                file_name = os.path.basename(file_path).lower()
                if any(priority in file_name for priority in ['installation', 'quick-start', 'features', 'contributing']):
                    priority_files.append(file_path)
                else:
                    regular_files.append(file_path)
            
            all_files = priority_files + regular_files
            linter = MarkdownLinter(self.logger)
            
            for i, file_path in enumerate(all_files):
                file_name = os.path.basename(file_path)
                relative_path = os.path.relpath(file_path, self.output_dir)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check if file needs enhancement
                    if '[INSERT_CONTENT]' not in content:
                        continue
                    
                    # Try to enhance the file with retry loop
                    max_attempts = 10
                    success = False
                    
                    for attempt in range(1, max_attempts + 1):
                        print(f"  📝 Generating {relative_path} (attempt {attempt}/{max_attempts})...")
                        
                        # Generate content for this file
                        enhanced_content = self._ai_enhance_single_file(content, file_path, repo_info)
                        
                        if not enhanced_content or enhanced_content == content:
                            self.logger.warning(f"AI failed to enhance {file_name} on attempt {attempt}")
                            continue
                        
                        # Lint the enhanced content
                        lint_errors = linter.lint_content(enhanced_content, file_name)
                        
                        # Check for critical errors and validation issues
                        critical_errors = [
                            error for error in lint_errors 
                            if error.error_type in ['unclosed_tag', 'email_as_jsx', 'url_as_jsx', 
                                                   'loose_angle_bracket', 'at_in_tag']
                        ]
                        
                        # Check for remaining placeholders
                        validation_errors = []
                        if '{{PROJECT_NAME}}' in enhanced_content:
                            validation_errors.append("Contains unreplaced {{PROJECT_NAME}} placeholder")
                        if '[INSERT_CONTENT]' in enhanced_content:
                            validation_errors.append("Contains unreplaced [INSERT_CONTENT] marker")
                        
                        if not critical_errors and not validation_errors:
                            # Success! Write the file
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(enhanced_content)
                            self.logger.debug(f"Successfully enhanced {file_name} on attempt {attempt}")
                            success = True
                            break
                        else:
                            error_msgs = []
                            if critical_errors:
                                error_msgs.append(f"{len(critical_errors)} critical lint errors")
                            if validation_errors:
                                error_msgs.append(f"validation issues: {', '.join(validation_errors)}")
                            self.logger.debug(f"Found {', '.join(error_msgs)} in {file_name}, retrying...")
                    
                    if not success:
                        print(f"❌ Failed to generate clean content for {file_name} after {max_attempts} attempts")
                        
                        # Show detailed error information
                        if 'enhanced_content' in locals():
                            final_lint_errors = linter.lint_content(enhanced_content, file_name)
                            final_critical_errors = [
                                error for error in final_lint_errors 
                                if error.error_type in ['unclosed_tag', 'email_as_jsx', 'url_as_jsx', 
                                                       'loose_angle_bracket', 'at_in_tag']
                            ]
                            
                            print(f"   📋 Final validation status for {file_name}:")
                            if '{{PROJECT_NAME}}' in enhanced_content:
                                print(f"   ⚠️  Contains unreplaced {{{{PROJECT_NAME}}}} placeholder")
                            if '[INSERT_CONTENT]' in enhanced_content:
                                print(f"   ⚠️  Contains unreplaced [INSERT_CONTENT] marker")
                            if final_critical_errors:
                                print(f"   🔍 Critical lint errors ({len(final_critical_errors)}):")
                                for error in final_critical_errors[:3]:  # Show first 3 errors
                                    print(f"      - {error.error_type}: {error.description}")
                                if len(final_critical_errors) > 3:
                                    print(f"      ... and {len(final_critical_errors) - 3} more errors")
                        
                        self.logger.warning(f"Failed to generate clean content for {file_name} after {max_attempts} attempts")
                        if self.strict_ai:
                            return False
                
                except Exception as e:
                    self.logger.warning(f"Error processing file {file_name}: {str(e)}")
                    if self.strict_ai:
                        return False
                    continue
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error during AI content enhancement: {str(e)}")
            return False
    
    def _ai_enhance_single_file(self, content: str, file_path: str, repo_info: Dict) -> str:
        """Use AI to generate content for [INSERT_CONTENT] markers only."""
        try:
            # Find all [INSERT_CONTENT] markers in the file
            if '[INSERT_CONTENT]' not in content:
                return content
            
            project_name = repo_info.get('project_name', 'this project')
            file_name = os.path.basename(file_path)
            languages = ', '.join(repo_info.get('languages', []))
            project_type = self._determine_project_type(repo_info)
            
            # Extract section context (heading before the marker)
            section_context = self._extract_section_context(content, file_name)
            
            # Generate content for the INSERT_CONTENT marker
            from jpl.slim.utils.ai_utils import generate_ai_content
            
            prompt_template = self._get_prompt_template("docs-website", "generate_content_only")
            if not prompt_template:
                self.logger.error("Could not find generate_content_only prompt template")
                return content
            
            # Format the prompt with context
            formatted_prompt = prompt_template.format(
                project_name=project_name,
                file_name=file_name,
                section_context=section_context,
                project_type=project_type,
                languages=languages
            )
            
            # Generate the content
            generated_content = generate_ai_content(formatted_prompt, self.use_ai)
            
            if generated_content:
                # Replace the [INSERT_CONTENT] marker with the generated content
                enhanced_content = content.replace('[INSERT_CONTENT]', generated_content.strip())
                return enhanced_content
            else:
                self.logger.warning(f"AI failed to generate content for {file_name}")
                return content
            
        except Exception as e:
            self.logger.warning(f"Error enhancing file '{file_path}': {str(e)}")
            return content
    
    def _extract_section_context(self, content: str, file_name: str) -> str:
        """Extract context around [INSERT_CONTENT] marker for AI prompt."""
        lines = content.split('\n')
        context_lines = []
        
        # Find the line with [INSERT_CONTENT]
        insert_line_idx = None
        for i, line in enumerate(lines):
            if '[INSERT_CONTENT]' in line:
                insert_line_idx = i
                break
        
        if insert_line_idx is None:
            return f"Content for {file_name}"
        
        # Look backwards for the most recent heading
        heading = None
        for i in range(insert_line_idx - 1, -1, -1):
            line = lines[i].strip()
            if line.startswith('#'):
                heading = line
                break
        
        # Build context description
        if heading:
            context_lines.append(f"Section: {heading}")
        
        context_lines.append(f"File: {file_name}")
        
        # Look at a few lines before the marker for additional context
        start_idx = max(0, insert_line_idx - 3)
        before_lines = [line.strip() for line in lines[start_idx:insert_line_idx] 
                       if line.strip() and not line.strip().startswith('#')]
        if before_lines:
            context_lines.append(f"Context: {' '.join(before_lines[-2:])}")
        
        return ' | '.join(context_lines)
    
    def _get_prompt_template(self, practice_type: str, section_name: str) -> str:
        """Get prompt template from prompts.yaml."""
        try:
            from jpl.slim.utils.prompt_utils import load_prompts
            prompts = load_prompts()
            
            if practice_type in prompts and section_name in prompts[practice_type]:
                return prompts[practice_type][section_name].get('prompt', '')
            
            return ''
        except Exception as e:
            self.logger.error(f"Error loading prompt template: {str(e)}")
            return ''
    
    def _has_empty_sections(self, content: str) -> bool:
        """Check if content has empty sections (headers with no content)."""
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('#') and i < len(lines) - 1:
                # Found a header, check if next non-empty line is another header
                for j in range(i + 1, len(lines)):
                    next_line = lines[j].strip()
                    if next_line:
                        if next_line.startswith('#'):
                            return True  # Empty section found
                        break
        return False
    
    
    def _determine_project_type(self, repo_info: Dict) -> str:
        """Determine the type of project based on repository analysis."""
        languages = repo_info.get('languages', [])
        files = repo_info.get('files', [])
        
        # Check for specific project types
        if any('package.json' in f for f in files):
            if any('react' in f.lower() for f in files):
                return "React web application"
            elif any('vue' in f.lower() for f in files):
                return "Vue.js web application"
            else:
                return "Node.js application"
        
        if any('setup.py' in f or 'pyproject.toml' in f for f in files):
            if any('fastapi' in f.lower() or 'flask' in f.lower() for f in files):
                return "Python web API"
            elif any('cli' in f.lower() or 'main.py' in f for f in files):
                return "Python CLI tool"
            else:
                return "Python library"
        
        if any('pom.xml' in f or 'build.gradle' in f for f in files):
            return "Java application"
        
        if any('Cargo.toml' in f for f in files):
            return "Rust application"
        
        if any('go.mod' in f for f in files):
            return "Go application"
        
        # Default based on primary language
        if 'JavaScript' in languages:
            return "JavaScript application"
        elif 'Python' in languages:
            return "Python project"
        elif 'Java' in languages:
            return "Java project"
        else:
            return "software project"
    
    def _validate_and_fix_content(self, repo_info: Dict) -> bool:
        """
        Simple validation - just check for any remaining [INSERT_CONTENT] markers.
        The heavy lifting is now done during generation with the linting retry loop.
        """
        try:
            docs_dir = self.output_dir / "docs"
            if not docs_dir.exists():
                self.logger.warning("No docs directory found for validation")
                return True
            
            # Quick check for remaining template markers
            remaining_markers = []
            for md_file in docs_dir.rglob("*.md"):
                try:
                    content = md_file.read_text(encoding='utf-8')
                    if '[INSERT_CONTENT]' in content:
                        remaining_markers.append(str(md_file))
                except Exception as e:
                    self.logger.warning(f"Error reading {md_file.name}: {str(e)}")
            
            if remaining_markers:
                self.logger.warning(f"Found {len(remaining_markers)} files with remaining [INSERT_CONTENT] markers")
                for marker_file in remaining_markers[:5]:  # Show first 5
                    print(f"   📄 {os.path.basename(marker_file)} still contains [INSERT_CONTENT]")
                if len(remaining_markers) > 5:
                    print(f"   ... and {len(remaining_markers) - 5} more files")
                print("   🔧 Some content may not have been generated successfully.")
            else:
                self.logger.info("✅ Content generation completed successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error during content validation: {str(e)}")
            return False
    
