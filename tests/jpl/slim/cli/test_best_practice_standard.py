"""
Test standard best practices using Typer's testing framework.

This module tests standard best practice aliases like readme, contributing,
changelog, code-of-conduct, governance-small, etc. Tests apply, deploy,
and apply-deploy commands with various options.
"""

import pytest
import tempfile
import os
from pathlib import Path
from typer.testing import CliRunner
from jpl.slim.cli import app

runner = CliRunner()


class TestStandardPracticeApply:
    """Test applying standard best practices."""
    
    def test_apply_readme_basic(self):
        """Test applying readme best practice."""
        result = runner.invoke(app, [
            "apply",
            "--best-practice-ids", "readme",
            "--repo-urls", "https://github.com/octocat/Hello-World",
        ])
        # Check for success indicators in output
        assert "Successfully applied" in result.output
        # Should not contain error messages
        assert "Error" not in result.output
        assert "Failed" not in result.output
    
    def test_apply_readme_with_repo_dir(self):
        """Test applying readme to local repository directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(app, [
                "apply",
                "--best-practice-ids", "readme",
                "--repo-dir", tmpdir,
                ])
            # Check for success indicators in output
        assert "Successfully applied" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_readme_with_local_ai(self):
        """Test applying readme with local AI model."""
        # Check if local model is available first
        model_check = runner.invoke(app, ["models", "validate", "ollama/llama3.2"])
        if model_check.exit_code != 0:
            pytest.skip("Local AI model not available. Install Ollama and pull llama3.2: 'ollama pull llama3.2'")
        
        result = runner.invoke(app, [
            "apply",
            "--best-practice-ids", "readme",
            "--repo-urls", "https://github.com/octocat/spoon-knife",
            "--use-ai", "ollama/llama3.2",
        ])
        # Check for success indicators in output
        assert "Successfully applied" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_contributing_basic(self):
        """Test applying contributing best practice."""
        result = runner.invoke(app, [
            "apply",
            "--best-practice-ids", "contributing",
            "--repo-urls", "https://github.com/octocat/Hello-World",
        ])
        # Check for success indicators in output
        assert "Successfully applied" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_changelog_basic(self):
        """Test applying changelog best practice."""
        result = runner.invoke(app, [
            "apply",
            "--best-practice-ids", "changelog",
            "--repo-urls", "https://github.com/octocat/Hello-World",
        ])
        # Check for success indicators in output
        assert "Successfully applied" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_code_of_conduct_basic(self):
        """Test applying code-of-conduct best practice."""
        result = runner.invoke(app, [
            "apply",
            "--best-practice-ids", "code-of-conduct",
            "--repo-urls", "https://github.com/octocat/Hello-World",
        ])
        # Check for success indicators in output
        assert "Successfully applied" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_governance_small_basic(self):
        """Test applying governance-small best practice."""
        result = runner.invoke(app, [
            "apply",
            "--best-practice-ids", "governance-small",
            "--repo-urls", "https://github.com/octocat/Hello-World",
        ])
        # Check for success indicators in output
        assert "Successfully applied" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_multiple_standard_practices(self):
        """Test applying multiple standard best practices."""
        result = runner.invoke(app, [
            "apply",
            "--best-practice-ids", "readme",
            "--best-practice-ids", "contributing",
            "--best-practice-ids", "changelog",
            "--repo-urls", "https://github.com/octocat/Hello-World",
        ])
        # Check for success indicators in output
        assert "Successfully applied" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_with_repo_urls_file(self):
        """Test applying best practice with repo URLs from file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("https://github.com/octocat/Hello-World\nhttps://github.com/octocat/Spoon-Knife")
            f.flush()
            
            try:
                result = runner.invoke(app, [
                    "apply",
                    "--best-practice-ids", "readme",
                    "--repo-urls-file", f.name,
                ])
                # Check for success indicators in output
                assert "Successfully applied" in result.output
                # Should not contain error messages
                assert "Error" not in result.output and "Failed" not in result.output
            finally:
                os.unlink(f.name)
    
    def test_apply_with_clone_to_dir(self):
        """Test applying best practice with clone-to-dir option."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(app, [
                "apply",
                "--best-practice-ids", "readme",
                "--repo-urls", "https://github.com/octocat/Hello-World",
                "--clone-to-dir", tmpdir,
                ])
            # Check for success indicators in output
        assert "Successfully applied" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_with_no_prompt(self):
        """Test applying best practice with no-prompt option."""
        result = runner.invoke(app, [
            "apply",
            "--best-practice-ids", "readme",
            "--repo-urls", "https://github.com/octocat/Hello-World",
            "--no-prompt",
        ])
        # Check for success indicators in output
        assert "Successfully applied" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output


class TestStandardPracticeDeploy:
    """Test deploying standard best practices."""
    
    def test_deploy_readme(self):
        """Test deploying readme best practice."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(app, [
                "deploy",
                "--best-practice-ids", "readme",
                "--repo-dir", tmpdir,
                ])
            # Check for success indicators in output
        assert "Successfully applied" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output
    
    def test_deploy_contributing_with_custom_remote(self):
        """Test deploying contributing with custom remote."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(app, [
                "deploy",
                "--best-practice-ids", "contributing",
                "--repo-dir", tmpdir,
                "--remote", "origin",
                ])
            # Check for success indicators in output
        assert "Successfully applied" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output
    
    def test_deploy_with_custom_commit_message(self):
        """Test deploying with custom commit message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(app, [
                "deploy",
                "--best-practice-ids", "changelog",
                "--repo-dir", tmpdir,
                "--commit-message", "Add changelog documentation",
                ])
            # Check for success indicators in output
        assert "Successfully applied" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output
    
    def test_deploy_multiple_practices(self):
        """Test deploying multiple standard practices."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(app, [
                "deploy",
                "--best-practice-ids", "readme",
                "--best-practice-ids", "contributing",
                "--repo-dir", tmpdir,
                ])
            # Check for success indicators in output
        assert "Successfully applied" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output


class TestStandardPracticeApplyDeploy:
    """Test combined apply-deploy for standard best practices."""
    
    def test_apply_deploy_readme(self):
        """Test apply-deploy for readme best practice."""
        result = runner.invoke(app, [
            "apply-deploy",
            "--best-practice-ids", "readme",
            "--repo-urls", "https://github.com/octocat/Hello-World",
        ])
        # Check for success indicators in output
        assert "Successfully applied" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_deploy_contributing_with_ai(self):
        """Test apply-deploy for contributing with AI."""
        # Check if local model is available first
        model_check = runner.invoke(app, ["models", "validate", "ollama/gemma2"])
        if model_check.exit_code != 0:
            pytest.skip("Local AI model not available. Install Ollama and pull gemma2: 'ollama pull gemma2'")
        
        result = runner.invoke(app, [
            "apply-deploy",
            "--best-practice-ids", "contributing",
            "--repo-urls", "https://github.com/octocat/Hello-World",
            "--use-ai", "ollama/gemma2",
        ])
        # Check for success indicators in output
        assert "Successfully applied" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_deploy_with_all_options(self):
        """Test apply-deploy with comprehensive options."""
        result = runner.invoke(app, [
            "apply-deploy",
            "--best-practice-ids", "readme",
            "--best-practice-ids", "governance-small",
            "--repo-urls", "https://github.com/octocat/Hello-World",
            "--remote", "https://github.com/octocat/Hello-World",
            "--commit-message", "Apply standard best practices",
            "--no-prompt",
        ])
        # Check for success indicators in output
        assert "Successfully applied" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_deploy_with_repo_dir(self):
        """Test apply-deploy with local repository directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(app, [
                "apply-deploy",
                "--best-practice-ids", "code-of-conduct",
                "--repo-dir", tmpdir,
                "--commit-message", "Add code of conduct",
                ])
            # Check for success indicators in output
        assert "Successfully applied" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output


class TestStandardPracticeErrorScenarios:
    """Test error scenarios for standard best practices."""
    
    def test_apply_nonexistent_repo_dir(self):
        """Test apply with non-existent repository directory."""
        result = runner.invoke(app, [
            "apply",
            "--best-practice-ids", "readme",
            "--repo-dir", "/nonexistent/directory"
        ])
        # Should contain error messages about directory not existing
        assert any(phrase in result.output.lower() for phrase in [
            "does not exist", "not found", "no such file", "error", "invalid"
        ])
    
    def test_deploy_nonexistent_repo_dir(self):
        """Test deploy with non-existent repository directory."""
        result = runner.invoke(app, [
            "deploy",
            "--best-practice-ids", "readme",
            "--repo-dir", "/nonexistent/directory"
        ])
        # Should contain error messages about directory not existing
        assert any(phrase in result.output.lower() for phrase in [
            "does not exist", "not found", "no such file", "error", "invalid"
        ])
    
    def test_apply_invalid_repo_urls_file(self):
        """Test apply with invalid repo URLs file."""
        result = runner.invoke(app, [
            "apply",
            "--best-practice-ids", "readme",
            "--repo-urls-file", "/nonexistent/file.txt"
        ])
        # Should contain error messages about file not existing
        assert any(phrase in result.output.lower() for phrase in [
            "does not exist", "not found", "no such file", "error", "invalid"
        ])
    
    def test_apply_missing_best_practice_ids(self):
        """Test apply without best-practice-ids."""
        result = runner.invoke(app, [
            "apply",
            "--repo-urls", "https://github.com/octocat/Hello-World"
        ])
        # Should contain error messages about missing required arguments
        assert any(phrase in result.output.lower() for phrase in [
            "missing", "required", "error", "missing option"
        ])
    
    def test_apply_nonexistent_github_repo(self):
        """Test apply with non-existent GitHub repository URL."""
        result = runner.invoke(app, [
            "apply",
            "--best-practice-ids", "readme",
            "--repo-urls", "https://github.com/nonexistent-user/nonexistent-repo-12345"
        ])
        # Should contain error messages about repository not found or clone failures
        assert any(phrase in result.output.lower() for phrase in [
            "not found", "clone", "error", "failed", "does not exist", "404"
        ])
    
    def test_apply_invalid_github_url(self):
        """Test apply with invalid GitHub URL format."""
        result = runner.invoke(app, [
            "apply",
            "--best-practice-ids", "readme",
            "--repo-urls", "https://invalid-git-host.com/user/repo"
        ])
        # Should contain error messages about invalid URL or connection failures
        assert any(phrase in result.output.lower() for phrase in [
            "clone", "error", "failed", "invalid", "connection", "not found"
        ])
