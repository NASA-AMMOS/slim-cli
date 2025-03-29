"""
Tests for Git utility functions.
"""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Import the module that will contain the functions (this will fail until implemented)
from jpl.slim.utils.git_utils import (
    generate_git_branch_name,
    deploy_best_practice,
    is_open_source
)


class TestGitUtils:
    """Tests for Git utility functions."""

    def test_generate_git_branch_name_multiple_ids(self):
        """Test generating a Git branch name with multiple best practice IDs."""
        # Arrange
        best_practice_ids = ['SLIM-1.1', 'SLIM-1.2']
        
        # Act
        result = generate_git_branch_name(best_practice_ids)
        
        # Assert
        assert result == 'slim-best-practices'

    def test_generate_git_branch_name_single_id(self):
        """Test generating a Git branch name with a single best practice ID."""
        # Arrange
        best_practice_ids = ['SLIM-1.1']
        
        # Act
        result = generate_git_branch_name(best_practice_ids)
        
        # Assert
        assert result == 'SLIM-1.1'

    def test_generate_git_branch_name_empty(self):
        """Test generating a Git branch name with no best practice IDs."""
        # Arrange
        best_practice_ids = []
        
        # Act
        result = generate_git_branch_name(best_practice_ids)
        
        # Assert
        assert result is None

    @patch('jpl.slim.utils.git_utils.git.Repo')
    def test_deploy_best_practice_success(self, mock_repo_class):
        """Test deploying a best practice successfully."""
        # Arrange
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        
        best_practice_id = 'SLIM-1.1'
        repo_dir = '/path/to/repo'
        remote = 'origin'
        commit_message = 'Add governance documentation'
        
        # Act
        result = deploy_best_practice(
            best_practice_id=best_practice_id,
            repo_dir=repo_dir,
            remote=remote,
            commit_message=commit_message
        )
        
        # Assert
        mock_repo_class.assert_called_once_with(repo_dir)
        mock_repo.git.checkout.assert_called_once_with(best_practice_id)
        mock_repo.git.add.assert_called_once_with(A=True)
        mock_repo.git.commit.assert_called_once_with('-m', commit_message)
        mock_repo.git.push.assert_called_once()
        assert result is True

    @patch('jpl.slim.utils.git_utils.git.Repo')
    def test_deploy_best_practice_git_error(self, mock_repo_class):
        """Test deploying a best practice when a Git error occurs."""
        # Arrange
        mock_repo = MagicMock()
        mock_repo.git.add.side_effect = Exception('Git error')
        mock_repo_class.return_value = mock_repo
        
        best_practice_id = 'SLIM-1.1'
        repo_dir = '/path/to/repo'
        
        # Act
        result = deploy_best_practice(
            best_practice_id=best_practice_id,
            repo_dir=repo_dir
        )
        
        # Assert
        mock_repo_class.assert_called_once_with(repo_dir)
        mock_repo.git.checkout.assert_called_once_with(best_practice_id)
        assert result is False

    @patch('jpl.slim.utils.git_utils.requests.get')
    def test_is_open_source_true(self, mock_get):
        """Test checking if a repository is open source (true case)."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'license': {'spdx_id': 'MIT'}
        }
        mock_get.return_value = mock_response
        
        repo_url = 'https://github.com/user/repo'
        
        # Act
        result = is_open_source(repo_url)
        
        # Assert
        assert result is True

    @patch('jpl.slim.utils.git_utils.requests.get')
    def test_is_open_source_false(self, mock_get):
        """Test checking if a repository is open source (false case)."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'license': {'spdx_id': 'PROPRIETARY'}
        }
        mock_get.return_value = mock_response
        
        repo_url = 'https://github.com/user/repo'
        
        # Act
        result = is_open_source(repo_url)
        
        # Assert
        assert result is False

    @patch('jpl.slim.utils.git_utils.requests.get')
    def test_is_open_source_error(self, mock_get):
        """Test checking if a repository is open source when an error occurs."""
        # Arrange
        mock_get.side_effect = Exception('API error')
        
        repo_url = 'https://github.com/user/repo'
        
        # Act
        result = is_open_source(repo_url)
        
        # Assert
        assert result is False
