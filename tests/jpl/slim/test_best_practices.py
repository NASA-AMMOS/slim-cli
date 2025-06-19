import pytest
import os
from unittest.mock import patch, MagicMock
from jpl.slim.best_practices.base import BestPractice
import tempfile


class TestBestPracticeBase:
    """Tests for the BestPractice base class."""

    class FakePractice(BestPractice):
        """A fake implementation of BestPractice for testing."""
        
        def apply(self, repo_path, use_ai=False, model=None):
            """Implement abstract method for testing."""
            raise NotImplementedError("This method should not be called in tests")
        
        def deploy(self, repo_path, remote=None, commit_message=None):
            """Implement abstract method for testing."""
            raise NotImplementedError("This method should not be called in tests")


    def test_init_sets_fields_properly(self):
        """Test that constructor sets fields properly."""
        # Arrange
        practice_id = "test-practice"
        uri = "https://example.com/practices/test"
        title = "Test Practice"
        description = "This is a test practice"

        # Act
        practice = self.FakePractice(
            best_practice_id=practice_id,
            uri=uri,
            title=title,
            description=description
        )

        # Assert
        assert practice.best_practice_id == practice_id
        assert practice.uri == uri
        assert practice.title == title
        assert practice.description == description

    def test_apply_not_implemented(self):
        """Test that apply() raises NotImplementedError if not implemented."""
        # Arrange
        practice = self.FakePractice(
            best_practice_id="test",
            uri="https://example.com",
            title="Test",
            description="Test"
        )

        # Act & Assert
        with pytest.raises((NotImplementedError, TypeError)):
            practice.apply(repo_path="test_repo")

    def test_deploy_not_implemented(self):
        """Test that deploy() raises NotImplementedError if not implemented."""
        # Arrange
        practice = self.FakePractice(
            best_practice_id="test",
            uri="https://example.com",
            title="Test",
            description="Test"
        )

        # Act & Assert
        with pytest.raises((NotImplementedError, TypeError)):
            practice.deploy(repo_path="test_repo")


class TestGovernancePractice:
    """Tests for the GovernancePractice class."""

    @patch('jpl.slim.best_practices.standard.git.Repo')
    @patch('jpl.slim.best_practices.standard.download_and_place_file')
    def test_apply_downloads_governance_file(self, mock_download, mock_git_repo):
        """Test that apply() downloads the governance file."""
        # Arrange
        # Import inside the test to avoid circular imports
        from jpl.slim.best_practices.standard import StandardPractice
        mock_download.return_value = "GOVERNANCE.md" # Assuming download_and_place_file returns filename for now
        mock_repo_obj = MagicMock()
        repo_path = tempfile.gettempdir()
        mock_repo_obj.working_tree_dir = repo_path # Set the mock's path attribute to match
        mock_git_repo.return_value = mock_repo_obj # Ensure git.Repo(repo_path) returns this mock
        practice = StandardPractice(
            best_practice_id="governance-small",
            uri="https://raw.githubusercontent.com/NASA-AMMOS/slim/main/static/assets/governance/governance-model/GOVERNANCE-TEMPLATE-SMALL-TEAMS.md",
            title="Governance Practice",
            description="Adds governance documentation"
        )

        # Act
        result = practice.apply(repo_path=repo_path)

        # Assert
        mock_download.assert_called_once()
        assert result is not None
        # The apply method now returns a git.Repo object instead of a string
        assert result == mock_repo_obj

    @patch('jpl.slim.best_practices.standard.git.Repo')
    @patch('jpl.slim.best_practices.standard.download_and_place_file')
    @patch('jpl.slim.best_practices.standard.generate_with_ai')
    @patch('builtins.open', new_callable=MagicMock)
    def test_apply_uses_ai_when_enabled(self, mock_open, mock_use_ai, mock_download, mock_git_repo):
        """Test that apply() uses AI when enabled."""
        # Arrange
        # Import inside the test to avoid circular imports
        from jpl.slim.best_practices.standard import StandardPractice
        mock_download.return_value = "GOVERNANCE.md"
        mock_use_ai.return_value = "AI-generated content"
        mock_repo_obj = MagicMock()
        repo_path = tempfile.gettempdir()
        mock_repo_obj.working_tree_dir = repo_path
        mock_git_repo.return_value = mock_repo_obj
        practice = StandardPractice(
            best_practice_id="governance-small",
            uri="https://raw.githubusercontent.com/NASA-AMMOS/slim/main/static/assets/governance/governance-model/GOVERNANCE-TEMPLATE-SMALL-TEAMS.md",
            title="Governance Practice",
            description="Adds governance documentation"
        )
        
        # Configure the mock_open
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        # Act
        result = practice.apply(repo_path=repo_path, use_ai=True, model="openai/gpt-4o")

        # Assert
        mock_download.assert_called_once()
        mock_use_ai.assert_called_once_with(
            "governance-small",
            repo_path,
            "GOVERNANCE.md",
            "openai/gpt-4o"
        )
        assert result is not None
        # The apply method now returns a git.Repo object instead of a string
        assert result == mock_repo_obj

    @patch('jpl.slim.best_practices.standard.git')
    def test_deploy_commits_and_pushes_changes(self, mock_git):
        """Test that deploy() commits and pushes changes."""
        # Arrange
        # Import inside the test to avoid circular imports
        from jpl.slim.best_practices.standard import StandardPractice
        mock_repo = MagicMock()
        mock_git.Repo.return_value = mock_repo
        practice = StandardPractice(
            best_practice_id="governance-small",
            uri="https://raw.githubusercontent.com/NASA-AMMOS/slim/main/static/assets/governance/governance-model/GOVERNANCE-TEMPLATE-SMALL-TEAMS.md",
            title="Governance Practice",
            description="Adds governance documentation"
        )

        # Act
        result = practice.deploy(
            repo_path="/path/to/repo", 
            remote="origin", 
            commit_message="Add governance documentation"
        )

        # Assert
        assert result is True
        mock_repo.git.add.assert_called_once_with(A=True)
        mock_repo.git.commit.assert_called_once()
        mock_repo.git.push.assert_called_once()
