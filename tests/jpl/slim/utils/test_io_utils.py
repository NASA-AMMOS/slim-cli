"""
Tests for I/O utility functions.
"""

import os
import tempfile
import pytest
import json
from unittest.mock import patch, mock_open, MagicMock

# Import the module that will contain the functions (this will fail until implemented)
from jpl.slim.utils.io_utils import (
    download_and_place_file,
    read_file_content,
    fetch_best_practices,
    fetch_best_practices_from_file,
    repo_file_to_list,
    fetch_relative_file_paths,
    create_slim_registry_dictionary
)


class TestIOUtils:
    """Tests for I/O utility functions."""

    @patch('jpl.slim.utils.io_utils.requests.get')
    def test_download_and_place_file_failure(self, mock_get):
        """Test downloading and placing a file when the request fails."""
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

    def test_read_file_content_error(self):
        """Test reading file content when an error occurs."""
        # Arrange
        with patch('builtins.open', side_effect=IOError('File not found')):
            # Act
            result = read_file_content('nonexistent.txt')
        
        # Assert
        assert result is None

    @patch('jpl.slim.utils.io_utils.requests.get')
    def test_fetch_best_practices_http_error(self, mock_get):
        """Test fetching best practices when HTTP request fails."""
        # Arrange
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        mock_get.return_value = mock_response
        
        url = 'https://example.com/practices.json'
        
        # Act & Assert
        with pytest.raises(Exception, match="HTTP Error"):
            fetch_best_practices(url)

    @patch('jpl.slim.utils.io_utils.requests.get')
    def test_fetch_best_practices_invalid_json(self, mock_get):
        """Test fetching best practices when JSON parsing fails."""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_get.return_value = mock_response
        
        url = 'https://example.com/practices.json'
        
        # Act & Assert
        assert [] == fetch_best_practices(url)

    def test_fetch_best_practices_from_file(self):
        """Test fetching best practices from a file with realistic SLIM registry structure."""
        # Arrange - Mock file content matching slim-registry.json structure
        file_content = json.dumps([
            {
                "title": "Governance.md",
                "uri": "/slim/docs/guides/governance/governance/",
                "category": "governance",
                "description": "A governance model template effective for open source software projects.",
                "tags": ["governance", "templates", "planning"],
                "assets": [
                    {
                        "name": "Governance Small Template",
                        "type": "text/md",
                        "uri": "https://example.com/governance-small.md",
                        "alias": "governance-small"
                    }
                ]
            },
            {
                "title": "Git Secrets",
                "uri": "/slim/docs/guides/software-lifecycle/security/secrets-detection/git-secrets/",
                "category": "software lifecycle",
                "description": "Sets up your local git environment to ensure you don't accidentally commit secrets.",
                "tags": ["cybersecurity", "github", "secrets"],
                "assets": [
                    {
                        "name": "GitHub Git Secrets",
                        "type": "text/md",
                        "uri": "https://example.com/secrets-github.md",
                        "alias": "secrets-github"
                    }
                ]
            }
        ])
        
        # Act
        with patch('builtins.open', mock_open(read_data=file_content)) as mock_file:
            result = fetch_best_practices_from_file('practices.json')
        
        # Assert
        mock_file.assert_called_once_with('practices.json', 'r')
        assert len(result) == 2
        assert result[0]['title'] == 'Governance.md'
        assert result[0]['assets'][0]['alias'] == 'governance-small'
        assert result[1]['assets'][0]['alias'] == 'secrets-github'

    def test_fetch_best_practices_from_file_not_found(self):
        """Test fetching best practices from a non-existent file."""
        # Arrange & Act & Assert
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            with pytest.raises(FileNotFoundError):
                fetch_best_practices_from_file('nonexistent.json')

    def test_fetch_best_practices_from_file_invalid_json(self):
        """Test fetching best practices from a file with invalid JSON."""
        # Arrange
        file_content = "invalid json content"
        
        # Act & Assert
        with patch('builtins.open', mock_open(read_data=file_content)):
            with pytest.raises(json.JSONDecodeError):
                fetch_best_practices_from_file('invalid.json')

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

    def test_repo_file_to_list_file_not_found(self):
        """Test converting a repository file when file doesn't exist."""
        # Arrange & Act & Assert
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            with pytest.raises(FileNotFoundError):
                repo_file_to_list('nonexistent.txt')

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

    def test_create_slim_registry_dictionary(self):
        """Test creating a dictionary from SLIM registry using aliases."""
        # Arrange
        practices = [
            {
                "title": "Governance.md",
                "description": "A governance model template",
                "assets": [
                    {
                        "name": "Governance Small Template",
                        "uri": "https://example.com/governance-small.md",
                        "alias": "governance-small"
                    },
                    {
                        "name": "Governance Large Template",
                        "uri": "https://example.com/governance-large.md",
                        "alias": "governance-large"
                    }
                ]
            },
            {
                "title": "Security Best Practices",
                "description": "Security guidelines",
                "assets": [
                    {
                        "name": "GitHub Secrets Detection",
                        "uri": "https://example.com/secrets.md",
                        "alias": "secrets-github"
                    }
                ]
            },
            {
                "title": "Practice Without Assets",
                "description": "This practice has no assets"
            },
            {
                "title": "Practice With Asset Without Alias",
                "description": "Asset without alias",
                "assets": [
                    {
                        "name": "No Alias Asset",
                        "uri": "https://example.com/no-alias.md"
                    }
                ]
            }
        ]
        
        # Act
        result = create_slim_registry_dictionary(practices)
        
        # Assert
        # Should only include assets with aliases
        assert len(result) == 3
        assert "governance-small" in result
        assert "governance-large" in result
        assert "secrets-github" in result
        
        # Check structure of mapped assets
        assert result["governance-small"]["title"] == "Governance.md"
        assert result["governance-small"]["description"] == "A governance model template"
        assert result["governance-small"]["asset_name"] == "Governance Small Template"
        assert result["governance-small"]["asset_uri"] == "https://example.com/governance-small.md"
        
        assert result["secrets-github"]["title"] == "Security Best Practices"
        assert result["secrets-github"]["asset_name"] == "GitHub Secrets Detection"
