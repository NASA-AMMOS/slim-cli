"""
Example usage of the SLIM-CLI MCP Server.

This module provides example code showing how to use the MCP server
both programmatically and through natural language interactions.
"""

import json
import asyncio
from typing import Dict, List, Any

# Example tool usage
def example_apply_best_practice():
    """Example of applying a best practice."""
    return {
        "tool": "slim_apply",
        "parameters": {
            "best_practice_ids": ["readme"],
            "repo_urls": ["https://github.com/octocat/Hello-World"],
            "use_ai": "anthropic/claude-3-5-sonnet-20241022",
            "no_prompt": True
        },
        "description": "Apply README best practice with AI customization"
    }

def example_deploy_best_practice():
    """Example of deploying best practices."""
    return {
        "tool": "slim_deploy", 
        "parameters": {
            "best_practice_ids": ["readme", "contributing"],
            "repo_dir": "/path/to/local/repo",
            "commit_message": "Add SLIM best practices",
            "remote": "origin"
        },
        "description": "Deploy multiple best practices to repository"
    }

def example_list_practices():
    """Example of listing best practices."""
    return {
        "tool": "slim_list",
        "parameters": {
            "category": "documentation",
            "detailed": True
        },
        "description": "List detailed documentation practices"
    }

def example_model_recommendations():
    """Example of getting model recommendations."""
    return {
        "tool": "slim_models_recommend",
        "parameters": {
            "task": "documentation",
            "tier": "premium"
        },
        "description": "Get premium AI models for documentation"
    }

def example_validate_model():
    """Example of validating an AI model."""
    return {
        "tool": "slim_models_validate",
        "parameters": {
            "model": "openai/gpt-4o"
        },
        "description": "Validate OpenAI GPT-4 model configuration"
    }

# Example resource usage
def example_registry_access():
    """Example of accessing the registry."""
    return {
        "resource": "slim://registry",
        "description": "Access complete SLIM registry data"
    }

def example_best_practice_details():
    """Example of getting specific practice details."""
    return {
        "resource": "slim://best_practices",
        "parameters": {
            "practice_id": "readme"
        },
        "description": "Get detailed README practice information"
    }

def example_model_information():
    """Example of getting model information."""
    return {
        "resource": "slim://models",
        "parameters": {
            "provider": "anthropic"
        },
        "description": "Get Anthropic model information"
    }

# Example prompt usage
def example_apply_prompt():
    """Example of using the apply best practice prompt."""
    return {
        "prompt": "apply_best_practice",
        "parameters": {
            "best_practice_ids": ["readme", "contributing"],
            "repo_url": "https://github.com/user/repo",
            "use_ai": True,
            "model": "anthropic/claude-3-5-sonnet-20241022"
        },
        "description": "Generate prompt for applying best practices"
    }

def example_customize_prompt():
    """Example of using the AI customization prompt."""
    return {
        "prompt": "customize_with_ai",
        "parameters": {
            "practice_type": "README",
            "repository_context": "Python machine learning project with scikit-learn",
            "customization_goals": "Include ML-specific setup and usage examples"
        },
        "description": "Generate prompt for AI customization"
    }

def example_review_prompt():
    """Example of using the review changes prompt."""
    return {
        "prompt": "review_changes",
        "parameters": {
            "changes_summary": "Added README.md and CONTRIBUTING.md files",
            "files_modified": ["README.md", "CONTRIBUTING.md", ".github/ISSUE_TEMPLATE.md"],
            "next_steps": "Review content, test links, and commit changes"
        },
        "description": "Generate prompt for reviewing changes"
    }

# Natural language interaction examples
NATURAL_LANGUAGE_EXAMPLES = [
    {
        "user_query": "Apply the README best practice to my repository at https://github.com/user/repo using AI",
        "expected_tool": "slim_apply",
        "expected_params": {
            "best_practice_ids": ["readme"],
            "repo_urls": ["https://github.com/user/repo"],
            "use_ai": "anthropic/claude-3-5-sonnet-20241022"
        }
    },
    {
        "user_query": "Show me all available security best practices",
        "expected_tool": "slim_list",
        "expected_params": {
            "category": "security",
            "detailed": True
        }
    },
    {
        "user_query": "What are the best AI models for documentation generation?",
        "expected_tool": "slim_models_recommend",
        "expected_params": {
            "task": "documentation",
            "tier": "premium"
        }
    },
    {
        "user_query": "Deploy the governance best practices to my local repo at /path/to/repo",
        "expected_tool": "slim_deploy",
        "expected_params": {
            "best_practice_ids": ["governance-small"],
            "repo_dir": "/path/to/repo"
        }
    },
    {
        "user_query": "Check if the OpenAI GPT-4 model is properly configured",
        "expected_tool": "slim_models_validate",
        "expected_params": {
            "model": "openai/gpt-4o"
        }
    }
]

# Common workflows
def example_complete_workflow():
    """Example of a complete SLIM workflow."""
    return {
        "workflow": "complete_best_practices_setup",
        "steps": [
            {
                "step": 1,
                "action": "List available practices",
                "tool": "slim_list",
                "parameters": {"detailed": True}
            },
            {
                "step": 2,
                "action": "Get model recommendations",
                "tool": "slim_models_recommend",
                "parameters": {"task": "documentation", "tier": "balanced"}
            },
            {
                "step": 3,
                "action": "Validate chosen model",
                "tool": "slim_models_validate",
                "parameters": {"model": "anthropic/claude-3-5-sonnet-20241022"}
            },
            {
                "step": 4,
                "action": "Apply best practices",
                "tool": "slim_apply",
                "parameters": {
                    "best_practice_ids": ["readme", "contributing", "changelog"],
                    "repo_urls": ["https://github.com/user/repo"],
                    "use_ai": "anthropic/claude-3-5-sonnet-20241022"
                }
            },
            {
                "step": 5,
                "action": "Deploy to repository",
                "tool": "slim_deploy",
                "parameters": {
                    "best_practice_ids": ["readme", "contributing", "changelog"],
                    "repo_dir": "/path/to/cloned/repo",
                    "commit_message": "Add SLIM best practices"
                }
            }
        ]
    }

def example_ai_customization_workflow():
    """Example of AI customization workflow."""
    return {
        "workflow": "ai_customization",
        "steps": [
            {
                "step": 1,
                "action": "Generate customization prompt",
                "prompt": "customize_with_ai",
                "parameters": {
                    "practice_type": "README",
                    "repository_context": "Python web API using FastAPI",
                    "customization_goals": "Include API documentation and deployment info"
                }
            },
            {
                "step": 2,
                "action": "Apply with AI customization",
                "tool": "slim_apply",
                "parameters": {
                    "best_practice_ids": ["readme"],
                    "repo_urls": ["https://github.com/user/api-project"],
                    "use_ai": "anthropic/claude-3-5-sonnet-20241022"
                }
            },
            {
                "step": 3,
                "action": "Review changes",
                "prompt": "review_changes",
                "parameters": {
                    "changes_summary": "Added customized README for FastAPI project",
                    "files_modified": ["README.md"],
                    "next_steps": "Review API documentation sections"
                }
            }
        ]
    }

# Error handling examples
def example_error_scenarios():
    """Examples of error handling scenarios."""
    return {
        "error_scenarios": [
            {
                "scenario": "Invalid repository URL",
                "tool": "slim_apply",
                "parameters": {
                    "best_practice_ids": ["readme"],
                    "repo_urls": ["not-a-valid-url"]
                },
                "expected_error": "Invalid repository URL"
            },
            {
                "scenario": "Missing required parameters",
                "tool": "slim_deploy",
                "parameters": {
                    "best_practice_ids": ["readme"]
                    # Missing repo_dir
                },
                "expected_error": "Missing required parameters"
            },
            {
                "scenario": "Invalid AI model format",
                "tool": "slim_models_validate",
                "parameters": {
                    "model": "invalid-model-format"
                },
                "expected_error": "Invalid model format"
            },
            {
                "scenario": "Non-existent practice ID",
                "tool": "slim_apply",
                "parameters": {
                    "best_practice_ids": ["non-existent-practice"],
                    "repo_urls": ["https://github.com/user/repo"]
                },
                "expected_error": "Practice not found"
            }
        ]
    }

def print_examples():
    """Print all examples in a formatted way."""
    print("SLIM-CLI MCP Server Examples")
    print("=" * 40)
    
    print("\n1. Tool Examples:")
    print("-" * 20)
    examples = [
        example_apply_best_practice(),
        example_deploy_best_practice(),
        example_list_practices(),
        example_model_recommendations(),
        example_validate_model()
    ]
    
    for example in examples:
        print(f"\nTool: {example['tool']}")
        print(f"Description: {example['description']}")
        print(f"Parameters: {json.dumps(example['parameters'], indent=2)}")
    
    print("\n2. Resource Examples:")
    print("-" * 20)
    resource_examples = [
        example_registry_access(),
        example_best_practice_details(),
        example_model_information()
    ]
    
    for example in resource_examples:
        print(f"\nResource: {example['resource']}")
        print(f"Description: {example['description']}")
        if 'parameters' in example:
            print(f"Parameters: {json.dumps(example['parameters'], indent=2)}")
    
    print("\n3. Prompt Examples:")
    print("-" * 20)
    prompt_examples = [
        example_apply_prompt(),
        example_customize_prompt(),
        example_review_prompt()
    ]
    
    for example in prompt_examples:
        print(f"\nPrompt: {example['prompt']}")
        print(f"Description: {example['description']}")
        print(f"Parameters: {json.dumps(example['parameters'], indent=2)}")
    
    print("\n4. Natural Language Examples:")
    print("-" * 20)
    for i, example in enumerate(NATURAL_LANGUAGE_EXAMPLES, 1):
        print(f"\n{i}. User Query: \"{example['user_query']}\"")
        print(f"   Expected Tool: {example['expected_tool']}")
        print(f"   Expected Params: {json.dumps(example['expected_params'], indent=4)}")
    
    print("\n5. Workflow Examples:")
    print("-" * 20)
    workflows = [
        example_complete_workflow(),
        example_ai_customization_workflow()
    ]
    
    for workflow in workflows:
        print(f"\nWorkflow: {workflow['workflow']}")
        print("Steps:")
        for step in workflow['steps']:
            print(f"  {step['step']}. {step['action']}")
            if 'tool' in step:
                print(f"     Tool: {step['tool']}")
            if 'prompt' in step:
                print(f"     Prompt: {step['prompt']}")

if __name__ == "__main__":
    print_examples()