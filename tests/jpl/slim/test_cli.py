import os
import sys
import tempfile
import unittest
from unittest.mock import mock_open, patch, MagicMock, call
import argparse
import json
import git # Keep import for type hinting if needed, but Repo is mocked
# Import the function being tested directly where needed
from jpl.slim.commands.apply_command import apply_best_practices, apply_best_practice
from jpl.slim.cli import main, repo_file_to_list, fetch_relative_file_paths
from jpl.slim.utils.git_utils import is_open_source # For testing this specific util
import pytest # Import pytest for raises

# Set test mode environment variable to prevent real API calls
os.environ['SLIM_TEST_MODE'] = 'True'

class MockGitRepo:
    """A test double for git.Repo that prevents actual git operations."""

    def __init__(self, path=None): # Accept path like the real Repo, but ignore it
        _ = path # Mark path as intentionally unused
        self.working_tree_dir = "/mock/repo/path" # Default mock path
        self.git = MagicMock()
        self.remotes = {}
        self.index = MagicMock()
        self.head = MagicMock()
        self.head.ref = MagicMock()
        # Add heads attribute that was missing
        self.heads = MagicMock()
        # Make is_valid_repository check pass
        self.git.rev_parse = MagicMock(return_value=True)

    def create_remote(self, name, url):
        remote = MagicMock()
        remote.name = name
        remote.url = url
        self.remotes[name] = remote
        return remote

    def remote(self, name=None):
        if name in self.remotes:
            return self.remotes[name]
        # Simulate default remote if name is None or not found
        mock_remote = MagicMock()
        mock_remote.name = name if name else "origin"
        mock_remote.url = "mock://url"
        return mock_remote

class TestApplyCommand:
    """Tests for the 'apply' subcommand."""

    # Test direct invocation using a local directory
    @patch('jpl.slim.cli.apply_best_practices') # Patch the function called by main
    def test_apply_command_direct_invocation_local_dir(self, mock_apply):
        """Test direct invocation with existing_repo_dir."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup
            best_practice_ids = ["SLIM-1.1"]
            existing_repo_path = temp_dir

            # Call the function (assuming it's imported or available in scope)
            # Note: This tests the *call* to apply_best_practices, not its internal logic
            # If apply_best_practices is the function *in* cli.py, we call it directly
            # If it's imported *into* cli.py, the patch target might need adjustment
            from jpl.slim.cli import apply_best_practices as cli_apply_func
            cli_apply_func(
                best_practice_ids=best_practice_ids,
                use_ai_flag=False,
                model=None,
                repo_urls=None, # Use local dir
                existing_repo_dir=existing_repo_path,
                target_dir_to_clone_to=None
            )

            # Assertions
            mock_apply.assert_called_once_with(
                best_practice_ids=best_practice_ids,
                use_ai_flag=False,
                model=None,
                repo_urls=None,
                existing_repo_dir=existing_repo_path,
                target_dir_to_clone_to=None
            )

    # Test invocation through main using a local directory
    @patch('argparse.ArgumentParser.parse_args')
    @patch('jpl.slim.cli.apply_best_practices') # Patch the function called by main
    @patch('jpl.slim.cli.setup_logging')
    def test_apply_command_through_main_local_dir(self, mock_setup_logging, mock_apply, mock_parse_args):
        """Test apply command through main using existing_repo_dir."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup
            args = argparse.Namespace()
            args.command = 'apply'
            args.best_practice_ids = ["SLIM-1.1"]
            args.repo_urls = None # Use local dir
            args.repo_urls_file = None
            args.repo_dir = temp_dir # Set local dir path
            args.clone_to_dir = None
            args.use_ai = None
            args.logging = 'INFO'
            args.dry_run = False
            # Import the specific function expected by the lambda
            from jpl.slim.cli import apply_best_practices as cli_apply_func
            args.func = lambda args: cli_apply_func(
                best_practice_ids=args.best_practice_ids,
                use_ai_flag=bool(args.use_ai),
                model=args.use_ai if args.use_ai else None,
                repo_urls=args.repo_urls,
                existing_repo_dir=args.repo_dir,
                target_dir_to_clone_to=args.clone_to_dir
            )

            mock_parse_args.return_value = args

            # Call main
            main()

            # Assertions
            mock_setup_logging.assert_called_once()
            mock_apply.assert_called_once_with(
                best_practice_ids=["SLIM-1.1"],
                use_ai_flag=False,
                model=None,
                repo_urls=None,
                existing_repo_dir=temp_dir,
                target_dir_to_clone_to=None
            )

def test_read_git_remotes():
    # mock content of the file
    mock_file_content = "https://github.com/user/repo1.git\nhttps://github.com/user/repo2.git\nhttps://github.com/user/repo3.git"

    # use mock_open to simulate file opening and reading
    with patch('builtins.open', mock_open(read_data=mock_file_content)):
        # call the function with any file path (it's mocked so doesn't matter)
        result = repo_file_to_list("dummy_path")

        # expected result
        expected_result = [
            "https://github.com/user/repo1.git",
            "https://github.com/user/repo2.git",
            "https://github.com/user/repo3.git"
        ]

        # assert that the function's result matches the expected result
        assert result == expected_result


def test_fetch_relative_file_paths():
    # create a temporary directory structure
    with tempfile.TemporaryDirectory() as temp_dir:
        # create subdirectories and files
        os.makedirs(os.path.join(temp_dir, "src"))
        os.makedirs(os.path.join(temp_dir, "tests"))

        open(os.path.join(temp_dir, "main.py"), 'w').close()
        open(os.path.join(temp_dir, "src", "function1.py"), 'w').close()
        open(os.path.join(temp_dir, "tests", "test_function1.py"), 'w').close()

        # expected relative paths
        expected_paths = sorted([
            "main.py",
            os.path.join("src", "function1.py"),
            os.path.join("tests", "test_function1.py")
        ])

        # call the function
        result = fetch_relative_file_paths(temp_dir)

        # sort and compare results
        assert sorted(result) == expected_paths


class TestListCommand:
    """Tests for the 'list' subcommand."""

    @patch('jpl.slim.commands.list_command.fetch_best_practices')
    @patch('jpl.slim.commands.list_command.create_slim_registry_dictionary')
    @patch('jpl.slim.commands.list_command.Console')
    def test_list_practices_success(self, mock_console, mock_create_dict, mock_fetch):
        """Test that list_practices successfully fetches and displays practices."""
        # Setup mocks
        mock_practices = [{"title": "Test Practice", "description": "Test Description"}]
        mock_fetch.return_value = mock_practices

        mock_asset_mapping = {
            "SLIM-1.1": {
                "title": "Test Practice",
                "description": "Test Description",
                "asset_name": "Test Asset"
            }
        }
        mock_create_dict.return_value = mock_asset_mapping

        mock_console_instance = MagicMock()
        mock_console.return_value = mock_console_instance

        # Create args object
        args = argparse.Namespace()

        # Call the function
        from jpl.slim.commands.list_command import handle_command
        handle_command(args)

        # Assertions
        mock_fetch.assert_called_once()
        mock_create_dict.assert_called_once_with(mock_practices)
        mock_console_instance.print.assert_called_once() # Check if print is called

    @patch('jpl.slim.commands.list_command.fetch_best_practices')
    @patch('jpl.slim.commands.list_command.print') # Patch built-in print if used directly
    def test_list_practices_no_practices(self, mock_print, mock_fetch):
        """Test that list_practices handles the case when no practices are found."""
        # Setup mocks
        mock_fetch.return_value = None # Simulate failure or empty list

        # Create args object
        args = argparse.Namespace()

        # Call the function
        from jpl.slim.commands.list_command import handle_command
        handle_command(args)

        # Assertions
        mock_fetch.assert_called_once()
        # Check if the correct message is printed (adjust if using logger or console)
        mock_print.assert_called_once_with("No practices found or failed to fetch practices.")


class TestErrorHandling:
    """Tests for error handling in the CLI."""

    @patch('argparse.ArgumentParser.parse_args')
    @patch('jpl.slim.cli.setup_logging')
    # No need to mock sys.exit, we expect a ValueError
    def test_invalid_logging_level(self, mock_setup_logging, mock_parse_args):
        """Test that the CLI raises ValueError for invalid logging levels."""
        # Setup args to simulate invalid or missing logging level if setup_logging raises error
        args = argparse.Namespace(command=None, logging='INVALID_LEVEL', dry_run=False) # Example invalid level
        # Simulate setup_logging raising an error for invalid level
        mock_setup_logging.side_effect = ValueError("Unknown level: 'INVALID_LEVEL'")
        mock_parse_args.return_value = args

        # Call main and assert ValueError is raised
        with pytest.raises(ValueError, match="Unknown level: 'INVALID_LEVEL'"):
            main()

        # Assertions
        # Check that setup_logging was called before the exception
        mock_setup_logging.assert_called_once_with('INVALID_LEVEL')
        # No need to check sys.exit anymore


    @patch('argparse.ArgumentParser.parse_args')
    @patch('jpl.slim.cli.setup_logging')
    @patch('argparse.ArgumentParser.print_help') # Mock print_help
    def test_no_command_specified(self, mock_print_help, mock_setup_logging, mock_parse_args):
        """Test that the CLI handles the case when no command is specified."""
        # Setup args without a 'func' attribute or 'command'
        args = argparse.Namespace(logging='INFO', dry_run=False)
        # Ensure 'func' attribute is not present
        if hasattr(args, 'func'):
            delattr(args, 'func')
        if hasattr(args, 'command'):
            delattr(args, 'command')

        mock_parse_args.return_value = args

        # Call main
        main()

        # Assertions
        # Check that setup_logging was called with the correct level
        mock_setup_logging.assert_called_once_with('INFO')
        mock_print_help.assert_called_once() # Expect help to be printed


    # Test is_open_source utility function directly
    @patch('jpl.slim.utils.git_utils.requests.get')
    def test_is_open_source_with_mocked_api(self, mock_get):
        """Test is_open_source function with mocked GitHub API."""
        # Temporarily disable test mode for this specific test
        original_test_mode = os.environ.pop('SLIM_TEST_MODE', None)

        try:
            # Setup mock response for an open-source license
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'license': {'spdx_id': 'MIT'}}
            mock_get.return_value = mock_response

            # Call function
            result = is_open_source("https://github.com/user/repo.git")

            # Assertions
            assert result is True
            mock_get.assert_called_once()
            # Verify the URL structure
            args, kwargs = mock_get.call_args
            assert "api.github.com/repos/user/repo/license" in args[0]

        finally:
            # Restore original test mode if it existed
            if original_test_mode is not None:
                os.environ['SLIM_TEST_MODE'] = original_test_mode


    @patch('jpl.slim.utils.git_utils.requests.get')
    def test_is_open_source_with_test_mode(self, mock_get):
        """Test is_open_source function skips API call in test mode."""
        # Ensure SLIM_TEST_MODE is set
        os.environ['SLIM_TEST_MODE'] = 'True'

        try:
            # Call function
            result = is_open_source("https://github.com/user/repo.git")

            # Assertions
            assert result is True  # In test mode, assumes open source
            mock_get.assert_not_called()  # Verify no API call was made
        finally:
            # Clean up test mode env var if necessary, or leave it if globally set for tests
            pass # Assuming it's set globally for the test suite
