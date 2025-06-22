"""
General CLI tests for the SLIM CLI using Typer's testing framework.

This module tests basic command functionality, argument validation,
global options, models command variations, list command, and error scenarios.
"""

import pytest
import tempfile
import os
from pathlib import Path
from typer.testing import CliRunner
from jpl.slim.cli import app

runner = CliRunner()


class TestListCommand:
    """Test the list command functionality."""
    
    def test_list_basic(self):
        """Test basic list command execution."""
        result = runner.invoke(app, ["list"])
        assert "Available SLIM Best Practices" in result.output
        assert "Total practices:" in result.output
    
    def test_list_dry_run(self):
        """Test list command with dry-run flag."""
        result = runner.invoke(app, ["list", "--dry-run"])
        assert "DRY RUN MODE" in result.output
        assert "Dry run complete. No actions were taken." in result.output
    
    def test_list_dry_run_short(self):
        """Test list command with short dry-run flag."""
        result = runner.invoke(app, ["list", "-d"])
        assert "DRY RUN MODE" in result.output
        assert "Dry run complete. No actions were taken." in result.output


class TestModelsCommand:
    """Test the models command and its subcommands."""
    
    def test_models_list(self):
        """Test models list subcommand."""
        result = runner.invoke(app, ["models", "list"])
        assert "Found" in result.output and "models:" in result.output
    
    def test_models_list_with_provider(self):
        """Test models list with provider filter."""
        result = runner.invoke(app, ["models", "list", "--provider", "anthropic"])
        assert "Found" in result.output and "models:" in result.output
    
    def test_models_list_with_tier(self):
        """Test models list with tier filter."""
        result = runner.invoke(app, ["models", "list", "--tier", "premium"])
        assert "Found" in result.output and "models:" in result.output
    
    def test_models_recommend(self):
        """Test models recommend subcommand."""
        result = runner.invoke(app, ["models", "recommend", "--task", "documentation", "--tier", "balanced"])
        assert "Recommended balanced models for documentation:" in result.output
    
    def test_models_setup(self):
        """Test models setup subcommand."""
        result = runner.invoke(app, ["models", "setup", "anthropic"])
        # Should provide setup instructions (output will vary by provider)
        assert "Setup:" in result.output
    
    def test_models_validate(self):
        """Test models validate subcommand."""
        result = runner.invoke(app, ["models", "validate", "ollama/gemma2"])
        # Should show either success (✅) or error (❌) message because we're only checking if validate works, not the model
        assert "✅" in result.output or "❌" in result.output

class TestGlobalOptions:
    """Test global CLI options."""
    
    def test_help_main(self):
        """Test main help command."""
        result = runner.invoke(app, ["--help"])
        assert "SLIM CLI" in result.output
        assert "Usage:" in result.output
    
    def test_command_help_apply(self):
        """Test apply command help."""
        result = runner.invoke(app, ["apply", "--help"])
        assert "Apply best practices" in result.output
        assert "Usage:" in result.output
    
    def test_command_help_deploy(self):
        """Test deploy command help."""
        result = runner.invoke(app, ["deploy", "--help"])
        assert "Deploy best practices" in result.output
        assert "Usage:" in result.output
    
    def test_command_help_models(self):
        """Test models command help."""
        result = runner.invoke(app, ["models", "--help"])
        assert "Discover and configure AI models" in result.output
        assert "Usage:" in result.output


class TestArgumentValidation:
    """Test CLI argument validation."""
    
    def test_enum_validation_tier(self):
        """Test that Enum arguments work correctly for tier."""
        result = runner.invoke(app, [
            "models", "recommend",
            "--task", "documentation",
            "--tier", "premium"
        ])
        assert "Recommended premium models for documentation:" in result.output
    
    def test_enum_validation_task(self):
        """Test that Enum arguments work correctly for task."""
        result = runner.invoke(app, [
            "models", "recommend", 
            "--task", "code_generation",
            "--tier", "fast"
        ])
        assert "Recommended fast models for code_generation:" in result.output


class TestErrorScenarios:
    """Test error scenarios and edge cases."""
    
    def test_apply_missing_required_args(self):
        """Test apply command without required arguments."""
        result = runner.invoke(app, ["apply"])
        assert any(phrase in result.output.lower() for phrase in [
            "missing option", "required", "error"
        ])
    
    def test_deploy_missing_required_args(self):
        """Test deploy command without required arguments."""
        result = runner.invoke(app, ["deploy"])
        assert any(phrase in result.output.lower() for phrase in [
            "missing option", "required", "error"
        ])
    
    def test_apply_invalid_file_path(self):
        """Test apply command with invalid file path."""
        result = runner.invoke(app, [
            "apply",
            "--best-practice-ids", "readme",
            "--repo-urls-file", "/nonexistent/file.txt"
        ])
        assert any(phrase in result.output.lower() for phrase in [
            "does not exist", "not found", "no such file", "invalid"
        ])
    
    def test_deploy_invalid_directory(self):
        """Test deploy command with invalid directory."""
        result = runner.invoke(app, [
            "deploy",
            "--best-practice-ids", "readme",
            "--repo-dir", "/nonexistent/dir"
        ])
        assert any(phrase in result.output.lower() for phrase in [
            "does not exist", "not found", "no such file", "invalid"
        ])
    
    def test_invalid_command(self):
        """Test invalid command."""
        result = runner.invoke(app, ["nonexistent-command"])
        assert any(phrase in result.output.lower() for phrase in [
            "no such command", "usage:", "invalid"
        ])
    
    def test_models_invalid_tier(self):
        """Test models command with invalid tier value."""
        result = runner.invoke(app, [
            "models", "recommend",
            "--tier", "invalid_tier"
        ])
        assert any(phrase in result.output.lower() for phrase in [
            "invalid value", "invalid choice", "error"
        ])
    
    def test_models_invalid_task(self):
        """Test models command with invalid task value."""
        result = runner.invoke(app, [
            "models", "recommend",
            "--task", "invalid_task"
        ])
        assert any(phrase in result.output.lower() for phrase in [
            "invalid value", "invalid choice", "error"
        ])


class TestDryRunScenarios:
    """Test various dry-run scenarios across commands."""
    
    def test_dry_run_positioning_before_command(self):
        """Test dry-run flag before command."""
        result = runner.invoke(app, ["--dry-run", "list"])
        assert "DRY RUN MODE" in result.output
        assert "Dry run complete. No actions were taken." in result.output
    
    def test_dry_run_positioning_after_command(self):
        """Test dry-run flag after command."""
        result = runner.invoke(app, ["list", "--dry-run"])
        assert "DRY RUN MODE" in result.output
        assert "Dry run complete. No actions were taken." in result.output
    
    def test_dry_run_with_complex_apply_command(self):
        """Test dry-run with complex apply command."""
        result = runner.invoke(app, [
            "apply",
            "--best-practice-ids", "readme",
            "--repo-urls", "https://github.com/octocat/Hello-World",
            "--dry-run"
        ])
        assert "DRY RUN MODE" in result.output
        assert "Dry run complete. No actions were taken." in result.output
    
    def test_dry_run_with_models_subcommand(self):
        """Test dry-run with models subcommand."""
        result = runner.invoke(app, [
            "models", "list",
            "--provider", "anthropic",
            "--dry-run"
        ])
        assert "DRY RUN MODE" in result.output
        assert "Dry run complete. No actions were taken." in result.output
