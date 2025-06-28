"""
Centralized test configuration for SLIM CLI tests.

This module provides shared test configuration, fixtures, and utilities
that can be used across all test files.
"""

import os
import subprocess
import pytest
import tempfile
import git
import shutil
from typing import Tuple, List, Optional
from typer.testing import CliRunner
from jpl.slim.cli import app

# Centralized AI model configuration for tests
# Can be overridden by environment variable SLIM_TEST_AI_MODEL
DEFAULT_TEST_AI_MODEL = "ollama/llama3.1"

# Get model from environment variable if set, otherwise use default
TEST_AI_MODEL = os.environ.get("SLIM_TEST_AI_MODEL", DEFAULT_TEST_AI_MODEL)

# Set up Ollama environment variables if not already set
if TEST_AI_MODEL.startswith("ollama/") and "OLLAMA_API_BASE" not in os.environ:
    os.environ["OLLAMA_API_BASE"] = "http://localhost:11434"


def get_test_ai_model():
    """
    Get the AI model to use for testing.
    
    Returns:
        str: The AI model identifier (e.g., 'ollama/gemma:2b')
    """
    return TEST_AI_MODEL


def initialize_test_ai_model():
    """
    Initialize/prepare the test AI model by pulling it if needed.
    
    Returns:
        bool: True if model is ready, False otherwise
    """
    # For Ollama models, ensure environment is set up
    if TEST_AI_MODEL.startswith("ollama/"):
        # Set default Ollama API base if not already set
        if "OLLAMA_API_BASE" not in os.environ:
            os.environ["OLLAMA_API_BASE"] = "http://localhost:11434"
        
        model_name = TEST_AI_MODEL.split("/")[-1]
        
        # Check if Ollama is running by trying to list models
        try:
            result = subprocess.run(
                ["ollama", "list"], 
                check=True, 
                capture_output=True, 
                text=True
            )
            
            # Check if our model is already pulled
            if model_name in result.stdout:
                return True
            
            # Model not found, try to pull it
            print(f"Pulling AI model {model_name} for tests...")
            subprocess.run(["ollama", "pull", model_name], check=True)
            return True
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Ollama not installed or not running
            return False
    
    # For non-Ollama models, check with CLI
    runner = CliRunner()
    result = runner.invoke(app, ["models", "validate", TEST_AI_MODEL])
    return result.exit_code == 0 and "configuration error" not in result.output


# Pytest fixture for AI model
@pytest.fixture
def test_ai_model():
    """Pytest fixture that provides the test AI model."""
    return TEST_AI_MODEL


@pytest.fixture
def test_ai_model_ready():
    """
    Pytest fixture that ensures the test AI model is initialized.
    
    Yields:
        str: The AI model identifier if ready, or skips the test
    """
    if not initialize_test_ai_model():
        model_name = TEST_AI_MODEL.split("/")[-1]
        if TEST_AI_MODEL.startswith("ollama/"):
            pytest.skip(f"Test AI model {TEST_AI_MODEL} not available. Ensure Ollama is running and run: 'ollama pull {model_name}'")
        else:
            pytest.skip(f"Test AI model {TEST_AI_MODEL} not available or properly configured")
    
    yield TEST_AI_MODEL


def create_temp_git_repo(repo_dir: str) -> git.Repo:
    """Create a temporary git repository with initial commit."""
    repo = git.Repo.init(repo_dir)
    readme_path = os.path.join(repo_dir, 'README.md')
    with open(readme_path, 'w') as f:
        f.write('# Test Repository\nThis is a test repository.')
    repo.index.add(['README.md'])
    repo.index.commit('Initial commit')
    return repo


def create_bare_repo_with_remote(working_dir: str, remote_name: str = 'origin') -> Tuple[git.Repo, str]:
    """Create a bare repository and set it up as remote for working directory."""
    bare_repo_dir = tempfile.mkdtemp(suffix='_bare')
    bare_repo = git.Repo.init(bare_repo_dir, bare=True)
    working_repo = create_temp_git_repo(working_dir)
    working_repo.create_remote(remote_name, bare_repo_dir)
    return working_repo, bare_repo_dir


class BestPracticeTestEnvironment:
    """Simple context manager for best practice test environment setup and cleanup."""
    
    def __init__(self, use_ai: bool = False):
        self.use_ai = use_ai
        self.ai_model = get_test_ai_model() if use_ai else None
        self.runner = CliRunner()
        self.temp_dirs = []
        self.target_dir = None
    
    def __enter__(self):
        # Validate AI model if AI is requested
        if self.use_ai:
            model_check = self.runner.invoke(app, ["models", "validate", self.ai_model])
            if model_check.exit_code != 0 or "configuration error" in model_check.output:
                model_name = self.ai_model.split("/")[-1]
                pytest.skip(f"Local AI model {self.ai_model} not available. Install Ollama and pull {model_name}: 'ollama pull {model_name}'")
        
        # Create temporary directory
        self.target_dir = tempfile.mkdtemp()
        self.temp_dirs.append(self.target_dir)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def add_temp_dir(self, temp_dir: str):
        """Track additional temporary directory for cleanup."""
        self.temp_dirs.append(temp_dir)
