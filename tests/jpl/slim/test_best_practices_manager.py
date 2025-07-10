import pytest
from unittest.mock import patch, MagicMock

# Import the BestPracticeManager directly from the module
from jpl.slim.manager.best_practices_manager import BestPracticeManager
from jpl.slim.best_practices import StandardPractice


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
                    "uri": "https://raw.githubusercontent.com/NASA-AMMOS/slim/main/static/assets/governance/governance-model/GOVERNANCE-TEMPLATE-SMALL-TEAMS.md",
                    "alias": "governance-small"
                },
                {
                    "name": "Governance Template (Medium Teams)",
                    "type": "text/md",
                    "uri": "https://raw.githubusercontent.com/NASA-AMMOS/slim/main/static/assets/governance/governance-model/GOVERNANCE-TEMPLATE-MEDIUM-TEAMS.md",
                    "alias": "governance-medium"
                },
                {
                    "name": "Governance Template (Large Teams)",
                    "type": "text/md",
                    "uri": "https://raw.githubusercontent.com/NASA-AMMOS/slim/main/static/assets/governance/governance-model/GOVERNANCE-TEMPLATE-LARGE-TEAMS.md",
                    "alias": "governance-large"
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
                    "uri": "https://raw.githubusercontent.com/NASA-AMMOS/slim/main/static/assets/software-lifecycle/security/secrets-detection/detect-secrets.yaml",
                    "alias": "secrets-github"
                },
                {
                    "name": "Scan Pre-commit Configuration",
                    "type": "text/yaml",
                    "uri": "https://raw.githubusercontent.com/NASA-AMMOS/slim/main/static/assets/software-lifecycle/security/secrets-detection/pre-commit-config.yml",
                    "alias": "secrets-precommit"
                }
            ]
        }
    ]


@pytest.mark.unit
class TestBestPracticeManager:
    """Tests for the BestPracticeManager class."""

    def test_get_best_practice_returns_governance_practice(self):
        """Test that get_best_practice returns a StandardPractice for governance-small."""
        # Arrange
        registry_dict = create_slim_registry_dictionary()
        manager = BestPracticeManager(registry_dict)
        
        # Act
        practice = manager.get_best_practice("governance-small")
        
        # Assert
        assert practice is not None
        assert isinstance(practice, StandardPractice)
        assert practice.best_practice_id == "governance-small"
        assert practice.title == "GOVERNANCE.md"
        assert practice.uri == "https://raw.githubusercontent.com/NASA-AMMOS/slim/main/static/assets/governance/governance-model/GOVERNANCE-TEMPLATE-SMALL-TEAMS.md"
        assert practice.description == "A governance model template seeking to generalize how most government-sponsored open source projects can expect to operate in the open source arena."

    def test_get_best_practice_returns_none_for_invalid_id(self):
        """Test that get_best_practice returns None for an invalid best practice alias."""
        # Arrange
        registry_dict = create_slim_registry_dictionary()
        manager = BestPracticeManager(registry_dict)
        
        # Act
        practice = manager.get_best_practice("invalid-alias")
        
        # Assert
        assert practice is None

    def test_get_best_practice_handles_multiple_assets(self):
        """Test that get_best_practice can handle practices with multiple assets."""
        # Arrange
        registry_dict = create_slim_registry_dictionary()
        manager = BestPracticeManager(registry_dict)
        
        # Act
        practice1 = manager.get_best_practice("governance-medium")  # Medium teams governance
        practice2 = manager.get_best_practice("governance-large")  # Large teams governance
        practice3 = manager.get_best_practice("governance-small")  # Small teams governance
        practice4 = manager.get_best_practice("secrets-github")
        
        # Assert
        assert practice1 is not None
        assert isinstance(practice1, StandardPractice)
        assert practice1.best_practice_id == "governance-medium"
        assert practice1.title == "GOVERNANCE.md"
        assert practice1.uri == "https://raw.githubusercontent.com/NASA-AMMOS/slim/main/static/assets/governance/governance-model/GOVERNANCE-TEMPLATE-MEDIUM-TEAMS.md"
        assert practice1.description == "A governance model template seeking to generalize how most government-sponsored open source projects can expect to operate in the open source arena."
        
        assert practice2 is not None
        assert isinstance(practice2, StandardPractice)
        assert practice2.best_practice_id == "governance-large"
        assert practice2.title == "GOVERNANCE.md"
        assert practice2.uri == "https://raw.githubusercontent.com/NASA-AMMOS/slim/main/static/assets/governance/governance-model/GOVERNANCE-TEMPLATE-LARGE-TEAMS.md"
        assert practice2.description == "A governance model template seeking to generalize how most government-sponsored open source projects can expect to operate in the open source arena."
        
        assert practice3 is not None
        assert isinstance(practice3, StandardPractice)
        assert practice3.best_practice_id == "governance-small"
        assert practice3.title == "GOVERNANCE.md"
        assert practice3.uri == "https://raw.githubusercontent.com/NASA-AMMOS/slim/main/static/assets/governance/governance-model/GOVERNANCE-TEMPLATE-SMALL-TEAMS.md"
        assert practice3.description == "A governance model template seeking to generalize how most government-sponsored open source projects can expect to operate in the open source arena."
        
        assert practice4 is not None
        from jpl.slim.best_practices.secrets_detection import SecretsDetection
        assert isinstance(practice4, SecretsDetection)
        assert practice4.best_practice_id == "secrets-github"
