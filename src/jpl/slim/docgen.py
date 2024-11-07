# docgen.py

import os
import re
import git
import yaml
import json
import shutil
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
from .cli import generate_content  # Import AI generation function from cli.py

class DocusaurusGenerator:
    """
    Generates Docusaurus documentation from repository content.
    """
    
    def __new__(cls, *args, **kwargs):
        """
        Ensure the class can be instantiated with arguments.
        """
        return super(DocusaurusGenerator, cls).__new__(cls)
    
    def __init__(self, repo_path: str, output_dir: str, config: Optional[Dict] = None, use_ai: Optional[str] = None):
        """
        Initialize the documentation generator.
        
        Args:
            repo_path: Path to the repository
            output_dir: Directory where documentation should be generated
            config: Optional configuration dictionary
            use_ai: Optional AI model to use for enhanced documentation (e.g., "openai/gpt-4")
        """
        self.repo_path = repo_path
        self.output_dir = output_dir
        self.config = config or {}
        self.use_ai = use_ai
        
        # Initialize directories
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, 'static'), exist_ok=True)
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
        
        if self.use_ai:
            self.logger.info(f"AI enhancement enabled using model: {self.use_ai}")

    def _generate_changelog(self) -> Optional[str]:
        """Generate changelog from CHANGELOG.md and git history."""
        changelog_content = []
        
        # Check for CHANGELOG file
        changelog_file = self._find_file("CHANGELOG.md")
        if changelog_file:
            with open(changelog_file, 'r') as f:
                changelog_content.append(f.read())
        
        # Add recent git history
        try:
            repo = git.Repo(self.repo_path)
            # Try to get the default branch name instead of assuming 'main'
            default_branch = None
            try:
                # Try getting the HEAD branch first
                default_branch = repo.active_branch.name
            except TypeError:
                # If HEAD is detached, try getting the default branch from remote
                try:
                    default_branch = repo.git.symbolic_ref('refs/remotes/origin/HEAD').replace('refs/remotes/origin/', '')
                except git.GitCommandError:
                    # If that fails too, try common branch names
                    for branch in ['main', 'master']:
                        try:
                            repo.git.rev_parse('--verify', branch)
                            default_branch = branch
                            break
                        except git.GitCommandError:
                            continue
            
            if default_branch:
                commits = list(repo.iter_commits(default_branch))[:20]
                if commits:
                    changelog_content.append("\n## Recent Changes\n")
                    for commit in commits:
                        date = datetime.fromtimestamp(commit.committed_date).strftime('%Y-%m-%d')
                        changelog_content.append(f"- {date}: {commit.summary}")
            else:
                self.logger.warning("Could not determine default branch. Skipping git history.")
                
        except Exception as e:
            self.logger.warning(f"Error getting git history: {str(e)}")
        
        if not changelog_content:
            return None
            
        return self._format_page(
            title="Changelog",
            content="\n\n".join(changelog_content)
        )

    def _enhance_with_ai(self, content: str, section_name: str) -> str:
        """
        Enhance documentation content using AI.
        
        Args:
            content: Original content to enhance
            section_name: Name of the section being enhanced
        
        Returns:
            Enhanced content string
        """
        if not self.use_ai:
            return content

        try:
            prompts = {
                'overview': "Enhance this project overview to be more comprehensive and user-friendly while maintaining accuracy. Add clear sections for features, use cases, and key concepts if they're not already present: ",
                'installation': "Improve this installation guide by adding clear prerequisites, troubleshooting tips, and platform-specific instructions while maintaining accuracy: ",
                'api': "Enhance this API documentation by adding more detailed descriptions, usage examples, and parameter explanations while maintaining technical accuracy: ",
                'guides': "Improve these guides by adding more context, best practices, and common pitfalls while maintaining accuracy: ",
                'contributing': "Enhance these contributing guidelines by adding more specific examples, workflow descriptions, and best practices while maintaining accuracy: ",
                'changelog': "Improve this changelog by adding more context and grouping related changes while maintaining accuracy: ",
                'deployment': "Enhance this deployment documentation with more detailed steps, prerequisites, and troubleshooting while maintaining accuracy: ",
                'architecture': "Improve this architecture documentation by adding more context, design decisions, and component relationships while maintaining accuracy: ",
                'testing': "Enhance this testing documentation by adding more specific examples, test strategies, and coverage goals while maintaining accuracy: ",
                'security': "Improve this security documentation by adding more best practices, common vulnerabilities, and mitigation strategies while maintaining accuracy: "
            }

            prompt = prompts.get(section_name, "Enhance this documentation while maintaining accuracy: ")
            enhanced_content = generate_content(prompt + content, self.use_ai)
            
            # If AI enhancement fails, log a warning and return original content
            if not enhanced_content:
                self.logger.warning(f"AI enhancement failed for {section_name}. Using original content.")
                return content
                
            return enhanced_content
            
        except Exception as e:
            self.logger.warning(f"Error during AI enhancement for {section_name}: {str(e)}")
            return content  # Return original content if enhancement fails


    def generate(self) -> bool:
        """
        Generate all documentation components.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Generate content sections
            sections = {
                'overview': self._generate_overview(),
                'installation': self._generate_installation(),
                'api': self._generate_api(),
                'guides': self._generate_guides(),
                'contributing': self._generate_contributing(),
                'changelog': self._generate_changelog(),
                'deployment': self._generate_deployment(),
                'architecture': self._generate_architecture(),
                'testing': self._generate_testing(),
                'security': self._generate_security()
            }
            
            # Write section files
            for section_name, content in sections.items():
                if content:
                    # Enhance content with AI if enabled
                    if self.use_ai:
                        content = self._enhance_with_ai(content, section_name)
                    
                    file_path = os.path.join(self.output_dir, f"{section_name}.md")
                    with open(file_path, 'w') as f:
                        f.write(content)
                    self.logger.info(f"Generated {section_name} documentation")
            
            # Generate supporting files
            self._generate_sidebar(sections)
            self._generate_search_index(sections)
            self._copy_static_assets()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Documentation generation failed: {str(e)}")
            return False


    def _generate_overview(self) -> Optional[str]:
        """Generate overview page from README."""
        readme_path = self._find_file("README.md")
        if not readme_path:
            return None
            
        with open(readme_path, 'r') as f:
            content = f.read()
            
        return self._format_page(
            title="Overview",
            content=content,
            frontmatter={
                'id': 'overview',
                'slug': '/'
            }
        )

    def _generate_installation(self) -> Optional[str]:
        """Generate installation guide."""
        install_content = []
        
        # Check README installation section
        readme = self._find_file("README.md")
        if readme:
            with open(readme, 'r') as f:
                content = f.read()
                install_section = self._extract_section(content, "Installation", "Usage")
                if install_section:
                    install_content.append(install_section)
        
        # Check for package files
        package_files = {
            'Python': ['requirements.txt', 'setup.py'],
            'Node.js': ['package.json'],
            'Java': ['pom.xml'],
            'Ruby': ['Gemfile']
        }
        
        for lang, files in package_files.items():
            for file in files:
                if os.path.exists(os.path.join(self.repo_path, file)):
                    install_content.append(f"\n## {lang} Installation\n")
                    with open(os.path.join(self.repo_path, file), 'r') as f:
                        install_content.append(f"```\n{f.read()}\n```")
        
        if not install_content:
            return None
            
        return self._format_page(
            title="Installation",
            content="\n\n".join(install_content)
        )

    def _generate_api(self) -> Optional[str]:
        """Generate API documentation from source files."""
        api_content = []
        source_extensions = {'.py', '.js', '.java', '.cpp', '.h'}
        
        for root, _, files in os.walk(self.repo_path):
            for file in files:
                if any(file.endswith(ext) for ext in source_extensions):
                    relative_path = os.path.relpath(os.path.join(root, file), self.repo_path)
                    api_content.append(f"\n## {relative_path}\n")
                    
                    with open(os.path.join(root, file), 'r') as f:
                        content = f.read()
                        
                    # Extract classes and functions
                    classes = re.findall(r'class\s+(\w+)', content)
                    functions = re.findall(r'def\s+(\w+)\s*\(', content)
                    
                    if classes:
                        api_content.append("\n### Classes\n")
                        api_content.extend(f"- `{cls}`" for cls in classes)
                    
                    if functions:
                        api_content.append("\n### Functions\n")
                        api_content.extend(f"- `{func}()`" for func in functions)
        
        if not api_content:
            return None
            
        return self._format_page(
            title="API Reference",
            content="\n".join(api_content)
        )

    def _generate_guides(self) -> Optional[str]:
        """Generate user guides from docs directory."""
        guides_content = []
        docs_dirs = ['docs', 'doc', 'guides', 'tutorials']
        
        for docs_dir in docs_dirs:
            dir_path = os.path.join(self.repo_path, docs_dir)
            if os.path.exists(dir_path):
                for root, _, files in os.walk(dir_path):
                    for file in files:
                        if file.endswith(('.md', '.rst')):
                            with open(os.path.join(root, file), 'r') as f:
                                guides_content.append(f.read())
        
        if not guides_content:
            return None
            
        return self._format_page(
            title="Guides & Tutorials",
            content="\n\n---\n\n".join(guides_content)
        )

    def _generate_contributing(self) -> Optional[str]:
        """Generate contributing guidelines."""
        contributing_file = self._find_file("CONTRIBUTING.md")
        if not contributing_file:
            return None
            
        with open(contributing_file, 'r') as f:
            content = f.read()
            
        return self._format_page(
            title="Contributing",
            content=content
        )

    def _generate_changelog(self) -> Optional[str]:
        """Generate changelog from CHANGELOG.md and git history."""
        changelog_content = []
        
        # Check for CHANGELOG file
        changelog_file = self._find_file("CHANGELOG.md")
        if changelog_file:
            with open(changelog_file, 'r') as f:
                changelog_content.append(f.read())
        
        # Add recent git history
        try:
            repo = git.Repo(self.repo_path)
            commits = list(repo.iter_commits('main'))[:20]
            
            if commits:
                changelog_content.append("\n## Recent Changes\n")
                for commit in commits:
                    date = datetime.fromtimestamp(commit.committed_date).strftime('%Y-%m-%d')
                    changelog_content.append(f"- {date}: {commit.summary}")
        except Exception as e:
            self.logger.warning(f"Error getting git history: {str(e)}")
        
        if not changelog_content:
            return None
            
        return self._format_page(
            title="Changelog",
            content="\n\n".join(changelog_content)
        )

    def _generate_sidebar(self, sections: Dict[str, Optional[str]]) -> None:
        """Generate sidebar configuration."""
        sidebar_items = [
            {
                'type': 'doc',
                'id': name,
                'label': name.title()
            }
            for name, content in sections.items()
            if content is not None
        ]
        
        sidebar_config = {
            'sidebar': sidebar_items
        }
        
        with open(os.path.join(self.output_dir, 'sidebars.js'), 'w') as f:
            f.write("module.exports = " + json.dumps(sidebar_config, indent=2))

    def _find_file(self, filename: str) -> Optional[str]:
        """Find a file in the repository."""
        for root, _, files in os.walk(self.repo_path):
            if filename in files:
                return os.path.join(root, filename)
        return None

    def _extract_section(self, content: str, start: str, end: str) -> Optional[str]:
        """Extract content between two headers."""
        pattern = f"#+ *{start}.*?(?=#+ *{end}|$)"
        match = re.search(pattern, content, re.DOTALL)
        return match.group(0).strip() if match else None

    def _format_page(self, title: str, content: str, frontmatter: Dict = None) -> str:
        """Format a documentation page with frontmatter."""
        fm = {
            'id': title.lower(),
            'title': title,
            'sidebar_label': title,
            **(frontmatter or {})
        }
        
        frontmatter_yaml = yaml.dump(fm, default_flow_style=False)
        return f"---\n{frontmatter_yaml}---\n\n{content}"

    def _copy_static_assets(self) -> None:
        """Copy static assets to the output directory."""
        static_dir = os.path.join(self.output_dir, 'static')
        os.makedirs(static_dir, exist_ok=True)
        
        for root, _, files in os.walk(self.repo_path):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg')):
                    try:
                        source_path = os.path.join(root, file)
                        target_path = os.path.join(static_dir, file)
                        
                        # Only copy if source and target are different
                        if os.path.abspath(source_path) != os.path.abspath(target_path):
                            shutil.copy2(source_path, target_path)
                            
                    except Exception as e:
                        self.logger.warning(f"Error copying asset {file}: {str(e)}")


    def _generate_deployment(self) -> Optional[str]:
        """Generate deployment documentation."""
        deployment_content = []
        
        # Check for deployment-related files
        deployment_files = {
            'Docker': ['Dockerfile', 'docker-compose.yml'],
            'Kubernetes': ['.kubernetes/', 'k8s/'],
            'CI/CD': ['.github/workflows/', '.gitlab-ci.yml', 'Jenkinsfile'],
            'Scripts': ['deploy.sh', 'deploy.py']
        }
        
        for category, files in deployment_files.items():
            found_files = []
            for file in files:
                file_path = os.path.join(self.repo_path, file)
                if os.path.exists(file_path):
                    found_files.append(file)
                    if os.path.isfile(file_path):
                        with open(file_path, 'r') as f:
                            deployment_content.append(f"\n### {file}\n```\n{f.read()}\n```")
            
            if found_files:
                deployment_content.insert(0, f"\n## {category}\n")
                deployment_content.insert(1, f"Found configuration in: {', '.join(found_files)}")
        
        if not deployment_content:
            return None
            
        return self._format_page(
            title="Deployment",
            content="\n".join(deployment_content)
        )

    def _generate_architecture(self) -> Optional[str]:
        """Generate architecture documentation."""
        architecture_content = []
        
        # Check for architecture documentation files
        arch_files = ['ARCHITECTURE.md', 'docs/architecture.md', 'docs/design.md']
        
        for file in arch_files:
            file_path = os.path.join(self.repo_path, file)
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    architecture_content.append(f.read())
                break
        
        # Add project structure
        architecture_content.append("\n## Project Structure\n")
        architecture_content.append("```")
        
        exclude_dirs = {'.git', '__pycache__', 'node_modules', 'build', 'dist'}
        
        for root, dirs, files in os.walk(self.repo_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            level = root.replace(self.repo_path, '').count(os.sep)
            indent = ' ' * 4 * level
            architecture_content.append(f"{indent}{os.path.basename(root)}/")
            
            subindent = ' ' * 4 * (level + 1)
            for f in sorted(files):
                architecture_content.append(f"{subindent}{f}")
        
        architecture_content.append("```")
        
        return self._format_page(
            title="Architecture",
            content="\n".join(architecture_content)
        )

    def _generate_testing(self) -> Optional[str]:
        """Generate testing documentation."""
        testing_content = []
        
        # Check for testing documentation
        test_docs = ['TESTING.md', 'docs/testing.md']
        for doc in test_docs:
            doc_path = os.path.join(self.repo_path, doc)
            if os.path.exists(doc_path):
                with open(doc_path, 'r') as f:
                    testing_content.append(f.read())
                break
        
        # Find test directories and files
        test_markers = ['test', 'tests', 'spec', 'specs']
        test_files = []
        
        for root, _, files in os.walk(self.repo_path):
            if any(marker in root.lower() for marker in test_markers):
                rel_path = os.path.relpath(root, self.repo_path)
                test_files.extend([
                    (rel_path, f) for f in files 
                    if f.endswith(('.py', '.js', '.ts', '.java', '.cpp'))
                ])
        
        if test_files:
            testing_content.append("\n## Test Structure\n")
            current_dir = None
            
            for dir_path, file in sorted(test_files):
                if dir_path != current_dir:
                    current_dir = dir_path
                    testing_content.append(f"\n### {dir_path}/\n")
                testing_content.append(f"- {file}")
        
        if not testing_content:
            return None
            
        return self._format_page(
            title="Testing",
            content="\n".join(testing_content)
        )

    def _generate_security(self) -> Optional[str]:
        """Generate security documentation."""
        security_content = []
        
        # Check for security documentation
        security_files = ['SECURITY.md', '.github/SECURITY.md', 'docs/security.md']
        for file in security_files:
            file_path = os.path.join(self.repo_path, file)
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    security_content.append(f.read())
                break
        
        # Check for security-related configurations
        security_configs = {
            'Authentication': ['.env.example', 'config/auth.*'],
            'Dependencies': ['package-lock.json', 'requirements.txt', 'Gemfile.lock'],
            'CI Security': [
                '.github/workflows/codeql-analysis.yml',
                '.github/workflows/security.yml',
                '.snyk'
            ]
        }
        
        for category, patterns in security_configs.items():
            found_files = []
            for pattern in patterns:
                for file in Path(self.repo_path).glob(pattern):
                    found_files.append(file.name)
            
            if found_files:
                security_content.append(f"\n## {category}\n")
                security_content.append(f"Security configurations found in: {', '.join(found_files)}")
        
        if not security_content:
            return None
            
        return self._format_page(
            title="Security",
            content="\n".join(security_content)
        )

    def _generate_search_index(self, sections: Dict[str, Optional[str]]) -> None:
        """Generate search index for documentation."""
        search_index = []
        
        for section_name, content in sections.items():
            if content:
                # Extract headings
                headings = re.findall(r'^#{1,6}\s+(.+)$', content, re.MULTILINE)
                
                search_index.append({
                    'id': section_name,
                    'title': section_name.title(),
                    'headings': headings,
                    'path': f'/{section_name}'
                })
        
        with open(os.path.join(self.output_dir, 'search-index.json'), 'w') as f:
            json.dump(search_index, f, indent=2)




