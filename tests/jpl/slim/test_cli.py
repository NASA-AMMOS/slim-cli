import os
import sys
import tempfile
import unittest
from unittest.mock import mock_open, patch, MagicMock, call
import argparse
import json
import git

# Set test mode environment variable to prevent real API calls
os.environ['SLIM_TEST_MODE'] = 'True'

class MockGitRepo:
    """A test double for git.Repo that prevents actual git operations."""
    
    def __init__(self, *args, **kwargs):
        self.working_tree_dir = "/mock/repo/path"
        self.git = MagicMock()
        self.remotes = {}
        self.index = MagicMock()
        self.head = MagicMock()
        self.head.ref = MagicMock()
    
    def create_remote(self, name, url):
        remote = MagicMock()
        remote.name = name
        remote.url = url
        self.remotes[name] = remote
        return remote
    
    def remote(self, name=None):
        if name in self.remotes:
            return self.remotes[name]
        mock_remote = MagicMock()
        mock_remote.name = name
        return mock_remote

from jpl.slim.cli import (
    repo_file_to_list,
    fetch_relative_file_paths,
    list_practices,
    apply_best_practices,
    deploy_best_practices,
    apply_and_deploy_best_practices,
    create_parser,
    main
)


def test_read_git_remotes():
    # mock content of the file
    mock_file_content = "https://github.com/user/repo1.git\nhttps://github.com/user/repo2.git\nhttps://github.com/user/repo3.git"
    
    # use mock_open to simulate file opening and reading
    # it ensures any function called within the block uses mock_file_content not real file data
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
        mock_console_instance.print.assert_called_once()
    
    @patch('jpl.slim.commands.list_command.fetch_best_practices')
    @patch('jpl.slim.commands.list_command.print')
    def test_list_practices_no_practices(self, mock_print, mock_fetch):
        """Test that list_practices handles the case when no practices are found."""
        # Setup mocks
        mock_fetch.return_value = None
        
        # Create args object
        args = argparse.Namespace()
        
        # Call the function
        from jpl.slim.commands.list_command import handle_command
        handle_command(args)
        
        # Assertions
        mock_fetch.assert_called_once()
        mock_print.assert_called_once_with("No practices found or failed to fetch practices.")


class TestErrorHandling:
    """Tests for error handling in the CLI."""
    
    @patch('argparse.ArgumentParser.parse_args')
    @patch('jpl.slim.cli.setup_logging')
    @patch('sys.exit')
    def test_invalid_logging_level(self, mock_exit, mock_setup_logging, mock_parse_args):
        """Test that the CLI handles invalid logging levels."""
        # Setup
        args = argparse.Namespace()
        args.logging = None
        args.dry_run = False
        
        mock_parse_args.return_value = args
        
        # Call main
        main()
        
        # Assertions
        mock_exit.assert_called_once_with(1)
    
    @patch('argparse.ArgumentParser.parse_args')
    @patch('jpl.slim.cli.setup_logging')
    @patch('argparse.ArgumentParser.print_help')
    def test_no_command_specified(self, mock_print_help, mock_setup_logging, mock_parse_args):
        """Test that the CLI handles the case when no command is specified."""
        # Setup
        args = argparse.Namespace()
        args.logging = 'INFO'
        args.dry_run = False
        # No func attribute, simulating no command specified
        
        mock_parse_args.return_value = args
        
        # Call main
        main()
        
        # Assertions
        mock_print_help.assert_called_once()
    
    @patch('jpl.slim.utils.git_utils.requests.get')
    def test_is_open_source_with_mocked_api(self, mock_get):
        """Test is_open_source function with mocked GitHub API."""
        # Temporarily disable test mode for this test
        original_test_mode = os.environ.get('SLIM_TEST_MODE')
        os.environ['SLIM_TEST_MODE'] = 'False'
        
        try:
            # Setup mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'license': {'spdx_id': 'MIT'}
            }
            mock_get.return_value = mock_response
            
            # Call function
            from jpl.slim.utils.git_utils import is_open_source
            result = is_open_source("https://github.com/user/repo.git")
            
            # Assertions
            assert result is True
            mock_get.assert_called_once()
        finally:
            # Restore original test mode
            if original_test_mode is not None:
                os.environ['SLIM_TEST_MODE'] = original_test_mode
            else:
                del os.environ['SLIM_TEST_MODE']
        # Verify the URL contains the expected path
        args, kwargs = mock_get.call_args
        assert "api.github.com/repos/" in args[0]
        assert "user/repo/license" in args[0]
    
    @patch('jpl.slim.utils.git_utils.requests.get')
    def test_is_open_source_with_test_mode(self, mock_get):
        """Test is_open_source function with test mode enabled."""
        # Setup - ensure SLIM_TEST_MODE is set
        os.environ['SLIM_TEST_MODE'] = 'True'
        
        # Call function without setting up mock response
        # This should not make a real API call due to test mode
        from jpl.slim.utils.git_utils import is_open_source
        result = is_open_source("https://github.com/user/repo.git")
        
        # Assertions
        assert result is True  # In test mode, we assume it's open source
        mock_get.assert_not_called()  # Verify no API call was made
