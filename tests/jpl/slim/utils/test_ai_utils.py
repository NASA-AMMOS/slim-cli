"""
Tests for AI utility functions.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

# Import the module that will contain the functions (this will fail until implemented)
from jpl.slim.utils.ai_utils import (
    generate_with_ai,
    construct_prompt,
    generate_content,
    generate_with_openai,
    generate_with_azure,
    generate_with_ollama
)


class TestAIUtils:
    """Tests for AI utility functions."""

    @patch('jpl.slim.utils.ai_utils.fetch_best_practices')
    @patch('jpl.slim.utils.ai_utils.create_slim_registry_dictionary')
    @patch('jpl.slim.utils.ai_utils.read_file_content')
    @patch('jpl.slim.utils.ai_utils.fetch_readme')
    @patch('jpl.slim.utils.ai_utils.generate_content')
    @patch('jpl.slim.commands.common.SLIM_REGISTRY_URI', 'https://raw.githubusercontent.com/NASA-AMMOS/slim/refs/heads/main/static/data/slim-registry.json')
    @patch.dict('os.environ', {'SLIM_TEST_MODE': 'False'})
    def test_use_ai_governance(self, mock_generate, mock_fetch_readme, mock_read_file, mock_create_dict, mock_fetch_practices):
        """Test using AI for governance best practice."""
        # Arrange
        best_practice_id = 'SLIM-1.1'
        repo_path = '/path/to/repo'
        template_path = '/path/to/template.md'
        model = 'openai/gpt-4o'
        
        mock_fetch_practices.return_value = [{'title': 'Governance', 'assets': [{'name': 'Governance', 'uri': 'https://example.com/governance.md'}]}]
        mock_create_dict.return_value = {'SLIM-1.1': {'title': 'Governance', 'description': 'Governance best practice'}}
        mock_read_file.return_value = 'Template content'
        mock_fetch_readme.return_value = 'README content'
        mock_generate.return_value = 'AI-generated content'
        
        # Act
        result = generate_with_ai(best_practice_id, repo_path, template_path, model)
        
        # Assert
        mock_fetch_practices.assert_called_once()
        mock_create_dict.assert_called_once()
        mock_read_file.assert_called_once_with(template_path)
        mock_fetch_readme.assert_called_once_with(repo_path)
        mock_generate.assert_called_once()
        assert result == 'AI-generated content'

    @patch('jpl.slim.utils.ai_utils.fetch_best_practices')
    @patch('jpl.slim.utils.ai_utils.create_slim_registry_dictionary')
    @patch('jpl.slim.commands.common.SLIM_REGISTRY_URI', 'https://example.com/registry')
    @patch.dict('os.environ', {'SLIM_TEST_MODE': 'False'})
    def test_use_ai_best_practice_not_found(self, mock_create_dict, mock_fetch_practices):
        """Test using AI when the best practice is not found."""
        # Arrange
        best_practice_id = 'SLIM-999'
        repo_path = '/path/to/repo'
        template_path = '/path/to/template.md'
        model = 'openai/gpt-4o'
        
        mock_fetch_practices.return_value = []
        mock_create_dict.return_value = {}
        
        # Act
        result = generate_with_ai(best_practice_id, repo_path, template_path, model)
        
        # Assert
        mock_fetch_practices.assert_called_once()
        mock_create_dict.assert_called_once()
        assert result is None

    def test_construct_prompt(self):
        """Test constructing a prompt for AI."""
        # Arrange
        template_content = 'Template: INSERT_NAME'
        best_practice = {'title': 'Governance', 'description': 'Governance best practice'}
        reference = 'Reference content'
        comment = 'Additional comment'
        
        # Act
        result = construct_prompt(template_content, best_practice, reference, comment)
        
        # Assert
        assert 'Template: INSERT_NAME' in result
        assert 'Reference content' in result
        assert 'Additional comment' in result

    @patch('jpl.slim.utils.ai_utils.generate_with_openai')
    def test_generate_content_openai(self, mock_generate_openai):
        """Test generating content with OpenAI."""
        # Arrange
        prompt = 'Test prompt'
        model = 'openai/gpt-4o'
        
        mock_generate_openai.return_value = iter(['AI', '-', 'generated', ' ', 'content'])
        
        # Act
        result = generate_content(prompt, model)
        
        # Assert
        mock_generate_openai.assert_called_once_with(prompt, 'gpt-4o')
        assert result == 'AI-generated content'

    @patch('jpl.slim.utils.ai_utils.generate_with_azure')
    def test_generate_content_azure(self, mock_generate_azure):
        """Test generating content with Azure."""
        # Arrange
        prompt = 'Test prompt'
        model = 'azure/gpt-4o'
        
        mock_generate_azure.return_value = 'AI-generated content'
        
        # Act
        result = generate_content(prompt, model)
        
        # Assert
        mock_generate_azure.assert_called_once_with(prompt, 'gpt-4o')
        assert result == 'AI-generated content'

    @patch('jpl.slim.utils.ai_utils.generate_with_ollama')
    def test_generate_content_ollama(self, mock_generate_ollama):
        """Test generating content with Ollama."""
        # Arrange
        prompt = 'Test prompt'
        model = 'ollama/llama3.3'
        
        mock_generate_ollama.return_value = 'AI-generated content'
        
        # Act
        result = generate_content(prompt, model)
        
        # Assert
        mock_generate_ollama.assert_called_once_with(prompt, 'llama3.3')
        assert result == 'AI-generated content'

    def test_generate_content_unsupported_provider(self):
        """Test generating content with an unsupported provider."""
        # Arrange
        prompt = 'Test prompt'
        model = 'unsupported/model'
        
        # Act
        result = generate_content(prompt, model)
        
        # Assert
        assert result is None

    @patch('openai.OpenAI')
    def test_generate_with_openai(self, mock_openai_class):
        """Test generating content with OpenAI."""
        # Arrange
        prompt = 'Test prompt'
        model_name = 'gpt-4o'
        
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_chunk = MagicMock()
        mock_chunk.choices[0].delta.content = 'AI-generated content'
        mock_response.__iter__.return_value = [mock_chunk]
        mock_client.chat.completions.create.return_value = mock_response
        
        # Act
        result = list(generate_with_openai(prompt, model_name))
        
        # Assert
        mock_openai_class.assert_called_once()
        mock_client.chat.completions.create.assert_called_once_with(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )
        assert result == ['AI-generated content']

    @patch('openai.AzureOpenAI')
    @patch('azure.identity.ClientSecretCredential')
    @patch('azure.identity.get_bearer_token_provider')
    @patch.dict('os.environ', {
        'AZURE_TENANT_ID': 'test-tenant-id',
        'AZURE_CLIENT_ID': 'test-client-id',
        'AZURE_CLIENT_SECRET': 'test-client-secret',
        'API_VERSION': 'test-api-version',
        'API_ENDPOINT': 'test-api-endpoint'
    })
    def test_generate_with_azure(self, mock_token_provider, mock_credential, mock_azure_openai_class):
        """Test generating content with Azure."""
        # Arrange
        prompt = 'Test prompt'
        model_name = 'gpt-4o'
        
        # Set up the credential mock
        mock_credential_instance = MagicMock()
        mock_credential.return_value = mock_credential_instance
        
        # Set up the token provider mock
        mock_token_provider_instance = MagicMock()
        mock_token_provider.return_value = mock_token_provider_instance
        
        # Set up the Azure OpenAI client mock
        mock_client = MagicMock()
        mock_azure_openai_class.return_value = mock_client
        
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = 'AI-generated content'
        mock_client.chat.completions.create.return_value = mock_completion
        
        # Act
        result = generate_with_azure(prompt, model_name)
        
        # Assert
        mock_azure_openai_class.assert_called_once()
        mock_client.chat.completions.create.assert_called_once()
        assert result == 'AI-generated content'

    @patch('ollama.chat')
    def test_generate_with_ollama(self, mock_ollama_chat):
        """Test generating content with Ollama."""
        # Arrange
        prompt = 'Test prompt'
        model_name = 'llama3.3'
        
        mock_response = {'message': {'content': 'AI-generated content'}}
        mock_ollama_chat.return_value = mock_response
        
        # Act
        result = generate_with_ollama(prompt, model_name)
        
        # Assert
        mock_ollama_chat.assert_called_once_with(
            model=model_name,
            messages=[{'role': 'user', 'content': prompt}]
        )
        assert result == 'AI-generated content'

    @patch('ollama.chat')
    def test_generate_with_ollama_error(self, mock_ollama_chat):
        """Test generating content with Ollama when an error occurs."""
        # Arrange
        prompt = 'Test prompt'
        model_name = 'llama3.3'
        
        mock_ollama_chat.side_effect = Exception('Ollama error')
        
        # Act
        result = generate_with_ollama(prompt, model_name)
        
        # Assert
        mock_ollama_chat.assert_called_once()
        assert result is None
