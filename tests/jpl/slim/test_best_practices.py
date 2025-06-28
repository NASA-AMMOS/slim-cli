import pytest
import os
from unittest.mock import patch, MagicMock
from jpl.slim.best_practices.base import BestPractice
import tempfile


@pytest.mark.unit
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
