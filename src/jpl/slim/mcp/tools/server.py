"""
SLIM-CLI MCP Server

Model Context Protocol server for SLIM-CLI best practices.
Provides tools, resources, and prompts for LLM interaction with SLIM functionality.
"""

import logging
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent directory to path for SLIM-CLI imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from fastmcp import FastMCP
    from mcp.server.fastmcp import Context
except ImportError:
    print("Error: FastMCP not available. Install with: pip install 'mcp[cli]'")
    sys.exit(1)

from .config import (
    MCP_SERVER_NAME,
    MCP_SERVER_VERSION,
    MCP_SERVER_DESCRIPTION,
    RESOURCE_URIS
)
from .tools import (
    slim_apply,
    slim_deploy,
    slim_list,
    slim_models_list,
    slim_models_recommend,
    slim_models_validate,
    TOOLS
)
from .ai_tools import AI_TOOLS
from .comprehensive_ai_tools import COMPREHENSIVE_AI_TOOLS
from .enhanced_tools import ENHANCED_TOOLS
from .resources import (
    slim_registry,
    slim_best_practices,
    slim_prompts,
    slim_models,
    RESOURCES
)
from .prompts import (
    apply_best_practice_prompt,
    customize_with_ai_prompt,
    review_changes_prompt,
    generate_prompt,
    PROMPTS
)
from .utils import (
    log_mcp_operation,
    format_error_message,
    check_slim_cli_dependencies,
    get_slim_cli_version
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    name=MCP_SERVER_NAME,
    version=MCP_SERVER_VERSION,
    description=MCP_SERVER_DESCRIPTION
)

# Tool implementations
@mcp.tool()
def slim_apply_tool(
    best_practice_ids: List[str],
    repo_urls: Optional[List[str]] = None,
    repo_dir: Optional[str] = None,
    repo_urls_file: Optional[str] = None,
    clone_to_dir: Optional[str] = None,
    use_ai: Optional[str] = None,
    no_prompt: bool = False,
    output_dir: Optional[str] = None,
    template_only: bool = False,
    revise_site: bool = False,
    dry_run: bool = False,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    SLIM: Apply SLIM best practices to repositories via existing SLIM CLI.
    Use when user mentions 'slim' and wants to apply best practices using the original SLIM CLI approach.
    
    Args:
        best_practice_ids: List of best practice IDs to apply
        repo_urls: Repository URLs to apply practices to
        repo_dir: Local repository directory path
        repo_urls_file: Path to file containing repository URLs
        clone_to_dir: Directory to clone repositories to
        use_ai: AI model to use for customization (format: provider/model)
        no_prompt: Skip user confirmation prompts
        output_dir: Output directory for generated files
        template_only: Generate template only without repository analysis
        revise_site: Revise existing documentation site
        dry_run: Show what would be done without making changes
    
    Returns:
        Dictionary with operation results
    """
    try:
        if ctx:
            ctx.info(f"Applying best practices: {', '.join(best_practice_ids)}")
        
        return slim_apply.execute(
            best_practice_ids=best_practice_ids,
            repo_urls=repo_urls,
            repo_dir=repo_dir,
            repo_urls_file=repo_urls_file,
            clone_to_dir=clone_to_dir,
            use_ai=use_ai,
            no_prompt=no_prompt,
            output_dir=output_dir,
            template_only=template_only,
            revise_site=revise_site,
            dry_run=dry_run
        )
    except Exception as e:
        logger.error(f"Error in slim_apply_tool: {e}")
        return {
            "success": False,
            "error": format_error_message(e, "SLIM apply operation failed")
        }

@mcp.tool()
def slim_deploy_tool(
    best_practice_ids: List[str],
    repo_dir: str,
    remote: Optional[str] = None,
    commit_message: Optional[str] = None,
    dry_run: bool = False,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Deploy SLIM best practices to git repositories.
    
    Args:
        best_practice_ids: List of best practice IDs to deploy
        repo_dir: Local repository directory path
        remote: Git remote name or URL
        commit_message: Commit message for the deployment
        dry_run: Show what would be done without making changes
    
    Returns:
        Dictionary with operation results
    """
    try:
        if ctx:
            ctx.info(f"Deploying best practices: {', '.join(best_practice_ids)}")
        
        return slim_deploy.execute(
            best_practice_ids=best_practice_ids,
            repo_dir=repo_dir,
            remote=remote,
            commit_message=commit_message,
            dry_run=dry_run
        )
    except Exception as e:
        logger.error(f"Error in slim_deploy_tool: {e}")
        return {
            "success": False,
            "error": format_error_message(e, "SLIM deploy operation failed")
        }

@mcp.tool()
def slim_list_tool(
    category: Optional[str] = None,
    detailed: bool = False
) -> Dict[str, Any]:
    """
    SLIM: List all available SLIM best practices.
    Use when user mentions 'slim' and wants to see available best practices like 'list slim practices', 'what slim templates are available', etc.
    
    Args:
        category: Filter by category (documentation, governance, security, licensing)
        detailed: Include detailed information about each practice
    
    Returns:
        Dictionary with list of best practices
    """
    try:
        return slim_list.execute(
            category=category,
            detailed=detailed
        )
    except Exception as e:
        logger.error(f"Error in slim_list_tool: {e}")
        return {
            "success": False,
            "error": format_error_message(e, "SLIM list operation failed")
        }

@mcp.tool()
def slim_models_list_tool(
    provider: Optional[str] = None,
    tier: Optional[str] = None
) -> Dict[str, Any]:
    """
    List available AI models.
    
    Args:
        provider: Filter by provider (e.g., openai, anthropic, google)
        tier: Filter by tier (premium, balanced, fast, local)
    
    Returns:
        Dictionary with list of AI models
    """
    try:
        return slim_models_list.execute(
            provider=provider,
            tier=tier
        )
    except Exception as e:
        logger.error(f"Error in slim_models_list_tool: {e}")
        return {
            "success": False,
            "error": format_error_message(e, "SLIM models list operation failed")
        }

@mcp.tool()
def slim_models_recommend_tool(
    task: str = "documentation",
    tier: str = "balanced"
) -> Dict[str, Any]:
    """
    Get AI model recommendations.
    
    Args:
        task: Task type (documentation, code_generation)
        tier: Quality tier (premium, balanced, fast, local)
    
    Returns:
        Dictionary with recommended models
    """
    try:
        return slim_models_recommend.execute(
            task=task,
            tier=tier
        )
    except Exception as e:
        logger.error(f"Error in slim_models_recommend_tool: {e}")
        return {
            "success": False,
            "error": format_error_message(e, "SLIM models recommend operation failed")
        }

@mcp.tool()
def slim_models_validate_tool(
    model: str
) -> Dict[str, Any]:
    """
    Validate AI model configuration.
    
    Args:
        model: Model in provider/model format
    
    Returns:
        Dictionary with validation results
    """
    try:
        return slim_models_validate.execute(
            model=model
        )
    except Exception as e:
        logger.error(f"Error in slim_models_validate_tool: {e}")
        return {
            "success": False,
            "error": format_error_message(e, "SLIM models validate operation failed")
        }

# New AI-focused tools
@mcp.tool()
def slim_apply_template_only_tool(
    best_practice_id: str,
    repo_dir: Optional[str] = None,
    repo_url: Optional[str] = None,
    output_dir: Optional[str] = None,
    dry_run: bool = False,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Apply SLIM best practice templates without AI customization.
    Demonstrates core SLIM functionality - pure template application and Git operations.
    """
    try:
        if ctx:
            ctx.info(f"Applying template-only for: {best_practice_id}")
        
        from .ai_tools import SlimApplyTemplateOnlyTool
        tool = SlimApplyTemplateOnlyTool()
        
        return tool.execute(
            best_practice_id=best_practice_id,
            repo_dir=repo_dir,
            repo_url=repo_url,
            output_dir=output_dir,
            dry_run=dry_run
        )
    except Exception as e:
        logger.error(f"Error in slim_apply_template_only_tool: {e}")
        return {
            "success": False,
            "error": format_error_message(e, "Template-only application failed")
        }

@mcp.tool()
def slim_apply_with_ai_tool(
    best_practice_id: str,
    repo_dir: Optional[str] = None,
    repo_url: Optional[str] = None,
    ai_model: str = "claude-3-5-sonnet",
    ai_instructions: Optional[str] = None,
    output_dir: Optional[str] = None,
    dry_run: bool = False,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Apply SLIM best practice templates with AI customization via MCP.
    Demonstrates MCP-coordinated AI integration with external tools like Claude Code.
    """
    try:
        if ctx:
            ctx.info(f"Applying template with AI for: {best_practice_id}")
        
        from .ai_tools import SlimApplyWithAITool
        tool = SlimApplyWithAITool()
        
        return tool.execute(
            best_practice_id=best_practice_id,
            repo_dir=repo_dir,
            repo_url=repo_url,
            ai_model=ai_model,
            ai_instructions=ai_instructions,
            output_dir=output_dir,
            dry_run=dry_run
        )
    except Exception as e:
        logger.error(f"Error in slim_apply_with_ai_tool: {e}")
        return {
            "success": False,
            "error": format_error_message(e, "AI-enhanced application failed")
        }

@mcp.tool()
def slim_get_prompt_tool(
    practice_type: str,
    section_name: str,
    additional_context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get SLIM prompts for AI customization.
    Provides access to SLIM's centralized prompt system for external AI tools.
    """
    try:
        from .ai_tools import SlimPromptTool
        tool = SlimPromptTool()
        
        return tool.execute(
            practice_type=practice_type,
            section_name=section_name,
            additional_context=additional_context
        )
    except Exception as e:
        logger.error(f"Error in slim_get_prompt_tool: {e}")
        return {
            "success": False,
            "error": format_error_message(e, "Prompt retrieval failed")
        }

# Comprehensive AI tool for all best practices
@mcp.tool()
def slim_apply_any_practice_with_ai_tool(
    best_practice_id: str,
    repo_dir: Optional[str] = None,
    repo_url: Optional[str] = None,
    ai_model: str = "claude-3-5-sonnet",
    ai_instructions: Optional[str] = None,
    output_dir: Optional[str] = None,
    dry_run: bool = False,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Apply ANY SLIM best practice with AI customization via comprehensive MCP coordination.
    Handles all complexity levels: simple templates, governance with Git analysis, complex multi-step workflows.
    """
    try:
        if ctx:
            ctx.info(f"Applying {best_practice_id} with comprehensive AI coordination")
        
        from .comprehensive_ai_tools import SlimComprehensiveAITool
        tool = SlimComprehensiveAITool()
        
        return tool.execute(
            best_practice_id=best_practice_id,
            repo_dir=repo_dir,
            repo_url=repo_url,
            ai_model=ai_model,
            ai_instructions=ai_instructions,
            output_dir=output_dir,
            dry_run=dry_run
        )
    except Exception as e:
        logger.error(f"Error in comprehensive AI tool: {e}")
        return {
            "success": False,
            "error": format_error_message(e, "Comprehensive AI application failed")
        }

# Enhanced tools for improved UX
@mcp.tool()
def slim_list_all_practices_tool(
    category: Optional[str] = None,
    detailed: bool = True
) -> Dict[str, Any]:
    """
    SLIM: List ALL available SLIM best practices with comprehensive coverage.
    Triggers when user mentions 'slim', 'list slim', 'show slim practices', 'what slim templates', etc.
    """
    try:
        from .enhanced_tools import EnhancedSlimListTool
        tool = EnhancedSlimListTool()
        
        return tool.execute(
            category=category,
            detailed=detailed
        )
    except Exception as e:
        logger.error(f"Error in enhanced slim list: {e}")
        return {
            "success": False,
            "error": format_error_message(e, "Enhanced SLIM list failed")
        }

@mcp.tool()
def slim_analyze_repository_context_tool(
    repo_dir: str,
    best_practice_id: Optional[str] = None,
    context_depth: str = "standard"
) -> Dict[str, Any]:
    """
    SLIM: Analyze repository context for AI customization.
    Provides repository analysis prompts for AI agents to gather project-specific context.
    """
    try:
        from .enhanced_tools import SlimRepositoryContextTool
        tool = SlimRepositoryContextTool()
        
        return tool.execute(
            repo_dir=repo_dir,
            best_practice_id=best_practice_id,
            context_depth=context_depth
        )
    except Exception as e:
        logger.error(f"Error in repository context analysis: {e}")
        return {
            "success": False,
            "error": format_error_message(e, "Repository context analysis failed")
        }

@mcp.tool()
def slim_manage_prompts_tool(
    action: str,
    practice_type: Optional[str] = None,
    prompt_key: Optional[str] = None,
    override_prompt: Optional[str] = None,
    user_instructions: Optional[str] = None
) -> Dict[str, Any]:
    """
    SLIM: Manage centralized SLIM prompts and user overrides.
    Supports listing, getting, overriding, and validating prompts for SLIM best practices.
    """
    try:
        from .enhanced_tools import SlimCentralizedPromptsManagementTool
        tool = SlimCentralizedPromptsManagementTool()
        
        return tool.execute(
            action=action,
            practice_type=practice_type,
            prompt_key=prompt_key,
            override_prompt=override_prompt,
            user_instructions=user_instructions
        )
    except Exception as e:
        logger.error(f"Error in prompt management: {e}")
        return {
            "success": False,
            "error": format_error_message(e, "Prompt management failed")
        }

# Resource implementations
@mcp.resource(RESOURCE_URIS["registry"])
def slim_registry_resource() -> str:
    """Get SLIM registry data."""
    try:
        data = slim_registry.get_data()
        return json.dumps(data, indent=2)
    except Exception as e:
        logger.error(f"Error in slim_registry_resource: {e}")
        return json.dumps({
            "error": format_error_message(e, "Failed to fetch SLIM registry")
        })

@mcp.resource(RESOURCE_URIS["best_practices"])
def slim_best_practices_resource(practice_id: Optional[str] = None) -> str:
    """Get SLIM best practices data."""
    try:
        data = slim_best_practices.get_data(practice_id)
        return json.dumps(data, indent=2)
    except Exception as e:
        logger.error(f"Error in slim_best_practices_resource: {e}")
        return json.dumps({
            "error": format_error_message(e, "Failed to fetch best practices")
        })

@mcp.resource(RESOURCE_URIS["prompts"])
def slim_prompts_resource(prompt_name: Optional[str] = None) -> str:
    """Get SLIM prompts data."""
    try:
        data = slim_prompts.get_data(prompt_name)
        return json.dumps(data, indent=2)
    except Exception as e:
        logger.error(f"Error in slim_prompts_resource: {e}")
        return json.dumps({
            "error": format_error_message(e, "Failed to fetch prompts")
        })

@mcp.resource(RESOURCE_URIS["models"])
def slim_models_resource(provider: Optional[str] = None) -> str:
    """Get SLIM AI models data."""
    try:
        data = slim_models.get_data(provider)
        return json.dumps(data, indent=2)
    except Exception as e:
        logger.error(f"Error in slim_models_resource: {e}")
        return json.dumps({
            "error": format_error_message(e, "Failed to fetch models")
        })

# Prompt implementations
@mcp.prompt("apply_best_practice")
async def apply_best_practice_prompt_impl(
    best_practice_ids: List[str],
    repo_url: str,
    use_ai: bool = False,
    model: str = ""
) -> List[Dict[str, str]]:
    """
    Template for applying SLIM best practices to repositories.
    
    Args:
        best_practice_ids: List of best practice IDs to apply
        repo_url: Repository URL to apply practices to
        use_ai: Whether to use AI for customization
        model: AI model to use for customization
    
    Returns:
        List of prompt messages
    """
    try:
        return apply_best_practice_prompt.generate(
            best_practice_ids=best_practice_ids,
            repo_url=repo_url,
            use_ai=use_ai,
            model=model
        )
    except Exception as e:
        logger.error(f"Error in apply_best_practice_prompt_impl: {e}")
        return [
            {
                "role": "system",
                "content": "Error generating prompt for SLIM best practices application."
            },
            {
                "role": "user",
                "content": f"Error: {format_error_message(e)}"
            }
        ]

@mcp.prompt("customize_with_ai")
async def customize_with_ai_prompt_impl(
    practice_type: str,
    repository_context: str,
    customization_goals: str
) -> List[Dict[str, str]]:
    """
    Template for AI-powered customization of best practices.
    
    Args:
        practice_type: Type of best practice being customized
        repository_context: Context about the target repository
        customization_goals: Goals for customization
    
    Returns:
        List of prompt messages
    """
    try:
        return customize_with_ai_prompt.generate(
            practice_type=practice_type,
            repository_context=repository_context,
            customization_goals=customization_goals
        )
    except Exception as e:
        logger.error(f"Error in customize_with_ai_prompt_impl: {e}")
        return [
            {
                "role": "system",
                "content": "Error generating prompt for AI customization."
            },
            {
                "role": "user",
                "content": f"Error: {format_error_message(e)}"
            }
        ]

@mcp.prompt("review_changes")
async def review_changes_prompt_impl(
    changes_summary: str,
    files_modified: List[str],
    next_steps: str
) -> List[Dict[str, str]]:
    """
    Template for reviewing SLIM best practice changes.
    
    Args:
        changes_summary: Summary of changes made
        files_modified: List of files that were modified
        next_steps: Recommended next steps
    
    Returns:
        List of prompt messages
    """
    try:
        return review_changes_prompt.generate(
            changes_summary=changes_summary,
            files_modified=files_modified,
            next_steps=next_steps
        )
    except Exception as e:
        logger.error(f"Error in review_changes_prompt_impl: {e}")
        return [
            {
                "role": "system",
                "content": "Error generating prompt for reviewing changes."
            },
            {
                "role": "user",
                "content": f"Error: {format_error_message(e)}"
            }
        ]

def check_dependencies() -> Dict[str, Any]:
    """Check if all required dependencies are available."""
    deps = check_slim_cli_dependencies()
    missing = [dep for dep, available in deps.items() if not available]
    
    return {
        "all_available": len(missing) == 0,
        "dependencies": deps,
        "missing": missing,
        "slim_cli_version": get_slim_cli_version()
    }

def main():
    """Main entry point for the MCP server."""
    try:
        # Check dependencies
        deps_status = check_dependencies()
        if not deps_status["all_available"]:
            logger.warning(f"Some dependencies are missing: {deps_status['missing']}")
            logger.warning("Some functionality may be limited")
        
        logger.info(f"Starting {MCP_SERVER_NAME} v{MCP_SERVER_VERSION}")
        logger.info(f"SLIM-CLI version: {deps_status['slim_cli_version']}")
        total_ai_tools = len(AI_TOOLS) + len(COMPREHENSIVE_AI_TOOLS) + len(ENHANCED_TOOLS)
        logger.info(f"Available tools: {len(TOOLS)} (+ {total_ai_tools} AI tools)")
        logger.info(f"Available resources: {len(RESOURCES)}")
        logger.info(f"Available prompts: {len(PROMPTS)}")
        logger.info(f"Comprehensive AI: {len(COMPREHENSIVE_AI_TOOLS)} universal tools")
        logger.info(f"Enhanced tools: {len(ENHANCED_TOOLS)} context & prompts tools")
        
        # Run the server
        mcp.run()
    
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()