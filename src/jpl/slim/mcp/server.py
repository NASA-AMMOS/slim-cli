#!/usr/bin/env python3
"""
Standalone MCP Server for SLIM CLI with live registry integration
"""

import sys
import os
import logging
import subprocess
from pathlib import Path

# Use package-based imports instead of relative paths
# This allows the server to work from any global installation location
import site

# Add standard Python package locations
paths_to_add = []

# Add user site-packages
user_site = site.getusersitepackages()
if user_site and os.path.exists(user_site):
    paths_to_add.append(user_site)

# Add system site-packages
for site_dir in site.getsitepackages():
    if os.path.exists(site_dir):
        paths_to_add.append(site_dir)

# Check for UV virtual environment
if 'VIRTUAL_ENV' in os.environ:
    venv_path = os.environ['VIRTUAL_ENV']
    python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    venv_site_packages = os.path.join(venv_path, 'lib', python_version, 'site-packages')
    if os.path.exists(venv_site_packages):
        paths_to_add.insert(0, venv_site_packages)

# Remove existing entries and add in correct order
for path in paths_to_add:
    while path in sys.path:
        sys.path.remove(path)

# Insert paths at the beginning to ensure they take precedence
for path in reversed(paths_to_add):
    sys.path.insert(0, path)

# Configure logging to stderr  
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)

logger = logging.getLogger(__name__)

logger.info(f"Python path configured with package locations: {paths_to_add}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f"Server script path: {__file__}")

# Try to import FastMCP
try:
    from fastmcp import FastMCP
    logger.info("FastMCP imported successfully")
except ImportError as e:
    logger.info(f"FastMCP not available: {e}")
    
    # Try auto-installation if possible
    install_commands = [
        [sys.executable, "-m", "pip", "install", "--user", "fastmcp"],
        [sys.executable, "-m", "pip", "install", "fastmcp", "--break-system-packages"],
    ]
    
    installed = False
    for cmd in install_commands:
        try:
            logger.info(f"Attempting installation with: {' '.join(cmd)}")
            subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Refresh import paths and try importing again
            import importlib
            importlib.invalidate_caches()
            
            from fastmcp import FastMCP
            logger.info("FastMCP installed and imported successfully")
            installed = True
            break
        except Exception as install_error:
            logger.debug(f"Installation attempt failed: {install_error}")
            continue
    
    if not installed:
        logger.error("FastMCP is required but not available")
        print("\n" + "="*60, file=sys.stderr)
        print("SLIM CLI MCP Server Setup Required", file=sys.stderr)
        print("="*60, file=sys.stderr)
        print("FastMCP is required to run the MCP server.", file=sys.stderr)
        print("Please install it using one of these methods:", file=sys.stderr)
        print("", file=sys.stderr)
        print("Option 1 (Recommended): Using pipx", file=sys.stderr)
        print("  pipx install fastmcp", file=sys.stderr)
        print("", file=sys.stderr)
        print("Option 2: User installation", file=sys.stderr)
        print("  pip install --user fastmcp", file=sys.stderr)
        print("", file=sys.stderr)
        print("Option 3: Virtual environment", file=sys.stderr)  
        print("  python3 -m venv mcp_env", file=sys.stderr)
        print("  source mcp_env/bin/activate", file=sys.stderr)
        print("  pip install fastmcp", file=sys.stderr)
        print("", file=sys.stderr)
        print("After installation, try running the MCP server again.", file=sys.stderr)
        print("="*60, file=sys.stderr)
        sys.exit(1)

# Import SLIM CLI modules
try:
    from jpl.slim.utils.io_utils import fetch_best_practices, create_slim_registry_dictionary
    from jpl.slim.commands.common import SLIM_REGISTRY_URI
    logger.info("SLIM CLI modules imported successfully")
except ImportError as e:
    logger.error(f"SLIM CLI import failed: {e}")
    logger.error(f"Python path: {sys.path}")
    print("Error: SLIM CLI modules not available", file=sys.stderr)
    sys.exit(1)

# Create MCP server
mcp = FastMCP("SLIM-CLI")

# Cache for registry data
_registry_cache = None

def get_live_registry_data():
    """Fetch and process live SLIM registry data with caching."""
    global _registry_cache
    
    if _registry_cache is not None:
        return _registry_cache
    
    try:
        logger.info(f"Fetching SLIM registry from: {SLIM_REGISTRY_URI}")
        raw_practices = fetch_best_practices(SLIM_REGISTRY_URI)
        
        if not raw_practices:
            logger.error("No practices fetched from registry")
            return {"practices": [], "registry_dict": {}}
        
        logger.info(f"Fetched {len(raw_practices)} practices from registry")
        
        # Create registry dictionary for asset mapping
        registry_dict = create_slim_registry_dictionary(raw_practices)
        logger.info(f"Created registry dictionary with {len(registry_dict)} assets")
        
        # Process practices to extract relevant information
        processed_practices = []
        for practice in raw_practices:
            practice_data = {
                "id": practice.get("title", "").lower().replace(" ", "-").replace(".md", "").replace("_", "-"),
                "title": practice.get("title", ""),
                "description": practice.get("description", ""),
                "category": practice.get("category", "unknown"),
                "uri": practice.get("uri", ""),
                "tags": practice.get("tags", []),
                "assets": []
            }
            
            # Add asset information
            if "assets" in practice and practice["assets"]:
                for asset in practice["assets"]:
                    asset_data = {
                        "name": asset.get("name", ""),
                        "alias": asset.get("alias", ""),
                        "uri": asset.get("uri", ""),
                        "description": asset.get("description", "")
                    }
                    practice_data["assets"].append(asset_data)
            
            processed_practices.append(practice_data)
        
        _registry_cache = {
            "practices": processed_practices,
            "registry_dict": registry_dict
        }
        
        return _registry_cache
        
    except Exception as e:
        logger.error(f"Failed to fetch registry data: {e}")
        # Return empty data on failure
        return {"practices": [], "registry_dict": {}}

@mcp.tool()
def slim_list_all_practices():
    """
    SLIM: List ALL available SLIM best practices.
    Use when user mentions 'slim', 'list slim', 'show slim practices', etc.
    """
    registry_data = get_live_registry_data()
    practices = registry_data["practices"]
    
    if not practices:
        return {
            "success": False,
            "error": "Failed to fetch SLIM registry data",
            "practices": [],
            "total_practices": 0,
            "categories": [],
            "message": "Unable to fetch SLIM best practices from registry"
        }
    
    # Group by category
    by_category = {}
    for practice in practices:
        category = practice["category"]
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(practice)
    
    return {
        "success": True,
        "total_practices": len(practices),
        "practices": practices,
        "practices_by_category": by_category,
        "categories": list(by_category.keys()),
        "registry_dict": registry_data["registry_dict"],
        "message": f"Found {len(practices)} SLIM best practices across {len(by_category)} categories from live registry",
        "source": "Live SLIM Registry",
        "registry_uri": SLIM_REGISTRY_URI
    }

@mcp.tool()
def slim_analyze_repository_context_tool(repo_dir: str = ".", practice_id: str = None):
    """
    SLIM: Analyze repository context for applying SLIM best practices.
    Gathers project-specific context for AI customization.
    """
    import os
    import json
    from pathlib import Path
    
    repo_path = Path(repo_dir).resolve()
    
    if not repo_path.exists():
        return {
            "success": False,
            "error": f"Repository directory does not exist: {repo_path}",
            "repo_dir": str(repo_path)
        }
    
    context = {
        "repo_path": str(repo_path),
        "repo_name": repo_path.name,
        "files": {},
        "directories": [],
        "languages": [],
        "frameworks": [],
        "project_type": "unknown"
    }
    
    # Analyze key files
    key_files = [
        "README.md", "README.rst", "README.txt",
        "package.json", "pyproject.toml", "setup.py", "requirements.txt",
        "Cargo.toml", "go.mod", "pom.xml", "build.gradle",
        "LICENSE", "CONTRIBUTING.md", "GOVERNANCE.md"
    ]
    
    for filename in key_files:
        file_path = repo_path / filename
        if file_path.exists() and file_path.is_file():
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')[:2000]  # First 2k chars
                context["files"][filename] = {
                    "exists": True,
                    "size": file_path.stat().st_size,
                    "content_preview": content
                }
            except Exception as e:
                context["files"][filename] = {
                    "exists": True,
                    "error": f"Could not read: {e}"
                }
    
    # Detect project type and languages
    if "package.json" in context["files"]:
        context["languages"].append("JavaScript/Node.js")
        context["project_type"] = "node"
    if any(f in context["files"] for f in ["pyproject.toml", "setup.py", "requirements.txt"]):
        context["languages"].append("Python")
        context["project_type"] = "python"
    if "Cargo.toml" in context["files"]:
        context["languages"].append("Rust")
        context["project_type"] = "rust"
    if "go.mod" in context["files"]:
        context["languages"].append("Go")
        context["project_type"] = "go"
    
    # Get registry data for the specific practice
    registry_data = get_live_registry_data()
    practice_info = None
    
    if practice_id:
        for practice in registry_data["practices"]:
            if practice["id"] == practice_id or practice["title"].lower() == practice_id.lower():
                practice_info = practice
                break
    
    return {
        "success": True,
        "repo_context": context,
        "practice_info": practice_info,
        "customization_suggestions": [
            f"Repository appears to be a {context['project_type']} project",
            f"Languages detected: {', '.join(context['languages']) if context['languages'] else 'None detected'}",
            f"Key files present: {', '.join([f for f in context['files'] if context['files'][f].get('exists')])}",
        ],
        "message": f"Analyzed repository context for {repo_path.name}"
    }

@mcp.tool()
def slim_apply_practice_with_ai(
    practice_id: str, 
    repo_dir: str = ".", 
    ai_instructions: str = None,
    dry_run: bool = True
):
    """
    SLIM: Apply SLIM best practice with AI customization.
    Use when user wants to apply a SLIM practice with AI enhancement.
    """
    # Get practice information from registry
    registry_data = get_live_registry_data()
    practice_info = None
    
    for practice in registry_data["practices"]:
        if practice["id"] == practice_id or practice["title"].lower().replace(".md", "") == practice_id.lower():
            practice_info = practice
            break
    
    if not practice_info:
        return {
            "success": False,
            "error": f"Practice '{practice_id}' not found in SLIM registry",
            "available_practices": [p["id"] for p in registry_data["practices"][:10]]
        }
    
    return {
        "success": True,
        "message": f"Ready to apply {practice_id} with AI customization",
        "practice_id": practice_id,
        "practice_info": practice_info,
        "repo_dir": repo_dir,
        "ai_instructions": ai_instructions,
        "dry_run": dry_run,
        "coordination_prompts": [
            {
                "step": "analyze_repository",
                "prompt": f"Use slim_analyze_repository_context_tool to analyze repository at {repo_dir} for {practice_id} customization",
                "tool": "slim_analyze_repository_context_tool",
                "args": {"repo_dir": repo_dir, "practice_id": practice_id}
            },
            {
                "step": "fetch_template",
                "prompt": f"Fetch template content for {practice_id} from practice assets: {practice_info.get('assets', [])}",
                "practice_assets": practice_info.get('assets', [])
            },
            {
                "step": "customize_content", 
                "prompt": f"Customize {practice_id} template based on repository analysis with instructions: {ai_instructions or 'Apply best practices for the detected project type and structure'}"
            },
            {
                "step": "apply_template",
                "prompt": f"Apply the customized {practice_id} template to the repository at {repo_dir}"
            }
        ],
        "next_step": "AI agent should execute coordination prompts in sequence",
        "template_info": {
            "title": practice_info.get("title"),
            "description": practice_info.get("description"),
            "category": practice_info.get("category"),
            "tags": practice_info.get("tags", []),
            "assets": practice_info.get("assets", [])
        }
    }

@mcp.tool()
def slim_fetch_template_content(practice_id: str, asset_alias: str = None):
    """
    SLIM: Fetch template content for a specific SLIM best practice.
    Retrieves the actual template files from the SLIM registry.
    """
    registry_data = get_live_registry_data()
    practice_info = None
    
    # Find the practice
    for practice in registry_data["practices"]:
        if practice["id"] == practice_id or practice["title"].lower().replace(".md", "") == practice_id.lower():
            practice_info = practice
            break
    
    if not practice_info:
        return {
            "success": False,
            "error": f"Practice '{practice_id}' not found in SLIM registry",
            "available_practices": [p["id"] for p in registry_data["practices"][:10]]
        }
    
    assets = practice_info.get("assets", [])
    if not assets:
        return {
            "success": False,
            "error": f"No template assets found for practice '{practice_id}'",
            "practice_info": practice_info
        }
    
    # If no specific asset requested, return info about all assets
    if not asset_alias:
        return {
            "success": True,
            "practice_id": practice_id,
            "practice_info": practice_info,
            "available_assets": assets,
            "message": f"Found {len(assets)} template assets for {practice_id}. Use asset_alias parameter to fetch specific content."
        }
    
    # Find specific asset
    target_asset = None
    for asset in assets:
        if asset.get("alias") == asset_alias:
            target_asset = asset
            break
    
    if not target_asset:
        return {
            "success": False,
            "error": f"Asset '{asset_alias}' not found for practice '{practice_id}'",
            "available_assets": [a.get("alias") for a in assets if a.get("alias")]
        }
    
    # Fetch the template content
    template_uri = target_asset.get("uri", "")
    if not template_uri:
        return {
            "success": False,
            "error": f"No URI found for asset '{asset_alias}'",
            "asset_info": target_asset
        }
    
    try:
        import requests
        response = requests.get(template_uri)
        response.raise_for_status()
        
        return {
            "success": True,
            "practice_id": practice_id,
            "asset_alias": asset_alias,
            "asset_info": target_asset,
            "template_content": response.text,
            "content_length": len(response.text),
            "template_uri": template_uri,
            "message": f"Successfully fetched template content for {practice_id}/{asset_alias}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to fetch template content: {str(e)}",
            "template_uri": template_uri,
            "asset_info": target_asset
        }

@mcp.tool()
def slim_models_recommend(task: str = "documentation", tier: str = "balanced"):
    """Get AI model recommendations for SLIM tasks"""
    recommendations = {
        "premium": ["openai/gpt-4o", "anthropic/claude-3-5-sonnet"],
        "balanced": ["anthropic/claude-3-haiku", "openai/gpt-3.5-turbo"],
        "fast": ["openai/gpt-3.5-turbo", "anthropic/claude-3-haiku"],
        "local": ["ollama/llama3.1", "ollama/codellama"]
    }
    
    models = recommendations.get(tier, recommendations["balanced"])
    
    return {
        "success": True,
        "recommended_models": models,
        "task": task,
        "tier": tier,
        "message": f"Recommended {len(models)} models for {task} ({tier} tier)"
    }

def main():
    try:
        logger.info("Starting SLIM CLI MCP server with live registry integration")
        logger.info("Available tools: slim_list_all_practices, slim_apply_practice_with_ai, slim_analyze_repository_context_tool, slim_fetch_template_content, slim_models_recommend")
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()