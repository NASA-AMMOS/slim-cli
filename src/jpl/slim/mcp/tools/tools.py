"""
MCP Tools for SLIM-CLI.

This module provides MCP tools that wrap SLIM-CLI functionality.
"""

import logging
import tempfile
import time
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

# Import SLIM-CLI modules
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.jpl.slim.commands.apply_command import apply_best_practices
from src.jpl.slim.commands.deploy_command import deploy_best_practices
from src.jpl.slim.commands.common import (
    get_dynamic_ai_model_pairs,
    get_dynamic_recommended_models,
    check_model_availability,
    get_provider_setup_instructions,
    validate_model_format
)
from src.jpl.slim.utils.io_utils import fetch_best_practices, repo_file_to_list
from src.jpl.slim.commands.common import SLIM_REGISTRY_URI

from .config import TOOL_NAMES, AI_MODEL_TIERS, AI_TASKS
from .utils import (
    log_mcp_operation,
    format_error_message,
    parse_best_practice_ids,
    validate_repo_url,
    validate_repo_path,
    validate_file_path,
    validate_ai_model,
    validate_mcp_tool_params,
    normalize_repo_url,
    create_temp_directory,
    format_duration
)

logger = logging.getLogger(__name__)

class SlimApplyTool:
    """MCP tool for applying SLIM best practices."""
    
    def __init__(self):
        self.name = TOOL_NAMES["apply"]
        self.description = "Apply SLIM best practices to repositories"
        self.parameters = {
            "type": "object",
            "properties": {
                "best_practice_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of best practice IDs to apply"
                },
                "repo_urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Repository URLs to apply practices to"
                },
                "repo_dir": {
                    "type": "string",
                    "description": "Local repository directory path"
                },
                "repo_urls_file": {
                    "type": "string",
                    "description": "Path to file containing repository URLs"
                },
                "clone_to_dir": {
                    "type": "string",
                    "description": "Directory to clone repositories to"
                },
                "use_ai": {
                    "type": "string",
                    "description": "AI model to use for customization (format: provider/model)"
                },
                "no_prompt": {
                    "type": "boolean",
                    "description": "Skip user confirmation prompts",
                    "default": False
                },
                "output_dir": {
                    "type": "string",
                    "description": "Output directory for generated files"
                },
                "template_only": {
                    "type": "boolean",
                    "description": "Generate template only without repository analysis",
                    "default": False
                },
                "revise_site": {
                    "type": "boolean",
                    "description": "Revise existing documentation site",
                    "default": False
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Show what would be done without making changes",
                    "default": False
                }
            },
            "required": ["best_practice_ids"]
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the apply tool."""
        try:
            start_time = time.time()
            
            # Validate parameters
            is_valid, error_msg = validate_mcp_tool_params(
                kwargs, 
                required_keys=["best_practice_ids"],
                optional_keys=["repo_urls", "repo_dir", "repo_urls_file", "clone_to_dir", 
                             "use_ai", "no_prompt", "output_dir", "template_only", 
                             "revise_site", "dry_run"]
            )
            if not is_valid:
                raise ValueError(error_msg)
            
            # Parse and validate parameters
            best_practice_ids = parse_best_practice_ids(kwargs["best_practice_ids"])
            repo_urls = kwargs.get("repo_urls", [])
            repo_dir = kwargs.get("repo_dir")
            repo_urls_file = kwargs.get("repo_urls_file")
            clone_to_dir = kwargs.get("clone_to_dir")
            use_ai = kwargs.get("use_ai")
            no_prompt = kwargs.get("no_prompt", False)
            output_dir = kwargs.get("output_dir")
            template_only = kwargs.get("template_only", False)
            revise_site = kwargs.get("revise_site", False)
            dry_run = kwargs.get("dry_run", False)
            
            # Validate inputs
            if repo_dir and not validate_repo_path(repo_dir):
                raise ValueError(f"Invalid repository directory: {repo_dir}")
            
            if repo_urls_file and not validate_file_path(repo_urls_file):
                raise ValueError(f"Invalid repository URLs file: {repo_urls_file}")
            
            if use_ai:
                is_valid, error_msg = validate_ai_model(use_ai)
                if not is_valid:
                    raise ValueError(f"Invalid AI model: {error_msg}")
            
            # Normalize repo URLs
            if repo_urls:
                repo_urls = [normalize_repo_url(url) for url in repo_urls]
                invalid_urls = [url for url in repo_urls if not validate_repo_url(url)]
                if invalid_urls:
                    raise ValueError(f"Invalid repository URLs: {invalid_urls}")
            
            # Read URLs from file if provided
            if repo_urls_file:
                file_urls = repo_file_to_list(repo_urls_file)
                repo_urls = file_urls if file_urls else repo_urls
            
            # Log operation
            log_mcp_operation("slim_apply", {
                "best_practice_ids": best_practice_ids,
                "repo_urls": repo_urls,
                "repo_dir": repo_dir,
                "use_ai": bool(use_ai),
                "model": use_ai,
                "dry_run": dry_run
            })
            
            # Handle dry run
            if dry_run:
                return {
                    "success": True,
                    "message": "Dry run completed - no changes made",
                    "would_apply": best_practice_ids,
                    "target_repos": repo_urls or ([repo_dir] if repo_dir else []),
                    "ai_model": use_ai,
                    "dry_run": True
                }
            
            # Execute apply
            success = apply_best_practices(
                best_practice_ids=best_practice_ids,
                use_ai_flag=bool(use_ai),
                model=use_ai,
                repo_urls=repo_urls,
                existing_repo_dir=repo_dir,
                target_dir_to_clone_to=clone_to_dir,
                no_prompt=no_prompt,
                output_dir=output_dir,
                template_only=template_only,
                revise_site=revise_site
            )
            
            duration = time.time() - start_time
            
            if success:
                return {
                    "success": True,
                    "message": f"Successfully applied {len(best_practice_ids)} best practices",
                    "applied_practices": best_practice_ids,
                    "duration": format_duration(duration),
                    "ai_model": use_ai,
                    "targets": repo_urls or ([repo_dir] if repo_dir else [])
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to apply best practices",
                    "error": "Apply operation returned false",
                    "duration": format_duration(duration)
                }
        
        except Exception as e:
            logger.error(f"Error in slim_apply: {e}")
            return {
                "success": False,
                "message": "Error applying best practices",
                "error": format_error_message(e)
            }

class SlimDeployTool:
    """MCP tool for deploying SLIM best practices."""
    
    def __init__(self):
        self.name = TOOL_NAMES["deploy"]
        self.description = "Deploy SLIM best practices to git repositories"
        self.parameters = {
            "type": "object",
            "properties": {
                "best_practice_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of best practice IDs to deploy"
                },
                "repo_dir": {
                    "type": "string",
                    "description": "Local repository directory path"
                },
                "remote": {
                    "type": "string",
                    "description": "Git remote name or URL"
                },
                "commit_message": {
                    "type": "string",
                    "description": "Commit message for the deployment"
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Show what would be done without making changes",
                    "default": False
                }
            },
            "required": ["best_practice_ids", "repo_dir"]
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the deploy tool."""
        try:
            start_time = time.time()
            
            # Validate parameters
            is_valid, error_msg = validate_mcp_tool_params(
                kwargs,
                required_keys=["best_practice_ids", "repo_dir"],
                optional_keys=["remote", "commit_message", "dry_run"]
            )
            if not is_valid:
                raise ValueError(error_msg)
            
            # Parse parameters
            best_practice_ids = parse_best_practice_ids(kwargs["best_practice_ids"])
            repo_dir = kwargs["repo_dir"]
            remote = kwargs.get("remote")
            commit_message = kwargs.get("commit_message", "SLIM-CLI Best Practices Bot Commit")
            dry_run = kwargs.get("dry_run", False)
            
            # Validate repository directory
            if not validate_repo_path(repo_dir):
                raise ValueError(f"Invalid repository directory: {repo_dir}")
            
            # Log operation
            log_mcp_operation("slim_deploy", {
                "best_practice_ids": best_practice_ids,
                "repo_dir": repo_dir,
                "remote": remote,
                "dry_run": dry_run
            })
            
            # Handle dry run
            if dry_run:
                return {
                    "success": True,
                    "message": "Dry run completed - no changes made",
                    "would_deploy": best_practice_ids,
                    "target_repo": repo_dir,
                    "remote": remote,
                    "commit_message": commit_message,
                    "dry_run": True
                }
            
            # Execute deploy
            success = deploy_best_practices(
                best_practice_ids=best_practice_ids,
                repo_dir=repo_dir,
                remote=remote,
                commit_message=commit_message
            )
            
            duration = time.time() - start_time
            
            if success:
                return {
                    "success": True,
                    "message": f"Successfully deployed {len(best_practice_ids)} best practices",
                    "deployed_practices": best_practice_ids,
                    "duration": format_duration(duration),
                    "repo_dir": repo_dir,
                    "remote": remote,
                    "commit_message": commit_message
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to deploy best practices",
                    "error": "Deploy operation returned false",
                    "duration": format_duration(duration)
                }
        
        except Exception as e:
            logger.error(f"Error in slim_deploy: {e}")
            return {
                "success": False,
                "message": "Error deploying best practices",
                "error": format_error_message(e)
            }

class SlimListTool:
    """MCP tool for listing SLIM best practices."""
    
    def __init__(self):
        self.name = TOOL_NAMES["list"]
        self.description = "List available SLIM best practices"
        self.parameters = {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Filter by category (documentation, governance, security, licensing)"
                },
                "detailed": {
                    "type": "boolean",
                    "description": "Include detailed information about each practice",
                    "default": False
                }
            },
            "required": []
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the list tool."""
        try:
            # Parse parameters
            category = kwargs.get("category")
            detailed = kwargs.get("detailed", False)
            
            # Log operation
            log_mcp_operation("slim_list", {
                "category": category,
                "detailed": detailed
            })
            
            # Fetch practices
            practices = fetch_best_practices(SLIM_REGISTRY_URI)
            if not practices:
                return {
                    "success": False,
                    "message": "Failed to fetch practices from registry",
                    "error": "No practices found"
                }
            
            # Filter by category if specified
            if category:
                category_lower = category.lower()
                practices = [
                    p for p in practices
                    if category_lower in (p.get("title", "").lower() + " " + p.get("description", "").lower())
                ]
            
            # Format response
            if detailed:
                practice_list = []
                for practice in practices:
                    practice_info = {
                        "id": practice.get("alias", ""),
                        "title": practice.get("title", ""),
                        "description": practice.get("description", ""),
                        "uri": practice.get("uri", ""),
                        "assets": practice.get("assets", [])
                    }
                    if practice.get("uri"):
                        practice_info["guide_url"] = f"https://nasa-ammos.github.io{practice.get('uri')}"
                    practice_list.append(practice_info)
            else:
                practice_list = [
                    {
                        "id": practice.get("alias", ""),
                        "title": practice.get("title", ""),
                        "description": practice.get("description", "")[:100] + "..." if len(practice.get("description", "")) > 100 else practice.get("description", "")
                    }
                    for practice in practices
                ]
            
            return {
                "success": True,
                "message": f"Found {len(practices)} best practices",
                "practices": practice_list,
                "total_count": len(practices),
                "category_filter": category,
                "detailed": detailed
            }
        
        except Exception as e:
            logger.error(f"Error in slim_list: {e}")
            return {
                "success": False,
                "message": "Error listing best practices",
                "error": format_error_message(e)
            }

class SlimModelsListTool:
    """MCP tool for listing AI models."""
    
    def __init__(self):
        self.name = TOOL_NAMES["models_list"]
        self.description = "List available AI models"
        self.parameters = {
            "type": "object",
            "properties": {
                "provider": {
                    "type": "string",
                    "description": "Filter by provider (e.g., openai, anthropic, google)"
                },
                "tier": {
                    "type": "string",
                    "description": "Filter by tier (premium, balanced, fast, local)"
                }
            },
            "required": []
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the models list tool."""
        try:
            # Parse parameters
            provider = kwargs.get("provider")
            tier = kwargs.get("tier")
            
            # Log operation
            log_mcp_operation("slim_models_list", {
                "provider": provider,
                "tier": tier
            })
            
            # Get models
            model_pairs = get_dynamic_ai_model_pairs()
            
            if not model_pairs:
                return {
                    "success": False,
                    "message": "No models found - LiteLLM may not be available",
                    "error": "Model discovery failed"
                }
            
            # Filter by provider if specified
            if provider:
                model_pairs = [m for m in model_pairs if m.startswith(f"{provider}/")]
            
            # Note: Tier filtering would require additional model metadata
            # For now, we'll just return all models with tier information
            
            return {
                "success": True,
                "message": f"Found {len(model_pairs)} models",
                "models": sorted(model_pairs),
                "total_count": len(model_pairs),
                "provider_filter": provider,
                "tier_filter": tier,
                "tiers": AI_MODEL_TIERS
            }
        
        except Exception as e:
            logger.error(f"Error in slim_models_list: {e}")
            return {
                "success": False,
                "message": "Error listing AI models",
                "error": format_error_message(e)
            }

class SlimModelsRecommendTool:
    """MCP tool for AI model recommendations."""
    
    def __init__(self):
        self.name = TOOL_NAMES["models_recommend"]
        self.description = "Get AI model recommendations"
        self.parameters = {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Task type (documentation, code_generation)",
                    "default": "documentation"
                },
                "tier": {
                    "type": "string",
                    "description": "Quality tier (premium, balanced, fast, local)",
                    "default": "balanced"
                }
            },
            "required": []
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the models recommend tool."""
        try:
            # Parse parameters
            task = kwargs.get("task", "documentation")
            tier = kwargs.get("tier", "balanced")
            
            # Log operation
            log_mcp_operation("slim_models_recommend", {
                "task": task,
                "tier": tier
            })
            
            # Get recommendations
            recommendations = get_dynamic_recommended_models()
            
            if not recommendations:
                return {
                    "success": False,
                    "message": "Failed to get model recommendations",
                    "error": "Recommendation service unavailable"
                }
            
            # Format response based on tier
            if tier == "premium":
                models = recommendations.get("premium", [])
            elif tier == "local":
                models = recommendations.get("local", [])
            else:
                # For balanced/fast, return a mix
                models = recommendations.get("premium", [])[:3] + recommendations.get("local", [])[:2]
            
            return {
                "success": True,
                "message": f"Found {len(models)} recommended models for {task} ({tier} tier)",
                "recommended_models": models,
                "task": task,
                "tier": tier,
                "all_recommendations": recommendations,
                "tasks": AI_TASKS,
                "tiers": AI_MODEL_TIERS
            }
        
        except Exception as e:
            logger.error(f"Error in slim_models_recommend: {e}")
            return {
                "success": False,
                "message": "Error getting model recommendations",
                "error": format_error_message(e)
            }

class SlimModelsValidateTool:
    """MCP tool for validating AI models."""
    
    def __init__(self):
        self.name = TOOL_NAMES["models_validate"]
        self.description = "Validate AI model configuration"
        self.parameters = {
            "type": "object",
            "properties": {
                "model": {
                    "type": "string",
                    "description": "Model in provider/model format"
                }
            },
            "required": ["model"]
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the models validate tool."""
        try:
            # Parse parameters
            model = kwargs["model"]
            
            # Log operation
            log_mcp_operation("slim_models_validate", {
                "model": model
            })
            
            # Validate model format
            is_valid, error_msg = validate_ai_model(model)
            if not is_valid:
                return {
                    "success": False,
                    "message": f"Invalid model format: {model}",
                    "error": error_msg,
                    "model": model,
                    "valid": False
                }
            
            # Check model availability
            is_available, error_msg = check_model_availability(model)
            
            if is_available:
                return {
                    "success": True,
                    "message": f"Model {model} is properly configured",
                    "model": model,
                    "valid": True,
                    "available": True
                }
            else:
                provider = model.split("/")[0]
                setup_instructions = get_provider_setup_instructions(provider)
                
                return {
                    "success": False,
                    "message": f"Model {model} configuration error",
                    "error": error_msg,
                    "model": model,
                    "valid": True,
                    "available": False,
                    "provider": provider,
                    "setup_instructions": setup_instructions
                }
        
        except Exception as e:
            logger.error(f"Error in slim_models_validate: {e}")
            return {
                "success": False,
                "message": "Error validating model",
                "error": format_error_message(e)
            }

# Tool instances
slim_apply = SlimApplyTool()
slim_deploy = SlimDeployTool()
slim_list = SlimListTool()
slim_models_list = SlimModelsListTool()
slim_models_recommend = SlimModelsRecommendTool()
slim_models_validate = SlimModelsValidateTool()

# Tool registry
TOOLS = {
    "slim_apply": slim_apply,
    "slim_deploy": slim_deploy,
    "slim_list": slim_list,
    "slim_models_list": slim_models_list,
    "slim_models_recommend": slim_models_recommend,
    "slim_models_validate": slim_models_validate
}

def get_tool(tool_name: str) -> Optional[object]:
    """Get a tool by name."""
    return TOOLS.get(tool_name)

def list_tools() -> List[Dict[str, Any]]:
    """List all available tools."""
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters
        }
        for tool in TOOLS.values()
    ]