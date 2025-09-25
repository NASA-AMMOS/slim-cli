"""
MCP Resources for SLIM-CLI.

This module provides MCP resources that expose SLIM registry data,
best practices information, and AI model details.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

# Import SLIM-CLI modules
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.jpl.slim.utils.io_utils import fetch_best_practices
from src.jpl.slim.commands.common import (
    SLIM_REGISTRY_URI,
    get_dynamic_ai_model_pairs,
    get_dynamic_recommended_models,
    get_dynamic_models_by_provider,
    MODEL_RECOMMENDATIONS
)
# Note: SLIM prompts are stored in YAML file, not Python module

from .config import RESOURCE_URIS, PROMPT_TEMPLATES, BEST_PRACTICE_CATEGORIES
from .utils import log_mcp_operation, format_error_message

logger = logging.getLogger(__name__)

class SlimRegistryResource:
    """Resource for SLIM registry data."""
    
    def __init__(self):
        self.uri = RESOURCE_URIS["registry"]
        self.name = "SLIM Registry"
        self.description = "Complete SLIM best practices registry"
        self._cache = None
    
    def get_data(self) -> Dict[str, Any]:
        """Get registry data."""
        try:
            log_mcp_operation("get_slim_registry", {"uri": SLIM_REGISTRY_URI})
            
            if self._cache is None:
                practices = fetch_best_practices(SLIM_REGISTRY_URI)
                if not practices:
                    raise ValueError("Failed to fetch practices from registry")
                
                self._cache = {
                    "practices": practices,
                    "total_count": len(practices),
                    "categories": self._categorize_practices(practices),
                    "registry_uri": SLIM_REGISTRY_URI
                }
            
            return self._cache
        except Exception as e:
            logger.error(f"Error fetching registry data: {e}")
            raise RuntimeError(format_error_message(e, "Failed to fetch SLIM registry"))
    
    def _categorize_practices(self, practices: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Categorize practices by type."""
        categories = {}
        for practice in practices:
            title = practice.get("title", "")
            practice_id = practice.get("alias", "")
            
            # Try to determine category
            category = "other"
            if any(keyword in title.lower() for keyword in ["readme", "documentation", "changelog"]):
                category = "documentation"
            elif any(keyword in title.lower() for keyword in ["governance", "conduct", "contributing"]):
                category = "governance"
            elif any(keyword in title.lower() for keyword in ["secret", "security"]):
                category = "security"
            elif any(keyword in title.lower() for keyword in ["license"]):
                category = "licensing"
            
            if category not in categories:
                categories[category] = []
            categories[category].append(practice_id or title)
        
        return categories

class SlimBestPracticesResource:
    """Resource for individual best practice details."""
    
    def __init__(self):
        self.uri = RESOURCE_URIS["best_practices"]
        self.name = "SLIM Best Practices"
        self.description = "Detailed information about SLIM best practices"
    
    def get_data(self, practice_id: Optional[str] = None) -> Dict[str, Any]:
        """Get best practices data."""
        try:
            log_mcp_operation("get_best_practices", {"practice_id": practice_id})
            
            practices = fetch_best_practices(SLIM_REGISTRY_URI)
            if not practices:
                raise ValueError("Failed to fetch practices from registry")
            
            if practice_id:
                # Return specific practice
                for practice in practices:
                    if practice.get("alias") == practice_id:
                        return {
                            "practice": practice,
                            "category": self._get_practice_category(practice_id),
                            "assets": practice.get("assets", []),
                            "guide_url": self._get_guide_url(practice)
                        }
                raise ValueError(f"Practice '{practice_id}' not found")
            else:
                # Return all practices with summaries
                return {
                    "practices": [
                        {
                            "id": p.get("alias", ""),
                            "title": p.get("title", ""),
                            "description": p.get("description", ""),
                            "category": self._get_practice_category(p.get("alias", "")),
                            "assets_count": len(p.get("assets", [])),
                            "guide_url": self._get_guide_url(p)
                        }
                        for p in practices
                    ],
                    "total_count": len(practices),
                    "categories": BEST_PRACTICE_CATEGORIES
                }
        except Exception as e:
            logger.error(f"Error fetching best practices data: {e}")
            raise RuntimeError(format_error_message(e, "Failed to fetch best practices"))
    
    def _get_practice_category(self, practice_id: str) -> str:
        """Get category for a practice ID."""
        for category, practices in BEST_PRACTICE_CATEGORIES.items():
            if practice_id in practices:
                return category
        return "other"
    
    def _get_guide_url(self, practice: Dict[str, Any]) -> str:
        """Get guide URL for a practice."""
        uri = practice.get("uri", "")
        if uri:
            return f"https://nasa-ammos.github.io{uri}"
        return ""

class SlimPromptsResource:
    """Resource for SLIM prompt templates."""
    
    def __init__(self):
        self.uri = RESOURCE_URIS["prompts"]
        self.name = "SLIM Prompts"
        self.description = "Available SLIM prompt templates"
    
    def get_data(self, prompt_name: Optional[str] = None) -> Dict[str, Any]:
        """Get prompts data."""
        try:
            log_mcp_operation("get_prompts", {"prompt_name": prompt_name})
            
            if prompt_name:
                # Return specific prompt
                if prompt_name in PROMPT_TEMPLATES:
                    return {
                        "prompt": PROMPT_TEMPLATES[prompt_name],
                        "source": "mcp_templates"
                    }
                
                # Check SLIM prompts (would need to load from YAML file)
                # For now, return placeholder
                if prompt_name in ["readme", "governance", "docs-website"]:
                    return {
                        "prompt": f"SLIM prompt template for {prompt_name} (loaded from prompts.yaml)",
                        "source": "slim_prompts"
                    }
                
                raise ValueError(f"Prompt '{prompt_name}' not found")
            else:
                # Return all available prompts
                return {
                    "mcp_templates": PROMPT_TEMPLATES,
                    "slim_prompts": self._get_slim_prompts_summary(),
                    "total_count": len(PROMPT_TEMPLATES)
                }
        except Exception as e:
            logger.error(f"Error fetching prompts data: {e}")
            raise RuntimeError(format_error_message(e, "Failed to fetch prompts"))
    
    def _get_slim_prompts_summary(self) -> Dict[str, Any]:
        """Get summary of SLIM prompts."""
        try:
            # This would need to be implemented based on the actual SLIM prompts structure
            return {
                "available": True,
                "description": "SLIM CLI prompt templates for AI interactions"
            }
        except Exception:
            return {
                "available": False,
                "description": "SLIM prompts not accessible"
            }

class SlimModelsResource:
    """Resource for AI model information."""
    
    def __init__(self):
        self.uri = RESOURCE_URIS["models"]
        self.name = "SLIM AI Models"
        self.description = "Available AI models and recommendations"
    
    def get_data(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Get AI models data."""
        try:
            log_mcp_operation("get_models", {"provider": provider})
            
            # Get dynamic models
            models_by_provider = get_dynamic_models_by_provider()
            model_pairs = get_dynamic_ai_model_pairs()
            recommendations = get_dynamic_recommended_models()
            
            if provider:
                # Return models for specific provider
                provider_models = models_by_provider.get(provider, [])
                return {
                    "provider": provider,
                    "models": provider_models,
                    "model_pairs": [f"{provider}/{model}" for model in provider_models],
                    "count": len(provider_models),
                    "available": len(provider_models) > 0
                }
            else:
                # Return all models data
                return {
                    "providers": list(models_by_provider.keys()),
                    "models_by_provider": models_by_provider,
                    "model_pairs": model_pairs,
                    "recommendations": recommendations,
                    "static_recommendations": MODEL_RECOMMENDATIONS,
                    "total_providers": len(models_by_provider),
                    "total_models": len(model_pairs)
                }
        except Exception as e:
            logger.error(f"Error fetching models data: {e}")
            raise RuntimeError(format_error_message(e, "Failed to fetch models"))

# Resource instances
slim_registry = SlimRegistryResource()
slim_best_practices = SlimBestPracticesResource()
slim_prompts = SlimPromptsResource()
slim_models = SlimModelsResource()

# Resource registry for MCP server
RESOURCES = {
    "slim_registry": slim_registry,
    "slim_best_practices": slim_best_practices,
    "slim_prompts": slim_prompts,
    "slim_models": slim_models
}

def get_resource(resource_name: str) -> Optional[object]:
    """Get a resource by name."""
    return RESOURCES.get(resource_name)

def list_resources() -> List[Dict[str, str]]:
    """List all available resources."""
    return [
        {
            "name": name,
            "uri": resource.uri,
            "description": resource.description
        }
        for name, resource in RESOURCES.items()
    ]