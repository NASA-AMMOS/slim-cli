"""
MCP Prompts for SLIM-CLI.

This module provides MCP prompt templates for common SLIM operations.
"""

import logging
from typing import Dict, List, Any, Optional

from .config import PROMPT_TEMPLATES
from .utils import log_mcp_operation, format_error_message

logger = logging.getLogger(__name__)

class SlimPromptTemplate:
    """Base class for SLIM prompt templates."""
    
    def __init__(self, name: str, description: str, arguments: List[Dict[str, str]]):
        self.name = name
        self.description = description
        self.arguments = arguments
    
    def generate(self, **kwargs) -> List[Dict[str, str]]:
        """Generate prompt messages."""
        raise NotImplementedError("Subclasses must implement generate method")
    
    def validate_arguments(self, **kwargs) -> bool:
        """Validate provided arguments."""
        required_args = [arg["name"] for arg in self.arguments]
        provided_args = set(kwargs.keys())
        missing_args = [arg for arg in required_args if arg not in provided_args]
        
        if missing_args:
            logger.error(f"Missing required arguments: {missing_args}")
            return False
        
        return True

class ApplyBestPracticePrompt(SlimPromptTemplate):
    """Prompt template for applying SLIM best practices."""
    
    def __init__(self):
        super().__init__(
            name="apply_best_practice",
            description="Template for applying SLIM best practices to repositories",
            arguments=[
                {"name": "best_practice_ids", "description": "List of best practice IDs to apply"},
                {"name": "repo_url", "description": "Repository URL to apply practices to"},
                {"name": "use_ai", "description": "Whether to use AI for customization"},
                {"name": "model", "description": "AI model to use for customization"}
            ]
        )
    
    def generate(self, **kwargs) -> List[Dict[str, str]]:
        """Generate apply best practice prompt."""
        if not self.validate_arguments(**kwargs):
            raise ValueError("Invalid arguments provided")
        
        best_practice_ids = kwargs.get("best_practice_ids", [])
        repo_url = kwargs.get("repo_url", "")
        use_ai = kwargs.get("use_ai", False)
        model = kwargs.get("model", "")
        
        # Convert to list if string
        if isinstance(best_practice_ids, str):
            best_practice_ids = [best_practice_ids]
        
        practices_text = ", ".join(best_practice_ids)
        ai_text = f" using AI model {model}" if use_ai and model else ""
        
        system_prompt = f"""You are helping apply SLIM best practices to a software repository.

SLIM (Software Lifecycle Improvement & Modernization) provides standardized best practices for software development including:
- Documentation (README, changelog, contributing guidelines)
- Governance (project governance, code of conduct)
- Security (secrets detection, security workflows)
- Licensing (open source licenses)

Your task is to help apply the following best practices: {practices_text}
Target repository: {repo_url}
AI customization: {"enabled" + ai_text if use_ai else "disabled"}

Provide guidance on:
1. What each best practice will add/modify
2. Any prerequisites or considerations
3. Expected outcomes
4. Next steps after application
"""
        
        user_prompt = f"""Please help me apply the SLIM best practices "{practices_text}" to the repository {repo_url}.

{"I want to use AI customization with the " + model + " model to tailor the content to my specific repository." if use_ai else "I want to apply the standard templates without AI customization."}

What should I expect from this operation?"""
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

class CustomizeWithAIPrompt(SlimPromptTemplate):
    """Prompt template for AI-powered customization."""
    
    def __init__(self):
        super().__init__(
            name="customize_with_ai",
            description="Template for AI-powered customization of best practices",
            arguments=[
                {"name": "practice_type", "description": "Type of best practice being customized"},
                {"name": "repository_context", "description": "Context about the target repository"},
                {"name": "customization_goals", "description": "Goals for customization"}
            ]
        )
    
    def generate(self, **kwargs) -> List[Dict[str, str]]:
        """Generate AI customization prompt."""
        if not self.validate_arguments(**kwargs):
            raise ValueError("Invalid arguments provided")
        
        practice_type = kwargs.get("practice_type", "")
        repository_context = kwargs.get("repository_context", "")
        customization_goals = kwargs.get("customization_goals", "")
        
        system_prompt = f"""You are an expert in software development best practices, helping to customize SLIM best practice templates for specific repositories.

The SLIM (Software Lifecycle Improvement & Modernization) framework provides standardized templates that should be customized based on:
- Repository purpose and technology stack
- Team size and organization
- Project maturity and goals
- Compliance requirements

Your task is to help customize a {practice_type} template.

Guidelines:
1. Maintain the core structure and purpose of the template
2. Adapt language and examples to the specific repository
3. Include relevant technical details and context
4. Ensure consistency with existing project conventions
5. Focus on practical, actionable content
"""
        
        user_prompt = f"""Please help me customize a {practice_type} template for my repository.

Repository Context:
{repository_context}

Customization Goals:
{customization_goals}

Please provide specific recommendations for how to tailor this best practice to my repository's needs."""
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

class ReviewChangesPrompt(SlimPromptTemplate):
    """Prompt template for reviewing SLIM changes."""
    
    def __init__(self):
        super().__init__(
            name="review_changes",
            description="Template for reviewing SLIM best practice changes",
            arguments=[
                {"name": "changes_summary", "description": "Summary of changes made"},
                {"name": "files_modified", "description": "List of files that were modified"},
                {"name": "next_steps", "description": "Recommended next steps"}
            ]
        )
    
    def generate(self, **kwargs) -> List[Dict[str, str]]:
        """Generate review changes prompt."""
        if not self.validate_arguments(**kwargs):
            raise ValueError("Invalid arguments provided")
        
        changes_summary = kwargs.get("changes_summary", "")
        files_modified = kwargs.get("files_modified", [])
        next_steps = kwargs.get("next_steps", "")
        
        files_text = "\n".join(f"- {file}" for file in files_modified) if files_modified else "No files specified"
        
        system_prompt = """You are helping review changes made by SLIM best practices application.

SLIM (Software Lifecycle Improvement & Modernization) applies standardized best practices to software repositories. After application, it's important to:
1. Review all changes for accuracy and completeness
2. Verify that templates were properly customized
3. Check for any conflicts or issues
4. Ensure compliance with project standards
5. Plan follow-up actions

Your task is to help review the changes and provide guidance on next steps."""
        
        user_prompt = f"""Please help me review the changes made by SLIM best practices application.

Changes Summary:
{changes_summary}

Files Modified:
{files_text}

Recommended Next Steps:
{next_steps}

Please provide:
1. Key points to verify in the modified files
2. Potential issues to check for
3. Additional actions I should take
4. Best practices for maintaining these changes"""
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

# Prompt instances
apply_best_practice_prompt = ApplyBestPracticePrompt()
customize_with_ai_prompt = CustomizeWithAIPrompt()
review_changes_prompt = ReviewChangesPrompt()

# Prompt registry
PROMPTS = {
    "apply_best_practice": apply_best_practice_prompt,
    "customize_with_ai": customize_with_ai_prompt,
    "review_changes": review_changes_prompt
}

def get_prompt(prompt_name: str) -> Optional[SlimPromptTemplate]:
    """Get a prompt by name."""
    return PROMPTS.get(prompt_name)

def list_prompts() -> List[Dict[str, str]]:
    """List all available prompts."""
    return [
        {
            "name": prompt.name,
            "description": prompt.description,
            "arguments": prompt.arguments
        }
        for prompt in PROMPTS.values()
    ]

def generate_prompt(prompt_name: str, **kwargs) -> List[Dict[str, str]]:
    """Generate a prompt by name with arguments."""
    try:
        log_mcp_operation("generate_prompt", {"prompt_name": prompt_name, "args": list(kwargs.keys())})
        
        prompt = get_prompt(prompt_name)
        if not prompt:
            raise ValueError(f"Prompt '{prompt_name}' not found")
        
        return prompt.generate(**kwargs)
    except Exception as e:
        logger.error(f"Error generating prompt: {e}")
        raise RuntimeError(format_error_message(e, f"Failed to generate prompt '{prompt_name}'"))