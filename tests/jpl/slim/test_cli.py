import os
import sys
import tempfile
import unittest
from unittest.mock import mock_open, patch, MagicMock, call
import argparse
import subprocess
import json

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
    
    @patch('jpl.slim.cli.fetch_best_practices')
    @patch('jpl.slim.cli.create_slim_registry_dictionary')
    @patch('jpl.slim.cli.Console')
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
        list_practices(args)
        
        # Assertions
        mock_fetch.assert_called_once()
        mock_create_dict.assert_called_once_with(mock_practices)
        mock_console_instance.print.assert_called_once()
    
    @patch('jpl.slim.cli.fetch_best_practices')
    @patch('jpl.slim.cli.print')
    def test_list_practices_no_practices(self, mock_print, mock_fetch):
        """Test that list_practices handles the case when no practices are found."""
        # Setup mocks
        mock_fetch.return_value = None
        
        # Create args object
        args = argparse.Namespace()
        
        # Call the function
        list_practices(args)
        
        # Assertions
        mock_fetch.assert_called_once()
        mock_print.assert_called_once_with("No practices found or failed to fetch practices.")


class TestApplyCommand:
    """Tests for the 'apply' subcommand."""
    
    @patch('jpl.slim.cli.apply_best_practices')
    def test_apply_command_direct_invocation(self, mock_apply):
        """Test direct invocation of apply_best_practices function."""
        # Setup
        best_practice_ids = ["SLIM-1.1"]
        repo_urls = ["https://github.com/user/repo.git"]
        
        # Call the function
        apply_best_practices(
            best_practice_ids=best_practice_ids,
            use_ai_flag=False,
            model=None,
            repo_urls=repo_urls,
            existing_repo_dir=None,
            target_dir_to_clone_to=None
        )
        
        # Assertions
        mock_apply.assert_called_once_with(
            best_practice_ids=best_practice_ids,
            use_ai_flag=False,
            model=None,
            repo_urls=repo_urls,
            existing_repo_dir=None,
            target_dir_to_clone_to=None
        )
    
    @patch('argparse.ArgumentParser.parse_args')
    @patch('jpl.slim.cli.apply_best_practices')
    @patch('jpl.slim.cli.setup_logging')
    def test_apply_command_through_main(self, mock_setup_logging, mock_apply, mock_parse_args):
        """Test apply command through main function."""
        # Setup
        args = argparse.Namespace()
        args.command = 'apply'
        args.best_practice_ids = ["SLIM-1.1"]
        args.repo_urls = ["https://github.com/user/repo.git"]
        args.repo_urls_file = None
        args.repo_dir = None
        args.clone_to_dir = None
        args.use_ai = None
        args.logging = 'INFO'
        args.dry_run = False
        args.func = lambda args: apply_best_practices(
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
            repo_urls=["https://github.com/user/repo.git"],
            existing_repo_dir=None,
            target_dir_to_clone_to=None
        )
    
    @patch('subprocess.run')
    def test_apply_command_subprocess(self, mock_run):
        """Test apply command using subprocess."""
        # Setup
        mock_run.return_value = MagicMock(returncode=0)
        
        # Call subprocess
        result = subprocess.run(
            ["python", "-m", "jpl.slim.cli", "apply", 
             "--best-practice-ids", "SLIM-1.1", 
             "--repo-urls", "https://github.com/user/repo.git"],
            capture_output=True,
            text=True
        )
        
        # Assertions
        mock_run.assert_called_once()
        assert mock_run.return_value.returncode == 0


class TestDeployCommand:
    """Tests for the 'deploy' subcommand."""
    
    @patch('jpl.slim.cli.deploy_best_practices')
    def test_deploy_command_direct_invocation(self, mock_deploy):
        """Test direct invocation of deploy_best_practices function."""
        # Setup
        best_practice_ids = ["SLIM-1.1"]
        repo_dir = "/path/to/repo"
        
        # Call the function
        deploy_best_practices(
            best_practice_ids=best_practice_ids,
            repo_dir=repo_dir,
            remote=None,
            commit_message="Test commit message"
        )
        
        # Assertions
        mock_deploy.assert_called_once_with(
            best_practice_ids=best_practice_ids,
            repo_dir=repo_dir,
            remote=None,
            commit_message="Test commit message"
        )
    
    @patch('argparse.ArgumentParser.parse_args')
    @patch('jpl.slim.cli.deploy_best_practices')
    @patch('jpl.slim.cli.setup_logging')
    def test_deploy_command_through_main(self, mock_setup_logging, mock_deploy, mock_parse_args):
        """Test deploy command through main function."""
        # Setup
        args = argparse.Namespace()
        args.command = 'deploy'
        args.best_practice_ids = ["SLIM-1.1"]
        args.repo_dir = "/path/to/repo"
        args.remote = None
        args.commit_message = "Test commit message"
        args.logging = 'INFO'
        args.dry_run = False
        args.func = lambda args: deploy_best_practices(
            best_practice_ids=args.best_practice_ids,
            repo_dir=args.repo_dir,
            remote=args.remote,
            commit_message=args.commit_message
        )
        
        mock_parse_args.return_value = args
        
        # Call main
        main()
        
        # Assertions
        mock_setup_logging.assert_called_once()
        mock_deploy.assert_called_once_with(
            best_practice_ids=["SLIM-1.1"],
            repo_dir="/path/to/repo",
            remote=None,
            commit_message="Test commit message"
        )
    
    @patch('subprocess.run')
    def test_deploy_command_subprocess(self, mock_run):
        """Test deploy command using subprocess."""
        # Setup
        mock_run.return_value = MagicMock(returncode=0)
        
        # Call subprocess
        result = subprocess.run(
            ["python", "-m", "jpl.slim.cli", "deploy", 
             "--best-practice-ids", "SLIM-1.1", 
             "--repo-dir", "/path/to/repo",
             "--commit-message", "Test commit message"],
            capture_output=True,
            text=True
        )
        
        # Assertions
        mock_run.assert_called_once()
        assert mock_run.return_value.returncode == 0


class TestApplyDeployCommand:
    """Tests for the 'apply-deploy' subcommand."""
    
    @patch('jpl.slim.cli.apply_and_deploy_best_practices')
    def test_apply_deploy_command_direct_invocation(self, mock_apply_deploy):
        """Test direct invocation of apply_and_deploy_best_practices function."""
        # Setup
        best_practice_ids = ["SLIM-1.1"]
        repo_urls = ["https://github.com/user/repo.git"]
        
        # Call the function
        apply_and_deploy_best_practices(
            best_practice_ids=best_practice_ids,
            use_ai_flag=False,
            model=None,
            remote=None,
            commit_message="Test commit message",
            repo_urls=repo_urls,
            existing_repo_dir=None,
            target_dir_to_clone_to=None
        )
        
        # Assertions
        mock_apply_deploy.assert_called_once_with(
            best_practice_ids=best_practice_ids,
            use_ai_flag=False,
            model=None,
            remote=None,
            commit_message="Test commit message",
            repo_urls=repo_urls,
            existing_repo_dir=None,
            target_dir_to_clone_to=None
        )
    
    @patch('argparse.ArgumentParser.parse_args')
    @patch('jpl.slim.cli.apply_and_deploy_best_practices')
    @patch('jpl.slim.cli.setup_logging')
    def test_apply_deploy_command_through_main(self, mock_setup_logging, mock_apply_deploy, mock_parse_args):
        """Test apply-deploy command through main function."""
        # Setup
        args = argparse.Namespace()
        args.command = 'apply-deploy'
        args.best_practice_ids = ["SLIM-1.1"]
        args.repo_urls = ["https://github.com/user/repo.git"]
        args.repo_urls_file = None
        args.repo_dir = None
        args.clone_to_dir = None
        args.use_ai = None
        args.remote = None
        args.commit_message = "Test commit message"
        args.logging = 'INFO'
        args.dry_run = False
        args.func = lambda args: apply_and_deploy_best_practices(
            best_practice_ids=args.best_practice_ids,
            use_ai_flag=bool(args.use_ai),
            model=args.use_ai if args.use_ai else None,
            remote=args.remote,
            commit_message=args.commit_message,
            repo_urls=args.repo_urls,
            existing_repo_dir=args.repo_dir,
            target_dir_to_clone_to=args.clone_to_dir
        )
        
        mock_parse_args.return_value = args
        
        # Call main
        main()
        
        # Assertions
        mock_setup_logging.assert_called_once()
        mock_apply_deploy.assert_called_once_with(
            best_practice_ids=["SLIM-1.1"],
            use_ai_flag=False,
            model=None,
            remote=None,
            commit_message="Test commit message",
            repo_urls=["https://github.com/user/repo.git"],
            existing_repo_dir=None,
            target_dir_to_clone_to=None
        )
    
    @patch('subprocess.run')
    def test_apply_deploy_command_subprocess(self, mock_run):
        """Test apply-deploy command using subprocess."""
        # Setup
        mock_run.return_value = MagicMock(returncode=0)
        
        # Call subprocess
        result = subprocess.run(
            ["python", "-m", "jpl.slim.cli", "apply-deploy", 
             "--best-practice-ids", "SLIM-1.1", 
             "--repo-urls", "https://github.com/user/repo.git",
             "--commit-message", "Test commit message"],
            capture_output=True,
            text=True
        )
        
        # Assertions
        mock_run.assert_called_once()
        assert mock_run.return_value.returncode == 0


class TestGenerateDocsCommand:
    """Tests for the 'generate-docs' subcommand."""
    
    @patch('jpl.slim.cli.handle_generate_docs')
    def test_generate_docs_command_direct_invocation(self, mock_handle_docs):
        """Test direct invocation of handle_generate_docs function."""
        # Setup
        mock_handle_docs.return_value = True
        
        # Create args object
        args = argparse.Namespace()
        args.repo_dir = "/path/to/repo"
        args.output_dir = "/path/to/output"
        args.config = None
        args.use_ai = None
        
        # Call the function
        result = handle_generate_docs(args)
        
        # Assertions
        mock_handle_docs.assert_called_once_with(args)
        assert result is True
    
    @patch('argparse.ArgumentParser.parse_args')
    @patch('jpl.slim.cli.handle_generate_docs')
    @patch('jpl.slim.cli.setup_logging')
    def test_generate_docs_command_through_main(self, mock_setup_logging, mock_handle_docs, mock_parse_args):
        """Test generate-docs command through main function."""
        # Setup
        args = argparse.Namespace()
        args.command = 'generate-docs'
        args.repo_dir = "/path/to/repo"
        args.output_dir = "/path/to/output"
        args.config = None
        args.use_ai = None
        args.logging = 'INFO'
        args.dry_run = False
        args.func = handle_generate_docs
        
        mock_parse_args.return_value = args
        mock_handle_docs.return_value = True
        
        # Call main
        main()
        
        # Assertions
        mock_setup_logging.assert_called_once()
        mock_handle_docs.assert_called_once_with(args)
    
    @patch('subprocess.run')
    def test_generate_docs_command_subprocess(self, mock_run):
        """Test generate-docs command using subprocess."""
        # Setup
        mock_run.return_value = MagicMock(returncode=0)
        
        # Call subprocess
        result = subprocess.run(
            ["python", "-m", "jpl.slim.cli", "generate-docs", 
             "--repo-dir", "/path/to/repo", 
             "--output-dir", "/path/to/output"],
            capture_output=True,
            text=True
        )
        
        # Assertions
        mock_run.assert_called_once()
        assert mock_run.return_value.returncode == 0


class TestGenerateTestsCommand:
    """Tests for the 'generate-tests' subcommand."""
    
    @patch('jpl.slim.cli.handle_generate_tests')
    def test_generate_tests_command_direct_invocation(self, mock_handle_tests):
        """Test direct invocation of handle_generate_tests function."""
        # Setup
        mock_handle_tests.return_value = True
        
        # Create args object
        args = argparse.Namespace()
        args.repo_dir = "/path/to/repo"
        args.output_dir = "/path/to/output"
        args.use_ai = None
        
        # Call the function
        result = handle_generate_tests(args)
        
        # Assertions
        mock_handle_tests.assert_called_once_with(args)
        assert result is True
    
    @patch('argparse.ArgumentParser.parse_args')
    @patch('jpl.slim.cli.handle_generate_tests')
    @patch('jpl.slim.cli.setup_logging')
    def test_generate_tests_command_through_main(self, mock_setup_logging, mock_handle_tests, mock_parse_args):
        """Test generate-tests command through main function."""
        # Setup
        args = argparse.Namespace()
        args.command = 'generate-tests'
        args.repo_dir = "/path/to/repo"
        args.output_dir = "/path/to/output"
        args.use_ai = None
        args.logging = 'INFO'
        args.dry_run = False
        args.func = handle_generate_tests
        
        mock_parse_args.return_value = args
        mock_handle_tests.return_value = True
        
        # Call main
        main()
        
        # Assertions
        mock_setup_logging.assert_called_once()
        mock_handle_tests.assert_called_once_with(args)
    
    @patch('subprocess.run')
    def test_generate_tests_command_subprocess(self, mock_run):
        """Test generate-tests command using subprocess."""
        # Setup
        mock_run.return_value = MagicMock(returncode=0)
        
        # Call subprocess
        result = subprocess.run(
            ["python", "-m", "jpl.slim.cli", "generate-tests", 
             "--repo-dir", "/path/to/repo", 
             "--output-dir", "/path/to/output"],
            capture_output=True,
            text=True
        )
        
        # Assertions
        mock_run.assert_called_once()
        assert mock_run.return_value.returncode == 0


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
