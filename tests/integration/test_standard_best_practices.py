"""
Integration tests for standard best practices.

This module contains integration tests for standard best practices that test
end-to-end functionality including AI enhancement, git repository operations,
and file generation.

NOTE: Use this module specifically for testing complex scenarios, such as
AI-generated content validation. For all other basic tests of commands that 
just need to check if the command was executed successfully, define your tests
in best_practices_test_commands.yaml
"""

import pytest
import os
import tempfile
import git
import logging
from jpl.slim.app import app
from tests.conftest import (
    BestPracticeTestEnvironment, 
    create_temp_git_repo, 
    get_test_ai_model,
    verify_repository_setup,
    verify_branch_creation
)


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.ai
def test_readme_best_practice_for_correct_ai_output(caplog):
    """
        Test README best practice with AI generated content.
        Checks to ensure content is project-adapted and
        doesn't include AI conversational text
        """
    with BestPracticeTestEnvironment(use_ai=True) as env:
        # Set the logging level to capture debug logs
        caplog.set_level(logging.DEBUG)
        
        # Execute command using centralized AI model config
        args = [
            'apply',
            '--best-practice-ids', 'readme', 
            '--repo-urls', 'https://github.com/NASA-AMMOS/anms', # Random repo
            '--clone-to-dir', env.target_dir,
            '--use-ai', env.ai_model,  # Uses get_test_ai_model() from conftest.py
            '--logging', 'DEBUG'
        ]
        result = env.runner.invoke(app, args)
        
        # Custom assertions for this specific test
        assert result.exit_code == 0, f"Command failed with output: {result.output}"
        assert "Successfully applied" in result.output
        assert "Asynchronous Network Management System" in caplog.text, "AI-generated content not found in debug logs"
        assert "completed template" not in caplog.text, "AI-generated content has chat text"
        
        # Verify repository setup
        repo_path = verify_repository_setup(env.target_dir, 'README.md')
        
        # Verify branch creation
        verify_branch_creation(repo_path, 'readme')

@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.ai
def test_contributing_best_practice_for_correct_ai_output(caplog):
    """
        Test CONTRIBUTING best practice with AI generated content.
        Checks to ensure content is project-adapted and
        doesn't include AI conversational text
        """
    with BestPracticeTestEnvironment(use_ai=True) as env:
        # Set the logging level to capture debug logs
        caplog.set_level(logging.DEBUG)
        
        # Execute command using centralized AI model config
        args = [
            'apply',
            '--best-practice-ids', 'contributing', 
            '--repo-urls', 'https://github.com/NASA-AMMOS/anms', # Random repo
            '--clone-to-dir', env.target_dir,
            '--use-ai', env.ai_model,  # Uses get_test_ai_model() from conftest.py
            '--logging', 'DEBUG'
        ]
        result = env.runner.invoke(app, args)
        
        # Custom assertions for this specific test
        assert result.exit_code == 0, f"Command failed with output: {result.output}"
        assert "Successfully applied" in result.output
        assert "https://github.com/NASA-AMMOS/anms/issues" in caplog.text, "AI-generated content not found in debug logs"
        assert "completed template" not in caplog.text, "AI-generated content has chat text"
        
        # Verify repository setup
        repo_path = verify_repository_setup(env.target_dir, 'CONTRIBUTING.md')
        
        # Verify branch creation
        verify_branch_creation(repo_path, 'contributing')

@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.ai
def test_testing_plan_best_practice_for_correct_ai_output(caplog):
    """
        Test TESTING PLAN best practice with AI generated content.
        Checks to ensure content is project-adapted and
        doesn't include AI conversational text
        """
    with BestPracticeTestEnvironment(use_ai=True) as env:
        # Set the logging level to capture debug logs
        caplog.set_level(logging.DEBUG)
        
        # Execute command using centralized AI model config
        args = [
            'apply',
            '--best-practice-ids', 'testing-plan', 
            '--repo-urls', 'https://github.com/NASA-AMMOS/3DTilesRendererJS', # Random repo
            '--clone-to-dir', env.target_dir,
            '--use-ai', env.ai_model,  # Uses get_test_ai_model() from conftest.py
            '--logging', 'DEBUG'
        ]
        result = env.runner.invoke(app, args)
        
        # Custom assertions for this specific test
        assert result.exit_code == 0, f"Command failed with output: {result.output}"
        assert "Successfully applied" in result.output
        assert "test/" in caplog.text, "AI-generated content (test/) not found in debug logs"
        assert ".eslintrc.json" in caplog.text, "AI-generated content (.eslintrc.json) not found in debug logs"
        assert "completed template" not in caplog.text, "AI-generated content has chat text"
        
        # Verify repository setup
        repo_path = verify_repository_setup(env.target_dir, 'TESTING.md')
        
        # Verify branch creation
        verify_branch_creation(repo_path, 'testing-plan')
