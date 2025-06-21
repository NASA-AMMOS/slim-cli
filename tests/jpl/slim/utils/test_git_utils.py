"""
Tests for Git utility functions.
"""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock, PropertyMock

# Import the module that will contain the functions (this will fail until implemented)
from jpl.slim.utils.git_utils import (
    generate_git_branch_name,
    clone_repository,
    create_branch,
    extract_git_info,
    is_git_repository,
    get_git_info_summary
)


class TestGitUtils:
    """Tests for Git utility functions."""

    def test_generate_git_branch_name_multiple_ids(self):
        """Test generating a Git branch name with multiple best practice IDs."""
        # Arrange
        best_practice_ids = ['readme', 'secrets-github']
        
        # Act
        result = generate_git_branch_name(best_practice_ids)
        
        # Assert
        assert result == 'slim-best-practices'

    def test_generate_git_branch_name_single_id(self):
        """Test generating a Git branch name with a single best practice ID."""
        # Arrange
        best_practice_ids = ['readme']
        
        # Act
        result = generate_git_branch_name(best_practice_ids)
        
        # Assert
        assert result == 'readme'

    def test_generate_git_branch_name_empty(self):
        """Test generating a Git branch name with no best practice IDs."""
        # Arrange
        best_practice_ids = []
        
        # Act
        result = generate_git_branch_name(best_practice_ids)
        
        # Assert
        assert result is None

    # Tests for clone_repository function
    @patch('jpl.slim.utils.git_utils.git.Repo.clone_from')
    def test_clone_repository_success(self, mock_clone_from):
        """Test successful repository cloning."""
        # Arrange
        mock_repo = MagicMock()
        mock_clone_from.return_value = mock_repo
        repo_url = 'https://github.com/user/repo.git'
        
        # Act
        result = clone_repository(repo_url)
        
        # Assert
        assert result == mock_repo
        mock_clone_from.assert_called_once()

    @patch('jpl.slim.utils.git_utils.git.Repo.clone_from')
    def test_clone_repository_git_command_error(self, mock_clone_from):
        """Test repository cloning with Git command error."""
        # Arrange
        from git.exc import GitCommandError
        mock_clone_from.side_effect = GitCommandError('clone', 'Repository not found')
        repo_url = 'https://github.com/user/nonexistent.git'
        
        # Act
        result = clone_repository(repo_url)
        
        # Assert
        assert result is None

    @patch('jpl.slim.utils.git_utils.git.Repo.clone_from')
    def test_clone_repository_general_exception(self, mock_clone_from):
        """Test repository cloning with general exception."""
        # Arrange
        mock_clone_from.side_effect = Exception('Network error')
        repo_url = 'https://github.com/user/repo.git'
        
        # Act
        result = clone_repository(repo_url)
        
        # Assert
        assert result is None

    # Tests for create_branch function
    def test_create_branch_success_new_branch(self):
        """Test successful branch creation on valid repo."""
        # Arrange
        mock_repo = MagicMock()
        mock_repo.head.is_valid.return_value = True
        mock_repo.heads = {}  # No existing branches
        mock_branch = MagicMock()
        mock_repo.create_head.return_value = mock_branch
        branch_name = 'feature-branch'
        
        # Act
        result = create_branch(mock_repo, branch_name)
        
        # Assert
        assert result == mock_branch
        mock_repo.create_head.assert_called_once_with(branch_name)
        mock_branch.checkout.assert_called_once()

    def test_create_branch_existing_branch(self):
        """Test branch creation when branch already exists."""
        # Arrange
        mock_repo = MagicMock()
        mock_repo.head.is_valid.return_value = True
        mock_branch = MagicMock()
        mock_repo.heads = {'feature-branch': mock_branch}
        branch_name = 'feature-branch'
        
        # Act
        result = create_branch(mock_repo, branch_name)
        
        # Assert
        assert result == mock_branch
        mock_branch.checkout.assert_called_once()

    def test_create_branch_git_command_error(self):
        """Test branch creation with Git command error."""
        # Arrange
        from git.exc import GitCommandError
        mock_repo = MagicMock()
        mock_repo.head.is_valid.return_value = True
        mock_repo.heads = {}
        mock_repo.create_head.side_effect = GitCommandError('create', 'Invalid branch name')
        branch_name = 'invalid@branch'
        
        # Act
        result = create_branch(mock_repo, branch_name)
        
        # Assert
        assert result is None

    def test_create_branch_empty_repo(self):
        """Test branch creation on empty repository."""
        # Arrange
        mock_repo = MagicMock()
        mock_repo.head.is_valid.return_value = False
        mock_repo.working_dir = '/tmp/test_repo'
        mock_branch = MagicMock()
        mock_repo.create_head.return_value = mock_branch
        branch_name = 'main'
        
        with patch('builtins.open', MagicMock()):
            # Act
            result = create_branch(mock_repo, branch_name)
        
        # Assert
        assert result == mock_branch
        mock_repo.index.add.assert_called_once_with(['README.md'])
        mock_repo.index.commit.assert_called_once_with('Initial commit')

    # Tests for extract_git_info function
    @patch('jpl.slim.utils.git_utils.git.Repo')
    def test_extract_git_info_github_success(self, mock_repo_class):
        """Test successful git info extraction from GitHub."""
        # Arrange
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_remote = MagicMock()
        mock_remote.urls = ['https://github.com/user/repo.git']
        mock_repo.remotes = [mock_remote]
        mock_repo.active_branch.name = 'main'
        
        repo_path = '/tmp/test_repo'
        repo_info = {}
        
        # Act
        extract_git_info(repo_path, repo_info)
        
        # Assert
        assert repo_info['org_name'] == 'user'
        assert repo_info['repo_url'] == 'https://github.com/user/repo'
        assert repo_info['default_branch'] == 'main'

    @patch('jpl.slim.utils.git_utils.git.Repo')
    def test_extract_git_info_gitlab_success(self, mock_repo_class):
        """Test successful git info extraction from GitLab."""
        # Arrange
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_remote = MagicMock()
        mock_remote.urls = ['git@gitlab.com:user/project.git']
        mock_repo.remotes = [mock_remote]
        mock_repo.active_branch.name = 'develop'
        
        repo_path = '/tmp/test_repo'
        repo_info = {}
        
        # Act
        extract_git_info(repo_path, repo_info)
        
        # Assert
        assert repo_info['org_name'] == 'user'
        assert repo_info['repo_url'] == 'https://gitlab.com/user/project'
        assert repo_info['default_branch'] == 'develop'

    @patch('jpl.slim.utils.git_utils.git.Repo')
    def test_extract_git_info_detached_head(self, mock_repo_class):
        """Test git info extraction with detached HEAD."""
        # Arrange
        from git.exc import GitCommandError
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_remote = MagicMock()
        mock_remote.urls = ['https://github.com/user/repo.git']
        mock_repo.remotes = [mock_remote]
        
        # Mock active_branch to raise TypeError when accessed
        type(mock_repo).active_branch = PropertyMock(side_effect=TypeError('HEAD is detached'))
        mock_repo.git.symbolic_ref.return_value = 'refs/remotes/origin/main'
        
        repo_path = '/tmp/test_repo'
        repo_info = {}
        
        # Act
        extract_git_info(repo_path, repo_info)
        
        # Assert
        assert repo_info['default_branch'] == 'main'

    @patch('jpl.slim.utils.git_utils.git.Repo')
    def test_extract_git_info_no_remotes(self, mock_repo_class):
        """Test git info extraction with no remotes."""
        # Arrange
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.remotes = []
        mock_repo.active_branch.name = 'main'
        
        repo_path = '/tmp/test_repo'
        repo_info = {}
        
        # Act
        extract_git_info(repo_path, repo_info)
        
        # Assert
        assert 'org_name' not in repo_info
        assert 'repo_url' not in repo_info
        assert repo_info['default_branch'] == 'main'

    @patch('jpl.slim.utils.git_utils.git.Repo')
    def test_extract_git_info_exception(self, mock_repo_class):
        """Test git info extraction with exception."""
        # Arrange
        mock_repo_class.side_effect = Exception('Repository corrupted')
        
        repo_path = '/tmp/test_repo'
        repo_info = {}
        
        # Act
        extract_git_info(repo_path, repo_info)
        
        # Assert
        assert repo_info == {}

    # Tests for is_git_repository function
    @patch('jpl.slim.utils.git_utils.git.Repo')
    def test_is_git_repository_valid(self, mock_repo_class):
        """Test valid git repository detection."""
        # Arrange
        mock_repo_class.return_value = MagicMock()
        repo_path = '/tmp/valid_repo'
        
        # Act
        result = is_git_repository(repo_path)
        
        # Assert
        assert result is True

    @patch('jpl.slim.utils.git_utils.git.Repo')
    def test_is_git_repository_invalid(self, mock_repo_class):
        """Test invalid git repository detection."""
        # Arrange
        from git.exc import InvalidGitRepositoryError
        mock_repo_class.side_effect = InvalidGitRepositoryError('Not a git repository')
        repo_path = '/tmp/not_a_repo'
        
        # Act
        result = is_git_repository(repo_path)
        
        # Assert
        assert result is False

    @patch('jpl.slim.utils.git_utils.git.Repo')
    def test_is_git_repository_no_such_path(self, mock_repo_class):
        """Test git repository detection with non-existent path."""
        # Arrange
        from git.exc import NoSuchPathError
        mock_repo_class.side_effect = NoSuchPathError('Path does not exist')
        repo_path = '/tmp/nonexistent'
        
        # Act
        result = is_git_repository(repo_path)
        
        # Assert
        assert result is False

    # Tests for get_git_info_summary function
    @patch('jpl.slim.utils.git_utils.is_git_repository')
    def test_get_git_info_summary_not_git_repo(self, mock_is_git_repo):
        """Test git info summary for non-git repository."""
        # Arrange
        mock_is_git_repo.return_value = False
        repo_path = '/tmp/not_a_repo'
        
        # Act
        result = get_git_info_summary(repo_path)
        
        # Assert
        assert result is None

    @patch('jpl.slim.utils.git_utils.extract_git_info')
    @patch('jpl.slim.utils.git_utils.is_git_repository')
    def test_get_git_info_summary_success(self, mock_is_git_repo, mock_extract_git_info):
        """Test successful git info summary."""
        # Arrange
        mock_is_git_repo.return_value = True
        
        def mock_extract(repo_path, repo_info):
            repo_info.update({
                'org_name': 'testuser',
                'repo_url': 'https://github.com/testuser/testrepo',
                'default_branch': 'main'
            })
        
        mock_extract_git_info.side_effect = mock_extract
        repo_path = '/tmp/test_repo'
        
        # Act
        result = get_git_info_summary(repo_path)
        
        # Assert
        assert result == {
            'org_name': 'testuser',
            'repo_url': 'https://github.com/testuser/testrepo',
            'default_branch': 'main'
        }
