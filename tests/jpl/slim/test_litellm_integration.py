"""
Tests for LiteLLM integration.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from jpl.slim.utils.ai_utils import generate_with_litellm, validate_model_config
from jpl.slim.commands.common import check_model_availability, get_recommended_models

class TestLiteLLMIntegration:
    """Test LiteLLM integration functionality."""
    
    @patch('jpl.slim.utils.ai_utils.completion')
    def test_generate_with_litellm_success(self, mock_completion):
        """Test successful generation with LiteLLM."""
        # Mock response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Generated content"
        mock_completion.return_value = mock_response
        
        result = generate_with_litellm("Test prompt", "openai/gpt-4o-mini")
        
        assert result == "Generated content"
        mock_completion.assert_called_once()
    
    def test_model_validation(self):
        """Test model format validation."""
        # Valid formats
        assert validate_model_config("openai/gpt-4o")[0] == True
        assert validate_model_config("anthropic/claude-3-5-sonnet-20241022")[0] == True
        
        # Invalid formats
        assert validate_model_config("invalid-format")[0] == False
        assert validate_model_config("")[0] == False
    
    def test_model_recommendations(self):
        """Test model recommendation system."""
        premium_models = get_recommended_models("documentation", "premium")
        assert len(premium_models) > 0
        assert any("claude" in model for model in premium_models)
        
        fast_models = get_recommended_models("documentation", "fast") 
        assert len(fast_models) > 0
        assert any("groq" in model for model in fast_models)