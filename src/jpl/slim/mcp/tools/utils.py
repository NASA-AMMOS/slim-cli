"""
Utility functions for the SLIM-CLI MCP server.
"""

import os
import logging
import tempfile
import urllib.parse
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

# Import SLIM-CLI modules
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.jpl.slim.utils.io_utils import fetch_best_practices, repo_file_to_list
from src.jpl.slim.commands.common import (
    SLIM_REGISTRY_URI,
    get_dynamic_ai_model_pairs,
    get_dynamic_recommended_models,
    validate_model_format,
    check_model_availability,
    get_provider_setup_instructions
)

logger = logging.getLogger(__name__)

def normalize_repo_url(url: str) -> str:
    """Normalize a repository URL."""
    if not url:
        return ""
    
    # Add https:// if no protocol is specified
    if not url.startswith(("http://", "https://", "git://", "ssh://")):
        url = f"https://{url}"
    
    return url

def validate_repo_url(url: str) -> bool:
    """Validate a repository URL."""
    try:
        parsed = urllib.parse.urlparse(url)
        return bool(parsed.netloc and parsed.scheme in ("http", "https", "git", "ssh"))
    except Exception:
        return False

def validate_repo_path(path: str) -> bool:
    """Validate a repository directory path."""
    try:
        repo_path = Path(path)
        return repo_path.exists() and repo_path.is_dir()
    except Exception:
        return False

def validate_file_path(path: str) -> bool:
    """Validate a file path."""
    try:
        file_path = Path(path)
        return file_path.exists() and file_path.is_file()
    except Exception:
        return False

def parse_best_practice_ids(practice_ids: Union[str, List[str]]) -> List[str]:
    """Parse and validate best practice IDs."""
    if isinstance(practice_ids, str):
        # Handle comma-separated string
        practice_ids = [pid.strip() for pid in practice_ids.split(",")]
    
    if not isinstance(practice_ids, list):
        raise ValueError("Best practice IDs must be a string or list of strings")
    
    # Filter out empty strings
    return [pid for pid in practice_ids if pid.strip()]

def validate_ai_model(model: str) -> Tuple[bool, str]:
    """Validate an AI model string."""
    if not model:
        return False, "Model string cannot be empty"
    
    is_valid, provider, model_name = validate_model_format(model)
    if not is_valid:
        return False, f"Invalid model format: {model}. Expected 'provider/model'"
    
    return True, ""

def format_error_message(error: Exception, context: str = "") -> str:
    """Format an error message for MCP responses."""
    error_msg = str(error)
    if context:
        return f"{context}: {error_msg}"
    return error_msg

def safe_path_join(*args) -> str:
    """Safely join path components."""
    try:
        return str(Path(*args))
    except Exception as e:
        logger.error(f"Error joining paths {args}: {e}")
        return ""

def create_temp_directory(prefix: str = "slim_mcp_") -> str:
    """Create a temporary directory."""
    try:
        temp_dir = tempfile.mkdtemp(prefix=prefix)
        logger.debug(f"Created temporary directory: {temp_dir}")
        return temp_dir
    except Exception as e:
        logger.error(f"Error creating temporary directory: {e}")
        raise

def get_repo_name_from_url(url: str) -> str:
    """Extract repository name from URL."""
    try:
        parsed = urllib.parse.urlparse(url)
        repo_name = os.path.basename(parsed.path)
        # Remove .git extension if present
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        return repo_name
    except Exception:
        return "unknown_repo"

def convert_to_absolute_path(path: str) -> str:
    """Convert a path to absolute path."""
    try:
        return str(Path(path).resolve())
    except Exception as e:
        logger.error(f"Error converting path to absolute: {e}")
        return path

def filter_dict_by_keys(data: Dict[str, Any], allowed_keys: List[str]) -> Dict[str, Any]:
    """Filter dictionary to only include allowed keys."""
    return {k: v for k, v in data.items() if k in allowed_keys}

def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries."""
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds < 1:
        return f"{seconds:.2f}s"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

def truncate_string(text: str, max_length: int = 100) -> str:
    """Truncate string to maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def sanitize_branch_name(name: str) -> str:
    """Sanitize a string to be a valid Git branch name."""
    # Replace invalid characters with hyphens
    sanitized = "".join(c if c.isalnum() or c in "-_" else "-" for c in name)
    # Remove leading/trailing hyphens
    sanitized = sanitized.strip("-")
    # Ensure it's not empty
    if not sanitized:
        sanitized = "slim-best-practices"
    return sanitized

def get_slim_cli_version() -> str:
    """Get the SLIM-CLI version."""
    try:
        # Try to read version from package info
        from src.jpl.slim import __version__
        return __version__
    except ImportError:
        try:
            # Try to read from setup.py or pyproject.toml
            setup_py = Path(__file__).parent.parent / "setup.py"
            if setup_py.exists():
                with open(setup_py, 'r') as f:
                    content = f.read()
                    # Simple version extraction
                    for line in content.split('\n'):
                        if 'version=' in line:
                            return line.split('=')[1].strip().strip('"\'')
        except Exception:
            pass
        return "unknown"

def log_mcp_operation(operation: str, details: Dict[str, Any]) -> None:
    """Log MCP operation with details."""
    logger.info(f"MCP Operation: {operation}")
    for key, value in details.items():
        logger.debug(f"  {key}: {value}")

def validate_mcp_tool_params(params: Dict[str, Any], required_keys: List[str], optional_keys: List[str] = None) -> Tuple[bool, str]:
    """Validate MCP tool parameters."""
    optional_keys = optional_keys or []
    
    # Check for required parameters
    missing_keys = [key for key in required_keys if key not in params]
    if missing_keys:
        return False, f"Missing required parameters: {', '.join(missing_keys)}"
    
    # Check for unknown parameters
    allowed_keys = set(required_keys + optional_keys)
    unknown_keys = [key for key in params.keys() if key not in allowed_keys]
    if unknown_keys:
        logger.warning(f"Unknown parameters (will be ignored): {', '.join(unknown_keys)}")
    
    return True, ""

def extract_git_info(repo_path: str) -> Dict[str, Any]:
    """Extract Git information from repository."""
    try:
        import git
        repo = git.Repo(repo_path)
        
        return {
            "branch": repo.active_branch.name,
            "commit": repo.head.commit.hexsha[:8],
            "remote_url": repo.remotes.origin.url if repo.remotes else None,
            "is_dirty": repo.is_dirty(),
            "untracked_files": len(repo.untracked_files)
        }
    except Exception as e:
        logger.error(f"Error extracting Git info: {e}")
        return {}

def check_slim_cli_dependencies() -> Dict[str, bool]:
    """Check if SLIM-CLI dependencies are available."""
    dependencies = {
        "git": False,
        "typer": False,
        "rich": False,
        "litellm": False
    }
    
    try:
        import git
        dependencies["git"] = True
    except ImportError:
        pass
    
    try:
        import typer
        dependencies["typer"] = True
    except ImportError:
        pass
    
    try:
        import rich
        dependencies["rich"] = True
    except ImportError:
        pass
    
    try:
        import litellm
        dependencies["litellm"] = True
    except ImportError:
        pass
    
    return dependencies