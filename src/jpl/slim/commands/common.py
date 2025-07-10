"""
Common utilities and constants for SLIM CLI commands with LiteLLM support.

This module contains constants and utility functions that are shared
across multiple command modules, including comprehensive model support
through LiteLLM integration.
"""

import logging
import os
from typing import Dict, List, Any, Tuple

# Constants
SLIM_REGISTRY_URI = "https://raw.githubusercontent.com/NASA-AMMOS/slim/main/static/data/slim-registry.json"

# Documentation practice aliases
DOCUMENTATION_PRACTICE_IDS = {'docs-website'}

def get_dynamic_models_by_provider() -> Dict[str, List[str]]:
    """
    Get available models by provider using LiteLLM's dynamic discovery.
    
    Returns:
        Dictionary mapping provider names to lists of available models
    """
    try:
        import litellm
        return dict(litellm.models_by_provider)
    except ImportError:
        logging.error("LiteLLM not available for dynamic model discovery")
        return {}
    except Exception as e:
        logging.error(f"Failed to get dynamic models: {e}")
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

# Model recommendations by use case and quality tier
MODEL_RECOMMENDATIONS = {
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
            "together/meta-llama/CodeLlama-7b-Instruct-hf"
        ],
        "fast": [
            "groq/llama-3.1-70b-versatile",
            "fireworks/accounts/fireworks/models/llama-v3-70b-instruct"
        ],
        "local": [
            "ollama/codellama",
            "ollama/llama3.1",
            "vllm/meta-llama/CodeLlama-7b-Instruct-hf"
        ]
    }
}

# Legacy supported models for backward compatibility
LEGACY_SUPPORTED_MODELS = {
    "openai": ["gpt-4o-mini", "gpt-4o"],
    "ollama": ["llama3.3", "gemma3"],
    "azure": ["gpt-4o-mini", "gpt-4o"],
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
    
    Args:
        supported_models: Dictionary of supported models by provider.
                         If None, uses dynamic discovery.
        
    Returns:
        List of model pairs in the format "provider/model"
    """
    if supported_models is None:
        supported_models = get_dynamic_models_by_provider()
        
    model_pairs = []
    for provider, models in supported_models.items():
        # Handle both new dynamic format (list) and old static format (dict with models key)
        if isinstance(models, dict):
            models = models.get("models", [])
        for model in models:
            model_pairs.append(f"{provider}/{model}")
    
    return model_pairs


def get_recommended_models(task: str = "documentation", tier: str = "balanced") -> List[str]:
    """
    Get recommended models for a specific task and quality tier.
    
    Args:
        task: The task type ("documentation", "code_generation")
        tier: Quality/cost tier ("premium", "balanced", "fast", "local")
        
    Returns:
        List of recommended model names in "provider/model" format
    """
    recommendations = MODEL_RECOMMENDATIONS.get(task, MODEL_RECOMMENDATIONS["documentation"])
    return recommendations.get(tier, recommendations["balanced"])


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
        # Fallback validation if LiteLLM not available
        logging.warning("LiteLLM not available for enhanced model validation, using basic validation")
        return True, "LiteLLM not available - cannot validate model configuration"
        
    except Exception as e:
        # If LiteLLM validation fails, it usually means the model is not properly configured
        error_msg = str(e)
        if "not found" in error_msg.lower() or "invalid" in error_msg.lower():
            return False, f"Model {model} is not valid or not available"
        else:
            return False, f"Model validation failed: {error_msg}"


def get_model_tier_info(model: str) -> Dict[str, str]:
    """
    Get tier and description information for a model.
    
    Args:
        model: Model string in "provider/model" format
        
    Returns:
        Dictionary with tier and description information
    """
    is_valid, provider, model_name = validate_model_format(model)
    
    if not is_valid:
        return {"tier": "unknown", "description": "Unknown model"}
    
    # Return generic info since we no longer have static tier information
    return {
        "tier": "dynamic",
        "description": f"Model from {provider} provider (via LiteLLM)"
    }


def configure_logging(logging_level: str, state) -> None:
    """
    Configure logging hierarchically - command level overrides global level.
    
    Args:
        logging_level: String logging level from command line
        state: Global state object containing default logging level
    """
    if logging_level:
        # Command-level logging overrides global
        level = getattr(logging, logging_level.upper(), None)
        if level is not None:
            logging.getLogger().setLevel(level)
    else:
        # Use global state logging level
        logging.getLogger().setLevel(state.logging_level)


def setup_logging(logging_level):
    """
    Set up logging with the specified level.
    
    Args:
        logging_level: Logging level to use
    """
    logging.basicConfig(level=logging_level, format='%(asctime)s - %(levelname)s - %(message)s')


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


def print_model_recommendations():
    """
    Print formatted model recommendations for different use cases.
    """
    print("\n🤖 SLIM CLI Model Recommendations\n")
    
    print("📚 For Documentation Generation:")
    print("  Premium Quality (Recommended for Production):")
    premium_models = MODEL_RECOMMENDATIONS["documentation"]["premium"]
    for model in premium_models:
        print(f"    • {model}")
    
    print("\n  Balanced Quality/Cost:")
    balanced_models = MODEL_RECOMMENDATIONS["documentation"]["balanced"][:3]  # Show top 3
    for model in balanced_models:
        print(f"    • {model}")
    
    print("\n  Fast & Affordable:")
    fast_models = MODEL_RECOMMENDATIONS["documentation"]["fast"]
    for model in fast_models:
        print(f"    • {model}")
    
    print("\n  Local/Offline:")
    local_models = MODEL_RECOMMENDATIONS["documentation"]["local"]
    for model in local_models:
        print(f"    • {model}")
    
    print("\n💡 Usage Examples:")
    print("  # Premium quality documentation")
    print("  slim apply --best-practices docs-website --use-ai anthropic/claude-3-5-sonnet-20241022 ...")
    print("\n  # Fast generation")
    print("  slim apply --best-practices docs-website --use-ai groq/llama-3.1-70b-versatile ...")
    print("\n  # Local/offline")
    print("  slim apply --best-practices docs-website --use-ai ollama/llama3.1 ...")
    
    dynamic_models = get_dynamic_models_by_provider()
    print(f"\n📋 Total supported providers: {len(dynamic_models)}")
    print(f"📋 Total model combinations: {len(get_ai_model_pairs())}+")
    print("\nFor setup instructions: slim models setup <provider>")


def get_legacy_ai_model_pairs(supported_models: Dict[str, List[str]]) -> List[str]:
    """
    Get a list of AI model pairs in the format "provider/model" (legacy format).
    
    Args:
        supported_models: Dictionary of supported models by provider (legacy format)
        
    Returns:
        List of model pairs in the format "provider/model"
    """
    return [f"{key}/{model}" for key, models in supported_models.items() for model in models]