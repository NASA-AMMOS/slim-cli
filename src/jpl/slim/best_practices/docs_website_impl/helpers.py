### src/jpl/slim/docgen/utils/helpers.py
"""
Helper functions for the SLIM documentation generator.
"""
import logging
import os
import subprocess
import yaml
import re
from typing import Dict, List, Optional, Tuple, Union


def load_config(config_file: str) -> Dict:
    """
    Load configuration from YAML file.
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    if not config_file:
        return {}
        
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
            return config or {}
    except Exception as e:
        logging.warning(f"Error loading configuration from {config_file}: {str(e)}")
        return {}


def extract_frontmatter(content: str) -> tuple:
    """
    Extract frontmatter from markdown content.
    
    Args:
        content: Markdown content with frontmatter
        
    Returns:
        Tuple of (frontmatter_dict, content_without_frontmatter)
    """
    import yaml
    
    # Match frontmatter between --- markers
    frontmatter_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    
    if frontmatter_match:
        frontmatter_yaml = frontmatter_match.group(1)
        try:
            frontmatter = yaml.safe_load(frontmatter_yaml)
            content_without_frontmatter = content[frontmatter_match.end():]
            return frontmatter, content_without_frontmatter
        except Exception as e:
            logging.warning(f"Error parsing frontmatter: {str(e)}")
    
    # Return empty dict and original content if no frontmatter found
    return {}, content


def escape_mdx_special_characters(content: str) -> str:
    """
    Escape special characters in markdown content that might cause issues with MDX parsing.
    
    Args:
        content: Markdown content to process
        
    Returns:
        Processed content with special characters escaped
    """
    if not content:
        return content
        
    # Keep track of code block state
    in_code_block = False
    
    # Process content line by line
    lines = content.split('\n')
    processed_lines = []
    
    for line in lines:
        # Check for code block delimiters
        code_block_match = re.match(r'^```(\w*)', line)
        if code_block_match:
            in_code_block = not in_code_block  # Toggle code block state
            processed_lines.append(line)
            continue
            
        if not in_code_block:
            # Process line for potential HTML-like tags and other special characters
            processed_line = _process_line(line)
            processed_lines.append(processed_line)
        else:
            # In a code block - no need to escape special characters
            processed_lines.append(line)
    
    return '\n'.join(processed_lines)


def _process_line(line: str) -> str:
    """
    Process a single line of text to escape special characters and handle HTML-like tags.
    
    Args:
        line: Line of text to process
        
    Returns:
        Processed line with special characters escaped
    """
    # Skip processing for lines that are Markdown headings, links, etc.
    if re.match(r'^#{1,6}\s', line) or re.match(r'^>\s', line) or re.match(r'^[-*+]\s', line):
        return line
        
    # Handle inline code blocks first
    parts = []
    current_pos = 0
    
    # Split by inline code (text wrapped in backticks)
    for match in re.finditer(r'`[^`]+`', line):
        start, end = match.span()
        
        # Add text before the code with escaped characters
        if start > current_pos:
            text_before = line[current_pos:start]
            parts.append(_process_text(text_before))
        
        # Add the code block unchanged
        parts.append(line[start:end])
        current_pos = end
    
    # Add any remaining text with escaped characters
    if current_pos < len(line):
        parts.append(_process_text(line[current_pos:]))
    
    return ''.join(parts)


def _process_text(text: str) -> str:
    """
    Process a segment of text to escape special characters and handle HTML-like tags.
    
    Args:
        text: Text to process
        
    Returns:
        Processed text with special characters escaped
    """
    # First, find any potential HTML-like tags
    tag_matches = list(re.finditer(r'<([A-Za-z][A-Za-z0-9_.-]*)(?:\s+[^>]*)?>', text))
    
    if not tag_matches:
        # No HTML-like tags, just escape special characters
        return _escape_special_chars(text)
        
    # Build the result, escaping each part appropriately
    result = []
    current_pos = 0
    
    for match in tag_matches:
        start, end = match.span()
        tag_name = match.group(1)
        
        # Check if this looks like a real HTML tag we should preserve or an accidental tag
        if _is_common_html_tag(tag_name):
            # This looks like a real HTML tag, preserve it
            # Process text before the tag
            if start > current_pos:
                result.append(_escape_special_chars(text[current_pos:start]))
            # Add the tag unchanged
            result.append(text[start:end])
        else:
            # This is not a common HTML tag, escape the angle brackets
            if start > current_pos:
                result.append(_escape_special_chars(text[current_pos:start]))
            # Add the "tag" with escaped angle brackets
            escaped_tag = text[start:end].replace('<', '\\<').replace('>', '\\>')
            result.append(escaped_tag)
        
        current_pos = end
    
    # Add any remaining text
    if current_pos < len(text):
        result.append(_escape_special_chars(text[current_pos:]))
    
    return ''.join(result)


def _escape_special_chars(text: str) -> str:
    """
    Escape special characters in text.
    
    Args:
        text: Text to escape
        
    Returns:
        Text with special characters escaped
    """
    # Escape curly braces that aren't already escaped
    text = re.sub(r'(?<!\\){', '\\{', text)
    text = re.sub(r'(?<!\\)}', '\\}', text)
    
    # Escape angle brackets not followed by standard HTML tag patterns
    text = re.sub(r'(?<!\\)<(?![a-zA-Z\/])', '\\<', text)
    text = re.sub(r'(?<![a-zA-Z\/])(?<!\\)>', '\\>', text)
    
    return text


def _is_common_html_tag(tag_name: str) -> bool:
    """
    Check if a tag name is a common HTML tag we should preserve.
    
    Args:
        tag_name: Tag name to check
        
    Returns:
        True if it's a common HTML tag, False otherwise
    """
    common_tags = {
        # Block elements
        'div', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'header', 'footer', 'main', 'section', 'article',
        'aside', 'nav', 'figure', 'figcaption', 'blockquote', 'pre', 'code', 'ul', 'ol', 'li', 'dl', 'dt',
        'dd', 'table', 'thead', 'tbody', 'tr', 'td', 'th', 'form', 'fieldset', 'legend', 'hr',
        
        # Inline elements
        'a', 'span', 'strong', 'em', 'i', 'b', 'u', 's', 'sub', 'sup', 'mark', 'q', 'cite', 'time',
        'address', 'abbr', 'dfn', 'code', 'var', 'samp', 'kbd', 'data', 'small', 'br', 'wbr', 'img',
        'picture', 'source', 'iframe', 'embed', 'object', 'param', 'audio', 'video', 'track', 'canvas',
        'map', 'area', 'math', 'svg',
        
        # Form elements
        'input', 'button', 'select', 'option', 'optgroup', 'textarea', 'label', 'datalist', 'output',
        'progress', 'meter',
    }
    
    # Check if it's a common HTML tag or if it starts with uppercase (likely a React component)
    return tag_name.lower() in common_tags or (tag_name[0].isupper() if tag_name else False)


def escape_yaml_value(value: str) -> str:
    """
    Escape a value for safe inclusion in YAML front matter.
    
    This function ensures that string values containing special characters
    (like colons, quotes, etc.) are properly quoted in YAML.
    
    Args:
        value: String value to escape for YAML
        
    Returns:
        Properly escaped/quoted value for YAML
    """
    if not value:
        return '""'
    
    # Check if the value needs quoting
    # Values with colons, quotes, or other YAML special characters need to be quoted
    needs_quoting = any(char in value for char in [':', '"', "'", '[', ']', '{', '}', '|', '>', '@', '`'])
    
    if needs_quoting:
        # Use double quotes and escape any internal double quotes
        escaped_value = value.replace('"', '\\"')
        return f'"{escaped_value}"'
    
    return value


def clean_api_doc(api_doc_path: str) -> None:
    """
    Clean up the API documentation file to fix common MDX parsing issues.
    Applies targeted fixes for specific patterns known to cause problems.
    
    Args:
        api_doc_path: Path to the API documentation file to clean
    """
    if not os.path.exists(api_doc_path):
        return
        
    try:
        # Read the file content
        with open(api_doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Specific fixes for common API documentation issues
        
        # Fix 1: Replace angle brackets around type parameters (like <T> or <ES>)
        # This handles cases like "Type<T>" or "<ES> tag"
        content = re.sub(r'(?<![a-zA-Z/="`])(<)([A-Za-z][A-Za-z0-9_]*)(>)', r'\\<\2\\>', content)
        
        # Fix 2: Fix unclosed apparent HTML tags in text
        # Look for potential unclosed tags in sentences (not in code blocks)
        lines = content.split('\n')
        in_code_block = False
        for i, line in enumerate(lines):
            if line.strip() == '```' or re.match(r'^```\w*', line.strip()):
                in_code_block = not in_code_block
                continue
                
            if not in_code_block and '<' in line and '>' in line:
                # Outside code blocks, escape any remaining angle brackets that look suspicious
                lines[i] = re.sub(r'<([A-Za-z][A-Za-z0-9_]*)(?!\s*[/>])(?!.*</\1>)', r'\\<\1', line)
                lines[i] = re.sub(r'(?<!\\)<([A-Za-z][A-Za-z0-9_]*)\s+', r'\\<\1 ', lines[i])
                
        content = '\n'.join(lines)
        
        # Fix 3: Replace problematic character sequences
        problematic_sequences = [
            ('<ES>', '\\<ES\\>'),
            ('<Type>', '\\<Type\\>'),
            ('<Generic>', '\\<Generic\\>'),
            ('<Value>', '\\<Value\\>'),
            ('<Key>', '\\<Key\\>'),
            ('<Parameter>', '\\<Parameter\\>'),
            ('<Class>', '\\<Class\\>'),
            ('<Method>', '\\<Method\\>'),
            ('<Function>', '\\<Function\\>'),
            ('<Property>', '\\<Property\\>'),
        ]
        
        for seq, replacement in problematic_sequences:
            content = content.replace(seq, replacement)
        
        # Write the cleaned content back
        with open(api_doc_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logging.debug(f"Cleaned API documentation for MDX compatibility")
            
    except Exception as e:
        logging.error(f"Error cleaning API documentation: {str(e)}")
        # Continue with generation even if cleaning fails
