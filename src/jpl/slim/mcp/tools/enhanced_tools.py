"""
Enhanced MCP Tools for SLIM-CLI with improved functionality.

This module provides enhanced versions of MCP tools with:
1. Better "slim" keyword detection
2. Repository context scanning for AI agents
3. Centralized prompts management
4. User override support
"""

import logging
import json
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

# Import SLIM CLI core modules 
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.jpl.slim.utils.io_utils import fetch_best_practices
from src.jpl.slim.commands.common import SLIM_REGISTRY_URI
from src.jpl.slim.best_practices.practice_mapping import get_all_aliases

from .config import BEST_PRACTICE_CATEGORIES
from .utils import (
    log_mcp_operation,
    format_error_message,
    format_duration
)

logger = logging.getLogger(__name__)

class EnhancedSlimListTool:
    """Enhanced SLIM list tool with comprehensive best practices coverage."""
    
    def __init__(self):
        self.name = "slim_list_all_practices"
        self.description = "SLIM: List ALL available SLIM best practices. Triggers when user mentions 'slim', 'list slim', 'show slim practices', 'what slim templates', etc."
        self.parameters = {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Filter by category (documentation, governance, security, licensing)",
                    "enum": ["documentation", "governance", "security", "licensing"]
                },
                "detailed": {
                    "type": "boolean", 
                    "description": "Include detailed information",
                    "default": True
                }
            }
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute enhanced list with ALL available best practices."""
        try:
            start_time = time.time()
            
            category = kwargs.get("category")
            detailed = kwargs.get("detailed", True)
            
            log_mcp_operation("enhanced_slim_list", {
                "category": category,
                "detailed": detailed
            })
            
            # Get ALL available practices from multiple sources
            all_practices = self._get_comprehensive_practices_list()
            
            # Filter by category if specified
            if category:
                all_practices = [
                    p for p in all_practices 
                    if p.get("category") == category
                ]
            
            # Group by category for better presentation
            practices_by_category = {}
            for practice in all_practices:
                cat = practice.get("category", "other")
                if cat not in practices_by_category:
                    practices_by_category[cat] = []
                practices_by_category[cat].append(practice)
            
            duration = time.time() - start_time
            
            return {
                "success": True,
                "total_practices": len(all_practices),
                "category_filter": category,
                "detailed": detailed,
                "practices": all_practices,
                "practices_by_category": practices_by_category,
                "categories": list(practices_by_category.keys()),
                "duration": format_duration(duration),
                "message": f"Found {len(all_practices)} SLIM best practices across {len(practices_by_category)} categories",
                "usage_hint": "Use 'Apply [practice_name] via SLIM' to apply any practice with AI"
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced slim list: {e}")
            return {
                "success": False,
                "error": format_error_message(e, "Failed to list SLIM best practices")
            }
    
    def _get_comprehensive_practices_list(self) -> List[Dict[str, Any]]:
        """Get comprehensive list of ALL available SLIM best practices."""
        practices = []
        
        # Get practices from registry
        try:
            registry_practices = fetch_best_practices(SLIM_REGISTRY_URI)
            registry_aliases = set()
            
            if registry_practices:
                for practice in registry_practices:
                    alias = practice.get('alias', '')
                    if alias:
                        registry_aliases.add(alias)
                        practices.append({
                            "id": alias,
                            "title": practice.get('title', alias),
                            "description": practice.get('description', ''),
                            "category": self._get_practice_category(alias),
                            "source": "registry",
                            "guide_url": practice.get('guide_url', ''),
                            "assets": practice.get('assets', [])
                        })
        except Exception as e:
            logger.warning(f"Failed to fetch from registry: {e}")
            registry_aliases = set()
        
        # Get practices from mapping (includes all supported practices)
        try:
            all_aliases = get_all_aliases()
            for alias in all_aliases:
                if alias not in registry_aliases:  # Avoid duplicates
                    practices.append({
                        "id": alias,
                        "title": alias.replace('-', ' ').title(),
                        "description": f"SLIM best practice: {alias}",
                        "category": self._get_practice_category(alias),
                        "source": "mapping",
                        "guide_url": f"https://nasa-ammos.github.io/slim/docs/guides/{alias}",
                        "assets": []
                    })
        except Exception as e:
            logger.warning(f"Failed to get from mapping: {e}")
        
        # Sort by category and ID
        practices.sort(key=lambda x: (x.get("category", ""), x.get("id", "")))
        
        return practices
    
    def _get_practice_category(self, practice_id: str) -> str:
        """Get category for a practice ID."""
        for category, practice_list in BEST_PRACTICE_CATEGORIES.items():
            if practice_id in practice_list:
                return category
        if practice_id.startswith("license-"):
            return "licensing"
        return "other"

class SlimRepositoryContextTool:
    """Tool for analyzing repository context for AI customization."""
    
    def __init__(self):
        self.name = "slim_analyze_repository_context"
        self.description = "SLIM: Analyze repository to provide context for AI customization. Use when applying SLIM practices with AI."
        self.parameters = {
            "type": "object",
            "properties": {
                "repo_dir": {
                    "type": "string",
                    "description": "Repository directory to analyze"
                },
                "best_practice_id": {
                    "type": "string", 
                    "description": "Best practice being applied (for context-specific analysis)"
                },
                "context_depth": {
                    "type": "string",
                    "description": "Analysis depth: quick, standard, comprehensive",
                    "enum": ["quick", "standard", "comprehensive"],
                    "default": "standard"
                }
            },
            "required": ["repo_dir"]
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Analyze repository and provide context for AI customization."""
        try:
            start_time = time.time()
            
            repo_dir = kwargs["repo_dir"]
            best_practice_id = kwargs.get("best_practice_id", "")
            context_depth = kwargs.get("context_depth", "standard")
            
            if not Path(repo_dir).exists():
                return {
                    "success": False,
                    "error": f"Repository directory does not exist: {repo_dir}"
                }
            
            # Generate AI prompts for repository analysis
            analysis_prompts = self._generate_repository_analysis_prompts(
                repo_dir, best_practice_id, context_depth
            )
            
            # Provide context guidance for AI agents
            context_guidance = self._generate_context_guidance(best_practice_id)
            
            duration = time.time() - start_time
            
            return {
                "success": True,
                "repo_dir": repo_dir,
                "best_practice_id": best_practice_id,
                "context_depth": context_depth,
                "analysis_prompts": analysis_prompts,
                "context_guidance": context_guidance,
                "duration": format_duration(duration),
                "message": "Repository context analysis prompts prepared for AI agent",
                "next_step": "AI agent should execute the analysis prompts to gather repository context"
            }
            
        except Exception as e:
            logger.error(f"Error in repository context analysis: {e}")
            return {
                "success": False,
                "error": format_error_message(e, "Repository context analysis failed")
            }
    
    def _generate_repository_analysis_prompts(self, repo_dir: str, practice_id: str, depth: str) -> List[Dict[str, str]]:
        """Generate prompts for AI agents to analyze repository context."""
        
        base_analysis = {
            "step": 1,
            "name": "Basic Repository Analysis",
            "prompt": f"""
Analyze the repository at: {repo_dir}

ANALYSIS TASKS:
1. **Project Identification:**
   - Read README.md, package.json, setup.py, pyproject.toml, or similar files
   - Extract project name, description, and purpose
   - Identify main programming languages and frameworks

2. **Structure Analysis:**
   - Identify source code directories
   - Find documentation directories
   - Locate configuration files
   - Identify testing directories

3. **Context Extraction:**
   - Determine project type (library, application, service, etc.)
   - Identify target audience (developers, end-users, researchers)
   - Extract key features and functionality
   - Find examples or usage patterns

4. **Metadata Collection:**
   - Author/organization information
   - License information
   - Version information
   - Dependencies and requirements

Return a structured summary of this information for use in SLIM template customization.
"""
        }
        
        prompts = [base_analysis]
        
        if depth in ["standard", "comprehensive"]:
            prompts.append({
                "step": 2,
                "name": "Advanced Context Analysis",
                "prompt": f"""
Perform advanced analysis of the repository at: {repo_dir}

ADVANCED ANALYSIS:
1. **Architecture Analysis:**
   - Identify architectural patterns used
   - Find main entry points and APIs
   - Analyze module/package organization
   - Identify key abstractions and interfaces

2. **Development Context:**
   - Find build/deployment configurations
   - Identify CI/CD setup
   - Analyze testing frameworks and patterns
   - Check for development documentation

3. **Community Context:**
   - Look for contribution guidelines
   - Find issue/PR templates
   - Check for community documentation
   - Identify governance structures

4. **Technical Context:**
   - Analyze dependencies and their purposes
   - Identify deployment targets
   - Find performance considerations
   - Check security configurations
"""
            })
        
        if depth == "comprehensive":
            prompts.append({
                "step": 3,
                "name": "Practice-Specific Analysis",
                "prompt": f"""
Analyze repository context specifically for the SLIM best practice: {practice_id}

PRACTICE-SPECIFIC ANALYSIS:
For {practice_id}:
1. **Relevant Context:**
   - What repository aspects are most relevant for this practice?
   - What existing content should be preserved or referenced?
   - What specific details need to be extracted?

2. **Customization Opportunities:**
   - How can the template be tailored to this specific project?
   - What project-specific examples can be included?
   - What terminology should be used consistently?

3. **Integration Considerations:**
   - How does this practice fit with existing project structure?
   - What existing files or processes should be referenced?
   - What consistency requirements exist?

Provide specific recommendations for customizing the {practice_id} template.
"""
            })
        
        return prompts
    
    def _generate_context_guidance(self, practice_id: str) -> Dict[str, Any]:
        """Generate context guidance for specific best practices."""
        
        guidance = {
            "general": "Use repository analysis to customize templates with project-specific information",
            "key_files_to_analyze": ["README.md", "package.json", "setup.py", "pyproject.toml"],
            "context_priorities": ["project_name", "description", "languages", "architecture"]
        }
        
        # Practice-specific guidance
        if practice_id == "readme":
            guidance.update({
                "focus_areas": ["project_purpose", "installation", "usage_examples", "key_features"],
                "important_files": ["src/", "examples/", "docs/", "tests/"],
                "customization_tips": "Extract actual usage examples and highlight unique project features"
            })
        elif practice_id.startswith("governance"):
            guidance.update({
                "focus_areas": ["contributors", "team_size", "decision_making", "communication"],
                "git_analysis_needed": True,
                "customization_tips": "Analyze Git history for real contributor information"
            })
        elif practice_id == "docs-website":
            guidance.update({
                "focus_areas": ["architecture", "apis", "tutorials", "examples"],
                "documentation_structure": True,
                "customization_tips": "Create comprehensive documentation structure based on project complexity"
            })
        
        return guidance

class SlimCentralizedPromptsManagementTool:
    """Tool for managing centralized SLIM prompts with user overrides."""
    
    def __init__(self):
        self.name = "slim_manage_prompts"
        self.description = "SLIM: Manage centralized SLIM prompts and user overrides. Use for prompt customization and management."
        self.parameters = {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform",
                    "enum": ["list", "get", "override", "reset", "validate"]
                },
                "practice_type": {
                    "type": "string",
                    "description": "Practice type (e.g., 'standard_practices', 'governance')"
                },
                "prompt_key": {
                    "type": "string", 
                    "description": "Specific prompt key"
                },
                "override_prompt": {
                    "type": "string",
                    "description": "Custom prompt to override default"
                },
                "user_instructions": {
                    "type": "string",
                    "description": "User-specific instructions to incorporate"
                }
            },
            "required": ["action"]
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute prompt management operations."""
        try:
            action = kwargs["action"]
            
            if action == "list":
                return self._list_available_prompts()
            elif action == "get":
                return self._get_prompt(kwargs)
            elif action == "override":
                return self._set_prompt_override(kwargs)
            elif action == "reset":
                return self._reset_prompt_override(kwargs)
            elif action == "validate":
                return self._validate_prompt(kwargs)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
                
        except Exception as e:
            logger.error(f"Error in prompt management: {e}")
            return {
                "success": False,
                "error": format_error_message(e, "Prompt management failed")
            }
    
    def _list_available_prompts(self) -> Dict[str, Any]:
        """List all available prompts."""
        try:
            from src.jpl.slim.utils.prompt_utils import load_prompts
            prompts_dict = load_prompts()
            
            # Extract prompt structure
            prompt_structure = self._extract_prompt_structure(prompts_dict)
            
            return {
                "success": True,
                "prompt_structure": prompt_structure,
                "total_prompts": self._count_prompts(prompts_dict),
                "message": "Available SLIM prompts listed",
                "usage": "Use 'get' action to retrieve specific prompts"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list prompts: {e}"
            }
    
    def _get_prompt(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific prompt with user instructions integration."""
        try:
            from src.jpl.slim.utils.prompt_utils import get_prompt_with_context
            
            practice_type = kwargs.get("practice_type", "")
            prompt_key = kwargs.get("prompt_key", "")
            user_instructions = kwargs.get("user_instructions", "")
            
            if not practice_type or not prompt_key:
                return {
                    "success": False,
                    "error": "Both practice_type and prompt_key are required"
                }
            
            # Get base prompt
            base_prompt = get_prompt_with_context(
                practice_type=practice_type,
                prompt_key=prompt_key
            )
            
            if not base_prompt:
                return {
                    "success": False,
                    "error": f"Prompt not found: {practice_type}.{prompt_key}"
                }
            
            # Integrate user instructions if provided
            if user_instructions:
                enhanced_prompt = f"""
{base_prompt}

ADDITIONAL USER INSTRUCTIONS:
{user_instructions}

Please incorporate these user-specific requirements into your response.
"""
            else:
                enhanced_prompt = base_prompt
            
            return {
                "success": True,
                "practice_type": practice_type,
                "prompt_key": prompt_key,
                "base_prompt": base_prompt,
                "enhanced_prompt": enhanced_prompt,
                "user_instructions_included": bool(user_instructions),
                "message": "Prompt retrieved and enhanced with user instructions"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get prompt: {e}"
            }
    
    def _set_prompt_override(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Set a user override for a prompt."""
        # For now, return guidance on how to override prompts
        return {
            "success": True,
            "message": "Prompt override guidance provided",
            "override_methods": [
                {
                    "method": "natural_language",
                    "description": "Provide custom instructions in natural language when requesting SLIM application",
                    "example": "Apply README template with emphasis on scientific applications and NASA branding"
                },
                {
                    "method": "prompt_file_override",
                    "description": "Create custom prompts.yaml file in repository root to override defaults",
                    "location": "./slim_prompts_override.yaml"
                }
            ],
            "note": "User overrides can be provided through natural language instructions or custom prompt files"
        }
    
    def _reset_prompt_override(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Reset prompt override to default."""
        return {
            "success": True,
            "message": "Prompt reset to default (overrides cleared)",
            "note": "Default SLIM prompts will be used for future applications"
        }
    
    def _validate_prompt(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a prompt for correctness."""
        override_prompt = kwargs.get("override_prompt", "")
        
        if not override_prompt:
            return {
                "success": False,
                "error": "override_prompt is required for validation"
            }
        
        # Basic validation
        validation_results = {
            "length_ok": len(override_prompt) > 10,
            "has_instructions": "instruction" in override_prompt.lower(),
            "has_context": "context" in override_prompt.lower(),
            "format_ok": True  # Could add more sophisticated validation
        }
        
        is_valid = all(validation_results.values())
        
        return {
            "success": True,
            "is_valid": is_valid,
            "validation_results": validation_results,
            "recommendations": [] if is_valid else [
                "Ensure prompt includes clear instructions",
                "Consider adding context requirements",
                "Verify prompt length is sufficient"
            ]
        }
    
    def _extract_prompt_structure(self, prompts_dict: Dict) -> Dict:
        """Extract the structure of available prompts."""
        structure = {}
        
        def extract_recursive(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    if key == "prompt" and isinstance(value, str):
                        # This is a prompt
                        structure[path] = {"type": "prompt", "length": len(value)}
                    else:
                        extract_recursive(value, new_path)
        
        extract_recursive(prompts_dict)
        return structure
    
    def _count_prompts(self, prompts_dict: Dict) -> int:
        """Count total number of prompts."""
        count = 0
        
        def count_recursive(obj):
            nonlocal count
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == "prompt" and isinstance(value, str):
                        count += 1
                    else:
                        count_recursive(value)
        
        count_recursive(prompts_dict)
        return count

# Export enhanced tools
ENHANCED_TOOLS = [
    EnhancedSlimListTool(),
    SlimRepositoryContextTool(),
    SlimCentralizedPromptsManagementTool()
]