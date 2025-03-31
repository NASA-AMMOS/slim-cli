import pytest
from unittest.mock import patch, MagicMock

# Import the BestPracticeManager directly from the module
from jpl.slim.manager.best_practices_manager import BestPracticeManager
from jpl.slim.best_practices import GovernancePractice, StandardPractice


def create_slim_registry_dictionary():
    """Create a small in-memory registry dictionary for testing."""
    return [
        {
            "title": "GOVERNANCE.md",
            "uri": "/slim/docs/guides/governance/governance-model",
            "category": "governance",
            "description": "A governance model template seeking to generalize how most government-sponsored open source projects can expect to operate in the open source arena.",
            "tags": [
                "governance",
                "templates",
                "repository-setup",
                "github"
            ],
            "assets": [
                {
                    "name": "Governance Template (Small Teams)",
                    "type": "text/md",
                    "uri": "https://raw.githubusercontent.com/NASA-AMMOS/slim/main/static/assets/governance/governance-model/GOVERNANCE-TEMPLATE-SMALL-TEAMS.md"
                },
                {
                    "name": "Governance Template (Medium Teams)",
                    "type": "text/md",
                    "uri": "https://raw.githubusercontent.com/NASA-AMMOS/slim/main/static/assets/governance/governance-model/GOVERNANCE-TEMPLATE-MEDIUM-TEAMS.md"
                },
                {
                    "name": "Governance Template (Large Teams)",
                    "type": "text/md",
                    "uri": "https://raw.githubusercontent.com/NASA-AMMOS/slim/main/static/assets/governance/governance-model/GOVERNANCE-TEMPLATE-LARGE-TEAMS.md"
                }
            ]
        },
        {
            "title": "Secrets Detection",
            "uri": "/slim/docs/guides/software-lifecycle/security/secrets-detection",
            "category": "software lifecycle",
            "description": "Detect-secrets is a security tool that scans code repositories to identify and prevent the accidental inclusion of sensitive information, such as API keys or passwords, by utilizing various detection techniques.",
            "tags": [
                "software-lifecycle",
                "security",
                "testing",
                "tools"
            ],
            "assets": [
                {
                    "name": "GitHub Action Workflow Scan",
                    "type": "text/yaml",
                    "uri": "https://raw.githubusercontent.com/NASA-AMMOS/slim/main/static/assets/software-lifecycle/security/secrets-detection/detect-secrets.yaml"
                },
                {
                    "name": "Scan Pre-commit Configuration",
                    "type": "text/yaml",
                    "uri": "https://raw.githubusercontent.com/NASA-AMMOS/slim/main/static/assets/software-lifecycle/security/secrets-detection/pre-commit-config.yml"
                }
            ]
        }
    ]


class TestBestPracticeManager:
    """Tests for the BestPracticeManager class."""

    def test_get_best_practice_returns_governance_practice(self):
        """Test that get_best_practice returns a GovernancePractice for SLIM-1.1."""
        # Arrange
        registry_dict = create_slim_registry_dictionary()
        manager = BestPracticeManager(registry_dict)
        
        # Act
        practice = manager.get_best_practice("SLIM-1.1")
        
        # Assert
        assert practice is not None
        assert isinstance(practice, StandardPractice)
        assert practice.best_practice_id == "SLIM-1.1"
        assert practice.title == "GOVERNANCE.md"
        assert practice.uri == "https://raw.githubusercontent.com/NASA-AMMOS/slim/main/static/assets/governance/governance-model/GOVERNANCE-TEMPLATE-SMALL-TEAMS.md"
        assert practice.description == "A governance model template seeking to generalize how most government-sponsored open source projects can expect to operate in the open source arena."

    def test_get_best_practice_returns_none_for_invalid_id(self):
        """Test that get_best_practice returns None for an invalid best practice ID."""
        # Arrange
        registry_dict = create_slim_registry_dictionary()
        manager = BestPracticeManager(registry_dict)
        
        # Act
        practice = manager.get_best_practice("INVALID-ID")
        
        # Assert
        assert practice is None

    def test_get_best_practice_handles_multiple_assets(self):
        """Test that get_best_practice can handle practices with multiple assets."""
        # Arrange
        registry_dict = create_slim_registry_dictionary()
        manager = BestPracticeManager(registry_dict)
        
        # Act
        practice = manager.get_best_practice("SLIM-1.2")  # Assuming SLIM-1.2 maps to medium teams
        
        # Assert
        assert practice is not None
        assert isinstance(practice, StandardPractice)
        assert practice.best_practice_id == "SLIM-1.2"
        assert practice.title == "GOVERNANCE.md"
        assert practice.uri == "https://raw.githubusercontent.com/NASA-AMMOS/slim/main/static/assets/governance/governance-model/GOVERNANCE-TEMPLATE-MEDIUM-TEAMS.md"
        assert practice.description == "A governance model template seeking to generalize how most government-sponsored open source projects can expect to operate in the open source arena."
        
    def test_get_best_practice_returns_standard_practice(self):
        """Test that get_best_practice returns a StandardPractice for supported IDs."""
        # Arrange
        registry_dict = create_slim_registry_dictionary()
        manager = BestPracticeManager(registry_dict)
        
        # Act - Add a standard practice ID to the registry for testing
        manager.registry_dict["SLIM-3.1"] = {
            "title": "README.md",
            "description": "A README template", 
            "asset_uri": "https://example.com/readme.md"
        }
        practice = manager.get_best_practice("SLIM-3.1")
        
        # Assert
        assert practice is not None
        assert isinstance(practice, StandardPractice)
        assert practice.best_practice_id == "SLIM-3.1"
