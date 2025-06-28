"""
Integration tests for standard best practices.

This module contains integration tests for standard best practices that test
end-to-end functionality including AI enhancement, git repository operations,
and file generation.
"""

import pytest
import os
import tempfile
import git
import logging
from jpl.slim.app import app
from tests.conftest import BestPracticeTestEnvironment, create_temp_git_repo, get_test_ai_model


@pytest.mark.slow
@pytest.mark.integration
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
        repo_dirs = [d for d in os.listdir(env.target_dir) if os.path.isdir(os.path.join(env.target_dir, d))]
        assert len(repo_dirs) > 0, "No repository directory found after cloning"
        repo_path = os.path.join(env.target_dir, repo_dirs[0])
        assert os.path.exists(os.path.join(repo_path, 'README.md')), "README.md file was not created"
        
        repo = git.Repo(repo_path)
        branch_names = [branch.name for branch in repo.branches]
        assert 'readme' in branch_names, f"Expected 'readme' branch was not created. Found branches: {branch_names}"


@pytest.mark.slow
@pytest.mark.integration
def test_readme_best_practice_without_ai():
    """Test README best practice without AI enhancement."""
    with BestPracticeTestEnvironment(use_ai=False) as env:  # No AI
        args = [
            'apply',
            '--best-practice-ids', 'readme',
            '--repo-urls', 'https://github.com/NASA-AMMOS/anms',
            '--clone-to-dir', env.target_dir
        ]
        result = env.runner.invoke(app, args)
        
        # Custom assertions for non-AI scenario
        assert result.exit_code == 0, f"Command failed with output: {result.output}"
        assert "Successfully applied" in result.output
        assert "Error" not in result.output
        
        # Verify basic file creation
        repo_dirs = [d for d in os.listdir(env.target_dir) if os.path.isdir(os.path.join(env.target_dir, d))]
        assert len(repo_dirs) > 0, "No repository directory found after cloning"
        repo_path = os.path.join(env.target_dir, repo_dirs[0])
        assert os.path.exists(os.path.join(repo_path, 'README.md')), "README.md file was not created"


@pytest.mark.slow
@pytest.mark.integration
def test_readme_best_practice_local_repo():
    """Test README best practice on local repository."""
    with BestPracticeTestEnvironment(use_ai=False) as env:
        # Create local git repo
        local_repo_dir = tempfile.mkdtemp()
        env.add_temp_dir(local_repo_dir)
        create_temp_git_repo(local_repo_dir)
        
        args = ['apply', '--best-practice-ids', 'readme', '--repo-dir', local_repo_dir]
        result = env.runner.invoke(app, args)
        
        # Custom assertions for local repo scenario
        assert result.exit_code == 0, f"Command failed with output: {result.output}"
        assert "Successfully applied" in result.output
        assert os.path.exists(os.path.join(local_repo_dir, 'README.md')), "README.md file was not created"
        
        # Verify git branch was created
        repo = git.Repo(local_repo_dir)
        branch_names = [branch.name for branch in repo.branches]
        assert 'readme' in branch_names, f"Expected 'readme' branch was not created. Found branches: {branch_names}"
