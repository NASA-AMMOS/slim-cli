"""
Tests for helper functions in the docgen utils module.
"""

import pytest
from jpl.slim.docgen.utils.helpers import escape_yaml_value


class TestEscapeYamlValue:
    """Test the escape_yaml_value function."""
    
    def test_empty_string(self):
        """Test that empty strings are properly handled."""
        assert escape_yaml_value("") == '""'
        assert escape_yaml_value(None) == '""'
    
    def test_simple_string(self):
        """Test that simple strings without special characters are returned as-is."""
        assert escape_yaml_value("simple") == "simple"
        assert escape_yaml_value("hello world") == "hello world"
    
    def test_title_with_colon(self):
        """Test that title strings with colons are properly quoted."""
        assert escape_yaml_value("Introduction: Getting Started") == '"Introduction: Getting Started"'
        assert escape_yaml_value("Step 1: Install Dependencies") == '"Step 1: Install Dependencies"'
        assert escape_yaml_value("Error: File not found") == '"Error: File not found"'
        assert escape_yaml_value("TODO: Add more tests") == '"TODO: Add more tests"'
    
    def test_yaml_special_cases(self):
        """Test strings that could be misinterpreted as YAML structures."""
        assert escape_yaml_value("key: value") == '"key: value"'
        assert escape_yaml_value("[item1, item2]") == '"[item1, item2]"'
        assert escape_yaml_value("{key: value}") == '"{key: value}"'
        assert escape_yaml_value("@directive") == '"@directive"'
        assert escape_yaml_value("|multiline") == '"|multiline"'
        assert escape_yaml_value(">folded") == '">folded"'
    
    def test_quotes_in_titles(self):
        """Test that titles with quotes are properly escaped."""
        assert escape_yaml_value('The "Best" Practices') == '"The \\"Best\\" Practices"'
        assert escape_yaml_value("User's Guide") == '"User\'s Guide"'
        assert escape_yaml_value('Section: "How to" Guide') == '"Section: \\"How to\\" Guide"'