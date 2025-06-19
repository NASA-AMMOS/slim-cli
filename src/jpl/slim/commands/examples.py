"""
Example commands and help text for SLIM CLI.
"""

DOCUMENTATION_EXAMPLES = {
    "premium": [
        "slim apply --best-practices doc-gen --repo-dir ./project --output-dir ./docs --use-ai anthropic/claude-3-5-sonnet-20241022",
        "slim apply --best-practices doc-gen --repo-dir ./project --output-dir ./docs --use-ai openai/gpt-4o"
    ],
    "balanced": [
        "slim apply --best-practices doc-gen --repo-dir ./project --output-dir ./docs --use-ai openai/gpt-4o-mini",
        "slim apply --best-practices doc-gen --repo-dir ./project --output-dir ./docs --use-ai cohere/command-r"
    ],
    "fast": [
        "slim apply --best-practices doc-gen --repo-dir ./project --output-dir ./docs --use-ai groq/llama-3.1-70b-versatile",
        "slim apply --best-practices doc-gen --repo-dir ./project --output-dir ./docs --use-ai together/meta-llama/Llama-3-8b-chat-hf"
    ],
    "local": [
        "slim apply --best-practices doc-gen --repo-dir ./project --output-dir ./docs --use-ai ollama/llama3.1",
        "slim apply --best-practices doc-gen --repo-dir ./project --output-dir ./docs --use-ai vllm/meta-llama/Llama-3-8b-chat-hf"
    ]
}

def get_example_commands(tier="balanced"):
    """Get example commands for a specific tier."""
    return DOCUMENTATION_EXAMPLES.get(tier, DOCUMENTATION_EXAMPLES["balanced"])
