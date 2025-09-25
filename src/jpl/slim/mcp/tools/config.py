"""
Configuration and constants for the SLIM-CLI MCP server.
"""

import os
from pathlib import Path
from typing import Dict, List, Any

# MCP Server Configuration
MCP_SERVER_NAME = "SLIM-CLI MCP Server"
MCP_SERVER_VERSION = "1.0.0"
MCP_SERVER_DESCRIPTION = "Model Context Protocol server for SLIM-CLI best practices"

# SLIM-CLI Configuration
SLIM_REGISTRY_URI = "https://raw.githubusercontent.com/NASA-AMMOS/slim/main/static/data/slim-registry.json"

# Common best practice categories
BEST_PRACTICE_CATEGORIES = {
    "documentation": [
        "readme",
        "changelog", 
        "contributing",
        "docs-website"
    ],
    "governance": [
        "governance-small",
        "governance-medium", 
        "governance-large",
        "code-of-conduct"
    ],
    "security": [
        "secrets-github",
        "secrets-precommit"
    ],
    "licensing": [
        "license-apache",
        "license-mit",
        "license-gpl"
    ]
}

# AI Model Tiers
AI_MODEL_TIERS = {
    "premium": "High-quality, most capable models",
    "balanced": "Good balance of quality and cost",
    "fast": "Fast, cost-effective models",
    "local": "Local/offline models"
}

# Common AI Tasks
AI_TASKS = {
    "documentation": "Documentation generation and improvement",
    "code_generation": "Code generation and enhancement"
}

# Resource URIs
RESOURCE_URIS = {
    "registry": "slim://registry",
    "best_practices": "slim://best_practices",
    "prompts": "slim://prompts", 
    "models": "slim://models"
}

# Tool Names
TOOL_NAMES = {
    "apply": "slim_apply",
    "deploy": "slim_deploy",
    "apply_deploy": "slim_apply_deploy",
    "list": "slim_list",
    "models_list": "slim_models_list",
    "models_recommend": "slim_models_recommend",
    "models_validate": "slim_models_validate"
}

# Prompt Templates
PROMPT_TEMPLATES = {
    "apply_best_practice": {
        "name": "apply_best_practice",
        "description": "Template for applying SLIM best practices to repositories",
        "arguments": [
            {"name": "best_practice_ids", "description": "List of best practice IDs to apply"},
            {"name": "repo_url", "description": "Repository URL to apply practices to"},
            {"name": "use_ai", "description": "Whether to use AI for customization"},
            {"name": "model", "description": "AI model to use for customization"}
        ]
    },
    "customize_with_ai": {
        "name": "customize_with_ai", 
        "description": "Template for AI-powered customization of best practices",
        "arguments": [
            {"name": "practice_type", "description": "Type of best practice being customized"},
            {"name": "repository_context", "description": "Context about the target repository"},
            {"name": "customization_goals", "description": "Goals for customization"}
        ]
    },
    "review_changes": {
        "name": "review_changes",
        "description": "Template for reviewing SLIM best practice changes",
        "arguments": [
            {"name": "changes_summary", "description": "Summary of changes made"},
            {"name": "files_modified", "description": "List of files that were modified"},
            {"name": "next_steps", "description": "Recommended next steps"}
        ]
    }
}

def get_working_directory() -> Path:
    """Get the current working directory."""
    return Path.cwd()

def get_slim_cli_path() -> Path:
    """Get the path to the SLIM-CLI source directory."""
    return Path(__file__).parent.parent

def validate_best_practice_id(practice_id: str) -> bool:
    """Validate a best practice ID."""
    all_practices = []
    for category_practices in BEST_PRACTICE_CATEGORIES.values():
        all_practices.extend(category_practices)
    return practice_id in all_practices or practice_id.startswith("license-")

def get_best_practice_category(practice_id: str) -> str:
    """Get the category for a best practice ID."""
    for category, practices in BEST_PRACTICE_CATEGORIES.items():
        if practice_id in practices:
            return category
    if practice_id.startswith("license-"):
        return "licensing"
    return "unknown"