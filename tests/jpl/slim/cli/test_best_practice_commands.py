"""
Unified best practice command tests using YAML configuration.

This module tests all best practices using commands defined in the YAML configuration file.
It replaces the individual test files with a single parameterized approach that's easy to extend.
"""

import pytest
import tempfile
import os
import yaml
import git
import shutil
from pathlib import Path
from typing import Dict, List, Any, Tuple
from typer.testing import CliRunner
from jpl.slim.cli import app
from tests.conftest import get_test_ai_model

runner = CliRunner()


def create_temp_git_repo(repo_dir: str) -> git.Repo:
    """Create a temporary git repository with initial commit."""
    repo = git.Repo.init(repo_dir)
    # Create initial commit
    readme_path = os.path.join(repo_dir, 'README.md')
    with open(readme_path, 'w') as f:
        f.write('# Test Repository\nThis is a test repository.')
    repo.index.add(['README.md'])
    repo.index.commit('Initial commit')
    return repo


def create_bare_repo_with_remote(working_dir: str, remote_name: str = 'origin') -> Tuple[git.Repo, str]:
    """Create a bare repository and set it up as remote for working directory."""
    # Create bare repository
    bare_repo_dir = tempfile.mkdtemp(suffix='_bare')
    bare_repo = git.Repo.init(bare_repo_dir, bare=True)
    
    # Initialize working repository
    working_repo = create_temp_git_repo(working_dir)
    
    # Add bare repo as remote with specified name
    working_repo.create_remote(remote_name, bare_repo_dir)
    
    return working_repo, bare_repo_dir


def load_test_commands() -> Dict[str, List[str]]:
    """Load test commands from YAML configuration file with support for enabled/disabled toggles."""
    config_file = Path(__file__).parent.parent.parent.parent / "best_practices_test_commands.yaml"
    with open(config_file, 'r') as f:
        raw_config = yaml.safe_load(f)
    
    # Process configuration to extract enabled commands
    enabled_commands = {}
    total_practices = 0
    enabled_practices = 0
    total_commands = 0
    enabled_commands_count = 0
    
    for practice_id, practice_config in raw_config.items():
        total_practices += 1
        
        # Handle backward compatibility - if it's a list, convert to new format
        if isinstance(practice_config, list):
            # Old format: practice_id: [command1, command2, ...]
            practice_enabled = True  # Default to enabled for backward compatibility
            commands = practice_config
        else:
            # New format: practice_id: {enabled: bool, commands: [...]}
            practice_enabled = practice_config.get('enabled', True)  # Default to enabled
            commands = practice_config.get('commands', [])
        
        if not practice_enabled:
            continue  # Skip entire practice if disabled
            
        enabled_practices += 1
        practice_commands = []
        
        for command_config in commands:
            total_commands += 1
            
            # Handle both old format (string) and new format (dict with command/enabled)
            if isinstance(command_config, str):
                # Old format: simple command string
                command = command_config
                command_enabled = True  # Default to enabled for backward compatibility
            else:
                # New format: {command: str, enabled: bool}
                command = command_config.get('command', '')
                command_enabled = command_config.get('enabled', True)  # Default to enabled
            
            if command_enabled and command:
                practice_commands.append(command)
                enabled_commands_count += 1
        
        if practice_commands:  # Only add practice if it has enabled commands
            enabled_commands[practice_id] = practice_commands
    
    # Print summary for debugging
    print(f"\n📊 Test Configuration Summary:")
    print(f"   Practices: {enabled_practices}/{total_practices} enabled")
    print(f"   Commands: {enabled_commands_count}/{total_commands} enabled")
    
    return enabled_commands


def get_all_test_commands() -> List[Tuple[str, str]]:
    """Get all enabled test commands as (practice_id, command) tuples for parameterization."""
    commands_config = load_test_commands()
    test_commands = []
    
    for practice_id, commands in commands_config.items():
        for command in commands:
            test_commands.append((practice_id, command))
    
    if not test_commands:
        print("\n⚠️  No test commands are enabled! Set enabled: true for specific commands in best_practices_test_commands.yaml")
    
    return test_commands


class CommandTestRunner:
    """Handles parsing and executing command templates with proper setup and cleanup."""
    
    def __init__(self):
        self.temp_dirs = []
        self.bare_repo_dirs = []
    
    def cleanup(self):
        """Clean up all temporary resources."""
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        
        for bare_repo_dir in self.bare_repo_dirs:
            if os.path.exists(bare_repo_dir):
                shutil.rmtree(bare_repo_dir, ignore_errors=True)
    
    def parse_and_execute(self, command_template: str) -> Any:
        """Parse command template, set up infrastructure, and execute command."""
        # Create variable substitutions
        substitutions = {}
        
        # Handle temp_dir
        if '{temp_dir}' in command_template:
            temp_dir = tempfile.mkdtemp()
            self.temp_dirs.append(temp_dir)
            substitutions['{temp_dir}'] = temp_dir
        
        # Handle temp_git_repo
        if '{temp_git_repo}' in command_template:
            temp_dir = tempfile.mkdtemp()
            self.temp_dirs.append(temp_dir)
            create_temp_git_repo(temp_dir)
            substitutions['{temp_git_repo}'] = temp_dir
        
        # Handle temp_git_repo_with_remote
        if '{temp_git_repo_with_remote}' in command_template:
            temp_dir = tempfile.mkdtemp()
            self.temp_dirs.append(temp_dir)
            working_repo, bare_repo_dir = create_bare_repo_with_remote(temp_dir)
            self.bare_repo_dirs.append(bare_repo_dir)
            substitutions['{temp_git_repo_with_remote}'] = temp_dir
            
            # For deploy commands, we need to apply the best practice first
            if "deploy" in command_template and "apply-deploy" not in command_template:
                # Extract all best practice IDs from command
                command_parts = command_template.split()
                apply_args = ['apply']
                
                # Add all best practice IDs
                i = 0
                while i < len(command_parts):
                    if command_parts[i] == '--best-practice-ids' and i + 1 < len(command_parts):
                        apply_args.extend(['--best-practice-ids', command_parts[i + 1]])
                        i += 2
                    else:
                        i += 1
                
                # Add the repo directory
                apply_args.extend(['--repo-dir', temp_dir])
                
                # Apply the best practices first
                if len(apply_args) > 1:  # Make sure we have some best practice IDs
                    runner.invoke(app, apply_args)
        
        # Handle custom_remote (must be after temp_git_repo_with_remote)
        if '{custom_remote}' in command_template:
            custom_remote_name = "custom-deploy-server"
            substitutions['{custom_remote}'] = custom_remote_name
            
            # If we have a git repo, update the remote name
            if '{temp_git_repo_with_remote}' in command_template:
                # Find the temp directory we created for the git repo
                repo_dir = substitutions['{temp_git_repo_with_remote}']
                # Remove existing origin remote and add custom remote
                repo = git.Repo(repo_dir)
                if 'origin' in [r.name for r in repo.remotes]:
                    # Get the bare repo URL from origin
                    origin_url = repo.remotes.origin.url
                    # Remove origin and create custom remote
                    repo.delete_remote('origin')
                    repo.create_remote(custom_remote_name, origin_url)
        
        # Handle test_ai_model
        if '{test_ai_model}' in command_template:
            substitutions['{test_ai_model}'] = get_test_ai_model()
        
        # Handle temp_urls_file
        if '{temp_urls_file}' in command_template:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write("https://github.com/octocat/Hello-World\nhttps://github.com/octocat/Spoon-Knife")
                f.flush()
                substitutions['{temp_urls_file}'] = f.name
                self.temp_dirs.append(f.name)  # Track for cleanup
        
        # Apply substitutions
        actual_command = command_template
        for placeholder, value in substitutions.items():
            actual_command = actual_command.replace(placeholder, value)
        
        # Parse command into args, handling quoted strings
        import shlex
        command_parts = shlex.split(actual_command)
        # Remove 'slim' prefix and execute
        args = command_parts[1:]
        
        # Check for AI model availability if command uses AI
        if '--use-ai' in args:
            ai_model_index = args.index('--use-ai') + 1
            if ai_model_index < len(args):
                ai_model = args[ai_model_index]
                model_check = runner.invoke(app, ["models", "validate", ai_model])
                if model_check.exit_code != 0 or "configuration error" in model_check.output:
                    model_name = ai_model.split("/")[-1]
                    pytest.skip(f"Local AI model {ai_model} not available. Install Ollama and pull {model_name}: 'ollama pull {model_name}'")
        
        # Execute command
        result = runner.invoke(app, args)
        return result
    
    def assert_command_success(self, result: Any, command: str):
        """Apply appropriate assertions based on command type and expected outcome."""
        # Determine if this is an error scenario
        is_error_scenario = any(error_indicator in command for error_indicator in [
            "/nonexistent/directory",
            "/nonexistent/file.txt", 
            "/nonexistent/parent/output",
            "random-nonexistent-github12414.com",
            "invalid-git-host.com",
            "--repo-urls https://github.com/octocat/Hello-World\"  # missing best-practice-ids",
            "slim apply --repo-urls"  # missing best-practice-ids completely
        ])
        
        # Special case: docs-website without output-dir
        if "docs-website" in command and "--output-dir" not in command and "/nonexistent/" not in command:
            is_error_scenario = True
        
        if is_error_scenario:
            # For error scenarios, check for appropriate error handling
            if "slim apply --repo-urls https://github.com/octocat/Hello-World" == command.strip():
                # Missing best-practice-ids should show missing option error
                assert any(phrase in result.output.lower() for phrase in [
                    "missing", "required", "error", "missing option"
                ])
            elif "docs-website" in command and "--output-dir" not in command:
                # Missing output-dir should show missing option error  
                assert any(phrase in result.output.lower() for phrase in [
                    "missing", "required", "error", "missing option"
                ])
            elif "/nonexistent/" in command:
                # File/directory not found errors
                if result.exit_code == 0:
                    # Sometimes these are caught and shown as user-friendly messages
                    assert any(phrase in result.output.lower() for phrase in [
                        "does not exist", "not found", "no such file", "error", "invalid"
                    ])
                else:
                    # Exit code should be non-zero for errors
                    assert result.exit_code != 0
            elif "random-nonexistent-github12414.com" in command or "invalid-git-host.com" in command:
                # Network/Git errors should show appropriate messages
                assert any(phrase in result.output.lower() for phrase in [
                    "not found", "clone", "error", "failed", "does not exist", "404", "could not resolve host"
                ])
            else:
                # General error case
                assert result.exit_code != 0 or any(phrase in result.output.lower() for phrase in [
                    "error", "failed", "invalid"
                ])
        else:
            # For success scenarios
            command_type = self._get_command_type(command)
            
            # Check if this is a multiple best practices deploy command (may have partial failures)
            is_multiple_practices_deploy = (
                (command_type == "deploy" or command_type == "apply-deploy") and
                command.count("--best-practice-ids") > 1
            )
            
            if command_type == "deploy" or command_type == "apply-deploy":
                # Deploy and apply-deploy commands should show "Successfully deployed"
                assert "Successfully deployed" in result.output or "Successfully applied and deployed" in result.output
                
                # For multiple practices, some may fail due to commit conflicts - only check overall success
                if not is_multiple_practices_deploy:
                    # Single practice should not have Error/Failed messages
                    assert "Error" not in result.output and "Failed" not in result.output
            else:
                # Apply commands should show "Successfully applied"
                assert "Successfully applied" in result.output or "TEST MODE" in result.output
                # Should not contain error messages in success cases
                assert "Error" not in result.output and "Failed" not in result.output
    
    def _get_command_type(self, command: str) -> str:
        """Determine the command type from the command string."""
        if "apply-deploy" in command:
            return "apply-deploy"
        elif "deploy" in command:
            return "deploy"
        elif "apply" in command:
            return "apply"
        else:
            return "unknown"


class TestBestPractices:
    """Unified test class for all best practices using YAML configuration."""
    
    @pytest.mark.parametrize("practice_id,command", get_all_test_commands() or [pytest.param(None, None, marks=pytest.mark.skip("No tests enabled"))])
    def test_best_practice_scenarios(self, practice_id: str, command: str):
        """Test all scenarios for all best practices using command templates."""
        # Skip if no tests are enabled
        if practice_id is None or command is None:
            pytest.skip("No test commands are enabled in best_practices_test_commands.yaml")
        
        runner_instance = CommandTestRunner()
        
        try:
            result = runner_instance.parse_and_execute(command)
            runner_instance.assert_command_success(result, command)
        finally:
            runner_instance.cleanup()