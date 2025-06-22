"""
Test secrets detection best practices using Typer's testing framework.

This module tests secrets detection best practice aliases like secrets-github
and secrets-precommit. Tests apply, deploy, and apply-deploy commands with
various options including no-prompt scenarios.
"""

import pytest
import tempfile
import os
from pathlib import Path
from typer.testing import CliRunner
from jpl.slim.cli import app

runner = CliRunner()


class TestSecretsDetectionApply:
    """Test applying secrets detection best practices."""
    
    def test_apply_secrets_github_basic(self):
        """Test applying secrets-github best practice."""
        result = runner.invoke(app, [
            "apply",
            "--best-practice-ids", "secrets-github",
            "--repo-urls", "https://github.com/octocat/Hello-World",
        ])
        # Check for success indicators in output
        assert "Successfully applied" in result.output or "TEST MODE" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_secrets_github_with_repo_dir(self):
        """Test applying secrets-github to local repository directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(app, [
                "apply",
                "--best-practice-ids", "secrets-github",
                "--repo-dir", tmpdir,
                ])
            # Check for success indicators in output
            assert "Successfully applied" in result.output
            # Should not contain error messages
            assert "Error" not in result.output and "Failed" not in result.output
            # Check for success indicators in output
        assert "Successfully applied" in result.output or "TEST MODE" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_secrets_github_with_no_prompt(self):
        """Test applying secrets-github with no-prompt option."""
        result = runner.invoke(app, [
            "apply",
            "--best-practice-ids", "secrets-github",
            "--repo-urls", "https://github.com/octocat/Hello-World",
            "--no-prompt",
        ])
        # Check for success indicators in output
        assert "Successfully applied" in result.output or "TEST MODE" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_secrets_precommit_basic(self):
        """Test applying secrets-precommit best practice."""
        result = runner.invoke(app, [
            "apply",
            "--best-practice-ids", "secrets-precommit",
            "--repo-urls", "https://github.com/octocat/Hello-World",
        ])
        # Check for success indicators in output
        assert "Successfully applied" in result.output or "TEST MODE" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_secrets_precommit_with_repo_dir(self):
        """Test applying secrets-precommit to local repository directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(app, [
                "apply",
                "--best-practice-ids", "secrets-precommit",
                "--repo-dir", tmpdir,
                ])
            # Check for success indicators in output
            assert "Successfully applied" in result.output
            # Should not contain error messages
            assert "Error" not in result.output and "Failed" not in result.output
            # Check for success indicators in output
        assert "Successfully applied" in result.output or "TEST MODE" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_secrets_precommit_with_no_prompt(self):
        """Test applying secrets-precommit with no-prompt option."""
        result = runner.invoke(app, [
            "apply",
            "--best-practice-ids", "secrets-precommit",
            "--repo-urls", "https://github.com/octocat/Hello-World",
            "--no-prompt",
        ])
        # Check for success indicators in output
        assert "Successfully applied" in result.output or "TEST MODE" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_both_secrets_practices(self):
        """Test applying both secrets detection practices together."""
        result = runner.invoke(app, [
            "apply",
            "--best-practice-ids", "secrets-github",
            "--best-practice-ids", "secrets-precommit",
            "--repo-urls", "https://github.com/octocat/Hello-World",
        ])
        # Check for success indicators in output
        assert "Successfully applied" in result.output or "TEST MODE" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_secrets_with_clone_to_dir(self):
        """Test applying secrets detection with clone-to-dir option."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(app, [
                "apply",
                "--best-practice-ids", "secrets-github",
                "--repo-urls", "https://github.com/octocat/Hello-World",
                "--clone-to-dir", tmpdir,
                ])
            # Check for success indicators in output
            assert "Successfully applied" in result.output
            # Should not contain error messages
            assert "Error" not in result.output and "Failed" not in result.output
            # Check for success indicators in output
        assert "Successfully applied" in result.output or "TEST MODE" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_secrets_with_repo_urls_file(self):
        """Test applying secrets detection with repo URLs from file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("https://github.com/octocat/Hello-World\nhttps://github.com/octocat/Spoon-Knife")
            f.flush()
            
            try:
                result = runner.invoke(app, [
                    "apply",
                    "--best-practice-ids", "secrets-precommit",
                    "--repo-urls-file", f.name,
                ])
                # Check for success indicators in output
                assert "Successfully applied" in result.output
                # Should not contain error messages
                assert "Error" not in result.output and "Failed" not in result.output
            finally:
                os.unlink(f.name)


class TestSecretsDetectionDeploy:
    """Test deploying secrets detection best practices."""
    
    def test_deploy_secrets_github(self):
        """Test deploying secrets-github best practice."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(app, [
                "deploy",
                "--best-practice-ids", "secrets-github",
                "--repo-dir", tmpdir,
                ])
            # Check for success indicators in output
            assert "Successfully applied" in result.output
            # Should not contain error messages
            assert "Error" not in result.output and "Failed" not in result.output
            # Check for success indicators in output
        assert "Successfully applied" in result.output or "TEST MODE" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output
    
    def test_deploy_secrets_precommit(self):
        """Test deploying secrets-precommit best practice."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(app, [
                "deploy",
                "--best-practice-ids", "secrets-precommit",
                "--repo-dir", tmpdir,
                ])
            # Check for success indicators in output
            assert "Successfully applied" in result.output
            # Should not contain error messages
            assert "Error" not in result.output and "Failed" not in result.output
            # Check for success indicators in output
        assert "Successfully applied" in result.output or "TEST MODE" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output
    
    def test_deploy_secrets_with_custom_remote(self):
        """Test deploying secrets detection with custom remote."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(app, [
                "deploy",
                "--best-practice-ids", "secrets-github",
                "--repo-dir", tmpdir,
                "--remote", "origin",
                ])
            # Check for success indicators in output
            assert "Successfully applied" in result.output
            # Should not contain error messages
            assert "Error" not in result.output and "Failed" not in result.output
            # Check for success indicators in output
        assert "Successfully applied" in result.output or "TEST MODE" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output
    
    def test_deploy_secrets_with_custom_commit_message(self):
        """Test deploying secrets detection with custom commit message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(app, [
                "deploy",
                "--best-practice-ids", "secrets-precommit",
                "--repo-dir", tmpdir,
                "--commit-message", "Add pre-commit secrets detection",
                ])
            # Check for success indicators in output
            assert "Successfully applied" in result.output
            # Should not contain error messages
            assert "Error" not in result.output and "Failed" not in result.output
            # Check for success indicators in output
        assert "Successfully applied" in result.output or "TEST MODE" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output
    
    def test_deploy_both_secrets_practices(self):
        """Test deploying both secrets detection practices."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(app, [
                "deploy",
                "--best-practice-ids", "secrets-github",
                "--best-practice-ids", "secrets-precommit",
                "--repo-dir", tmpdir,
                ])
            # Check for success indicators in output
            assert "Successfully applied" in result.output
            # Should not contain error messages
            assert "Error" not in result.output and "Failed" not in result.output
            # Check for success indicators in output
        assert "Successfully applied" in result.output or "TEST MODE" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output


class TestSecretsDetectionApplyDeploy:
    """Test combined apply-deploy for secrets detection best practices."""
    
    def test_apply_deploy_secrets_github(self):
        """Test apply-deploy for secrets-github best practice."""
        result = runner.invoke(app, [
            "apply-deploy",
            "--best-practice-ids", "secrets-github",
            "--repo-urls", "https://github.com/octocat/Hello-World",
        ])
        # Check for success indicators in output
        assert "Successfully applied" in result.output or "TEST MODE" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_deploy_secrets_precommit(self):
        """Test apply-deploy for secrets-precommit best practice."""
        result = runner.invoke(app, [
            "apply-deploy",
            "--best-practice-ids", "secrets-precommit",
            "--repo-urls", "https://github.com/octocat/Hello-World",
        ])
        # Check for success indicators in output
        assert "Successfully applied" in result.output or "TEST MODE" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_deploy_secrets_with_no_prompt(self):
        """Test apply-deploy for secrets detection with no-prompt."""
        result = runner.invoke(app, [
            "apply-deploy",
            "--best-practice-ids", "secrets-github",
            "--repo-urls", "https://github.com/octocat/Hello-World",
            "--no-prompt",
        ])
        # Check for success indicators in output
        assert "Successfully applied" in result.output or "TEST MODE" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_deploy_secrets_with_all_options(self):
        """Test apply-deploy for secrets detection with comprehensive options."""
        result = runner.invoke(app, [
            "apply-deploy",
            "--best-practice-ids", "secrets-github",
            "--best-practice-ids", "secrets-precommit",
            "--repo-urls", "https://github.com/octocat/Hello-World",
            "--remote", "https://github.com/octocat/Hello-World",
            "--commit-message", "Add comprehensive secrets detection",
            "--no-prompt",
        ])
        # Check for success indicators in output
        assert "Successfully applied" in result.output or "TEST MODE" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_deploy_secrets_with_repo_dir(self):
        """Test apply-deploy for secrets detection with local repository directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(app, [
                "apply-deploy",
                "--best-practice-ids", "secrets-precommit",
                "--repo-dir", tmpdir,
                "--commit-message", "Add pre-commit secrets scanning",
                ])
            # Check for success indicators in output
            assert "Successfully applied" in result.output
            # Should not contain error messages
            assert "Error" not in result.output and "Failed" not in result.output
            # Check for success indicators in output
        assert "Successfully applied" in result.output or "TEST MODE" in result.output
        # Should not contain error messages
        assert "Error" not in result.output and "Failed" not in result.output



class TestSecretsDetectionErrorScenarios:
    """Test error scenarios for secrets detection best practices."""
    
    def test_apply_secrets_nonexistent_repo_dir(self):
        """Test apply secrets with non-existent repository directory."""
        result = runner.invoke(app, [
            "apply",
            "--best-practice-ids", "secrets-github",
            "--repo-dir", "/nonexistent/directory"
        ])
        assert result.exit_code != 0
    
    def test_deploy_secrets_nonexistent_repo_dir(self):
        """Test deploy secrets with non-existent repository directory."""
        result = runner.invoke(app, [
            "deploy",
            "--best-practice-ids", "secrets-precommit",
            "--repo-dir", "/nonexistent/directory"
        ])
        assert result.exit_code != 0
    
    def test_apply_secrets_invalid_repo_urls_file(self):
        """Test apply secrets with invalid repo URLs file."""
        result = runner.invoke(app, [
            "apply",
            "--best-practice-ids", "secrets-github",
            "--repo-urls-file", "/nonexistent/file.txt"
        ])
        assert result.exit_code != 0
    
    def test_apply_secrets_missing_best_practice_ids(self):
        """Test apply secrets without best-practice-ids."""
        result = runner.invoke(app, [
            "apply",
            "--repo-urls", "https://github.com/octocat/Hello-World"
        ])
        assert result.exit_code != 0

