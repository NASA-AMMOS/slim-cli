"""
Enhanced unit tests for ai_utils module focusing on new functionality.
"""

import pytest
import os
from unittest.mock import patch, MagicMock

from jpl.slim.utils.ai_utils import (
    enhance_content,
    generate_ai_content,
    generate_with_model,
    validate_model
)


class TestEnhanceContent:
    """Test the enhance_content function."""
    
    @patch('jpl.slim.utils.ai_utils.get_prompt_with_context')
    @patch('jpl.slim.utils.ai_utils.generate_ai_content')
    def test_enhance_content_success(self, mock_generate, mock_get_prompt):
        """Test successful content enhancement."""
        # Setup mocks
        mock_get_prompt.return_value = "Enhance this content: {content}"
        mock_generate.return_value = "Enhanced content"
        
        # Test
        result = enhance_content(
            content="Original content",
            practice_type="docgen",
            section_name="overview",
            model="openai/gpt-4o"
        )
        
        # Verify
        assert result == "Enhanced content"
        mock_get_prompt.assert_called_once_with("docgen", "overview", None)
        mock_generate.assert_called_once()
    
    @patch('jpl.slim.utils.ai_utils.get_prompt_with_context')
    @patch('jpl.slim.utils.ai_utils.generate_ai_content')
    def test_enhance_content_with_additional_context(self, mock_generate, mock_get_prompt):
        """Test content enhancement with additional context."""
        # Setup mocks
        mock_get_prompt.return_value = "Context + prompt"
        mock_generate.return_value = "Enhanced content"
        
        # Test
        result = enhance_content(
            content="Original content",
            practice_type="docgen",
            section_name="overview",
            model="openai/gpt-4o",
            additional_context="Extra context"
        )
        
        # Verify
        assert result == "Enhanced content"
        mock_get_prompt.assert_called_once_with("docgen", "overview", "Extra context")
    
    @patch('jpl.slim.utils.ai_utils.get_prompt_with_context')
    def test_enhance_content_no_prompt(self, mock_get_prompt):
        """Test content enhancement when no prompt is found."""
        # Setup mocks
        mock_get_prompt.return_value = None
        
        # Test
        result = enhance_content(
            content="Original content",
            practice_type="docgen",
            section_name="nonexistent",
            model="openai/gpt-4o"
        )
        
        # Should return original content
        assert result == "Original content"
    
    @patch('jpl.slim.utils.ai_utils.get_prompt_with_context')
    @patch('jpl.slim.utils.ai_utils.generate_ai_content')
    def test_enhance_content_generation_fails(self, mock_generate, mock_get_prompt):
        """Test content enhancement when AI generation fails."""
        # Setup mocks
        mock_get_prompt.return_value = "Some prompt"
        mock_generate.return_value = None
        
        # Test
        result = enhance_content(
            content="Original content",
            practice_type="docgen",
            section_name="overview",
            model="openai/gpt-4o"
        )
        
        # Should return original content
        assert result == "Original content"
    
    @patch('jpl.slim.utils.ai_utils.get_prompt_with_context')
    def test_enhance_content_exception(self, mock_get_prompt):
        """Test content enhancement when an exception occurs."""
        # Setup mocks
        mock_get_prompt.side_effect = Exception("Test error")
        
        # Test
        result = enhance_content(
            content="Original content",
            practice_type="docgen",
            section_name="overview",
            model="openai/gpt-4o"
        )
        
        # Should return original content
        assert result == "Original content"


class TestGenerateAiContent:
    """Test the generate_ai_content function."""
    
    def test_generate_ai_content_invalid_model_format(self):
        """Test generate_ai_content with invalid model format."""
        result = generate_ai_content("test prompt", "invalid-model")
        assert result is None
    
    @patch('jpl.slim.utils.ai_utils.generate_with_model')
    def test_generate_ai_content_success(self, mock_generate):
        """Test successful AI content generation."""
        mock_generate.return_value = "Generated content"
        
        result = generate_ai_content("test prompt", "openai/gpt-4o")
        
        assert result == "Generated content"
        mock_generate.assert_called_once_with("test prompt", "openai/gpt-4o")
    
    @patch('jpl.slim.utils.ai_utils.generate_with_model')
    @patch('jpl.slim.utils.ai_utils.generate_with_openai')
    def test_generate_ai_content_fallback_to_openai(self, mock_openai, mock_generate):
        """Test fallback to OpenAI when primary method fails."""
        # Setup mocks
        mock_generate.side_effect = Exception("Primary failed")
        mock_openai.return_value = iter(["Generated", " content"])
        
        result = generate_ai_content("test prompt", "openai/gpt-4o")
        
        assert result == "Generated content"
    
    @patch('jpl.slim.utils.ai_utils.generate_with_model')
    @patch('jpl.slim.utils.ai_utils.generate_with_azure')
    def test_generate_ai_content_fallback_to_azure(self, mock_azure, mock_generate):
        """Test fallback to Azure when primary method fails."""
        # Setup mocks
        mock_generate.side_effect = Exception("Primary failed")
        mock_azure.return_value = "Generated content"
        
        result = generate_ai_content("test prompt", "azure/gpt-4o")
        
        assert result == "Generated content"
    
    @patch('jpl.slim.utils.ai_utils.generate_with_model')
    @patch('jpl.slim.utils.ai_utils.generate_with_ollama')
    def test_generate_ai_content_fallback_to_ollama(self, mock_ollama, mock_generate):
        """Test fallback to Ollama when primary method fails."""
        # Setup mocks
        mock_generate.side_effect = Exception("Primary failed")
        mock_ollama.return_value = "Generated content"
        
        result = generate_ai_content("test prompt", "ollama/llama3")
        
        assert result == "Generated content"
    
    @patch('jpl.slim.utils.ai_utils.generate_with_model')
    def test_generate_ai_content_unsupported_provider(self, mock_generate):
        """Test handling of unsupported provider."""
        mock_generate.side_effect = Exception("Primary failed")
        
        result = generate_ai_content("test prompt", "unsupported/model")
        
        assert result is None


class TestGenerateWithModel:
    """Test the generate_with_model function."""
    
    @patch('jpl.slim.utils.ai_utils.completion')
    def test_generate_with_model_success(self, mock_completion):
        """Test successful model generation."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated content"
        mock_completion.return_value = mock_response
        
        with patch('jpl.slim.utils.ai_utils.completion', mock_completion):
            result = generate_with_model("test prompt", "openai/gpt-4o")
        
        assert result == "Generated content"
    
    @patch('jpl.slim.utils.ai_utils.completion')
    def test_generate_with_model_no_content(self, mock_completion):
        """Test model generation with no content returned."""
        # Setup mock response with no choices
        mock_response = MagicMock()
        mock_response.choices = []
        mock_completion.return_value = mock_response
        
        with patch('jpl.slim.utils.ai_utils.completion', mock_completion):
            result = generate_with_model("test prompt", "openai/gpt-4o")
        
        assert result is None
    
    def test_generate_with_model_import_error(self):
        """Test model generation when LiteLLM is not available."""
        with patch('jpl.slim.utils.ai_utils.completion', side_effect=ImportError()):
            result = generate_with_model("test prompt", "openai/gpt-4o")
        
        assert result is None
    
    @patch('jpl.slim.utils.ai_utils.completion')
    def test_generate_with_model_exception(self, mock_completion):
        """Test model generation when an exception occurs."""
        mock_completion.side_effect = Exception("Test error")
        
        with patch('jpl.slim.utils.ai_utils.completion', mock_completion):
            result = generate_with_model("test prompt", "openai/gpt-4o")
        
        assert result is None
    
    @patch('jpl.slim.utils.ai_utils.completion')
    def test_generate_with_model_custom_params(self, mock_completion):
        """Test model generation with custom parameters."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated content"
        mock_completion.return_value = mock_response
        
        with patch('jpl.slim.utils.ai_utils.completion', mock_completion):
            result = generate_with_model(
                "test prompt", 
                "openai/gpt-4o",
                temperature=0.8,
                max_tokens=2048
            )
        
        assert result == "Generated content"
        
        # Verify parameters were passed
        call_args = mock_completion.call_args[1]
        assert call_args["temperature"] == 0.8
        assert call_args["max_tokens"] == 2048


class TestValidateModel:
    """Test the validate_model function."""
    
    def test_validate_model_invalid_format(self):
        """Test model validation with invalid format."""
        is_valid, error = validate_model("invalid-model")
        assert not is_valid
        assert "Invalid model format" in error
    
    def test_validate_model_openai_missing_key(self):
        """Test OpenAI model validation with missing API key."""
        with patch.dict(os.environ, {}, clear=True):
            is_valid, error = validate_model("openai/gpt-4o")
            assert not is_valid
            assert "OPENAI_API_KEY" in error
    
    def test_validate_model_openai_with_key(self):
        """Test OpenAI model validation with API key present."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            is_valid, error = validate_model("openai/gpt-4o")
            assert is_valid
            assert error == ""
    
    def test_validate_model_azure_missing_keys(self):
        """Test Azure model validation with missing keys."""
        with patch.dict(os.environ, {}, clear=True):
            is_valid, error = validate_model("azure/gpt-4o")
            assert not is_valid
            assert "AZURE_API_KEY" in error
            assert "AZURE_API_BASE" in error
            assert "AZURE_API_VERSION" in error
    
    def test_validate_model_azure_with_keys(self):
        """Test Azure model validation with all keys present."""
        env_vars = {
            "AZURE_API_KEY": "test-key",
            "AZURE_API_BASE": "https://test.openai.azure.com/",
            "AZURE_API_VERSION": "2024-02-01"
        }
        with patch.dict(os.environ, env_vars):
            is_valid, error = validate_model("azure/gpt-4o")
            assert is_valid
            assert error == ""
    
    def test_validate_model_ollama_no_key_required(self):
        """Test Ollama model validation (no API key required)."""
        with patch.dict(os.environ, {}, clear=True):
            is_valid, error = validate_model("ollama/llama3")
            assert is_valid
            assert error == ""
    
    def test_validate_model_anthropic_missing_key(self):
        """Test Anthropic model validation with missing API key."""
        with patch.dict(os.environ, {}, clear=True):
            is_valid, error = validate_model("anthropic/claude-3-5-sonnet-20241022")
            assert not is_valid
            assert "ANTHROPIC_API_KEY" in error
    
    def test_validate_model_anthropic_with_key(self):
        """Test Anthropic model validation with API key present."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            is_valid, error = validate_model("anthropic/claude-3-5-sonnet-20241022")
            assert is_valid
            assert error == ""
    
    def test_validate_model_unknown_provider(self):
        """Test validation of unknown provider."""
        with patch.dict(os.environ, {}, clear=True):
            is_valid, error = validate_model("unknown/model")
            assert is_valid  # Unknown providers have no requirements by default
            assert error == ""


class TestLegacyFunctions:
    """Test legacy function aliases."""
    
    @patch('jpl.slim.utils.ai_utils.generate_ai_content')
    def test_generate_content_legacy_alias(self, mock_generate_ai):
        """Test that generate_content is an alias for generate_ai_content."""
        from jpl.slim.utils.ai_utils import generate_content
        
        mock_generate_ai.return_value = "Generated content"
        
        result = generate_content("test prompt", "openai/gpt-4o")
        
        assert result == "Generated content"
        mock_generate_ai.assert_called_once_with("test prompt", "openai/gpt-4o")
    
    @patch('jpl.slim.utils.ai_utils.generate_with_model')
    def test_generate_with_litellm_legacy_alias(self, mock_generate_with_model):
        """Test that generate_with_litellm is an alias for generate_with_model."""
        from jpl.slim.utils.ai_utils import generate_with_litellm
        
        mock_generate_with_model.return_value = "Generated content"
        
        result = generate_with_litellm("test prompt", "openai/gpt-4o")
        
        assert result == "Generated content"
        mock_generate_with_model.assert_called_once_with("test prompt", "openai/gpt-4o")
    
    @patch('jpl.slim.utils.ai_utils.validate_model')
    def test_validate_model_config_legacy_alias(self, mock_validate_model):
        """Test that validate_model_config is an alias for validate_model."""
        from jpl.slim.utils.ai_utils import validate_model_config
        
        mock_validate_model.return_value = (True, "")
        
        result = validate_model_config("openai/gpt-4o")
        
        assert result == (True, "")
        mock_validate_model.assert_called_once_with("openai/gpt-4o")