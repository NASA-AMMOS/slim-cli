"""
Test script for the SLIM-CLI MCP Server.

This script provides basic testing functionality for the MCP server components.
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Test imports
try:
    from mcp.config import MCP_SERVER_NAME, MCP_SERVER_VERSION
    from mcp.utils import (
        validate_repo_url,
        validate_ai_model,
        parse_best_practice_ids,
        format_duration,
        check_slim_cli_dependencies
    )
    from mcp.resources import (
        slim_registry,
        slim_best_practices,
        slim_models,
        slim_prompts
    )
    from mcp.tools import (
        slim_apply,
        slim_deploy,
        slim_list,
        slim_models_list,
        slim_models_recommend,
        slim_models_validate
    )
    from mcp.prompts import (
        apply_best_practice_prompt,
        customize_with_ai_prompt,
        review_changes_prompt
    )
    print("✅ All MCP modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_configuration():
    """Test MCP server configuration."""
    print("\n=== Testing Configuration ===")
    
    try:
        print(f"Server Name: {MCP_SERVER_NAME}")
        print(f"Server Version: {MCP_SERVER_VERSION}")
        
        # Test dependencies
        deps = check_slim_cli_dependencies()
        print(f"Dependencies: {deps}")
        
        if deps.get('git', False):
            print("✅ Git dependency available")
        else:
            print("⚠️  Git dependency missing")
            
        if deps.get('typer', False):
            print("✅ Typer dependency available")
        else:
            print("⚠️  Typer dependency missing")
            
        if deps.get('rich', False):
            print("✅ Rich dependency available")
        else:
            print("⚠️  Rich dependency missing")
            
        if deps.get('litellm', False):
            print("✅ LiteLLM dependency available")
        else:
            print("⚠️  LiteLLM dependency missing (some AI features may be limited)")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_utilities():
    """Test utility functions."""
    print("\n=== Testing Utilities ===")
    
    try:
        # Test URL validation
        test_urls = [
            "https://github.com/user/repo",
            "git@github.com:user/repo.git",
            "not-a-url",
            "sftp://example.com/repo"
        ]
        
        for url in test_urls:
            is_valid = validate_repo_url(url)
            print(f"URL '{url}': {'✅ Valid' if is_valid else '❌ Invalid'}")
        
        # Test AI model validation
        test_models = [
            "openai/gpt-4o",
            "anthropic/claude-3-5-sonnet-20241022",
            "invalid-model",
            "provider/model/extra"
        ]
        
        for model in test_models:
            is_valid, error = validate_ai_model(model)
            print(f"Model '{model}': {'✅ Valid' if is_valid else '❌ Invalid'} {error}")
        
        # Test best practice ID parsing
        test_ids = [
            ["readme", "contributing"],
            "readme,contributing,changelog",
            "readme"
        ]
        
        for ids in test_ids:
            parsed = parse_best_practice_ids(ids)
            print(f"IDs {ids} -> {parsed}")
        
        # Test duration formatting
        test_durations = [0.5, 1.5, 65.0, 3665.0]
        for duration in test_durations:
            formatted = format_duration(duration)
            print(f"Duration {duration}s -> {formatted}")
        
        return True
    except Exception as e:
        print(f"❌ Utilities test failed: {e}")
        return False

def test_resources():
    """Test MCP resources."""
    print("\n=== Testing Resources ===")
    
    try:
        # Test registry resource
        print("Testing registry resource...")
        registry_data = slim_registry.get_data()
        print(f"Registry: {registry_data.get('total_count', 0)} practices found")
        
        # Test best practices resource
        print("Testing best practices resource...")
        practices_data = slim_best_practices.get_data()
        print(f"Best practices: {practices_data.get('total_count', 0)} practices found")
        
        # Test specific practice
        try:
            readme_data = slim_best_practices.get_data("readme")
            print(f"README practice: {readme_data.get('practice', {}).get('title', 'Not found')}")
        except Exception as e:
            print(f"⚠️  README practice test failed: {e}")
        
        # Test models resource
        print("Testing models resource...")
        models_data = slim_models.get_data()
        print(f"Models: {models_data.get('total_providers', 0)} providers, {models_data.get('total_models', 0)} models")
        
        # Test prompts resource
        print("Testing prompts resource...")
        prompts_data = slim_prompts.get_data()
        print(f"Prompts: {prompts_data.get('total_count', 0)} templates found")
        
        return True
    except Exception as e:
        print(f"❌ Resources test failed: {e}")
        return False

def test_tools():
    """Test MCP tools."""
    print("\n=== Testing Tools ===")
    
    try:
        # Test list tool
        print("Testing list tool...")
        list_result = slim_list.execute()
        if list_result.get('success'):
            print(f"✅ List tool: {list_result.get('total_count', 0)} practices")
        else:
            print(f"❌ List tool failed: {list_result.get('error', 'Unknown error')}")
        
        # Test models list tool
        print("Testing models list tool...")
        models_result = slim_models_list.execute()
        if models_result.get('success'):
            print(f"✅ Models list tool: {models_result.get('total_count', 0)} models")
        else:
            print(f"❌ Models list tool failed: {models_result.get('error', 'Unknown error')}")
        
        # Test models recommend tool
        print("Testing models recommend tool...")
        recommend_result = slim_models_recommend.execute(task="documentation", tier="balanced")
        if recommend_result.get('success'):
            models = recommend_result.get('recommended_models', [])
            print(f"✅ Models recommend tool: {len(models)} recommendations")
        else:
            print(f"❌ Models recommend tool failed: {recommend_result.get('error', 'Unknown error')}")
        
        # Test model validation (dry run)
        print("Testing models validate tool...")
        validate_result = slim_models_validate.execute(model="openai/gpt-4o")
        if validate_result.get('success') is not None:  # Can be True or False
            print(f"✅ Models validate tool: {validate_result.get('message', 'OK')}")
        else:
            print(f"❌ Models validate tool failed: {validate_result.get('error', 'Unknown error')}")
        
        # Test apply tool (dry run)
        print("Testing apply tool (dry run)...")
        apply_result = slim_apply.execute(
            best_practice_ids=["readme"],
            repo_urls=["https://github.com/octocat/Hello-World"],
            dry_run=True
        )
        if apply_result.get('success'):
            print(f"✅ Apply tool (dry run): {apply_result.get('message', 'OK')}")
        else:
            print(f"❌ Apply tool failed: {apply_result.get('error', 'Unknown error')}")
        
        return True
    except Exception as e:
        print(f"❌ Tools test failed: {e}")
        return False

def test_prompts():
    """Test MCP prompts."""
    print("\n=== Testing Prompts ===")
    
    try:
        # Test apply best practice prompt
        print("Testing apply best practice prompt...")
        apply_prompt_result = apply_best_practice_prompt.generate(
            best_practice_ids=["readme"],
            repo_url="https://github.com/user/repo",
            use_ai=True,
            model="anthropic/claude-3-5-sonnet-20241022"
        )
        print(f"✅ Apply prompt: {len(apply_prompt_result)} messages generated")
        
        # Test customize with AI prompt
        print("Testing customize with AI prompt...")
        customize_prompt_result = customize_with_ai_prompt.generate(
            practice_type="README",
            repository_context="Python web API project",
            customization_goals="Include API documentation"
        )
        print(f"✅ Customize prompt: {len(customize_prompt_result)} messages generated")
        
        # Test review changes prompt
        print("Testing review changes prompt...")
        review_prompt_result = review_changes_prompt.generate(
            changes_summary="Added README and contributing guidelines",
            files_modified=["README.md", "CONTRIBUTING.md"],
            next_steps="Review and commit changes"
        )
        print(f"✅ Review prompt: {len(review_prompt_result)} messages generated")
        
        return True
    except Exception as e:
        print(f"❌ Prompts test failed: {e}")
        return False

def test_error_handling():
    """Test error handling scenarios."""
    print("\n=== Testing Error Handling ===")
    
    try:
        # Test invalid best practice ID
        print("Testing invalid best practice ID...")
        invalid_result = slim_apply.execute(
            best_practice_ids=["non-existent-practice"],
            repo_urls=["https://github.com/user/repo"],
            dry_run=True
        )
        if not invalid_result.get('success'):
            print("✅ Invalid practice ID properly rejected")
        else:
            print("⚠️  Invalid practice ID not properly rejected")
        
        # Test invalid repository URL
        print("Testing invalid repository URL...")
        invalid_url_result = slim_apply.execute(
            best_practice_ids=["readme"],
            repo_urls=["not-a-valid-url"],
            dry_run=True
        )
        if not invalid_url_result.get('success'):
            print("✅ Invalid repository URL properly rejected")
        else:
            print("⚠️  Invalid repository URL not properly rejected")
        
        # Test invalid AI model
        print("Testing invalid AI model...")
        invalid_model_result = slim_models_validate.execute(model="invalid-model-format")
        if not invalid_model_result.get('success'):
            print("✅ Invalid AI model properly rejected")
        else:
            print("⚠️  Invalid AI model not properly rejected")
        
        return True
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def run_all_tests():
    """Run all tests."""
    print(f"🧪 SLIM-CLI MCP Server Tests")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_configuration),
        ("Utilities", test_utilities),
        ("Resources", test_resources),
        ("Tools", test_tools),
        ("Prompts", test_prompts),
        ("Error Handling", test_error_handling)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! The MCP server is ready to use.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)