"""
Tests for I/O utility functions.
"""

import os
import tempfile
import pytest
from unittest.mock import patch, mock_open, MagicMock

# Import the module that will contain the functions (this will fail until implemented)
from jpl.slim.utils.io_utils import (
    download_and_place_file,
    read_file_content,
    fetch_best_practices,
    fetch_best_practices_from_file,
    repo_file_to_list,
    fetch_relative_file_paths
)


class TestIOUtils:
    """Tests for I/O utility functions."""

    @patch('jpl.slim.utils.io_utils.requests.get')
    def test_download_and_place_file(self, mock_get):
        """Test downloading and placing a file."""
        # Temporarily disable test mode for this test
        original_test_mode = os.environ.get('SLIM_TEST_MODE')
        os.environ['SLIM_TEST_MODE'] = 'False'
        
        try:
            # Arrange
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b'file content'
            mock_get.return_value = mock_response
            
            mock_repo = MagicMock()
            mock_repo.working_tree_dir = tempfile.mkdtemp()
            
            url = 'https://example.com/file.md'
            filename = 'file.md'
            
            # Act
            with patch('builtins.open', mock_open()) as mock_file:
                result = download_and_place_file(mock_repo, url, filename)
            
            # Assert
            mock_get.assert_called_once_with(url)
            mock_file.assert_called_once()
            assert result is not None
            assert os.path.basename(result) == filename
        finally:
            # Restore original test mode
            if original_test_mode is not None:
                os.environ['SLIM_TEST_MODE'] = original_test_mode
            else:
                del os.environ['SLIM_TEST_MODE']

    @patch('jpl.slim.utils.io_utils.requests.get')
    def test_download_and_place_file_failure(self, mock_get):
        """Test downloading and placing a file when the request fails."""
        # Temporarily disable test mode for this test
        original_test_mode = os.environ.get('SLIM_TEST_MODE')
        os.environ['SLIM_TEST_MODE'] = 'False'
        
        try:
            # Arrange
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response
            
            mock_repo = MagicMock()
            mock_repo.working_tree_dir = tempfile.mkdtemp()
            
            url = 'https://example.com/file.md'
            filename = 'file.md'
            
            # Act
            result = download_and_place_file(mock_repo, url, filename)
            
            # Assert
            mock_get.assert_called_once_with(url)
            assert result is None
        finally:
            # Restore original test mode
            if original_test_mode is not None:
                os.environ['SLIM_TEST_MODE'] = original_test_mode
            else:
                del os.environ['SLIM_TEST_MODE']

    def test_read_file_content(self):
        """Test reading file content."""
        # Arrange
        file_content = 'file content'
        
        # Act
        with patch('builtins.open', mock_open(read_data=file_content)) as mock_file:
            result = read_file_content('file.txt')
        
        # Assert
        mock_file.assert_called_once_with('file.txt', 'r')
        assert result == file_content

    def test_read_file_content_error(self):
        """Test reading file content when an error occurs."""
        # Arrange
        with patch('builtins.open', side_effect=IOError('File not found')):
            # Act
            result = read_file_content('nonexistent.txt')
        
        # Assert
        assert result is None

    @patch('jpl.slim.utils.io_utils.requests.get')
    def test_fetch_best_practices(self, mock_get):
        """Test fetching best practices from a URL."""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = [{'id': 1, 'title': 'Practice 1'}]
        mock_get.return_value = mock_response
        
        url = 'https://example.com/practices.json'
        
        # Act
        result = fetch_best_practices(url)
        
        # Assert
        mock_get.assert_called_once_with(url)
        mock_response.raise_for_status.assert_called_once()
        assert result == [{'id': 1, 'title': 'Practice 1'}]

    def test_fetch_best_practices_from_file(self):
        """Test fetching best practices from a file."""
        # Arrange
        file_content = '[{"id": 1, "title": "Practice 1"}]'
        
        # Act
        with patch('builtins.open', mock_open(read_data=file_content)) as mock_file:
            result = fetch_best_practices_from_file('practices.json')
        
        # Assert
        mock_file.assert_called_once_with('practices.json', 'r')
        assert result == [{'id': 1, 'title': 'Practice 1'}]

    def test_repo_file_to_list(self):
        """Test converting a repository file to a list."""
        # Arrange
        file_content = 'https://github.com/user/repo1.git\nhttps://github.com/user/repo2.git'
        
        # Act
        with patch('builtins.open', mock_open(read_data=file_content)) as mock_file:
            result = repo_file_to_list('repos.txt')
        
        # Assert
        mock_file.assert_called_once_with('repos.txt', 'r')
        assert result == ['https://github.com/user/repo1.git', 'https://github.com/user/repo2.git']

    def test_fetch_relative_file_paths(self):
        """Test fetching relative file paths."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create subdirectories and files
            os.makedirs(os.path.join(temp_dir, "src"))
            os.makedirs(os.path.join(temp_dir, "tests"))

            open(os.path.join(temp_dir, "main.py"), 'w').close()
            open(os.path.join(temp_dir, "src", "function1.py"), 'w').close()
            open(os.path.join(temp_dir, "tests", "test_function1.py"), 'w').close()

            # Expected relative paths
            expected_paths = sorted([
                "main.py",
                os.path.join("src", "function1.py"),
                os.path.join("tests", "test_function1.py")
            ])

            # Act
            result = fetch_relative_file_paths(temp_dir)

            # Assert
            assert sorted(result) == expected_paths
