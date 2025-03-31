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

    @patch('jpl.slim.utils.git_utils.requests.get')
    def test_is_open_source_true(self, mock_get):
        """Test checking if a repository is open source (true case)."""
        # Temporarily disable test mode for this test
        original_test_mode = os.environ.get('SLIM_TEST_MODE')
        os.environ['SLIM_TEST_MODE'] = 'False'
        
        try:
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
            mock_get.assert_called_once()
        finally:
            # Restore original test mode
            if original_test_mode is not None:
                os.environ['SLIM_TEST_MODE'] = original_test_mode
            else:
                del os.environ['SLIM_TEST_MODE']

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
