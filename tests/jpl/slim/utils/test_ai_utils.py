"""
Tests for AI utility functions.
"""

from unittest.mock import patch, MagicMock

from jpl.slim.utils.ai_utils import (
    generate_with_ai,
    construct_prompt,
    generate_ai_content,
    generate_with_model,
    enhance_content,
    validate_model,
    get_model_recommendations
)


class TestAIUtils:
    """Tests for AI utility functions."""

    @patch('jpl.slim.utils.ai_utils.fetch_best_practices')
    @patch('jpl.slim.commands.common.SLIM_REGISTRY_URI', 'https://example.com/registry')
    def test_generate_with_ai_best_practice_not_found(self, mock_fetch_practices):
        """Test using AI when the best practice is not found."""
        # Arrange
        best_practice_alias = 'governance-microtiny' # doesn't exist
        repo_path = '/path/to/repo' # doesn't matter
        template_path = '/path/to/template.md'  # doesn't matter
        model = 'openai/gpt-4o' # doesn't matter
        
        # best_practice_alias doesn't exist in the below
        mock_fetch_practices.return_value = [
        {
          "title": "GOVERNANCE.md",
          "uri": "/slim/docs/guides/governance/governance-model",
          "category": "governance",
          "description": "A governance model template seeking to generalize how most government-sponsored open source projects can expect to operate in the open source arena.",
          "tags": [
            "governance",
            "templates",
            "repository-setup",
            "github",
            "markdown"
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
        }]
        
        # Act
        result = generate_with_ai(best_practice_alias, repo_path, template_path, model)
        
        # Assert
        mock_fetch_practices.assert_called_once()
        assert result is None

    def test_construct_prompt(self):
        """Test constructing a prompt for AI."""
        # Arrange
        template_content = 'Template: [INSERT_NAME_HERE]'
        best_practice = {'title': 'Governance', 'description': 'Governance best practice'}
        reference = 'Reference content'
        comment = 'Additional comment'
        
        # Act
        result = construct_prompt(template_content, best_practice, reference, comment)
        
        # Assert
        assert 'Template: [INSERT_NAME_HERE]' in result
        assert 'Reference content' in result
        assert 'Additional comment' in result

    def test_generate_ai_content_invalid_model_format(self):
        """Test generate_ai_content with invalid model format."""
        # Arrange
        prompt = 'Test prompt'
        model = 'anthropic/claude-0'
        
        # Act
        result = generate_ai_content(prompt, model)
        
        # Assert
        assert result is None


    def test_validate_model_valid(self):
        """Test validate_model with valid model and environment."""
        # Arrange
        model = 'ollama/llama3.1'  # Ollama doesn't require API keys
        
        # Act
        is_valid, error_message = validate_model(model)
        
        # Assert
        assert is_valid is True
        assert error_message == ""

    def test_validate_model_invalid_format(self):
        """Test validate_model with invalid format."""
        # Arrange
        model = 'invalid-format'
        
        # Act
        is_valid, error_message = validate_model(model)
        
        # Assert
        assert is_valid is False
        assert "Invalid model format" in error_message

    @patch.dict('os.environ', {}, clear=True)
    def test_validate_model_missing_api_key(self):
        """Test validate_model with missing API key."""
        # Arrange
        model = 'anthropic/claude-3-5-sonnet-20241022'
        
        # Act
        is_valid, error_message = validate_model(model)
        
        # Assert
        assert is_valid is False
        assert "Missing required environment variables" in error_message
        assert "ANTHROPIC_API_KEY" in error_message

    @patch('jpl.slim.utils.ai_utils.get_prompt_with_context')
    def test_enhance_content_no_prompt(self, mock_get_prompt):
        """Test enhance_content when no prompt is found."""
        # Arrange
        content = "Original content"
        practice_type = "unknown"
        section_name = "unknown"
        model = "openai/gpt-4o"
        
        mock_get_prompt.return_value = None
        
        # Act
        result = enhance_content(content, practice_type, section_name, model)
        
        # Assert
        assert result == content  # Returns original content

    @patch('jpl.slim.utils.ai_utils.get_prompt_with_context')
    @patch('jpl.slim.utils.ai_utils.generate_ai_content')
    def test_enhance_content_ai_fails(self, mock_generate, mock_get_prompt):
        """Test enhance_content when AI generation fails."""
        # Arrange
        content = "Original content"
        practice_type = "docgen"
        section_name = "overview"
        model = "openai/gpt-4o"
        
        mock_get_prompt.return_value = "Enhancement prompt"
        mock_generate.return_value = None  # AI fails
        
        # Act
        result = enhance_content(content, practice_type, section_name, model)
        
        # Assert
        assert result == content  # Returns original content
