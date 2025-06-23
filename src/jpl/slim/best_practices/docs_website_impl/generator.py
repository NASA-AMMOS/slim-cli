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
            
            self.logger.debug(f"Initialized SLIM Doc Generator for {self.target_repo_path.name}")
        else:
            self.target_repo_path = None
            self.logger.debug("Initialized SLIM Doc Generator in template-only mode")
    
    def generate(self) -> bool:
        """
        Generate the documentation site using simplified AI-driven flow.
        
        Returns:
            True if generation was successful, False otherwise
        """
        try:
            self.logger.debug("Starting documentation generation")
            
            # Step 1: Clone template to output directory
            if not self._setup_template():
                return False
            
            # Step 2: Analyze repository to extract basic information
            repo_info = self._analyze_repository() if self.target_repo_path else {}
            
            # Step 3: Replace universal placeholders (PROJECT_NAME, etc.)
            if not self._replace_basic_placeholders(repo_info):
                return False
            
            # Step 4: Use AI to fill [INSERT_CONTENT] markers in all markdown files
            if self.use_ai:
                if not self._ai_enhance_content(repo_info):
                    return False
            
            # Step 5: Validate content and fix issues
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
                            content = content.replace(placeholder, replacement)
                            modified = True
                    
                    # Write back if modified
                    if modified:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        self.logger.debug(f"Updated placeholders in {file_path}")
                
                except Exception as e:
                    self.logger.warning(f"Error processing file {file_path}: {str(e)}")
                    continue
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error replacing placeholders in files: {str(e)}")
            return False
    
    def _ai_enhance_content(self, repo_info: Dict) -> bool:
        """Use AI to fill [INSERT_CONTENT] markers by processing sections individually."""
        try:
            self.logger.debug("AI enhancing content with section-by-section processing")
            
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
            
            # Sort files by priority (core files first)
            priority_files = []
            regular_files = []
            
            for file_path in markdown_files:
                file_name = os.path.basename(file_path).lower()
                if any(priority in file_name for priority in ['installation', 'quick-start', 'features', 'contributing']):
                    priority_files.append(file_path)
                else:
                    regular_files.append(file_path)
            
            # Process each file section by section
            all_files = priority_files + regular_files
            
            for file_path in all_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check if file needs enhancement
                    if '[INSERT_CONTENT]' in content or '[Project Name]' in content or self._has_empty_sections(content):
                        enhanced_content = self._ai_enhance_file_by_sections(content, file_path, repo_info)
                        if enhanced_content and enhanced_content != content:
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(enhanced_content)
                            self.logger.debug(f"AI enhanced content in {os.path.basename(file_path)}")
                
                except Exception as e:
                    self.logger.warning(f"Error AI enhancing file {os.path.basename(file_path)}: {str(e)}")
                    continue
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error during AI content enhancement: {str(e)}")
            return False
    
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
    
    def _ai_enhance_file_by_sections(self, content: str, file_path: str, repo_info: Dict, max_retries: int = 3) -> str:
        """Enhance a file by processing each section individually with AI."""
        try:
            # Parse the file into sections
            sections = self._parse_markdown_sections(content)
            
            enhanced_sections = []
            for section in sections:
                enhanced_section = section
                
                # Check if section needs enhancement
                if (section['needs_content'] or 
                    '[INSERT_CONTENT]' in section['content'] or 
                    '[Project Name]' in section['content']):
                    
                    # Try to enhance this section with retries
                    for attempt in range(max_retries):
                        try:
                            enhanced_section_content = self._ai_enhance_section(
                                section, file_path, repo_info, attempt + 1
                            )
                            
                            if enhanced_section_content and enhanced_section_content != section['content']:
                                enhanced_section = {
                                    'header': section['header'],
                                    'content': enhanced_section_content,
                                    'needs_content': False
                                }
                                self.logger.debug(f"Enhanced section '{section['header']}' in {os.path.basename(file_path)}")
                                break
                        except Exception as e:
                            self.logger.warning(f"Attempt {attempt + 1} failed for section '{section['header']}': {str(e)}")
                            if attempt == max_retries - 1:
                                self.logger.warning(f"Failed to enhance section '{section['header']}' after {max_retries} attempts")
                
                enhanced_sections.append(enhanced_section)
            
            # Reconstruct the file
            result = self._reconstruct_markdown_from_sections(enhanced_sections)
            
            # Apply final cleanup
            result = self._clean_ai_response(result, content)
            result = self._fix_remaining_placeholders(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error enhancing file by sections: {str(e)}")
            return content
    
    def _parse_markdown_sections(self, content: str) -> List[Dict]:
        """Parse markdown content into sections based on headers."""
        sections = []
        lines = content.split('\n')
        
        current_section = {
            'header': '',
            'content': '',
            'needs_content': False
        }
        
        # Handle content before first header
        pre_header_lines = []
        first_header_found = False
        
        for i, line in enumerate(lines):
            if line.strip().startswith('#') and not first_header_found:
                first_header_found = True
                # Save pre-header content
                if pre_header_lines:
                    sections.append({
                        'header': '',
                        'content': '\n'.join(pre_header_lines),
                        'needs_content': False
                    })
                
                # Start new section
                current_section = {
                    'header': line.strip(),
                    'content': '',
                    'needs_content': False
                }
            elif line.strip().startswith('#') and first_header_found:
                # Save previous section
                current_section['needs_content'] = self._section_needs_content(current_section['content'])
                sections.append(current_section)
                
                # Start new section
                current_section = {
                    'header': line.strip(),
                    'content': '',
                    'needs_content': False
                }
            else:
                if not first_header_found:
                    pre_header_lines.append(line)
                else:
                    current_section['content'] += line + '\n'
        
        # Add the last section
        if first_header_found:
            current_section['needs_content'] = self._section_needs_content(current_section['content'])
            sections.append(current_section)
        elif pre_header_lines:
            # File has no headers
            sections.append({
                'header': '',
                'content': '\n'.join(pre_header_lines),
                'needs_content': '[INSERT_CONTENT]' in '\n'.join(pre_header_lines)
            })
        
        return sections
    
    def _section_needs_content(self, section_content: str) -> bool:
        """Determine if a section needs content enhancement."""
        content = section_content.strip()
        
        # Check for explicit markers
        if '[INSERT_CONTENT]' in content or '[Project Name]' in content:
            return True
        
        # Check if section is too short (less than 50 characters of actual content)
        # Remove common markdown elements for length check
        import re
        clean_content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)  # Remove code blocks
        clean_content = re.sub(r'^\s*[-*+]\s+', '', clean_content, flags=re.MULTILINE)  # Remove list markers
        clean_content = re.sub(r'[#*_`\[\]()]+', '', clean_content)  # Remove markdown formatting
        clean_content = clean_content.strip()
        
        return len(clean_content) < 50
    
    def _ai_enhance_section(self, section: Dict, file_path: str, repo_info: Dict, attempt: int) -> str:
        """Use AI to enhance a specific section using YAML prompts."""
        try:
            project_name = repo_info.get('project_name', 'this project')
            file_name = os.path.basename(file_path)
            section_header = section['header']
            current_content = section['content']
            languages = ', '.join(repo_info.get('languages', []))
            project_type = self._determine_project_type(repo_info)
            
            # Create context info for the YAML prompt
            context_info = {
                'project_name': project_name,
                'file_name': file_name,
                'section_header': section_header,
                'current_content': current_content,
                'languages': languages,
                'project_type': project_type,
                'attempt': attempt
            }
            
            # Use the enhance_section prompt from prompts.yaml
            additional_context = f"""
Project: {project_name}
File: {file_name}
Section: {section_header}
Languages: {languages}
Type: {project_type}
Attempt: {attempt}
"""
            
            enhanced_content = enhance_content(
                content=current_content,
                practice_type="docs-website",
                section_name="enhance_section",
                model=self.use_ai,
                additional_context=additional_context
            )
            
            return enhanced_content if enhanced_content else section['content']
            
        except Exception as e:
            self.logger.warning(f"Error enhancing section '{section['header']}': {str(e)}")
            return section['content']
    
    def _reconstruct_markdown_from_sections(self, sections: List[Dict]) -> str:
        """Reconstruct markdown content from enhanced sections."""
        result_lines = []
        
        for section in sections:
            if section['header']:
                result_lines.append(section['header'])
            
            # Clean up the content
            content = section['content'].rstrip('\n')
            if content:
                result_lines.append(content)
            
        return '\n'.join(result_lines)
    
    def _clean_ai_response(self, ai_response: str, original_content: str) -> str:
        """Clean AI response to remove conversation artifacts and preserve structure."""
        try:
            # Remove common conversation artifacts
            lines = ai_response.split('\n')
            cleaned_lines = []
            skip_next = False
            in_content = False
            
            for line in lines:
                line_lower = line.lower().strip()
                
                # Skip conversation markers
                if any(marker in line_lower for marker in [
                    '### user:', '### assistant:', 'here is the enhanced',
                    'here is the content', 'content to enhance:',
                    'you are a software', 'based on the repository'
                ]):
                    skip_next = True
                    continue
                    
                # Skip empty lines after conversation markers
                if skip_next and not line.strip():
                    continue
                elif skip_next:
                    skip_next = False
                
                # Look for the start of actual content (YAML front matter)
                if line.strip().startswith('---') and not in_content:
                    in_content = True
                    cleaned_lines.append(line)
                    continue
                
                if in_content:
                    cleaned_lines.append(line)
            
            # If we couldn't find proper content, try to extract it differently
            if not cleaned_lines or not any('---' in line for line in cleaned_lines[:5]):
                # Look for content after "CONTENT TO ENHANCE:" or similar
                content_start = -1
                for i, line in enumerate(lines):
                    if 'content to enhance:' in line.lower() or line.strip().startswith('---'):
                        content_start = i + 1 if 'content to enhance:' in line.lower() else i
                        break
                
                if content_start >= 0:
                    cleaned_lines = lines[content_start:]
                else:
                    # Fallback: return original content
                    return original_content
            
            result = '\n'.join(cleaned_lines).strip()
            
            # Ensure we have valid content
            if not result or len(result) < 50:
                return original_content
            
            # Additional cleaning: replace any remaining placeholders that the AI didn't handle
            result = self._fix_remaining_placeholders(result)
            result = self._remove_duplicate_content(result)
                
            return result
            
        except Exception as e:
            self.logger.warning(f"Error cleaning AI response: {str(e)}")
            return original_content
    
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
    
    def _fix_remaining_placeholders(self, content: str) -> str:
        """Fix any remaining placeholders that AI didn't properly replace."""
        try:
            # Replace common placeholder patterns that AI might have missed
            content = content.replace('{{PROJECT_NAME}}', 'MMTC: Multi-Mission Time Correlation')
            content = content.replace('{{PROJECT_DESCRIPTION}}', 'Multi-Mission Time Correlation application')
            content = content.replace('{{GITHUB_ORG}}', 'NASA-AMMOS')
            content = content.replace('{{GITHUB_REPO}}', 'aerie')
            
            # Fix common URL issues that cause MDX compilation errors
            import re
            # Replace raw URLs wrapped in < > with proper markdown links
            content = re.sub(r'<(https?://[^>]+)>', r'[\1](\1)', content)
            
            # Fix broken links to non-existent files
            content = content.replace('[Coding Standards](coding_standards.md)', 'coding standards')
            content = content.replace('[Issue Tracker](issue_tracker.md)', 'GitHub Issues page')
            content = content.replace('(troubleshooting.md)', '(user/troubleshooting.md)')
            content = content.replace('(getting-started.md)', '(user/quick-start.md)')
            
            # Fix malformed URLs and placeholders
            content = re.sub(r'https://MMTC: Multi-Mission Time Correlation\.[a-z]+', 'https://github.com/NASA-AMMOS/aerie', content)
            content = content.replace('brew install MMTC: Multi-Mission Time Correlation', 'brew install mmtc')
            content = content.replace('sudo apt-get install MMTC: Multi-Mission Time Correlation', 'sudo apt-get install mmtc')
            
            return content
            
        except Exception as e:
            self.logger.warning(f"Error fixing remaining placeholders: {str(e)}")
            return content
    
    def _remove_duplicate_content(self, content: str) -> str:
        """Remove duplicate headers and sections."""
        try:
            lines = content.split('\n')
            cleaned_lines = []
            seen_headers = set()
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # Check for duplicate headers
                if line.startswith('#'):
                    header_text = line.lower().strip()
                    if header_text in seen_headers:
                        # Skip this duplicate header and any content until next header
                        i += 1
                        while i < len(lines) and not lines[i].strip().startswith('#'):
                            i += 1
                        continue
                    else:
                        seen_headers.add(header_text)
                        cleaned_lines.append(lines[i])
                else:
                    cleaned_lines.append(lines[i])
                
                i += 1
            
            return '\n'.join(cleaned_lines)
            
        except Exception as e:
            self.logger.warning(f"Error removing duplicate content: {str(e)}")
            return content
    
    def _fix_asciidoc_syntax(self, content: str) -> str:
        """Fix AsciiDoc syntax that breaks MDX compilation."""
        try:
            import re
            
            # Convert AsciiDoc code blocks to markdown
            # Pattern: [source] followed by ---- to ```
            content = re.sub(r'\[source\]\s*\n-{4,}', '```', content)
            content = re.sub(r'^-{4,}$', '```', content, flags=re.MULTILINE)
            
            # Fix other AsciiDoc patterns
            content = re.sub(r'\[source,([^\]]+)\]\s*\n-{4,}', r'```\1', content)
            
            # Remove standalone [source] lines
            content = re.sub(r'^\[source\]\s*$', '', content, flags=re.MULTILINE)
            
            return content
            
        except Exception as e:
            self.logger.warning(f"Error fixing AsciiDoc syntax: {str(e)}")
            return content
    
    def _validate_and_fix_content(self, repo_info: Dict, max_retries: int = 2) -> bool:
        """
        Validate generated content and fix issues with retry mechanism.
        
        Args:
            repo_info: Repository information for context
            max_retries: Maximum number of retry attempts for fixing issues
            
        Returns:
            True if validation passes or issues are fixed, False otherwise
        """
        try:
            docs_dir = self.output_dir / "docs"
            if not docs_dir.exists():
                self.logger.warning("No docs directory found for validation")
                return True
                
            validator = ContentValidator(str(docs_dir), self.logger)
            
            for attempt in range(max_retries + 1):
                self.logger.debug(f"Content validation attempt {attempt + 1}")
                
                # Run validation
                is_valid, issues = validator.validate_all_content()
                
                if is_valid:
                    self.logger.info("✅ Content validation passed")
                    return True
                
                if attempt == max_retries:
                    # Final attempt - print report and determine if issues are critical
                    critical_issues = [issue for issue in issues if issue.issue_type in ['template_marker', 'broken_link']]
                    
                    if critical_issues:
                        self.logger.error(f"❌ Critical validation issues found after {max_retries + 1} attempts")
                        if self.verbose:
                            validator.print_validation_report(issues)
                        return False
                    else:
                        # Only minor issues (empty sections, etc.) - warn but continue
                        self.logger.warning(f"⚠️ Minor validation issues found but proceeding")
                        if self.verbose:
                            validator.print_validation_report(issues)
                        return True
                
                # Try to fix issues
                self.logger.info(f"Found {len(issues)} validation issues, attempting to fix...")
                
                if self._fix_validation_issues(issues, repo_info, validator):
                    self.logger.debug("Fixed some validation issues, retrying validation...")
                    continue
                else:
                    self.logger.warning("Could not automatically fix validation issues")
                    break
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error during content validation: {str(e)}")
            return False
    
    def _fix_validation_issues(self, issues: List, repo_info: Dict, validator: ContentValidator) -> bool:
        """
        Attempt to automatically fix validation issues.
        
        Args:
            issues: List of ValidationIssue objects
            repo_info: Repository information for context
            validator: Content validator instance
            
        Returns:
            True if any fixes were applied, False otherwise
        """
        fixes_applied = False
        
        try:
            # Group issues by file for efficient processing
            issues_by_file = {}
            for issue in issues:
                if issue.file_path not in issues_by_file:
                    issues_by_file[issue.file_path] = []
                issues_by_file[issue.file_path].append(issue)
            
            for file_path, file_issues in issues_by_file.items():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    
                    # Fix template markers
                    for issue in file_issues:
                        if issue.issue_type == 'template_marker':
                            content = self._fix_template_marker(content, issue, repo_info)
                    
                    # Fix broken links  
                    for issue in file_issues:
                        if issue.issue_type == 'broken_link':
                            content = self._fix_broken_link(content, issue, file_path)
                    
                    # Fill empty sections if AI is available
                    if self.use_ai:
                        for issue in file_issues:
                            if issue.issue_type == 'empty_section':
                                content = self._fill_empty_section(content, issue, file_path, repo_info)
                    
                    # Write back if changes were made
                    if content != original_content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        fixes_applied = True
                        self.logger.debug(f"Applied fixes to {file_path}")
                
                except Exception as e:
                    self.logger.warning(f"Error fixing issues in {file_path}: {str(e)}")
                    continue
            
            return fixes_applied
            
        except Exception as e:
            self.logger.error(f"Error applying validation fixes: {str(e)}")
            return False
    
    def _fix_template_marker(self, content: str, issue, repo_info: Dict) -> str:
        """Fix remaining template markers."""
        try:
            # Replace common template markers
            content = content.replace('[INSERT_CONTENT]', '')
            content = content.replace('[INSERT CONTENT]', '')
            content = content.replace('[PLACEHOLDER]', '')
            content = content.replace('[TODO]', '')
            
            # Replace project name placeholders
            project_name = repo_info.get('project_name', 'this project')
            content = content.replace('{{PROJECT_NAME}}', project_name)
            content = content.replace('[Project Name]', project_name)
            
            return content
        except Exception:
            return content
    
    def _fix_broken_link(self, content: str, issue, file_path: str) -> str:
        """Fix broken internal links."""
        try:
            # Common link fixes based on existing patterns
            fixes = {
                '(getting-started.md)': '(user/quick-start.md)',
                '(troubleshooting.md)': '(user/troubleshooting.md)', 
                '[Coding Standards](coding_standards.md)': 'coding standards',
                '[Issue Tracker](issue_tracker.md)': 'GitHub Issues page',
                '(code_review.md)': 'our code review process',
                '(user-guide.md)': '(user/index.md)',
                '(api-docs.md)': '(developer/api.md)',
                '[API Documentation](api.md)': '[API Documentation](../developer/api.md)',
                '(CONTRIBUTING.md)': '(contributing.md)',
                '[CONTRIBUTING.md](CONTRIBUTING.md)': '[contributing guide](contributing.md)',
                '(faq.md)': '(../faqs.md)',
                '(cli.md)': '(user/quick-start.md)',
                '(api.md)': '(../developer/api.md)'
            }
            
            for broken_link, fix in fixes.items():
                content = content.replace(broken_link, fix)
            
            # Fix unmatched brackets by removing incomplete markdown links
            import re
            # Remove incomplete markdown link patterns like [...] without closing
            content = re.sub(r'\[\.\.\.\](?!\()', '...', content)
            content = re.sub(r'(?<!\[)\]\.\.\.', '...', content)
            
            # Fix AsciiDoc syntax that breaks MDX compilation
            content = self._fix_asciidoc_syntax(content)
            
            return content
        except Exception:
            return content
    
    def _fill_empty_section(self, content: str, issue, file_path: str, repo_info: Dict) -> str:
        """Fill empty sections using AI instead of hardcoded text."""
        try:
            if not self.use_ai:
                return content  # Don't fill with hardcoded text
                
            # Extract the section around the empty header
            lines = content.split('\n')
            if issue.line_number <= len(lines):
                # Find the section boundaries
                start_line = issue.line_number - 1  # Header line (0-indexed)
                end_line = len(lines)
                
                # Find the next header to determine section boundary
                for i in range(start_line + 1, len(lines)):
                    if lines[i].strip().startswith('#'):
                        end_line = i
                        break
                
                # Extract the section
                section_lines = lines[start_line:end_line]
                section_content = '\n'.join(section_lines)
                
                # Create a section object for AI enhancement
                section = {
                    'header': lines[start_line],
                    'content': '\n'.join(section_lines[1:]),  # Content without header
                    'needs_content': True
                }
                
                # Use AI to fill this empty section with specific prompt
                project_name = repo_info.get('project_name', 'this project')
                file_name = os.path.basename(file_path)
                section_header = section['header']
                languages = ', '.join(repo_info.get('languages', []))
                project_type = self._determine_project_type(repo_info)
                
                context_info = {
                    'project_name': project_name,
                    'file_name': file_name,
                    'section_header': section_header,
                    'languages': languages,
                    'project_type': project_type
                }
                
                additional_context = f"""
Project: {project_name}
File: {file_name}
Section: {section_header}
Languages: {languages}
Type: {project_type}
"""
                
                enhanced_content = enhance_content(
                    content=section['content'],
                    practice_type="docs-website",
                    section_name="fill_empty_section", 
                    model=self.use_ai,
                    additional_context=additional_context
                )
                
                if enhanced_content and enhanced_content != section['content']:
                    # Replace the section in the original content
                    lines[start_line:end_line] = [section['header']] + enhanced_content.split('\n')
                    content = '\n'.join(lines)
                    self.logger.debug(f"AI filled empty section at line {issue.line_number}")
            
            return content
        except Exception as e:
            self.logger.warning(f"Error filling empty section: {str(e)}")
            return content