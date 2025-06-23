"""
Centralized test configuration for SLIM CLI tests.

This module provides shared test configuration, fixtures, and utilities
that can be used across all test files.
"""

import os
import subprocess
import pytest
from typer.testing import CliRunner
from jpl.slim.cli import app

# Centralized AI model configuration for tests
# Can be overridden by environment variable SLIM_TEST_AI_MODEL
DEFAULT_TEST_AI_MODEL = "ollama/gemma:2b"

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