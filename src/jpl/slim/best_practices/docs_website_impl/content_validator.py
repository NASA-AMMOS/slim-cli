"""
Content validation module for documentation generator.

This module provides validation for generated markdown content to ensure
quality and completeness before finalizing documentation sites.
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ValidationIssue:
    """Represents a validation issue found in content."""
    file_path: str
    issue_type: str
    line_number: int
    description: str
    content_snippet: str


class ContentValidator:
    """
    Validates generated markdown content for completeness and correctness.
    
    This validator checks for:
    - Remaining template markers ([INSERT_CONTENT], etc.)
    - Broken internal links
    - Empty or incomplete sections
    - Malformed markdown syntax
    """
    
    def __init__(self, docs_dir: str, logger: Optional[logging.Logger] = None):
        """
        Initialize the content validator.
        
        Args:
            docs_dir: Path to the docs directory to validate
            logger: Optional logger instance
        """
        self.docs_dir = Path(docs_dir)
        self.logger = logger or logging.getLogger(__name__)
        
        # Template markers that should not remain in final content
        self.template_markers = [
            r'\[INSERT_CONTENT\]',
            r'\[INSERT CONTENT\]', 
            r'\{\{[^}]+\}\}',  # {{PLACEHOLDER}} style
            r'TODO:',
            r'FIXME:',
            r'XXX:',
            r'\[PLACEHOLDER\]',
            r'\[TODO\]',
            r'\[REPLACE.*?\]'
        ]
        
        # Patterns for potentially broken links
        self.link_patterns = [
            r'\[([^\]]+)\]\(([^)]+)\)',  # [text](url)
            r'<([^>]+\.md)>',           # <file.md>
            r'href=["\']([^"\']+)["\']' # href="url"
        ]
    
    def validate_all_content(self) -> Tuple[bool, List[ValidationIssue]]:
        """
        Validate all markdown files in the docs directory.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        if not self.docs_dir.exists():
            issues.append(ValidationIssue(
                file_path=str(self.docs_dir),
                issue_type="missing_directory",
                line_number=0,
                description="Docs directory does not exist",
                content_snippet=""
            ))
            return False, issues
        
        # Find all markdown files
        md_files = list(self.docs_dir.rglob("*.md")) + list(self.docs_dir.rglob("*.mdx"))
        
        if not md_files:
            issues.append(ValidationIssue(
                file_path=str(self.docs_dir),
                issue_type="no_content",
                line_number=0,
                description="No markdown files found in docs directory",
                content_snippet=""
            ))
            return False, issues
        
        self.logger.info(f"Validating {len(md_files)} markdown files...")
        
        # Collect all existing files for link validation
        all_files = self._collect_all_files()
        
        for md_file in md_files:
            file_issues = self._validate_file(md_file, all_files)
            issues.extend(file_issues)
        
        is_valid = len(issues) == 0
        
        if is_valid:
            self.logger.info("✅ All content validation passed")
        else:
            self.logger.warning(f"❌ Found {len(issues)} validation issues")
            
        return is_valid, issues
    
    def _validate_file(self, file_path: Path, all_files: Set[str]) -> List[ValidationIssue]:
        """
        Validate a single markdown file.
        
        Args:
            file_path: Path to the markdown file
            all_files: Set of all available files for link validation
            
        Returns:
            List of validation issues found
        """
        issues = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            # Check for template markers
            marker_issues = self._check_template_markers(file_path, lines)
            issues.extend(marker_issues)
            
            # Check for broken links
            link_issues = self._check_links(file_path, lines, all_files)
            issues.extend(link_issues)
            
            # Check for empty sections
            empty_issues = self._check_empty_sections(file_path, lines)
            issues.extend(empty_issues)
            
            # Check for basic markdown syntax
            syntax_issues = self._check_markdown_syntax(file_path, lines)
            issues.extend(syntax_issues)
            
        except Exception as e:
            issues.append(ValidationIssue(
                file_path=str(file_path),
                issue_type="read_error",
                line_number=0,
                description=f"Failed to read file: {str(e)}",
                content_snippet=""
            ))
        
        return issues
    
    def _check_template_markers(self, file_path: Path, lines: List[str]) -> List[ValidationIssue]:
        """Check for remaining template markers that should have been replaced."""
        issues = []
        
        for line_num, line in enumerate(lines, 1):
            for marker_pattern in self.template_markers:
                matches = re.findall(marker_pattern, line, re.IGNORECASE)
                for match in matches:
                    issues.append(ValidationIssue(
                        file_path=str(file_path),
                        issue_type="template_marker",
                        line_number=line_num,
                        description=f"Remaining template marker: {match}",
                        content_snippet=line.strip()
                    ))
        
        return issues
    
    def _check_links(self, file_path: Path, lines: List[str], all_files: Set[str]) -> List[ValidationIssue]:
        """Check for broken internal links."""
        issues = []
        
        for line_num, line in enumerate(lines, 1):
            # Find all markdown links
            markdown_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', line)
            
            for link_text, link_url in markdown_links:
                # Skip external links (http/https)
                if link_url.startswith(('http://', 'https://', 'mailto:', '#')):
                    continue
                
                # Clean up the link URL
                clean_url = link_url.split('#')[0].strip()  # Remove anchors
                if not clean_url:
                    continue
                
                # Check if it's a relative path to a markdown file
                if clean_url.endswith(('.md', '.mdx')):
                    # Convert to absolute path from docs root
                    if clean_url.startswith('./'):
                        clean_url = clean_url[2:]
                    elif clean_url.startswith('../'):
                        # Handle relative paths from current file location
                        file_dir = file_path.parent.relative_to(self.docs_dir)
                        target_path = (file_dir / clean_url).resolve()
                        clean_url = str(target_path)
                    
                    # Check if file exists
                    full_path = self.docs_dir / clean_url
                    if not full_path.exists():
                        # Also check without .md extension
                        without_ext = clean_url.replace('.md', '').replace('.mdx', '')
                        alt_paths = [
                            self.docs_dir / f"{without_ext}.md",
                            self.docs_dir / f"{without_ext}.mdx",
                            self.docs_dir / f"{without_ext}/index.md",
                            self.docs_dir / f"{without_ext}/index.mdx"
                        ]
                        
                        if not any(p.exists() for p in alt_paths):
                            issues.append(ValidationIssue(
                                file_path=str(file_path),
                                issue_type="broken_link",
                                line_number=line_num,
                                description=f"Broken link to: {clean_url}",
                                content_snippet=line.strip()
                            ))
        
        return issues
    
    def _check_empty_sections(self, file_path: Path, lines: List[str]) -> List[ValidationIssue]:
        """Check for empty sections that should have content."""
        issues = []
        
        # Look for headers followed immediately by another header or end of file
        for i, line in enumerate(lines):
            if re.match(r'^#+\s+', line):  # Found a header
                # Check if the next non-empty line is another header
                next_content_line = None
                for j in range(i + 1, len(lines)):
                    if lines[j].strip():
                        next_content_line = lines[j]
                        break
                
                if next_content_line and re.match(r'^#+\s+', next_content_line):
                    issues.append(ValidationIssue(
                        file_path=str(file_path),
                        issue_type="empty_section",
                        line_number=i + 1,
                        description="Empty section with no content",
                        content_snippet=line.strip()
                    ))
                elif next_content_line is None:  # End of file
                    issues.append(ValidationIssue(
                        file_path=str(file_path),
                        issue_type="empty_section",
                        line_number=i + 1,
                        description="Header at end of file with no content",
                        content_snippet=line.strip()
                    ))
        
        return issues
    
    def _check_markdown_syntax(self, file_path: Path, lines: List[str]) -> List[ValidationIssue]:
        """Check for basic markdown syntax issues."""
        issues = []
        
        for line_num, line in enumerate(lines, 1):
            # Check for unmatched brackets in links
            if '[' in line or ']' in line:
                open_brackets = line.count('[')
                close_brackets = line.count(']')
                if open_brackets != close_brackets:
                    issues.append(ValidationIssue(
                        file_path=str(file_path),
                        issue_type="syntax_error",
                        line_number=line_num,
                        description="Unmatched brackets in markdown link",
                        content_snippet=line.strip()
                    ))
            
            # Check for unmatched parentheses in links
            link_matches = re.findall(r'\[[^\]]*\]', line)
            for match in link_matches:
                following_text = line[line.find(match) + len(match):]
                if following_text.startswith('('):
                    paren_match = re.match(r'\(([^)]*)\)', following_text)
                    if not paren_match:
                        issues.append(ValidationIssue(
                            file_path=str(file_path),
                            issue_type="syntax_error",
                            line_number=line_num,
                            description="Unmatched parentheses in markdown link",
                            content_snippet=line.strip()
                        ))
        
        return issues
    
    def _collect_all_files(self) -> Set[str]:
        """Collect all files in the docs directory for link validation."""
        all_files = set()
        
        for file_path in self.docs_dir.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(self.docs_dir)
                all_files.add(str(rel_path))
                all_files.add(str(rel_path).replace('\\', '/'))  # Handle Windows paths
        
        return all_files
    
    def print_validation_report(self, issues: List[ValidationIssue]) -> None:
        """Print a formatted validation report."""
        if not issues:
            print("✅ Content validation passed - no issues found!")
            return
        
        print(f"\n❌ Content Validation Report - {len(issues)} issues found:\n")
        
        # Group issues by type
        issues_by_type = {}
        for issue in issues:
            if issue.issue_type not in issues_by_type:
                issues_by_type[issue.issue_type] = []
            issues_by_type[issue.issue_type].append(issue)
        
        for issue_type, type_issues in issues_by_type.items():
            print(f"🔍 {issue_type.replace('_', ' ').title()} ({len(type_issues)} issues):")
            for issue in type_issues[:5]:  # Show first 5 issues of each type
                print(f"   📄 {issue.file_path}:{issue.line_number}")
                print(f"      {issue.description}")
                if issue.content_snippet:
                    print(f"      → {issue.content_snippet[:80]}...")
                print()
            
            if len(type_issues) > 5:
                print(f"   ... and {len(type_issues) - 5} more issues of this type\n")
        
        print("🔧 Please fix these issues before finalizing the documentation site.")