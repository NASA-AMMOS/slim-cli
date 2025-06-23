"""
Markdown linting module for documentation generator.

This module provides markdown and MDX syntax validation to prevent
compilation errors in generated documentation.
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class LintError:
    """Represents a markdown linting error."""
    line_number: int
    column: int
    error_type: str
    message: str
    content_snippet: str
    suggested_fix: Optional[str] = None


class MarkdownLinter:
    """
    Validates markdown content for syntax errors that could break MDX compilation.
    
    Focuses on MDX-specific issues that cause Docusaurus build failures.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the markdown linter."""
        self.logger = logger or logging.getLogger(__name__)
        
        # MDX-problematic patterns
        self.mdx_error_patterns = [
            # Unclosed or malformed HTML/JSX tags
            (r'<([^/>][^>]*[^/])>(?![^<]*</\1>)', 'unclosed_tag', 'Unclosed HTML/JSX tag'),
            # Email addresses that look like JSX
            (r'<([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})>', 'email_as_jsx', 'Email address interpreted as JSX'),
            # URLs in angle brackets
            (r'<(https?://[^>]+)>', 'url_as_jsx', 'URL in angle brackets interpreted as JSX'),
            # Standalone < or > that might be interpreted as JSX
            (r'(?<!\S)[<>](?!\S)', 'loose_angle_bracket', 'Loose angle bracket might be interpreted as JSX'),
            # @ symbol at start of what looks like a tag
            (r'<@[^>]*>', 'at_in_tag', '@ symbol in tag-like structure'),
            # Comparison operators not in code blocks
            (r'(?<!`)[<>]=?(?!`)', 'comparison_operator', 'Comparison operator outside code block'),
            # Unclosed markdown links
            (r'\[[^\]]+\](?!\()', 'unclosed_link', 'Markdown link missing URL'),
            # Malformed markdown links
            (r'\[[^\]]*\]\([^)]*$', 'malformed_link', 'Malformed markdown link'),
        ]
        
        # General markdown issues
        self.markdown_patterns = [
            # Multiple consecutive blank lines
            (r'\n{3,}', 'multiple_blanks', 'Multiple consecutive blank lines'),
            # Tabs instead of spaces
            (r'\t', 'tabs', 'Tab character found (use spaces)'),
            # Trailing whitespace
            (r'[ \t]+$', 'trailing_whitespace', 'Trailing whitespace'),
        ]
    
    def lint_file(self, file_path: str) -> List[LintError]:
        """
        Lint a markdown file and return errors.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            List of linting errors found
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.lint_content(content, file_path)
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {str(e)}")
            return []
    
    def lint_content(self, content: str, file_name: str = "content") -> List[LintError]:
        """
        Lint markdown content and return errors.
        
        Args:
            content: Markdown content to lint
            file_name: Name of the file for error reporting
            
        Returns:
            List of linting errors found
        """
        errors = []
        lines = content.split('\n')
        
        # Check for MDX-specific issues
        for pattern, error_type, message in self.mdx_error_patterns:
            errors.extend(self._check_pattern(content, lines, pattern, error_type, message))
        
        # Check for general markdown issues
        for pattern, error_type, message in self.markdown_patterns:
            errors.extend(self._check_pattern(content, lines, pattern, error_type, message, severity='warning'))
        
        # Check for specific MDX compilation issues
        errors.extend(self._check_mdx_specific_issues(content, lines))
        
        return sorted(errors, key=lambda e: (e.line_number, e.column))
    
    def _check_pattern(self, content: str, lines: List[str], pattern: str, 
                      error_type: str, message: str, severity: str = 'error') -> List[LintError]:
        """Check content against a regex pattern and return errors."""
        errors = []
        
        # Check line by line for better error reporting
        for line_num, line in enumerate(lines, 1):
            # Skip checking in code blocks
            if self._is_in_code_block(lines, line_num - 1):
                continue
                
            for match in re.finditer(pattern, line):
                errors.append(LintError(
                    line_number=line_num,
                    column=match.start() + 1,
                    error_type=error_type,
                    message=message,
                    content_snippet=line[max(0, match.start()-20):match.end()+20].strip()
                ))
        
        return errors
    
    def _check_mdx_specific_issues(self, content: str, lines: List[str]) -> List[LintError]:
        """Check for MDX-specific compilation issues."""
        errors = []
        
        # Check for unescaped JSX-like content
        for line_num, line in enumerate(lines, 1):
            if self._is_in_code_block(lines, line_num - 1):
                continue
            
            # Check for potential JSX expressions
            jsx_chars = re.finditer(r'[<>{}]', line)
            for match in jsx_chars:
                char = match.group()
                pos = match.start()
                
                # Check context around the character
                before = line[max(0, pos-10):pos]
                after = line[pos+1:min(len(line), pos+10)]
                
                # Heuristic: if it looks like it might be interpreted as JSX
                if char == '<' and after and after[0].isalpha():
                    # Might be a tag
                    if not re.match(r'^[a-zA-Z]+[>\/\s]', after):
                        errors.append(LintError(
                            line_number=line_num,
                            column=pos + 1,
                            error_type='potential_jsx',
                            message=f'Character "{char}" might be interpreted as JSX',
                            content_snippet=line[max(0, pos-20):pos+20].strip(),
                            suggested_fix=f'Wrap in backticks: `{char}`'
                        ))
        
        return errors
    
    def _is_in_code_block(self, lines: List[str], line_index: int) -> bool:
        """Check if a line is inside a code block."""
        in_code_block = False
        fence_pattern = re.compile(r'^```')
        
        for i in range(line_index):
            if fence_pattern.match(lines[i]):
                in_code_block = not in_code_block
        
        return in_code_block
    
    def get_fix_suggestions(self, errors: List[LintError]) -> Dict[str, str]:
        """
        Get suggested fixes for common errors.
        
        Args:
            errors: List of lint errors
            
        Returns:
            Dictionary of error types to suggested fixes
        """
        suggestions = {
            'unclosed_tag': 'Close the HTML/JSX tag or make it self-closing',
            'email_as_jsx': 'Wrap email in backticks or use [email](mailto:email) format',
            'url_as_jsx': 'Convert to markdown link: [url](url)',
            'loose_angle_bracket': 'Wrap in backticks or use words "less than"/"greater than"',
            'at_in_tag': 'Escape the @ symbol or restructure the content',
            'comparison_operator': 'Wrap in backticks for code or use words',
            'unclosed_link': 'Add the URL part: [text](url)',
            'malformed_link': 'Fix the markdown link syntax',
        }
        
        return {error.error_type: suggestions.get(error.error_type, 'Fix the syntax error') 
                for error in errors}