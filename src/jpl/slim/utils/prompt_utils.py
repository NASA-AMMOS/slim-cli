"""
Prompt management utilities for SLIM CLI.

This module provides functionality for loading and managing AI prompts
with hierarchical context support. Context can be optionally defined
at any level of the YAML structure and will be inherited by child levels.
"""

import os
import yaml
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

# Cache for loaded prompts to avoid repeated file I/O
_prompts_cache: Optional[Dict[str, Any]] = None

__all__ = [
    "get_prompt_with_context",
    "get_prompt",
    "get_context_hierarchy",
    "load_prompts",
    "clear_prompts_cache"
]


def load_prompts(prompts_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Load prompts from YAML file.
    
    Args:
        prompts_file: Path to prompts YAML file. If None, uses default location.
        
    Returns:
        Dictionary containing all prompt definitions
        
    Raises:
        FileNotFoundError: If prompts file doesn't exist
        yaml.YAMLError: If YAML file is malformed
    """
    global _prompts_cache
    
    if prompts_file is None:
        # Default location relative to this file
        current_dir = Path(__file__).parent.parent
        prompts_file = current_dir / "prompts" / "prompts.yaml"
    
    prompts_file = Path(prompts_file)
    
    # Use cache if file hasn't changed
    if _prompts_cache is not None:
        return _prompts_cache
    
    if not prompts_file.exists():
        raise FileNotFoundError(f"Prompts file not found: {prompts_file}")
    
    try:
        with open(prompts_file, 'r', encoding='utf-8') as f:
            prompts_dict = yaml.safe_load(f) or {}
            _prompts_cache = prompts_dict
            logging.debug(f"Loaded prompts from {prompts_file}")
            return prompts_dict
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing prompts YAML file {prompts_file}: {str(e)}")
    except Exception as e:
        logging.error(f"Error loading prompts from {prompts_file}: {str(e)}")
        return {}


def clear_prompts_cache():
    """Clear the prompts cache. Useful for testing or when prompts file changes."""
    global _prompts_cache
    _prompts_cache = None


def get_context_hierarchy(practice_type: str, prompt_key: Optional[str] = None) -> List[str]:
    """
    Get all applicable context values from the hierarchy.
    
    Collects context from root level, practice type level, and specific prompt level
    (if prompt_key is provided). Only includes context values that are actually
    defined in the YAML structure.
    
    Args:
        practice_type: The practice type (e.g., 'docgen', 'standard_practices')
        prompt_key: Optional specific prompt key (e.g., 'overview', 'readme')
        
    Returns:
        List of context strings in hierarchy order (root -> practice -> specific)
    """
    try:
        prompts_dict = load_prompts()
    except Exception as e:
        logging.warning(f"Could not load prompts for context hierarchy: {str(e)}")
        return []
    
    contexts = []
    
    # Check for global/root context
    if 'context' in prompts_dict:
        contexts.append(prompts_dict['context'])
    
    # Check for practice type context
    if practice_type in prompts_dict:
        practice_dict = prompts_dict[practice_type]
        if isinstance(practice_dict, dict) and 'context' in practice_dict:
            contexts.append(practice_dict['context'])
        
        # Check for specific prompt context (if prompt_key provided)
        if prompt_key and prompt_key in practice_dict:
            prompt_dict = practice_dict[prompt_key]
            if isinstance(prompt_dict, dict) and 'context' in prompt_dict:
                contexts.append(prompt_dict['context'])
    
    return contexts


def get_prompt(practice_type: str, prompt_key: str) -> Optional[str]:
    """
    Get a prompt without context.
    
    Args:
        practice_type: The practice type (e.g., 'docgen', 'standard_practices')
        prompt_key: The specific prompt key (e.g., 'overview', 'readme')
        
    Returns:
        The prompt string, or None if not found
    """
    try:
        prompts_dict = load_prompts()
    except Exception as e:
        logging.warning(f"Could not load prompts: {str(e)}")
        return None
    
    if practice_type not in prompts_dict:
        logging.warning(f"Practice type '{practice_type}' not found in prompts")
        return None
    
    practice_dict = prompts_dict[practice_type]
    if not isinstance(practice_dict, dict):
        logging.warning(f"Practice type '{practice_type}' is not a dictionary")
        return None
    
    if prompt_key not in practice_dict:
        logging.warning(f"Prompt key '{prompt_key}' not found in practice '{practice_type}'")
        return None
    
    prompt_config = practice_dict[prompt_key]
    
    # Handle simple string prompts
    if isinstance(prompt_config, str):
        return prompt_config
    
    # Handle dictionary prompts with 'prompt' key
    if isinstance(prompt_config, dict) and 'prompt' in prompt_config:
        return prompt_config['prompt']
    
    logging.warning(f"No prompt found for {practice_type}.{prompt_key}")
    return None


def get_prompt_with_context(practice_type: str, prompt_key: str, 
                          additional_context: Optional[str] = None) -> Optional[str]:
    """
    Get a prompt with all applicable context from the hierarchy.
    
    Collects context from all levels (global, practice type, specific prompt)
    and combines them with the prompt. Context is only included if the 'context'
    key exists at each level.
    
    Args:
        practice_type: The practice type (e.g., 'docgen', 'standard_practices')
        prompt_key: The specific prompt key (e.g., 'overview', 'readme')
        additional_context: Optional additional context to append
        
    Returns:
        Combined context and prompt string, or None if prompt not found
    """
    # Get the base prompt
    prompt = get_prompt(practice_type, prompt_key)
    if prompt is None:
        return None
    
    # Get context hierarchy
    contexts = get_context_hierarchy(practice_type, prompt_key)
    
    # Add additional context if provided
    if additional_context:
        contexts.append(additional_context)
    
    # Combine contexts with prompt
    if contexts:
        full_context = '\n\n'.join(contexts)
        return f"{full_context}\n\n{prompt}"
    else:
        return prompt


def substitute_variables(text: str, variables: Dict[str, str]) -> str:
    """
    Substitute variables in text using {variable_name} format.
    
    Args:
        text: Text containing variables to substitute
        variables: Dictionary of variable names to values
        
    Returns:
        Text with variables substituted
    """
    if not variables:
        return text
    
    try:
        return text.format(**variables)
    except KeyError as e:
        # Use string.Template for partial substitution
        import string
        import re
        
        # Find all variables in the text
        pattern = r'\{([^}]+)\}'
        all_vars = re.findall(pattern, text)
        
        # Find missing variables
        missing_vars = [var for var in all_vars if var not in variables]
        
        if missing_vars:
            import warnings
            warnings.warn(f"Some variables were not found and cannot be substituted: {missing_vars}")
        
        # Perform partial substitution
        result = text
        for var_name, var_value in variables.items():
            result = result.replace(f'{{{var_name}}}', str(var_value))
        
        return result
    except Exception as e:
        logging.warning(f"Error substituting variables: {str(e)}")
        return text


def validate_prompts_file(prompts_file: Optional[str] = None) -> List[str]:
    """
    Validate the structure of the prompts YAML file.
    
    Args:
        prompts_file: Path to prompts file. If None, uses default location.
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    try:
        prompts_dict = load_prompts(prompts_file)
    except Exception as e:
        return [f"Could not load prompts file: {str(e)}"]
    
    # Check overall structure
    if not isinstance(prompts_dict, dict):
        errors.append("Prompts file must contain a dictionary at root level")
        return errors
    
    # Validate each practice type
    for practice_type, practice_config in prompts_dict.items():
        if practice_type == 'context':
            # Global context is valid
            continue
            
        if not isinstance(practice_config, dict):
            errors.append(f"Practice type '{practice_type}' must be a dictionary")
            continue
        
        # Check for prompts within practice type
        has_prompts = False
        for key, value in practice_config.items():
            if key == 'context':
                continue
                
            if isinstance(value, str):
                has_prompts = True
            elif isinstance(value, dict):
                if 'prompt' in value:
                    has_prompts = True
                else:
                    errors.append(f"Prompt configuration '{practice_type}.{key}' missing 'prompt' key")
            else:
                errors.append(f"Invalid prompt configuration type for '{practice_type}.{key}'")
        
        if not has_prompts:
            errors.append(f"Practice type '{practice_type}' contains no valid prompts")
    
    return errors