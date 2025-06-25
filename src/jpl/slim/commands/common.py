"""
Common utilities and constants for SLIM CLI commands with LiteLLM support.

This module contains constants and utility functions that are shared
across multiple command modules, including comprehensive model support
through LiteLLM integration.
"""

import logging
import os
from typing import Dict, List, Any, Tuple
import typer

# Constants
SLIM_REGISTRY_URI = "https://raw.githubusercontent.com/NASA-AMMOS/slim/main/static/data/slim-registry.json"

# Documentation practice aliases
DOCUMENTATION_PRACTICE_IDS = {'docs-website'}

# Minimal provider environment variable mapping for validation
PROVIDER_ENV_VARS = {
    "openai": ["OPENAI_API_KEY"],
    "anthropic": ["ANTHROPIC_API_KEY"],
    "google": ["GOOGLE_API_KEY"],
    "cohere": ["COHERE_API_KEY"],
    "mistral": ["MISTRAL_API_KEY"],
    "groq": ["GROQ_API_KEY"],
    "together": ["TOGETHER_API_KEY"],
    "openrouter": ["OPENROUTER_API_KEY"],
    "huggingface": ["HUGGINGFACE_API_KEY"],
    "bedrock": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "vertex_ai": ["GOOGLE_APPLICATION_CREDENTIALS"],
    "azure": ["AZURE_API_KEY", "AZURE_API_BASE", "AZURE_API_VERSION"],
    "replicate": ["REPLICATE_API_TOKEN"],
    "fireworks": ["FIREWORKS_API_KEY"],
    "deepinfra": ["DEEPINFRA_API_TOKEN"],
    "perplexity": ["PERPLEXITYAI_API_KEY"],
    "ollama": [],  # No API key required for local Ollama
    "vllm": []     # No API key required for local VLLM
}

# Git-related constants
GIT_BRANCH_NAME_FOR_MULTIPLE_COMMITS = 'slim-best-practices'
GIT_DEFAULT_REMOTE_NAME = 'origin'
GIT_CUSTOM_REMOTE_NAME = 'slim-custom'
GIT_DEFAULT_COMMIT_MESSAGE = 'SLIM-CLI Best Practices Bot Commit'


def is_documentation_practice(practice_id: str) -> bool:
    """
    Check if a practice ID is for documentation generation.
    
    Args:
        practice_id: The practice ID to check
        
    Returns:
        True if it's a documentation practice, False otherwise
    """
    return practice_id in DOCUMENTATION_PRACTICE_IDS


def get_ai_model_pairs(supported_models: Dict[str, Any] = None) -> List[str]:
    """
    Get a list of AI model pairs in the format "provider/model".
    
    This function now redirects to the dynamic model discovery for current models.
    The supported_models parameter is ignored for backward compatibility.
    
    Returns:
        List of model pairs in the format "provider/model"
    """
    # Use dynamic model discovery instead of static data
    return get_dynamic_ai_model_pairs()


def get_dynamic_models_by_provider() -> Dict[str, List[str]]:
    """
    Get available models by provider from LiteLLM's dynamic registry.
    
    Returns:
        Dictionary of models by provider, or empty dict if LiteLLM unavailable
    """
    try:
        import litellm
        return dict(litellm.models_by_provider)
    except ImportError:
        logging.error("LiteLLM not available for dynamic model discovery")
        return {}
    except Exception as e:
        logging.error(f"Failed to fetch models from LiteLLM: {str(e)}")
        return {}


def get_dynamic_ai_model_pairs() -> List[str]:
    """
    Get a list of AI model pairs in format "provider/model" from LiteLLM's dynamic registry.
    
    Returns:
        List of model pairs, or empty list if unavailable
    """
    models_by_provider = get_dynamic_models_by_provider()
    
    if not models_by_provider:
        return []
    
    model_pairs = []
    for provider, models in models_by_provider.items():
        for model in models:
            model_pairs.append(f"{provider}/{model}")
    
    return model_pairs


def get_dynamic_recommended_models() -> Dict[str, List[str]]:
    """
    Get dynamic model recommendations from LiteLLM's current model registry.
    
    Returns:
        Dictionary with 'premium' and 'local' model categories
    """
    models_by_provider = get_dynamic_models_by_provider()
    
    if not models_by_provider:
        # Fallback to basic recommendations if LiteLLM unavailable
        return {
            "premium": [
                "anthropic/claude-3-5-sonnet-20241022",
                "openai/gpt-4o", 
                "openai/gpt-4o-mini"
            ],
            "local": [
                "ollama/llama3.1:8b",
                "ollama/gemma3:12b"
            ]
        }
    
    recommendations = {"premium": [], "local": []}
    
    # Premium cloud models
    # Claude models (prioritize latest versions)
    claude_models = models_by_provider.get("anthropic", [])
    claude_filtered = []
    for model in claude_models:
        if "claude-3" in model or "claude-4" in model:
            if "sonnet" in model or "haiku" in model:
                claude_filtered.append(f"anthropic/{model}")
    
    # Prioritize latest Claude models
    priority_claude = [m for m in claude_filtered if "20241022" in m or "latest" in m or "claude-4" in m]
    other_claude = [m for m in claude_filtered if m not in priority_claude]
    recommendations["premium"].extend(priority_claude[:3])  # Top 3 Claude models
    
    # OpenAI GPT-4 models (prioritize common ones)
    openai_models = models_by_provider.get("openai", [])
    gpt4_filtered = []
    for model in openai_models:
        if "gpt-4" in model and "preview" not in model.lower() and "search" not in model.lower():
            gpt4_filtered.append(f"openai/{model}")
    
    # Prioritize key GPT-4 models
    priority_gpt4 = [m for m in gpt4_filtered if any(x in m for x in ["gpt-4o", "gpt-4-turbo"])]
    recommendations["premium"].extend(priority_gpt4[:3])  # Top 3 GPT-4 models
    
    # Local models (static list as these are ollama-specific)
    recommendations["local"] = [
        "ollama/llama3.1:8b",
        "ollama/llama3.1:70b", 
        "ollama/gemma3:12b",
        "ollama/gemma3:27b",
        "ollama/llama4:16x17b"
    ]
    
    return recommendations


def validate_model_format(model: str) -> Tuple[bool, str, str]:
    """
    Validate model format and extract provider/model components.
    
    Args:
        model: Model string in "provider/model" format
        
    Returns:
        Tuple of (is_valid, provider, model_name)
    """
    if '/' not in model:
        return False, "", ""
    
    try:
        provider, model_name = model.split('/', 1)
        return True, provider, model_name
    except ValueError:
        return False, "", ""


def check_model_availability(model: str) -> Tuple[bool, str]:
    """
    Check if a model is supported and properly configured using LiteLLM's built-in validation.
    
    Args:
        model: Model string in "provider/model" format
        
    Returns:
        Tuple of (is_available, error_message)
    """
    is_valid, provider, model_name = validate_model_format(model)
    
    if not is_valid:
        return False, f"Invalid model format: {model}. Expected 'provider/model'"
    
    # Check if provider is supported
    if provider not in PROVIDER_ENV_VARS:
        return False, f"Unsupported provider: {provider}. Supported providers: {', '.join(PROVIDER_ENV_VARS.keys())}"
    
    # Use LiteLLM's built-in validation for more accurate checking
    try:
        from litellm import validate_environment
        
        # Use LiteLLM's validate_environment function for accurate validation
        env_result = validate_environment(model)
        
        if not env_result.get('keys_in_environment', False):
            missing_keys = env_result.get('missing_keys', [])
            if missing_keys:
                return False, f"Missing required environment variables for {provider}: {', '.join(missing_keys)}"
            else:
                return False, f"Environment validation failed for model {model}"
        
        return True, ""
        
    except ImportError:
        # Fallback to original validation if LiteLLM not available
        logging.warning("LiteLLM not available for enhanced model validation, using basic validation")
        
        # Check required environment variables using our minimal mapping
        required_env_vars = PROVIDER_ENV_VARS[provider]
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            return False, f"Missing required environment variables for {provider}: {', '.join(missing_vars)}"
        
        return True, ""
        
    except Exception as e:
        # If LiteLLM validation fails, it usually means the model is not properly configured
        error_msg = str(e)
        if "not found" in error_msg.lower() or "invalid" in error_msg.lower():
            return False, f"Model {model} is not valid or not available"
        else:
            return False, f"Model validation failed: {error_msg}"


def setup_logging(logging_level):
    """
    Set up logging with the specified level.
    
    Args:
        logging_level: Logging level to use
    """
    logging.basicConfig(
        level=logging_level, 
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        force=True  # Force reconfiguration if already configured
    )


def configure_logging(command_logging: str = None, state=None):
    """
    Configure logging based on command-level or global-level logging option.
    
    Args:
        command_logging: Command-specific logging level (takes precedence)
        state: Global state object with logging_level attribute
        
    Returns:
        The configured logging level
    """
    # Command-level logging takes precedence over global
    if command_logging:
        log_level = getattr(logging, command_logging.upper(), None)
        if log_level is None:
            from rich.console import Console
            console = Console()
            console.print("❌ Invalid logging level provided. Choose from DEBUG, INFO, WARNING, ERROR, CRITICAL.", style="red")
            raise typer.Exit(1)
        setup_logging(log_level)
        return log_level
    
    # Use global logging level if set
    if state and hasattr(state, 'logging_level') and state.logging_level:
        return state.logging_level
    
    # Default to INFO
    return logging.INFO


def get_provider_setup_instructions(provider: str) -> str:
    """
    Get setup instructions for a specific provider.
    
    Args:
        provider: Provider name
        
    Returns:
        String with setup instructions
    """
    instructions = {
        "openai": """
OpenAI Setup:
1. Get API key from https://platform.openai.com/api-keys
2. Set environment variable: export OPENAI_API_KEY="sk-..."
""",
        "anthropic": """
Anthropic Setup:
1. Get API key from https://console.anthropic.com/
2. Set environment variable: export ANTHROPIC_API_KEY="sk-ant-..."
""",
        "google": """
Google AI Studio Setup:
1. Get API key from https://makersuite.google.com/app/apikey
2. Set environment variable: export GOOGLE_API_KEY="AIza..."
""",
        "cohere": """
Cohere Setup:
1. Get API key from https://dashboard.cohere.ai/api-keys
2. Set environment variable: export COHERE_API_KEY="..."
""",
        "mistral": """
Mistral AI Setup:
1. Get API key from https://console.mistral.ai/
2. Set environment variable: export MISTRAL_API_KEY="..."
""",
        "groq": """
Groq Setup:
1. Get API key from https://console.groq.com/keys
2. Set environment variable: export GROQ_API_KEY="gsk_..."
""",
        "together": """
Together AI Setup:
1. Get API key from https://api.together.xyz/settings/api-keys
2. Set environment variable: export TOGETHER_API_KEY="..."
""",
        "openrouter": """
OpenRouter Setup:
1. Get API key from https://openrouter.ai/keys
2. Set environment variable: export OPENROUTER_API_KEY="sk-or-..."
""",
        "huggingface": """
Hugging Face Setup:
1. Get API key from https://huggingface.co/settings/tokens
2. Set environment variable: export HUGGINGFACE_API_KEY="hf_..."
""",
        "replicate": """
Replicate Setup:
1. Get API token from https://replicate.com/account/api-tokens
2. Set environment variable: export REPLICATE_API_TOKEN="r8_..."
""",
        "fireworks": """
Fireworks AI Setup:
1. Get API key from https://fireworks.ai/api-keys
2. Set environment variable: export FIREWORKS_API_KEY="..."
""",
        "bedrock": """
AWS Bedrock Setup:
1. Configure AWS credentials via AWS CLI or environment variables:
   export AWS_ACCESS_KEY_ID="..."
   export AWS_SECRET_ACCESS_KEY="..."
   export AWS_DEFAULT_REGION="us-east-1"
2. Ensure you have access to Bedrock models in your AWS account
""",
        "vertex_ai": """
Google Vertex AI Setup:
1. Create a service account in Google Cloud Console
2. Download the service account JSON file
3. Set environment variable: export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
""",
        "azure": """
Azure OpenAI Setup:
1. Get your Azure OpenAI credentials from Azure portal
2. Set environment variables:
   export AZURE_API_KEY="..."
   export AZURE_API_BASE="https://your-resource.openai.azure.com/"
   export AZURE_API_VERSION="2024-02-01"
""",
        "ollama": """
Ollama Setup (Local):
1. Install Ollama from https://ollama.ai/
2. Start the service: ollama serve
3. Pull a model: ollama pull llama3.1
4. No API key required for local usage
""",
        "vllm": """
vLLM Setup (Local):
1. Install vLLM: pip install vllm
2. Start a vLLM server with your chosen model
3. No API key required for local usage
"""
    }
    
    return instructions.get(provider, f"No setup instructions available for {provider}")


def get_legacy_ai_model_pairs(supported_models: Dict[str, List[str]]) -> List[str]:
    """
    Get a list of AI model pairs in the format "provider/model" (legacy format).
    
    Args:
        supported_models: Dictionary of supported models by provider (legacy format)
        
    Returns:
        List of model pairs in the format "provider/model"
    """
    return [f"{key}/{model}" for key, models in supported_models.items() for model in models]