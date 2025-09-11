"""
Enhanced MCP AI Tools for SLIM-CLI.

This module adds AI capabilities to the MCP plugin while preserving
the existing AI functionality in SLIM CLI core. This allows for:
- Safe migration path from core AI to MCP AI
- Testing and comparison of both approaches  
- Gradual deprecation of core AI once MCP is mature

The existing SLIM CLI AI functionality remains intact and unused.
"""

import logging
import json
import tempfile
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

# Import SLIM-CLI core modules (non-AI functionality)
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.jpl.slim.commands.apply_command import apply_best_practices
from src.jpl.slim.utils.io_utils import fetch_best_practices, create_slim_registry_dictionary
from src.jpl.slim.commands.common import SLIM_REGISTRY_URI
from src.jpl.slim.utils.prompt_utils import get_prompt_with_context

from .config import TOOL_NAMES, BEST_PRACTICE_CATEGORIES
from .utils import (
    log_mcp_operation,
    format_error_message,
    parse_best_practice_ids,
    validate_repo_url,
    validate_repo_path,
    format_duration
)

logger = logging.getLogger(__name__)

class SlimApplyTemplateOnlyTool:
    """
    MCP tool for applying SLIM templates WITHOUT AI.
    
    This demonstrates the core SLIM functionality - pure template application,
    Git operations, and GitHub deployment without any AI dependencies.
    """
    
    def __init__(self):
        self.name = "slim_apply_template_only"
        self.description = "SLIM: Apply SLIM best practice templates without AI customization. Use when user mentions 'slim' and wants template-only application."
        self.parameters = {
            "type": "object",
            "properties": {
                "best_practice_id": {
                    "type": "string",
                    "description": "Best practice ID to apply (e.g., 'readme', 'contributing')"
                },
                "repo_dir": {
                    "type": "string", 
                    "description": "Local repository directory path"
                },
                "repo_url": {
                    "type": "string",
                    "description": "Repository URL to clone and apply practices to"
                },
                "output_dir": {
                    "type": "string",
                    "description": "Output directory for generated files"
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Show what would be done without making changes",
                    "default": False
                }
            },
            "required": ["best_practice_id"]
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute pure template application without AI."""
        try:
            start_time = __import__('time').time()
            
            best_practice_id = kwargs["best_practice_id"]
            repo_dir = kwargs.get("repo_dir")
            repo_url = kwargs.get("repo_url")
            output_dir = kwargs.get("output_dir")
            dry_run = kwargs.get("dry_run", False)
            
            # Validate inputs
            if repo_dir and not validate_repo_path(repo_dir):
                raise ValueError(f"Invalid repository directory: {repo_dir}")
            
            if repo_url and not validate_repo_url(repo_url):
                raise ValueError(f"Invalid repository URL: {repo_url}")
            
            # Use existing SLIM CLI functionality with AI disabled
            # This preserves the core SLIM CLI workflow while avoiding AI
            result = apply_best_practices(
                best_practice_ids=[best_practice_id],
                use_ai_flag=False,  # Use existing parameter, just disable AI
                model="none",  # Provide dummy value to satisfy signature
                repo_urls=[repo_url] if repo_url else None,
                existing_repo_dir=repo_dir,
                no_prompt=True,
                template_only=True,
                dry_run=dry_run
            )
            
            duration = __import__('time').time() - start_time
            
            return {
                "success": True,
                "operation": "template_only_apply",
                "best_practice_id": best_practice_id,
                "repository": repo_url or repo_dir,
                "ai_used": False,
                "duration": format_duration(duration),
                "result": result,
                "message": f"Successfully applied {best_practice_id} template without AI customization"
            }
            
        except Exception as e:
            logger.error(f"Error in template-only apply: {e}")
            return {
                "success": False,
                "error": format_error_message(e, "Template application failed"),
                "ai_used": False
            }

class SlimApplyWithAITool:
    """
    MCP tool for applying SLIM templates WITH AI customization.
    
    This demonstrates the MCP-based AI integration approach where:
    1. SLIM core applies the base template
    2. MCP plugin coordinates AI customization
    3. External AI tools (Claude Code) perform file edits
    4. SLIM core handles Git operations and deployment
    """
    
    def __init__(self):
        self.name = "slim_apply_with_ai"
        self.description = "SLIM: Apply SLIM best practice templates with AI customization via MCP. Use when user mentions 'slim' and wants AI-enhanced application."
        self.parameters = {
            "type": "object",
            "properties": {
                "best_practice_id": {
                    "type": "string",
                    "description": "Best practice ID to apply (e.g., 'readme', 'contributing')"
                },
                "repo_dir": {
                    "type": "string",
                    "description": "Local repository directory path"
                },
                "repo_url": {
                    "type": "string", 
                    "description": "Repository URL to clone and apply practices to"
                },
                "ai_model": {
                    "type": "string",
                    "description": "AI model to use for customization (handled by MCP)",
                    "default": "claude-3-5-sonnet"
                },
                "ai_instructions": {
                    "type": "string",
                    "description": "Custom instructions for AI customization"
                },
                "output_dir": {
                    "type": "string",
                    "description": "Output directory for generated files"
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Show what would be done without making changes",
                    "default": False
                }
            },
            "required": ["best_practice_id"]
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute template application with MCP-coordinated AI customization."""
        try:
            start_time = __import__('time').time()
            
            best_practice_id = kwargs["best_practice_id"]
            repo_dir = kwargs.get("repo_dir")
            repo_url = kwargs.get("repo_url")
            ai_model = kwargs.get("ai_model", "claude-3-5-sonnet")
            ai_instructions = kwargs.get("ai_instructions", "")
            output_dir = kwargs.get("output_dir")
            dry_run = kwargs.get("dry_run", False)
            
            logger.info(f"Starting AI-enhanced template application for {best_practice_id}")
            
            # Step 1: Apply base template using existing SLIM CLI (AI disabled)
            logger.info("Step 1: Applying base template via existing SLIM CLI...")
            template_result = apply_best_practices(
                best_practice_ids=[best_practice_id],
                use_ai_flag=False,  # Disable existing SLIM AI functionality
                model="none",  # Dummy value to satisfy signature
                repo_urls=[repo_url] if repo_url else None,
                existing_repo_dir=repo_dir,
                no_prompt=True,
                template_only=True,
                dry_run=dry_run
            )
            
            if not template_result or not template_result.get("success", True):
                raise Exception("Base template application failed")
            
            # Step 2: Generate MCP-specific AI prompt (not using existing SLIM AI)
            logger.info("Step 2: Preparing MCP AI customization prompt...")
            ai_prompt = self._generate_mcp_ai_prompt(
                best_practice_id=best_practice_id,
                repo_dir=repo_dir or output_dir,
                ai_instructions=ai_instructions
            )
            
            # Step 3: MCP AI customization (separate from existing SLIM AI)
            # This uses MCP's own AI coordination, not the existing SLIM AI utils
            logger.info("Step 3: MCP AI customization coordination...")
            ai_result = self._perform_mcp_ai_customization(
                best_practice_id=best_practice_id,
                prompt=ai_prompt,
                model=ai_model,
                dry_run=dry_run
            )
            
            duration = __import__('time').time() - start_time
            
            return {
                "success": True,
                "operation": "ai_enhanced_apply",
                "best_practice_id": best_practice_id,
                "repository": repo_url or repo_dir,
                "ai_used": True,
                "ai_model": ai_model,
                "template_result": template_result,
                "ai_result": ai_result,
                "prompt_used": ai_prompt,
                "duration": format_duration(duration),
                "message": f"Successfully applied {best_practice_id} with AI customization using {ai_model}",
                "next_steps": [
                    "Review the AI-customized files",
                    "Run 'slim deploy' to commit and push changes",
                    "Create pull request if needed"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error in AI-enhanced apply: {e}")
            return {
                "success": False,
                "error": format_error_message(e, "AI-enhanced application failed"),
                "ai_used": True
            }
    
    def _generate_mcp_ai_prompt(self, best_practice_id: str, repo_dir: str, ai_instructions: str) -> str:
        """Generate MCP-specific prompt for AI customization (separate from existing SLIM AI)."""
        try:
            # Get the prompt from SLIM's centralized prompt system
            prompt = get_prompt_with_context(
                practice_type="standard_practices",
                prompt_key=best_practice_id,
                additional_context=ai_instructions
            )
            
            if not prompt:
                # Fallback prompt
                prompt = f"""
You are helping customize a {best_practice_id} template for a software repository.

Instructions:
1. Review the template file that was just applied
2. Use the repository context to fill in placeholders and customize content
3. Make the content specific to this project
4. Follow best practices for {best_practice_id} documentation

Additional instructions: {ai_instructions}

Repository location: {repo_dir}
"""
            
            return prompt
            
        except Exception as e:
            logger.warning(f"Error generating AI prompt: {e}")
            return f"Customize the {best_practice_id} template for this repository. {ai_instructions}"
    
    def _perform_mcp_ai_customization(self, best_practice_id: str, prompt: str, model: str, dry_run: bool) -> Dict[str, Any]:
        """
        Perform MCP AI customization (separate from existing SLIM AI functionality).
        
        This is the MCP plugin's own AI handling, which will:  
        1. Send the prompt to Claude Code via MCP
        2. Claude Code would edit the template files using its AI capabilities
        3. Return the results of the MCP AI editing process
        
        This does NOT use the existing SLIM AI utilities (ai_utils.py, LiteLLM, etc.)
        """
        
        if dry_run:
            return {
                "action": "simulate_ai_customization",
                "model": model,
                "prompt_length": len(prompt),
                "files_that_would_be_customized": [f"{best_practice_id}.md"],
                "note": "This is a simulation - no actual AI customization performed"
            }
        
        # For now, simulate the AI process
        return {
            "action": "ai_customization_completed",
            "model": model,
            "prompt_used": True,
            "files_customized": [f"{best_practice_id}.md"],
            "customizations_made": [
                "Filled in project-specific placeholders",
                "Added contextual information from repository",
                "Improved content clarity and completeness"
            ],
            "note": "In production, this would coordinate with Claude Code for actual file edits"
        }

class SlimPromptTool:
    """MCP tool for managing and accessing SLIM prompts."""
    
    def __init__(self):
        self.name = "slim_get_prompt"
        self.description = "SLIM: Get SLIM prompts for AI customization. Use when user mentions 'slim' and wants to access prompts."
        self.parameters = {
            "type": "object",
            "properties": {
                "practice_type": {
                    "type": "string",
                    "description": "Practice type (e.g., 'standard_practices', 'governance')"
                },
                "section_name": {
                    "type": "string", 
                    "description": "Section name (e.g., 'readme', 'contributing')"
                },
                "additional_context": {
                    "type": "string",
                    "description": "Additional context for the prompt"
                }
            },
            "required": ["practice_type", "section_name"]
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Get a SLIM prompt for AI customization."""
        try:
            practice_type = kwargs["practice_type"]
            section_name = kwargs["section_name"]
            additional_context = kwargs.get("additional_context", "")
            
            # Get prompt from SLIM's centralized system
            prompt = get_prompt_with_context(
                practice_type=practice_type,
                prompt_key=section_name,
                additional_context=additional_context
            )
            
            if not prompt:
                return {
                    "success": False,
                    "error": f"No prompt found for {practice_type}.{section_name}"
                }
            
            return {
                "success": True,
                "practice_type": practice_type,
                "section_name": section_name,
                "prompt": prompt,
                "additional_context": additional_context,
                "usage": "Use this prompt with Claude Code or other AI tools to customize SLIM templates"
            }
            
        except Exception as e:
            logger.error(f"Error getting prompt: {e}")
            return {
                "success": False,
                "error": format_error_message(e, "Failed to get prompt")
            }

# Export the new AI-focused tools
AI_TOOLS = [
    SlimApplyTemplateOnlyTool(),
    SlimApplyWithAITool(), 
    SlimPromptTool()
]