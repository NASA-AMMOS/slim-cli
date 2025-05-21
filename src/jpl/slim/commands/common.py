"""
Common utilities and constants for SLIM CLI commands.

This module contains constants and utility functions that are shared
across multiple command modules.
"""

import logging
import os
from typing import Dict, List, Any

# Constants
SLIM_REGISTRY_URI = "https://raw.githubusercontent.com/NASA-AMMOS/slim/main/static/data/slim-registry.json"
SUPPORTED_MODELS = {
    "openai": ["gpt-4o-mini", "gpt-4o"],
    "ollama": ["llama3.3", "gemma3"],
    "azure": ["gpt-4o-mini", "gpt-4o"],
    # Add more models as needed
}
GIT_BRANCH_NAME_FOR_MULTIPLE_COMMITS = 'slim-best-practices'
GIT_DEFAULT_REMOTE_NAME = 'origin'
GIT_CUSTOM_REMOTE_NAME = 'slim-custom'
GIT_DEFAULT_COMMIT_MESSAGE = 'SLIM-CLI Best Practices Bot Commit'

def get_ai_model_pairs(supported_models: Dict[str, List[str]]) -> List[str]:
    """
    Get a list of AI model pairs in the format "provider/model".
    
    Args:
        supported_models: Dictionary of supported models by provider
        
    Returns:
        List of model pairs in the format "provider/model"
    """
    return [f"{key}/{model}" for key, models in supported_models.items() for model in models]

def setup_logging(logging_level):
    """
    Set up logging with the specified level.
    
    Args:
        logging_level: Logging level to use
    """
    logging.basicConfig(level=logging_level, format='%(asctime)s - %(levelname)s - %(message)s')
