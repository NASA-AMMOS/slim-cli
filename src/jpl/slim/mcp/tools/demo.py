#!/usr/bin/env python3
"""
SLIM-CLI MCP Server Demo

This script demonstrates the capabilities of the SLIM-CLI MCP server
by running various tool operations and showing their results.
"""

import sys
import json
import time
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from mcp.tools import (
    slim_list,
    slim_models_list,
    slim_models_recommend,
    slim_models_validate,
    slim_apply
)
from mcp.resources import (
    slim_registry,
    slim_best_practices,
    slim_models
)
from mcp.prompts import (
    apply_best_practice_prompt,
    customize_with_ai_prompt
)

def demo_header(title):
    """Print a demo section header."""
    print("\n" + "=" * 60)
    print(f"🎯 {title}")
    print("=" * 60)

def demo_separator():
    """Print a separator."""
    print("-" * 60)

def show_result(operation, result, show_full=False):
    """Show operation result."""
    print(f"\n📊 {operation}:")
    
    if result.get('success'):
        print(f"   ✅ Success: {result.get('message', 'Operation completed')}")
        
        if show_full:
            # Show interesting parts of the result
            for key, value in result.items():
                if key not in ['success', 'message'] and value:
                    if isinstance(value, (list, dict)):
                        print(f"   📋 {key}: {len(value) if isinstance(value, list) else 'object'}")
                    else:
                        print(f"   📋 {key}: {value}")
    else:
        print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")

def demo_list_practices():
    """Demo listing best practices."""
    demo_header("Listing SLIM Best Practices")
    
    # List all practices
    print("🔍 Listing all available best practices...")
    result = slim_list.execute()
    show_result("List All Practices", result)
    
    if result.get('success'):
        practices = result.get('practices', [])
        print(f"\n📋 Found {len(practices)} practices:")
        for i, practice in enumerate(practices[:5], 1):  # Show first 5
            print(f"   {i}. {practice.get('id', 'N/A')}: {practice.get('title', 'N/A')}")
        if len(practices) > 5:
            print(f"   ... and {len(practices) - 5} more")
    
    demo_separator()
    
    # List documentation practices
    print("\n🔍 Listing documentation-specific practices...")
    result = slim_list.execute(category="documentation", detailed=True)
    show_result("List Documentation Practices", result)

def demo_ai_models():
    """Demo AI model operations."""
    demo_header("AI Model Operations")
    
    # List models
    print("🤖 Getting available AI models...")
    result = slim_models_list.execute()
    show_result("List AI Models", result)
    
    demo_separator()
    
    # Get recommendations
    print("\n🏆 Getting model recommendations for documentation...")
    result = slim_models_recommend.execute(task="documentation", tier="premium")
    show_result("Model Recommendations", result, show_full=True)
    
    if result.get('success'):
        models = result.get('recommended_models', [])
        if models:
            print(f"\n🎯 Top recommended models:")
            for i, model in enumerate(models[:3], 1):
                print(f"   {i}. {model}")
    
    demo_separator()
    
    # Validate a model
    test_model = "openai/gpt-4o"
    print(f"\n🔧 Validating model: {test_model}")
    result = slim_models_validate.execute(model=test_model)
    show_result(f"Validate {test_model}", result, show_full=True)

def demo_resources():
    """Demo resource access."""
    demo_header("Accessing SLIM Resources")
    
    # Get registry data
    print("📚 Accessing SLIM registry...")
    try:
        registry_data = slim_registry.get_data()
        print(f"   ✅ Registry loaded: {registry_data.get('total_count', 0)} practices")
        print(f"   📋 Categories: {list(registry_data.get('categories', {}).keys())}")
    except Exception as e:
        print(f"   ❌ Registry access failed: {e}")
    
    demo_separator()
    
    # Get model data
    print("\n🤖 Accessing AI models data...")
    try:
        models_data = slim_models.get_data()
        print(f"   ✅ Models loaded: {models_data.get('total_providers', 0)} providers")
        print(f"   📋 Total models: {models_data.get('total_models', 0)}")
        
        # Show some providers
        providers = list(models_data.get('providers', []))[:5]
        if providers:
            print(f"   🏢 Sample providers: {', '.join(providers)}")
    except Exception as e:
        print(f"   ❌ Models access failed: {e}")

def demo_prompts():
    """Demo prompt generation."""
    demo_header("Generating Prompts")
    
    # Apply best practice prompt
    print("📝 Generating apply best practice prompt...")
    try:
        prompt_messages = apply_best_practice_prompt.generate(
            best_practice_ids=["readme"],
            repo_url="https://github.com/user/example-repo",
            use_ai=True,
            model="anthropic/claude-3-5-sonnet-20241022"
        )
        print(f"   ✅ Generated {len(prompt_messages)} prompt messages")
        print(f"   📋 System prompt length: {len(prompt_messages[0]['content'])} chars")
        print(f"   📋 User prompt length: {len(prompt_messages[1]['content'])} chars")
    except Exception as e:
        print(f"   ❌ Prompt generation failed: {e}")
    
    demo_separator()
    
    # Customization prompt
    print("\n🎨 Generating AI customization prompt...")
    try:
        custom_prompt = customize_with_ai_prompt.generate(
            practice_type="README",
            repository_context="Python data science project using pandas and matplotlib",
            customization_goals="Include data science workflow and visualization examples"
        )
        print(f"   ✅ Generated {len(custom_prompt)} customization messages")
        print(f"   📋 Focuses on data science project customization")
    except Exception as e:
        print(f"   ❌ Customization prompt failed: {e}")

def demo_apply_dry_run():
    """Demo applying best practices in dry-run mode."""
    demo_header("Applying Best Practices (Dry Run)")
    
    print("🧪 Testing apply operation with dry-run...")
    
    # Simple apply with dry run
    result = slim_apply.execute(
        best_practice_ids=["readme"],
        repo_urls=["https://github.com/octocat/Hello-World"],
        dry_run=True
    )
    show_result("Apply README (dry-run)", result, show_full=True)
    
    demo_separator()
    
    # Apply with AI (dry run)
    print("\n🤖 Testing AI-powered apply with dry-run...")
    result = slim_apply.execute(
        best_practice_ids=["readme", "contributing"],
        repo_urls=["https://github.com/octocat/Hello-World"],
        use_ai="anthropic/claude-3-5-sonnet-20241022",
        dry_run=True
    )
    show_result("Apply with AI (dry-run)", result, show_full=True)

def demo_usage_examples():
    """Show practical usage examples."""
    demo_header("Practical Usage Examples")
    
    examples = [
        {
            "scenario": "New Open Source Project Setup",
            "steps": [
                "1. List available practices: slim_list",
                "2. Get AI model recommendations: slim_models_recommend",
                "3. Apply core practices: slim_apply (readme, contributing, license)",
                "4. Deploy to repository: slim_deploy"
            ]
        },
        {
            "scenario": "Documentation Generation",
            "steps": [
                "1. Validate AI model: slim_models_validate",
                "2. Apply docs practices: slim_apply (docs-website)",
                "3. Customize with AI: use customize_with_ai prompt",
                "4. Review changes: use review_changes prompt"
            ]
        },
        {
            "scenario": "Security Enhancement",
            "steps": [
                "1. List security practices: slim_list (category=security)",
                "2. Apply secrets detection: slim_apply (secrets-github, secrets-precommit)",
                "3. Deploy security configs: slim_deploy"
            ]
        }
    ]
    
    for example in examples:
        print(f"\n🎯 {example['scenario']}:")
        for step in example['steps']:
            print(f"   {step}")

def main():
    """Run the demo."""
    print("🚀 SLIM-CLI MCP Server Demo")
    print("Welcome to the SLIM-CLI Model Context Protocol Server demonstration!")
    print("This demo shows the key capabilities of the MCP server.")
    
    try:
        # Run all demo sections
        demo_list_practices()
        time.sleep(1)
        
        demo_ai_models()
        time.sleep(1)
        
        demo_resources()
        time.sleep(1)
        
        demo_prompts()
        time.sleep(1)
        
        demo_apply_dry_run()
        time.sleep(1)
        
        demo_usage_examples()
        
        # Final summary
        demo_header("Demo Complete")
        print("🎉 Demo completed successfully!")
        print("\n🔧 Next Steps:")
        print("   1. Install MCP client (e.g., Claude Desktop)")
        print("   2. Configure MCP server in client settings")
        print("   3. Start using natural language to interact with SLIM")
        print("\n📚 Documentation:")
        print("   - See mcp/README.md for setup instructions")
        print("   - Check mcp/examples.py for more usage examples")
        print("   - Run mcp/test_server.py to validate installation")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())