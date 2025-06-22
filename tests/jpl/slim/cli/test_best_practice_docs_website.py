"""
Test documentation website best practice using Typer's testing framework.

This module tests the docs-website best practice alias. Tests apply, deploy,
and apply-deploy commands with various options including template-only,
revise-site, and output-dir scenarios.
"""

import pytest
import tempfile
import os
from pathlib import Path
from typer.testing import CliRunner
from jpl.slim.cli import app

runner = CliRunner()


class TestDocsWebsiteApply:
    """Test applying docs-website best practice."""
    
    def test_apply_docs_website_basic(self):
        """Test applying docs-website best practice with dry-run."""
        with tempfile.TemporaryDirectory() as output_dir:
            result = runner.invoke(app, [
                "apply",
                "--best-practice-ids", "docs-website",
                "--repo-urls", "https://github.com/octocat/Hello-World",
                "--output-dir", output_dir,
                ])
            # Check for success indicators in output
            assert "Successfully applied" in result.output
            # Should not contain error messages
            assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_docs_website_with_repo_dir(self):
        """Test applying docs-website to local repository directory."""
        with tempfile.TemporaryDirectory() as tmpdir, \
             tempfile.TemporaryDirectory() as output_dir:
            result = runner.invoke(app, [
                "apply",
                "--best-practice-ids", "docs-website",
                "--repo-dir", tmpdir,
                "--output-dir", output_dir,
                ])
            # Check for success indicators in output
            assert "Successfully applied" in result.output
            # Should not contain error messages
            assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_docs_website_template_only(self):
        """Test applying docs-website with template-only option."""
        with tempfile.TemporaryDirectory() as output_dir:
            result = runner.invoke(app, [
                "apply",
                "--best-practice-ids", "docs-website",
                "--repo-urls", "https://github.com/octocat/Hello-World",
                "--output-dir", output_dir,
                "--template-only",
                ])
            # Check for success indicators in output
            assert "Successfully applied" in result.output
            # Should not contain error messages
            assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_docs_website_revise_site(self):
        """Test applying docs-website with revise-site option."""
        with tempfile.TemporaryDirectory() as output_dir:
            result = runner.invoke(app, [
                "apply",
                "--best-practice-ids", "docs-website",
                "--repo-urls", "https://github.com/octocat/Hello-World",
                "--output-dir", output_dir,
                "--revise-site",
                ])
            # Check for success indicators in output
            assert "Successfully applied" in result.output
            # Should not contain error messages
            assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_docs_website_template_only_and_revise_site(self):
        """Test applying docs-website with both template-only and revise-site options."""
        with tempfile.TemporaryDirectory() as output_dir:
            result = runner.invoke(app, [
                "apply",
                "--best-practice-ids", "docs-website",
                "--repo-urls", "https://github.com/octocat/Hello-World",
                "--output-dir", output_dir,
                "--template-only",
                "--revise-site",
                ])
            # Check for success indicators in output
            assert "Successfully applied" in result.output
            # Should not contain error messages
            assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_docs_website_with_local_ai(self):
        """Test applying docs-website with local AI model."""
        # Check if local model is available first
        model_check = runner.invoke(app, ["models", "validate", "ollama/llama3.2"])
        if model_check.exit_code != 0:
            pytest.skip("Local AI model not available. Install Ollama and pull llama3.2: 'ollama pull llama3.2'")
        
        with tempfile.TemporaryDirectory() as output_dir:
            result = runner.invoke(app, [
                "apply",
                "--best-practice-ids", "docs-website",
                "--repo-urls", "https://github.com/octocat/Hello-World",
                "--output-dir", output_dir,
                "--use-ai", "ollama/llama3.2",
                ])
            # Check for success indicators in output
            assert "Successfully applied" in result.output
            # Should not contain error messages
            assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_docs_website_with_clone_to_dir(self):
        """Test applying docs-website with clone-to-dir option."""
        with tempfile.TemporaryDirectory() as clone_dir, \
             tempfile.TemporaryDirectory() as output_dir:
            result = runner.invoke(app, [
                "apply",
                "--best-practice-ids", "docs-website",
                "--repo-urls", "https://github.com/octocat/Hello-World",
                "--clone-to-dir", clone_dir,
                "--output-dir", output_dir,
                ])
            # Check for success indicators in output
            assert "Successfully applied" in result.output
            # Should not contain error messages
            assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_docs_website_with_no_prompt(self):
        """Test applying docs-website with no-prompt option."""
        with tempfile.TemporaryDirectory() as output_dir:
            result = runner.invoke(app, [
                "apply",
                "--best-practice-ids", "docs-website",
                "--repo-urls", "https://github.com/octocat/Hello-World",
                "--output-dir", output_dir,
                "--no-prompt",
                ])
            # Check for success indicators in output
            assert "Successfully applied" in result.output
            # Should not contain error messages
            assert "Error" not in result.output and "Failed" not in result.output


class TestDocsWebsiteDeploy:
    """Test deploying docs-website best practice."""
    
    def test_deploy_docs_website(self):
        """Test deploying docs-website best practice."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(app, [
                "deploy",
                "--best-practice-ids", "docs-website",
                "--repo-dir", tmpdir,
                ])
            # Check for success indicators in output
            assert "Successfully applied" in result.output
            # Should not contain error messages
            assert "Error" not in result.output and "Failed" not in result.output
    
    def test_deploy_docs_website_with_custom_remote(self):
        """Test deploying docs-website with custom remote."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(app, [
                "deploy",
                "--best-practice-ids", "docs-website",
                "--repo-dir", tmpdir,
                "--remote", "origin",
                ])
            # Check for success indicators in output
            assert "Successfully applied" in result.output
            # Should not contain error messages
            assert "Error" not in result.output and "Failed" not in result.output
    
    def test_deploy_docs_website_with_custom_commit_message(self):
        """Test deploying docs-website with custom commit message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(app, [
                "deploy",
                "--best-practice-ids", "docs-website",
                "--repo-dir", tmpdir,
                "--commit-message", "Add documentation website",
                ])
            # Check for success indicators in output
            assert "Successfully applied" in result.output
            # Should not contain error messages
            assert "Error" not in result.output and "Failed" not in result.output


class TestDocsWebsiteApplyDeploy:
    """Test combined apply-deploy for docs-website best practice."""
    
    def test_apply_deploy_docs_website_basic(self):
        """Test apply-deploy for docs-website best practice."""
        with tempfile.TemporaryDirectory() as output_dir:
            result = runner.invoke(app, [
                "apply-deploy",
                "--best-practice-ids", "docs-website",
                "--repo-urls", "https://github.com/octocat/Hello-World",
                "--output-dir", output_dir,
                ])
            # Check for success indicators in output
            assert "Successfully applied" in result.output
            # Should not contain error messages
            assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_deploy_docs_website_template_only(self):
        """Test apply-deploy for docs-website with template-only."""
        with tempfile.TemporaryDirectory() as output_dir:
            result = runner.invoke(app, [
                "apply-deploy",
                "--best-practice-ids", "docs-website",
                "--repo-urls", "https://github.com/octocat/Hello-World",
                "--output-dir", output_dir,
                "--template-only",
                ])
            # Check for success indicators in output
            assert "Successfully applied" in result.output
            # Should not contain error messages
            assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_deploy_docs_website_with_ai(self):
        """Test apply-deploy for docs-website with AI."""
        # Check if local model is available first
        model_check = runner.invoke(app, ["models", "validate", "ollama/gemma2"])
        if model_check.exit_code != 0:
            pytest.skip("Local AI model not available. Install Ollama and pull gemma2: 'ollama pull gemma2'")
        
        with tempfile.TemporaryDirectory() as output_dir:
            result = runner.invoke(app, [
                "apply-deploy",
                "--best-practice-ids", "docs-website",
                "--repo-urls", "https://github.com/octocat/Hello-World",
                "--output-dir", output_dir,
                "--use-ai", "ollama/gemma2",
                ])
            # Check for success indicators in output
            assert "Successfully applied" in result.output
            # Should not contain error messages
            assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_deploy_docs_website_with_all_options(self):
        """Test apply-deploy for docs-website with comprehensive options."""
        with tempfile.TemporaryDirectory() as output_dir:
            result = runner.invoke(app, [
                "apply-deploy",
                "--best-practice-ids", "docs-website",
                "--repo-urls", "https://github.com/octocat/Hello-World",
                "--output-dir", output_dir,
                "--template-only",
                "--revise-site",
                "--remote", "https://github.com/octocat/Hello-World",
                "--commit-message", "Generate comprehensive documentation",
                "--no-prompt",
                ])
            # Check for success indicators in output
            assert "Successfully applied" in result.output
            # Should not contain error messages
            assert "Error" not in result.output and "Failed" not in result.output
    
    def test_apply_deploy_docs_website_with_repo_dir(self):
        """Test apply-deploy for docs-website with local repository directory."""
        with tempfile.TemporaryDirectory() as tmpdir, \
             tempfile.TemporaryDirectory() as output_dir:
            result = runner.invoke(app, [
                "apply-deploy",
                "--best-practice-ids", "docs-website",
                "--repo-dir", tmpdir,
                "--output-dir", output_dir,
                "--commit-message", "Add documentation site",
                ])
            # Check for success indicators in output
            assert "Successfully applied" in result.output
            # Should not contain error messages
            assert "Error" not in result.output and "Failed" not in result.output




class TestDocsWebsiteErrorScenarios:
    """Test error scenarios for docs-website best practice."""
    
    def test_apply_docs_website_missing_output_dir(self):
        """Test apply docs-website without required output-dir."""
        result = runner.invoke(app, [
            "apply",
            "--best-practice-ids", "docs-website",
            "--repo-urls", "https://github.com/octocat/Hello-World"
        ])
        # Should contain error messages about missing required arguments
        assert any(phrase in result.output.lower() for phrase in [
            "missing", "required", "error", "missing option"
        ])
    
    def test_apply_docs_website_nonexistent_repo_dir(self):
        """Test apply docs-website with non-existent repository directory."""
        with tempfile.TemporaryDirectory() as output_dir:
            result = runner.invoke(app, [
                "apply",
                "--best-practice-ids", "docs-website",
                "--repo-dir", "/nonexistent/directory",
                "--output-dir", output_dir
            ])
            # Should contain error messages about directory not existing
            assert any(phrase in result.output.lower() for phrase in [
                "does not exist", "not found", "no such file", "error", "invalid"
            ])
    
    def test_deploy_docs_website_nonexistent_repo_dir(self):
        """Test deploy docs-website with non-existent repository directory."""
        result = runner.invoke(app, [
            "deploy",
            "--best-practice-ids", "docs-website",
            "--repo-dir", "/nonexistent/directory"
        ])
        # Should contain error messages about directory not existing
        assert any(phrase in result.output.lower() for phrase in [
            "does not exist", "not found", "no such file", "error", "invalid"
        ])
    
    def test_apply_docs_website_invalid_output_dir_parent(self):
        """Test apply docs-website with invalid output directory parent."""
        result = runner.invoke(app, [
            "apply",
            "--best-practice-ids", "docs-website",
            "--repo-urls", "https://github.com/octocat/Hello-World",
            "--output-dir", "/nonexistent/parent/output",
        ])
        # Should either succeed (dry-run) or fail with error messages
        if "Successfully applied" not in result.output:
            assert any(phrase in result.output.lower() for phrase in [
                "does not exist", "not found", "no such file", "error", "invalid"
            ])


class TestDocsWebsiteSpecialOptions:
    """Test special options unique to docs-website best practice."""
    
    def test_template_only_without_revise_site(self):
        """Test template-only option without revise-site."""
        with tempfile.TemporaryDirectory() as output_dir:
            result = runner.invoke(app, [
                "apply",
                "--best-practice-ids", "docs-website",
                "--repo-urls", "https://github.com/octocat/Hello-World",
                "--output-dir", output_dir,
                "--template-only",
                ])
            # Check for success indicators in output
            assert "Successfully applied" in result.output
            # Should not contain error messages
            assert "Error" not in result.output and "Failed" not in result.output
    
    def test_revise_site_without_template_only(self):
        """Test revise-site option without template-only."""
        with tempfile.TemporaryDirectory() as output_dir:
            result = runner.invoke(app, [
                "apply",
                "--best-practice-ids", "docs-website",
                "--repo-urls", "https://github.com/octocat/Hello-World",
                "--output-dir", output_dir,
                "--revise-site",
                ])
            # Check for success indicators in output
            assert "Successfully applied" in result.output
            # Should not contain error messages
            assert "Error" not in result.output and "Failed" not in result.output
    
    def test_docs_website_with_repo_urls_file(self):
        """Test docs-website with repo URLs from file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f, \
             tempfile.TemporaryDirectory() as output_dir:
            f.write("https://github.com/octocat/Hello-World")
            f.flush()
            
            try:
                result = runner.invoke(app, [
                    "apply",
                    "--best-practice-ids", "docs-website",
                    "--repo-urls-file", f.name,
                    "--output-dir", output_dir,
                        ])
                # Check for success indicators in output
                assert "Successfully applied" in result.output
                # Should not contain error messages
                assert "Error" not in result.output and "Failed" not in result.output
            finally:
                os.unlink(f.name)
    
    def test_docs_website_with_complex_ai_scenario(self):
        """Test docs-website with AI and complex options."""
        # Check if local model is available first
        model_check = runner.invoke(app, ["models", "validate", "ollama/llama3.2"])
        if model_check.exit_code != 0:
            pytest.skip("Local AI model not available. Install Ollama and pull llama3.2: 'ollama pull llama3.2'")
        
        with tempfile.TemporaryDirectory() as clone_dir, \
             tempfile.TemporaryDirectory() as output_dir:
            result = runner.invoke(app, [
                "apply-deploy",
                "--best-practice-ids", "docs-website",
                "--repo-urls", "https://github.com/octocat/Hello-World",
                "--clone-to-dir", clone_dir,
                "--output-dir", output_dir,
                "--use-ai", "ollama/llama3.2",
                "--template-only",
                "--revise-site",
                "--no-prompt",
                "--remote", "origin",
                "--commit-message", "AI-generated documentation site",
                ])
            # Check for success indicators in output
            assert "Successfully applied" in result.output
            # Should not contain error messages
            assert "Error" not in result.output and "Failed" not in result.output