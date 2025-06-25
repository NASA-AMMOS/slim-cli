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

# LiteLLM supported models organized by provider and use case
SUPPORTED_MODELS = {
    # Premium cloud providers (recommended for production)
    "openai": {
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo", "gpt-4-turbo"],
        "description": "OpenAI models - excellent for documentation and code generation",
        "tier": "premium",
        "env_vars": ["OPENAI_API_KEY"]
    },
    "anthropic": {
        "models": [
            "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", 
            "claude-3-haiku-20240307", "claude-3-sonnet-20240229"
        ],
        "description": "Anthropic Claude models - superior reasoning and documentation quality",
        "tier": "premium", 
        "env_vars": ["ANTHROPIC_API_KEY"]
    },
    "google": {
        "models": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"],
        "description": "Google Gemini models - excellent multimodal capabilities",
        "tier": "premium",
        "env_vars": ["GOOGLE_API_KEY"]
    },
    
    # Balanced quality/cost providers
    "cohere": {
        "models": ["command-r-plus", "command-r", "command"],
        "description": "Cohere models - good balance of quality and cost",
        "tier": "balanced",
        "env_vars": ["COHERE_API_KEY"]
    },
    "mistral": {
        "models": ["mistral-large-latest", "mistral-medium-latest", "codestral-latest"],
        "description": "Mistral models - excellent for code and European data compliance",
        "tier": "balanced",
        "env_vars": ["MISTRAL_API_KEY"]
    },
    
    # High-performance providers
    "groq": {
        "models": [
            "llama-3.1-70b-versatile", "llama-3.1-8b-instant", 
            "mixtral-8x7b-32768", "gemma-7b-it"
        ],
        "description": "Groq models - ultra-fast inference (10-100x faster)",
        "tier": "fast",
        "env_vars": ["GROQ_API_KEY"]
    },
    "together": {
        "models": [
            "meta-llama/Llama-3-8b-chat-hf", "meta-llama/Llama-3-70b-chat-hf",
            "mistralai/Mixtral-8x7B-Instruct-v0.1", "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO"
        ],
        "description": "Together AI - cost-effective access to open source models",
        "tier": "balanced",
        "env_vars": ["TOGETHER_API_KEY"]
    },
    
    # Multi-model access providers
    "openrouter": {
        "models": [
            "anthropic/claude-3.5-sonnet", "openai/gpt-4o", "google/gemini-pro",
            "meta-llama/llama-3.1-8b-instruct", "mistralai/mixtral-8x7b-instruct"
        ],
        "description": "OpenRouter - access to 200+ models through single API",
        "tier": "balanced",
        "env_vars": ["OPENROUTER_API_KEY"]
    },
    "huggingface": {
        "models": [
            "meta-llama/Llama-2-7b-chat-hf", "meta-llama/CodeLlama-7b-Instruct-hf",
            "microsoft/DialoGPT-medium", "facebook/blenderbot-400M-distill"
        ],
        "description": "Hugging Face - access to 1000+ open source models",
        "tier": "balanced",
        "env_vars": ["HUGGINGFACE_API_KEY"]
    },
    
    # Cloud infrastructure providers
    "bedrock": {
        "models": [
            "anthropic.claude-3-sonnet-20240229-v1:0", "anthropic.claude-v2",
            "meta.llama3-70b-instruct-v1:0", "amazon.titan-text-express-v1"
        ],
        "description": "AWS Bedrock - enterprise-grade model hosting",
        "tier": "premium",
        "env_vars": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
    },
    "vertex_ai": {
        "models": ["gemini-pro", "gemini-1.5-pro", "text-bison", "chat-bison"],
        "description": "Google Vertex AI - enterprise Google models",
        "tier": "premium", 
        "env_vars": ["GOOGLE_APPLICATION_CREDENTIALS"]
    },
    "azure": {
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo", "gpt-4"],
        "description": "Azure OpenAI - enterprise OpenAI models",
        "tier": "premium",
        "env_vars": ["AZURE_API_KEY", "AZURE_API_BASE", "AZURE_API_VERSION"]
    },
    
    # Cost-effective providers
    "replicate": {
        "models": [
            "meta/llama-2-70b-chat", "meta/llama-2-13b-chat",
            "mistralai/mixtral-8x7b-instruct-v0.1"
        ],
        "description": "Replicate - pay-per-use model hosting",
        "tier": "balanced",
        "env_vars": ["REPLICATE_API_TOKEN"]
    },
    "fireworks": {
        "models": [
            "accounts/fireworks/models/llama-v3-70b-instruct",
            "accounts/fireworks/models/mixtral-8x7b-instruct"
        ],
        "description": "Fireworks AI - optimized inference for open source models",
        "tier": "fast",
        "env_vars": ["FIREWORKS_API_KEY"]
    },
    
    # Local/self-hosted options
    "ollama": {
        "models": ["llama3.1", "gemma2", "codellama", "mistral", "qwen2.5"],
        "description": "Ollama - local model serving (offline capable)",
        "tier": "local",
        "env_vars": []
    },
    "vllm": {
        "models": [
            "meta-llama/Llama-3-8b-chat-hf", "meta-llama/CodeLlama-7b-Instruct-hf",
            "mistralai/Mixtral-8x7B-Instruct-v0.1"
        ],
        "description": "vLLM - high-performance local inference server",
        "tier": "local",
        "env_vars": []
    }
}

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
                         If None, uses SUPPORTED_MODELS.
        
    Returns:
        List of model pairs in the format "provider/model"
    """
    if supported_models is None:
        supported_models = SUPPORTED_MODELS
        
    model_pairs = []
    for provider, config in supported_models.items():
        models = config.get("models", config) if isinstance(config, dict) else config
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
    
    # Check if provider is supported
    if provider not in SUPPORTED_MODELS:
        return False, f"Unsupported provider: {provider}. Supported providers: {', '.join(SUPPORTED_MODELS.keys())}"
    
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
        
        provider_config = SUPPORTED_MODELS[provider]
        
        # Check if model is in supported list (optional check - LiteLLM might support more)
        supported_models = provider_config.get("models", [])
        if supported_models and model_name not in supported_models:
            logging.warning(f"Model {model_name} not in known supported models for {provider}, but will attempt to use it")
        
        # Check required environment variables using our fallback method
        required_env_vars = provider_config.get("env_vars", [])
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


def get_model_tier_info(model: str) -> Dict[str, str]:
    """
    Get tier and description information for a model.
    
    Args:
        model: Model string in "provider/model" format
        
    Returns:
        Dictionary with tier and description information
    """
    is_valid, provider, model_name = validate_model_format(model)
    
    if not is_valid or provider not in SUPPORTED_MODELS:
        return {"tier": "unknown", "description": "Unknown model"}
    
    provider_config = SUPPORTED_MODELS[provider]
    return {
        "tier": provider_config.get("tier", "unknown"),
        "description": provider_config.get("description", "No description available")
    }


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


def print_model_recommendations():
    """
    Print formatted model recommendations for different use cases.
    """
    print("\n🤖 SLIM CLI Model Recommendations\n")
    
    print("📚 For Documentation Generation:")
    print("  Premium Quality (Recommended for Production):")
    for model in MODEL_RECOMMENDATIONS["documentation"]["premium"]:
        tier_info = get_model_tier_info(model)
        print(f"    • {model} - {tier_info['description']}")
    
    print("\n  Balanced Quality/Cost:")
    for model in MODEL_RECOMMENDATIONS["documentation"]["balanced"][:3]:  # Show top 3
        tier_info = get_model_tier_info(model)
        print(f"    • {model} - {tier_info['description']}")
    
    print("\n  Fast & Affordable:")
    for model in MODEL_RECOMMENDATIONS["documentation"]["fast"]:
        tier_info = get_model_tier_info(model)
        print(f"    • {model} - {tier_info['description']}")
    
    print("\n  Local/Offline:")
    for model in MODEL_RECOMMENDATIONS["documentation"]["local"]:
        tier_info = get_model_tier_info(model)
        print(f"    • {model} - {tier_info['description']}")
    
    print("\n💡 Usage Examples:")
    print("  # Premium quality documentation")
    print("  slim apply --best-practices docs-website --use-ai anthropic/claude-3-5-sonnet-20241022 ...")
    print("\n  # Fast generation")
    print("  slim apply --best-practices docs-website --use-ai groq/llama-3.1-70b-versatile ...")
    print("\n  # Local/offline")
    print("  slim apply --best-practices docs-website --use-ai ollama/llama3.1 ...")
    
    print(f"\n📋 Total supported providers: {len(SUPPORTED_MODELS)}")
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