"""
Unit tests for prompt_utils module.
"""

import pytest
import tempfile
import os
from pathlib import Path
import yaml
from unittest.mock import patch, mock_open

from jpl.slim.utils.prompt_utils import (
    load_prompts,
    clear_prompts_cache,
    get_context_hierarchy,
    get_prompt,
    get_prompt_with_context,
    substitute_variables,
    validate_prompts_file
)


@pytest.fixture
def sample_prompts_data():
    """Sample prompts data for testing."""
    return {
        'context': 'Global context for all practices',
        'docgen': {
            'context': 'Documentation generation context',
            'overview': {
                'context': 'Project overview specific context',
                'prompt': 'Enhance this project overview...'
            },
            'installation': {
                'prompt': 'Improve this installation guide...'
            }
        },
        'standard_practices': {
            'readme': {
                'context': 'README specific context',
                'prompt': 'Fill out the README template...'
            },
            'governance': {
                'prompt': 'Fill out governance template...'
            }
        }
    }


@pytest.fixture
def sample_prompts_file(sample_prompts_data):
    """Create a temporary prompts file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(sample_prompts_data, f)
        yield f.name
    os.unlink(f.name)


class TestLoadPrompts:
    """Test the load_prompts function."""
    
    def test_load_prompts_with_file(self, sample_prompts_file, sample_prompts_data):
        """Test loading prompts from a specific file."""
        clear_prompts_cache()
        result = load_prompts(sample_prompts_file)
        assert result == sample_prompts_data
    
    def test_load_prompts_file_not_found(self):
        """Test handling of missing prompts file."""
        clear_prompts_cache()
        with pytest.raises(FileNotFoundError):
            load_prompts('/nonexistent/prompts.yaml')
    
    def test_load_prompts_caching(self, sample_prompts_file):
        """Test that prompts are cached properly."""
        clear_prompts_cache()
        
        # First load
        result1 = load_prompts(sample_prompts_file)
        
        # Second load should return cached result
        result2 = load_prompts(sample_prompts_file)
        
        assert result1 is result2  # Same object reference
    
    def test_clear_prompts_cache(self, sample_prompts_file):
        """Test clearing the prompts cache."""
        clear_prompts_cache()
        
        # Load prompts
        result1 = load_prompts(sample_prompts_file)
        
        # Clear cache and load again
        clear_prompts_cache()
        result2 = load_prompts(sample_prompts_file)
        
        # Should be different objects but same content
        assert result1 == result2
        assert result1 is not result2


class TestGetContextHierarchy:
    """Test the get_context_hierarchy function."""
    
    def test_context_hierarchy_full_path(self, sample_prompts_file):
        """Test getting context hierarchy with all levels present."""
        clear_prompts_cache()
        
        with patch('jpl.slim.utils.prompt_utils.load_prompts') as mock_load:
            mock_load.return_value = {
                'context': 'Global context',
                'docgen': {
                    'context': 'Docgen context',
                    'overview': {
                        'context': 'Overview context',
                        'prompt': 'Some prompt'
                    }
                }
            }
            
            contexts = get_context_hierarchy('docgen', 'overview')
            expected = ['Global context', 'Docgen context', 'Overview context']
            assert contexts == expected
    
    def test_context_hierarchy_partial_path(self, sample_prompts_file):
        """Test getting context hierarchy with only some levels present."""
        clear_prompts_cache()
        
        with patch('jpl.slim.utils.prompt_utils.load_prompts') as mock_load:
            mock_load.return_value = {
                'context': 'Global context',
                'docgen': {
                    'overview': {
                        'prompt': 'Some prompt'
                        # No context at this level
                    }
                }
            }
            
            contexts = get_context_hierarchy('docgen', 'overview')
            expected = ['Global context']  # Only global context available
            assert contexts == expected
    
    def test_context_hierarchy_no_context(self, sample_prompts_file):
        """Test getting context hierarchy when no context is defined."""
        clear_prompts_cache()
        
        with patch('jpl.slim.utils.prompt_utils.load_prompts') as mock_load:
            mock_load.return_value = {
                'docgen': {
                    'overview': {
                        'prompt': 'Some prompt'
                    }
                }
            }
            
            contexts = get_context_hierarchy('docgen', 'overview')
            assert contexts == []
    
    def test_context_hierarchy_practice_only(self, sample_prompts_file):
        """Test getting context hierarchy for practice type only."""
        clear_prompts_cache()
        
        with patch('jpl.slim.utils.prompt_utils.load_prompts') as mock_load:
            mock_load.return_value = {
                'context': 'Global context',
                'docgen': {
                    'context': 'Docgen context'
                }
            }
            
            contexts = get_context_hierarchy('docgen')
            expected = ['Global context', 'Docgen context']
            assert contexts == expected


class TestGetPrompt:
    """Test the get_prompt function."""
    
    def test_get_prompt_success(self, sample_prompts_file):
        """Test successfully getting a prompt."""
        clear_prompts_cache()
        
        with patch('jpl.slim.utils.prompt_utils.load_prompts') as mock_load:
            mock_load.return_value = {
                'docgen': {
                    'overview': {
                        'prompt': 'Test prompt'
                    }
                }
            }
            
            prompt = get_prompt('docgen', 'overview')
            assert prompt == 'Test prompt'
    
    def test_get_prompt_string_format(self, sample_prompts_file):
        """Test getting a prompt that's stored as a simple string."""
        clear_prompts_cache()
        
        with patch('jpl.slim.utils.prompt_utils.load_prompts') as mock_load:
            mock_load.return_value = {
                'docgen': {
                    'overview': 'Simple string prompt'
                }
            }
            
            prompt = get_prompt('docgen', 'overview')
            assert prompt == 'Simple string prompt'
    
    def test_get_prompt_not_found(self, sample_prompts_file):
        """Test getting a prompt that doesn't exist."""
        clear_prompts_cache()
        
        with patch('jpl.slim.utils.prompt_utils.load_prompts') as mock_load:
            mock_load.return_value = {
                'docgen': {
                    'installation': {
                        'prompt': 'Test prompt'
                    }
                }
            }
            
            prompt = get_prompt('docgen', 'nonexistent')
            assert prompt is None
    
    def test_get_prompt_practice_not_found(self, sample_prompts_file):
        """Test getting a prompt when practice type doesn't exist."""
        clear_prompts_cache()
        
        with patch('jpl.slim.utils.prompt_utils.load_prompts') as mock_load:
            mock_load.return_value = {
                'docgen': {
                    'overview': {'prompt': 'Test prompt'}
                }
            }
            
            prompt = get_prompt('nonexistent', 'overview')
            assert prompt is None


class TestGetPromptWithContext:
    """Test the get_prompt_with_context function."""
    
    def test_get_prompt_with_context_full(self, sample_prompts_file):
        """Test getting prompt with full context hierarchy."""
        clear_prompts_cache()
        
        with patch('jpl.slim.utils.prompt_utils.load_prompts') as mock_load:
            mock_load.return_value = {
                'context': 'Global context',
                'docgen': {
                    'context': 'Docgen context',
                    'overview': {
                        'context': 'Overview context',
                        'prompt': 'Test prompt'
                    }
                }
            }
            
            result = get_prompt_with_context('docgen', 'overview')
            expected = 'Global context\n\nDocgen context\n\nOverview context\n\nTest prompt'
            assert result == expected
    
    def test_get_prompt_with_context_partial(self, sample_prompts_file):
        """Test getting prompt with partial context hierarchy."""
        clear_prompts_cache()
        
        with patch('jpl.slim.utils.prompt_utils.load_prompts') as mock_load:
            mock_load.return_value = {
                'context': 'Global context',
                'docgen': {
                    'overview': {
                        'prompt': 'Test prompt'
                    }
                }
            }
            
            result = get_prompt_with_context('docgen', 'overview')
            expected = 'Global context\n\nTest prompt'
            assert result == expected
    
    def test_get_prompt_with_context_none(self, sample_prompts_file):
        """Test getting prompt with no context."""
        clear_prompts_cache()
        
        with patch('jpl.slim.utils.prompt_utils.load_prompts') as mock_load:
            mock_load.return_value = {
                'docgen': {
                    'overview': {
                        'prompt': 'Test prompt'
                    }
                }
            }
            
            result = get_prompt_with_context('docgen', 'overview')
            assert result == 'Test prompt'
    
    def test_get_prompt_with_additional_context(self, sample_prompts_file):
        """Test getting prompt with additional context."""
        clear_prompts_cache()
        
        with patch('jpl.slim.utils.prompt_utils.load_prompts') as mock_load:
            mock_load.return_value = {
                'context': 'Global context',
                'docgen': {
                    'overview': {
                        'prompt': 'Test prompt'
                    }
                }
            }
            
            result = get_prompt_with_context('docgen', 'overview', 'Additional context')
            expected = 'Global context\n\nAdditional context\n\nTest prompt'
            assert result == expected
    
    def test_get_prompt_with_context_prompt_not_found(self, sample_prompts_file):
        """Test getting prompt with context when prompt doesn't exist."""
        clear_prompts_cache()
        
        with patch('jpl.slim.utils.prompt_utils.load_prompts') as mock_load:
            mock_load.return_value = {
                'docgen': {
                    'installation': {'prompt': 'Test prompt'}
                }
            }
            
            result = get_prompt_with_context('docgen', 'nonexistent')
            assert result is None


class TestSubstituteVariables:
    """Test the substitute_variables function."""
    
    def test_substitute_variables_success(self):
        """Test successful variable substitution."""
        text = "Hello {name}, your project is {status}."
        variables = {'name': 'John', 'status': 'ready'}
        result = substitute_variables(text, variables)
        assert result == "Hello John, your project is ready."
    
    def test_substitute_variables_missing_variable(self):
        """Test variable substitution with missing variable."""
        import warnings
        
        text = "Hello {name}, your project is {status}."
        variables = {'name': 'John'}
        
        # Capture warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = substitute_variables(text, variables)
            
            # Check that a warning was issued
            assert len(w) == 1
            assert "Some variables were not found" in str(w[0].message)
            assert "['status']" in str(w[0].message)
        
        # Should return text with available variables substituted
        expected = "Hello John, your project is {status}."
        assert result == expected
    
    def test_substitute_variables_no_variables(self):
        """Test variable substitution with no variables."""
        text = "Hello world."
        result = substitute_variables(text, {})
        assert result == text
    
    def test_substitute_variables_empty_text(self):
        """Test variable substitution with empty text."""
        result = substitute_variables("", {'name': 'John'})
        assert result == ""
    
    def test_substitute_variables_multiple_missing(self):
        """Test variable substitution with multiple missing variables."""
        import warnings
        
        text = "Hello {name}, your {type} project is {status} at {location}."
        variables = {'name': 'John', 'location': 'NYC'}
        
        # Capture warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = substitute_variables(text, variables)
            
            # Check that a warning was issued
            assert len(w) == 1
            assert "Some variables were not found" in str(w[0].message)
            assert "'type'" in str(w[0].message)
            assert "'status'" in str(w[0].message)
        
        # Should return text with available variables substituted
        expected = "Hello John, your {type} project is {status} at NYC."
        assert result == expected


class TestValidatePromptsFile:
    """Test the validate_prompts_file function."""
    
    def test_validate_prompts_file_valid(self, sample_prompts_file):
        """Test validation of a valid prompts file."""
        clear_prompts_cache()
        errors = validate_prompts_file(sample_prompts_file)
        assert errors == []
    
    def test_validate_prompts_file_invalid_structure(self):
        """Test validation of prompts file with invalid structure."""
        clear_prompts_cache()
        
        with patch('jpl.slim.utils.prompt_utils.load_prompts') as mock_load:
            mock_load.return_value = "not a dictionary"
            
            errors = validate_prompts_file()
            assert len(errors) > 0
            assert "must contain a dictionary" in errors[0]
    
    def test_validate_prompts_file_missing_prompts(self):
        """Test validation of prompts file with missing prompts."""
        clear_prompts_cache()
        
        with patch('jpl.slim.utils.prompt_utils.load_prompts') as mock_load:
            mock_load.return_value = {
                'docgen': {
                    'context': 'Some context',
                    # No actual prompts
                }
            }
            
            errors = validate_prompts_file()
            assert len(errors) > 0
            assert "contains no valid prompts" in errors[0]
    
    def test_validate_prompts_file_invalid_prompt_config(self):
        """Test validation of prompts file with invalid prompt configuration."""
        clear_prompts_cache()
        
        with patch('jpl.slim.utils.prompt_utils.load_prompts') as mock_load:
            mock_load.return_value = {
                'docgen': {
                    'overview': {
                        'context': 'Some context'
                        # Missing 'prompt' key
                    }
                }
            }
            
            errors = validate_prompts_file()
            assert len(errors) > 0
            assert "missing 'prompt' key" in errors[0]