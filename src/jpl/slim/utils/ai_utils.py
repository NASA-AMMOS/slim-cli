"""
AI utility functions for SLIM with library-agnostic AI integration.

This module contains utility functions for AI operations, including generating content
with various AI models through a unified interface. Function names are kept
library-agnostic to support future changes in underlying AI libraries.
Integrates with the centralized prompt management system.
"""

import os
import logging
from typing import Optional, Generator, Any, Dict

# Import functions from io_utils
from jpl.slim.utils.io_utils import (
    fetch_best_practices,
    create_slim_registry_dictionary,
    read_file_content,
    fetch_readme,
    fetch_code_base,
    fetch_relative_file_paths
)
from jpl.slim.utils.prompt_utils import get_prompt_with_context

__all__ = [
    "generate_with_ai",
    "construct_prompt",
    "generate_ai_content",
    "generate_with_model",
    "enhance_content",
    "validate_model",
    "get_model_recommendations"
]


def generate_with_ai(best_practice_id, repo_path, template_path, model="openai/gpt-4o-mini"):
    """
    Uses AI to generate or modify content based on the provided best practice and repository.
    
    Args:
        best_practice_id: ID of the best practice to apply
        repo_path: Path to the cloned repository
        template_path: Path to the template file for the best practice
        model: Name of the AI model to use (example: "openai/gpt-4o", "anthropic/claude-3-5-sonnet-20241022")
        
    Returns:
        str: Generated or modified content, or None if an error occurs
    """
    # In test mode, return a mock response instead of calling AI services
    if os.environ.get('SLIM_TEST_MODE', 'False').lower() in ('true', '1', 't'):
        logging.info(f"TEST MODE: Simulating AI generation for best practice {best_practice_id}")
        return f"Mock AI-generated content for {best_practice_id}"
        
    logging.debug(f"Using AI to apply best practice ID: {best_practice_id} in repository {repo_path}")
    
    # Fetch best practice information
    from jpl.slim.commands.common import SLIM_REGISTRY_URI
    practices = fetch_best_practices(SLIM_REGISTRY_URI)
    asset_mapping = create_slim_registry_dictionary(practices)
    best_practice = asset_mapping.get(best_practice_id)
    
    if not best_practice:
        logging.error(f"Best practice ID {best_practice_id} not found.")
        return None
    
    # Read the template content
    template_content = read_file_content(template_path)
    if not template_content:
        return None
    
    # Import the AI context mapping
    from jpl.slim.best_practices.practice_mapping import get_ai_context_type
    
    # Fetch appropriate reference content based on best practice alias
    context_type = get_ai_context_type(best_practice_id)
    
    if context_type == 'governance':
        reference = fetch_readme(repo_path)
        additional_instruction = ""
    elif context_type == 'readme':
        reference = fetch_code_base(repo_path)
        additional_instruction = ""
    elif context_type == 'testing':
        reference1 = fetch_readme(repo_path)
        reference2 = "\n".join(fetch_relative_file_paths(repo_path))
        reference = "EXISTING README:\n" + reference1 + "\n\n" + "EXISTING DIRECTORY LISTING: " + reference2
        additional_instruction = "Within the provided testing template, only fill out the sections that plausibly have existing tests to fill out based on the directory listing provided (do not make up tests that do not exist)."
    else:
        reference = fetch_readme(repo_path)
        additional_instruction = ""
    
    if not reference:
        return None
        
    # Construct the prompt for the AI
    prompt = construct_prompt(template_content, best_practice, reference, additional_instruction if best_practice_id == 'SLIM-13.1' else "")
    
    # Generate and return the content using the specified model
    return generate_ai_content(prompt, model)


def construct_prompt(template_content, best_practice, reference, comment=""):
    """
    Construct a prompt for AI.
    
    Args:
        template_content: Content of the template
        best_practice: Best practice information
        reference: Reference content
        comment: Additional comment
        
    Returns:
        str: Constructed prompt
    """
    return (
        f"Fill out all blanks in the template below that start with INSERT. Use the provided context information to fill the blanks. Return the template with filled out values. {comment}\n\n"
        f"TEMPLATE:\n{template_content}\n\n"
        f"CONTEXT INFORMATION:\n{reference}\n\n"
    )


def enhance_content(content: str, practice_type: str, section_name: str, 
                   model: str, additional_context: Optional[str] = None) -> Optional[str]:
    """
    Enhance content using AI with centralized prompts and context.
    
    Args:
        content: Original content to enhance
        practice_type: Practice type (e.g., 'docgen', 'standard_practices')
        section_name: Section name (e.g., 'overview', 'installation') 
        model: AI model to use
        additional_context: Optional additional context
        
    Returns:
        Enhanced content, or original content if enhancement fails
    """
    try:
        # Get prompt with hierarchical context
        enhancement_prompt = get_prompt_with_context(practice_type, section_name, additional_context)
        
        if not enhancement_prompt:
            logging.warning(f"No prompt found for {practice_type}.{section_name}, using content as-is")
            return content
        
        # Combine prompt with content
        full_prompt = f"{enhancement_prompt}\n\nCONTENT TO ENHANCE:\n{content}"
        
        # Generate enhanced content
        enhanced = generate_ai_content(full_prompt, model)
        
        if enhanced:
            logging.debug(f"Successfully enhanced {section_name} content")
            return enhanced
        else:
            logging.warning(f"AI enhancement failed for {section_name}, using original content")
            return content
            
    except Exception as e:
        logging.error(f"Error during content enhancement: {str(e)}")
        return content


def generate_ai_content(prompt: str, model: str, **kwargs) -> Optional[str]:
    """
    Generate content using an AI model through a unified interface.
    
    Args:
        prompt: Prompt for the AI model
        model: Model name in format "provider/model" (e.g., "openai/gpt-4o", "anthropic/claude-3-5-sonnet-20241022")
        **kwargs: Additional parameters to pass to the model
        
    Returns:
        str: Generated content, or None if an error occurs
    """
    # Validate model format
    if '/' not in model:
        logging.error(f"Invalid model format: {model}. Expected format: 'provider/model'")
        return None
        
    provider, model_name = model.split('/', 1)
    
    # Use LiteLLM as the primary interface
    try:
        return generate_with_model(prompt, model, **kwargs)
    except Exception as e:
        logging.error(f"LiteLLM generation failed for {model}: {str(e)}")
        return None


def generate_with_model(prompt: str, model: str, **kwargs) -> Optional[str]:
    """
    Generate content using the primary AI interface (currently LiteLLM).
    
    Args:
        prompt: Prompt for the AI model
        model: Model name in format "provider/model" (e.g., "openai/gpt-4o", "anthropic/claude-3-5-sonnet-20241022")
        **kwargs: Additional parameters to pass to the model
        
    Returns:
        str: Generated content, or None if an error occurs
    """
    try:
        from litellm import completion
        
        # Prepare messages
        messages = [{"role": "user", "content": prompt}]
        
        # Set default parameters
        completion_kwargs = {
            "model": model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "temperature": kwargs.get("temperature", 0.1),
        }
        
        # Add any additional kwargs
        completion_kwargs.update(kwargs)
        
        logging.debug(f"Generating content using model: {model}")
        
        response = completion(**completion_kwargs)
        
        if response and response.choices:
            content = response.choices[0].message.content
            logging.debug(f"Successfully generated {len(content)} characters with {model}")
            return content
        else:
            logging.error(f"No content returned from {model}")
            return None
            
    except ImportError:
        logging.error("AI library not available. Install with: pip install litellm")
        return None
    except Exception as e:
        logging.error(f"Error generating content with model ({model}): {str(e)}")
        return None


def get_model_recommendations(task: str = "documentation") -> Dict[str, Dict[str, list]]:
    """
    Get model recommendations based on task and quality/cost preferences.
    
    Args:
        task: The task type ("documentation", "code_generation", "general")
        
    Returns:
        Dict with recommended models organized by quality/cost tiers
    """
    recommendations = {
        "documentation": {
            "premium": [
                "anthropic/claude-4"
                "anthropic/claude-opus-4-20250514",
                "anthropic/claude-sonnet-4-20250514",
                "anthropic/claude-3-5-sonnet-20241022",
                "openai/gpt-4o",
                "google/gemini-1.5-pro"
            ],
            "balanced": [
                "openai/gpt-4o-mini", 
                "anthropic/claude-3-haiku-20240307",
                "cohere/command-r",
                "mistral/mistral-large-latest"
            ],
            "fast": [
                "groq/llama-3.1-70b-versatile",
                "groq/mixtral-8x7b-32768",
                "together/meta-llama/Llama-3-8b-chat-hf"
            ],
            "local": [
                "ollama/llama3.1",
                "ollama/gemma2",
                "vllm/meta-llama/Llama-3-8b-chat-hf"
            ]
        },
        "code_generation": {
            "premium": [
                "anthropic/claude-4"
                "anthropic/claude-opus-4-20250514",
                "anthropic/claude-sonnet-4-20250514",
                "anthropic/claude-3-5-sonnet-20241022",
                "openai/gpt-4o",
                "mistral/codestral-latest"
            ],
            "balanced": [
                "openai/gpt-4o-mini",
                "anthropic/claude-3-haiku-20240307", 
                "cohere/command-r"
            ],
            "fast": [
                "groq/llama-3.1-70b-versatile",
                "together/meta-llama/CodeLlama-7b-Instruct-hf"
            ],
            "local": [
                "ollama/codellama",
                "ollama/llama3.1",
                "vllm/meta-llama/CodeLlama-7b-Instruct-hf"
            ]
        }
    }
    
    return recommendations.get(task, recommendations["documentation"])


def validate_model(model: str) -> tuple[bool, str]:
    """
    Validate model configuration and check if required environment variables are set.
    
    Args:
        model: Model name in format "provider/model"
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if '/' not in model:
        return False, f"Invalid model format: {model}. Expected format: 'provider/model'"
    
    provider, model_name = model.split('/', 1)
    
    # Check required environment variables by provider
    env_vars = {
        "openai": ["OPENAI_API_KEY"],
        "azure": ["AZURE_API_KEY", "AZURE_API_BASE", "AZURE_API_VERSION"],
        "anthropic": ["ANTHROPIC_API_KEY"],
        "google": ["GOOGLE_API_KEY"],
        "cohere": ["COHERE_API_KEY"],
        "mistral": ["MISTRAL_API_KEY"],
        "groq": ["GROQ_API_KEY"],
        "together": ["TOGETHER_API_KEY"],
        "huggingface": ["HUGGINGFACE_API_KEY"],
        "openrouter": ["OPENROUTER_API_KEY"],
        "replicate": ["REPLICATE_API_TOKEN"],
        "fireworks": ["FIREWORKS_API_KEY"],
        "deepinfra": ["DEEPINFRA_API_TOKEN"],
        "perplexity": ["PERPLEXITYAI_API_KEY"],
        "bedrock": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
        "vertex_ai": ["GOOGLE_APPLICATION_CREDENTIALS"],
        "ollama": [],  # No API key required for local Ollama
        "vllm": []     # No API key required for local VLLM
    }
    
    required_vars = env_vars.get(provider, [])
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        return False, f"Missing required environment variables for {provider}: {', '.join(missing_vars)}"
    
    return True, ""
