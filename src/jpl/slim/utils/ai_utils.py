"""
AI utility functions for SLIM with LiteLLM integration.

This module contains utility functions for AI operations, including generating content
with various AI models through LiteLLM's unified interface, plus legacy functions
for backward compatibility.
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

__all__ = [
    "generate_with_ai",
    "construct_prompt",
    "generate_content",
    "generate_with_litellm",
    "get_model_recommendations",
    "validate_model_config",
    # Legacy functions for backward compatibility
    "generate_with_openai",
    "generate_with_azure", 
    "generate_with_ollama"
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
    return generate_content(prompt, model)


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


def generate_content(prompt: str, model: str, **kwargs) -> Optional[str]:
    """
    Generate content using an AI model through LiteLLM's unified interface.
    
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
        return generate_with_litellm(prompt, model, **kwargs)
    except Exception as e:
        logging.warning(f"LiteLLM generation failed for {model}: {str(e)}")
        
        # Fallback to legacy implementations for backward compatibility
        if provider == "openai":
            collected_response = []
            for token in generate_with_openai(prompt, model_name):
                if token is not None:
                    collected_response.append(token)
                else:
                    logging.error("Error occurred during OpenAI generation.")
                    return None
            return ''.join(collected_response)
        elif provider == "azure":
            return generate_with_azure(prompt, model_name)
        elif provider == "ollama":
            return generate_with_ollama(prompt, model_name)
        else:
            logging.error(f"Unsupported model provider: {provider}")
            return None


def generate_with_litellm(prompt: str, model: str, **kwargs) -> Optional[str]:
    """
    Generate content using LiteLLM's unified interface.
    
    Args:
        prompt: Prompt for the AI model
        model: Model name in LiteLLM format (e.g., "openai/gpt-4o", "anthropic/claude-3-5-sonnet-20241022")
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
        
        logging.debug(f"Generating content with LiteLLM using model: {model}")
        
        response = completion(**completion_kwargs)
        
        if response and response.choices:
            content = response.choices[0].message.content
            logging.debug(f"Successfully generated {len(content)} characters with {model}")
            return content
        else:
            logging.error(f"No content returned from {model}")
            return None
            
    except ImportError:
        logging.error("LiteLLM not installed. Install with: pip install litellm")
        return None
    except Exception as e:
        logging.error(f"Error generating content with LiteLLM ({model}): {str(e)}")
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


def validate_model_config(model: str) -> tuple[bool, str]:
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


# Legacy functions for backward compatibility
def generate_with_openai(prompt, model_name):
    """
    Generate content using OpenAI (legacy function for backward compatibility).
    
    Args:
        prompt: Prompt for the AI model
        model_name: Name of the OpenAI model to use
        
    Yields:
        str: Generated content tokens
    """
    try:
        from openai import OpenAI
        from dotenv import load_dotenv
        load_dotenv()
        
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    except Exception as e:
        logging.error(f"An error occurred running OpenAI model: {e}")
        yield None


def generate_with_azure(prompt, model_name):
    """
    Generate content using Azure OpenAI (legacy function for backward compatibility).
    
    Args:
        prompt: Prompt for the AI model
        model_name: Name of the Azure OpenAI model to use
        
    Returns:
        str: Generated content, or None if an error occurs
    """
    try:
        from azure.identity import ClientSecretCredential, get_bearer_token_provider
        from openai import AzureOpenAI
        from dotenv import load_dotenv
        
        load_dotenv()

        APIM_SUBSCRIPTION_KEY = os.getenv("APIM_SUBSCRIPTION_KEY")
        default_headers = {}
        if APIM_SUBSCRIPTION_KEY:
            default_headers["Ocp-Apim-Subscription-Key"] = APIM_SUBSCRIPTION_KEY 

        # Set up authority and credentials for Azure authentication
        credential = ClientSecretCredential(
            tenant_id=os.getenv("AZURE_TENANT_ID"),
            client_id=os.getenv("AZURE_CLIENT_ID"),
            client_secret=os.getenv("AZURE_CLIENT_SECRET"),
            authority="https://login.microsoftonline.com",
        )

        token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")

        client = AzureOpenAI(
            azure_ad_token_provider=token_provider,
            api_version=os.getenv("API_VERSION"),
            azure_endpoint=os.getenv("API_ENDPOINT"),
            default_headers=default_headers,
        )

        completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "As a SLIM Best Practice User, your role is to understand, apply, and implement the best practices for Software Lifecycle Improvement and Modernization (SLIM) within your software projects. You should aim to optimize your software development processes, enhance the quality of your software products, and ensure continuous improvement across all stages of the software lifecycle.",
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=model_name
        )
        return completion.choices[0].message.content
    except Exception as e:
        logging.error(f"An error occurred running on Azure model: {str(e)}")
        return None


def generate_with_ollama(prompt, model_name):
    """
    Generate content using Ollama (legacy function for backward compatibility).
    
    Args:
        prompt: Prompt for the AI model
        model_name: Name of the Ollama model to use
        
    Returns:
        str: Generated content, or None if an error occurs
    """
    try:
        import ollama

        response = ollama.chat(model=model_name, messages=[
            {
                'role': 'user',
                'content': prompt,
            },
        ])
        return response['message']['content']
    except Exception as e:
        logging.error(f"Error running Ollama model: {e}")
        return None
    

def generate_content_with_fallback(prompt: str, model: str, **kwargs) -> Optional[str]:
    """
    Generate content with automatic fallback to alternative models.
    
    Args:
        prompt: Prompt for the AI model
        model: Primary model to try
        **kwargs: Additional parameters
        
    Returns:
        Generated content or None if all attempts fail
    """
    # Try primary model
    result = generate_content(prompt, model, **kwargs)
    if result:
        return result
    
    # Get tier info and try fallback models from same tier
    tier_info = get_model_tier_info(model)
    tier = tier_info.get("tier", "balanced")
    
    fallback_models = get_recommended_models("documentation", tier)
    
    for fallback_model in fallback_models:
        if fallback_model != model:  # Don't try the same model again
            logging.warning(f"Trying fallback model: {fallback_model}")
            result = generate_content(prompt, fallback_model, **kwargs)
            if result:
                return result
    
    logging.error("All AI models failed to generate content")
    return None