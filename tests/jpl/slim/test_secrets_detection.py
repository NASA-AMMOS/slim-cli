"""
Tests for the secrets detection best practices module.

This module contains tests for the SLIM-2.1 and SLIM-2.2 best practices implementation.
"""

import os
import unittest
import tempfile
import shutil
import git
import logging
from unittest.mock import patch, MagicMock, call
from pathlib import Path

# Import the class to test
from jpl.slim.best_practices.secrets_detection import SecretsDetection

# Set test mode environment variable
os.environ['SLIM_TEST_MODE'] = 'True'


class TestSecretsDetection(unittest.TestCase):
    """Test suite for the SecretsDetection class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for tests
        self.test_dir = tempfile.mkdtemp()
        
        # Initialize a git repo in the test directory
        self.repo = git.Repo.init(self.test_dir)
        
        # Create dummy README file and commit it
        readme_path = os.path.join(self.test_dir, 'README.md')
        with open(readme_path, 'w') as f:
            f.write('# Test Repository\n\nThis is a test repository.')
        
        self.repo.git.add(A=True)
        self.repo.git.commit('-m', 'Initial commit')
        
        # Create instances for testing
        self.secrets_detection_2_1 = SecretsDetection(
            best_practice_id='SLIM-2.1',
            uri='https://example.com/detect-secrets.yaml',
            title='Secrets Detection',
            description='Implements detect-secrets for scanning repositories'
        )
        
        self.secrets_detection_2_2 = SecretsDetection(
            best_practice_id='SLIM-2.2',
            uri='https://example.com/pre-commit-config.yaml',
            title='Pre-commit',
            description='Implements pre-commit hooks'
        )
        
        # Silence logging during tests
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        """Tear down test fixtures."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
        # Re-enable logging
        logging.disable(logging.NOTSET)

    @patch('jpl.slim.best_practices.secrets_detection.download_and_place_file')
    def test_apply_slim_2_1(self, mock_download):
        """Test applying SLIM-2.1 best practice."""
        # Setup
        mock_download.return_value = os.path.join(self.test_dir, '.github/workflows/detect-secrets.yaml')
        
        # Execute - always use no_prompt=True for automated testing
        result = self.secrets_detection_2_1.apply(self.test_dir, no_prompt=True)
        
        # Assert
        self.assertIsNotNone(result)
        mock_download.assert_called_once_with(
            self.repo, 
            'https://example.com/detect-secrets.yaml', 
            '.github/workflows/detect-secrets.yaml'
        )

    @patch('jpl.slim.best_practices.secrets_detection.download_and_place_file')
    def test_apply_slim_2_2(self, mock_download):
        """Test applying SLIM-2.2 best practice."""
        # Setup
        mock_download.return_value = os.path.join(self.test_dir, '.pre-commit-config.yaml')
        
        # Execute - always use no_prompt=True for automated testing
        result = self.secrets_detection_2_2.apply(self.test_dir, no_prompt=True)
        
        # Assert
        self.assertIsNotNone(result)
        mock_download.assert_called_once_with(
            self.repo, 
            'https://example.com/pre-commit-config.yaml', 
            '.pre-commit-config.yaml'
        )

    @patch('jpl.slim.best_practices.secrets_detection.subprocess.check_call')
    @patch('jpl.slim.best_practices.secrets_detection.download_and_place_file')
    def test_apply_slim_2_1_with_no_prompt(self, mock_download, mock_subprocess):
        """Test SLIM-2.1 with no_prompt flag."""
        # Setup
        mock_download.return_value = os.path.join(self.test_dir, '.github/workflows/detect-secrets.yaml')
        
        # Make sure test mode is disabled to verify no_prompt behavior
        old_test_mode = os.environ.get('SLIM_TEST_MODE')
        os.environ['SLIM_TEST_MODE'] = 'False'
        
        try:
            # Execute
            result = self.secrets_detection_2_1.apply(self.test_dir, no_prompt=True)
            
            # Assert
            self.assertIsNotNone(result)
            mock_subprocess.assert_called_once()
        finally:
            # Restore test mode
            os.environ['SLIM_TEST_MODE'] = old_test_mode

    @patch('jpl.slim.best_practices.secrets_detection.subprocess.check_call')
    @patch('jpl.slim.best_practices.secrets_detection.download_and_place_file')
    def test_apply_slim_2_2_with_no_prompt(self, mock_download, mock_subprocess):
        """Test SLIM-2.2 with no_prompt flag."""
        # Setup
        mock_download.return_value = os.path.join(self.test_dir, '.pre-commit-config.yaml')
        
        # Make sure test mode is disabled to verify no_prompt behavior
        old_test_mode = os.environ.get('SLIM_TEST_MODE')
        os.environ['SLIM_TEST_MODE'] = 'False'
        
        try:
            # Execute
            result = self.secrets_detection_2_2.apply(self.test_dir, no_prompt=True)
            
            # Assert
            self.assertIsNotNone(result)
            self.assertEqual(mock_subprocess.call_count, 2)  # Should call for both pip install and pre-commit install
        finally:
            # Restore test mode
            os.environ['SLIM_TEST_MODE'] = old_test_mode

    def test_deploy(self):
        """Test deploying changes made by the best practice."""
        # First apply a practice with no_prompt=True
        with patch('jpl.slim.best_practices.secrets_detection.download_and_place_file') as mock_download:
            mock_download.return_value = os.path.join(self.test_dir, '.github/workflows/detect-secrets.yaml')
            self.secrets_detection_2_1.apply(self.test_dir, no_prompt=True)
        
        # Then deploy
        result = self.secrets_detection_2_1.deploy(self.test_dir)
        
        # Assert
        self.assertTrue(result)
        
        # Verify the commit message
        latest_commit = self.repo.head.commit
        self.assertIn('detect-secrets', latest_commit.message)


if __name__ == '__main__':
    unittest.main()
