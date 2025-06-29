"""
AI utility functions for SLIM with library-agnostic AI integration.

This module contains utility functions for AI operations, including generating content
with various AI models through a unified interface. Function names are kept
library-agnostic to support future changes in underlying AI libraries.
Integrates with the centralized prompt management system.
"""

import os
import logging
import re
from typing import Optional, Generator, Any, Dict, List, Union
from dataclasses import dataclass

# Import functions from io_utils
from jpl.slim.utils.io_utils import (
    fetch_best_practices,
    create_slim_registry_dictionary,
    read_file_content,
    fetch_readme,
    fetch_code_base,
    fetch_relative_file_paths
)
from jpl.slim.utils.prompt_utils import get_prompt_with_context

# Configure LiteLLM logging at module level to suppress output by default
def _configure_litellm_logging():
    """Configure LiteLLM logging to be silent by default."""
    try:
        import litellm
        
        # Set global LiteLLM verbosity to False
        litellm.set_verbose = False
        litellm.suppress_debug_info = True
        
        # Suppress all LiteLLM loggers unless in debug mode
        loggers_to_suppress = [
            "LiteLLM",
            "litellm", 
            "litellm.main",
            "litellm.router",
            "litellm.proxy",
            "litellm.utils",
            "litellm.cost_calculator",
            "httpx",  # HTTP client used by LiteLLM
            "httpcore",  # HTTP core library
            "urllib3",  # Another HTTP library
            "requests"  # HTTP requests library
        ]
        
        root_logger_level = logging.getLogger().getEffectiveLevel()
        
        for logger_name in loggers_to_suppress:
            logger = logging.getLogger(logger_name)
            if root_logger_level > logging.DEBUG:
                # Completely disable the logger
                logger.setLevel(logging.CRITICAL + 1)
                logger.propagate = False
            else:
                # In debug mode, allow logs but set to DEBUG level
                logger.setLevel(logging.DEBUG)
                
    except ImportError:
        # LiteLLM not available, skip configuration
        pass

# Apply LiteLLM logging configuration when module is imported
_configure_litellm_logging()

__all__ = [
    "generate_with_ai",
    "construct_prompt",
    "generate_ai_content",
    "generate_with_model",
    "enhance_content",
    "validate_model",
    "get_model_recommendations",
    "PlaceholderAIGenerator",
    "PlaceholderMapping",
    "FileType"
]


def generate_with_ai(best_practice_id, repo_path, template_path, model="openai/gpt-4o-mini"):
    """
    Uses AI to generate or modify content based on the provided best practice and repository.
    
    Args:
        best_practice_id: ID of the best practice to apply
        repo_path: Path to the cloned repository
        template_path: Path to the template file for the best practice
        model: Name of the AI model to use (example: "openai/gpt-4o", "anthropic/claude-3-5-sonnet-20241022")
        
    Returns:
        str: Generated or modified content, or None if an error occurs
    """
    # In test mode, return a mock response instead of calling AI services
    if os.environ.get('SLIM_TEST_MODE', 'False').lower() in ('true', '1', 't'):
        logging.debug(f"TEST MODE: Simulating AI generation for best practice {best_practice_id}")
        return f"Mock AI-generated content for {best_practice_id}"
        
    logging.debug(f"Using AI to apply best practice ID: {best_practice_id} in repository {repo_path}")
    
    # Fetch best practice information
    from jpl.slim.commands.common import SLIM_REGISTRY_URI
    practices = fetch_best_practices(SLIM_REGISTRY_URI)
    asset_mapping = create_slim_registry_dictionary(practices)
    best_practice = asset_mapping.get(best_practice_id)
    
    if not best_practice:
        logging.error(f"Best practice ID {best_practice_id} not found.")
        return None
    
    # Read the template content
    template_content = read_file_content(template_path)
    if not template_content:
        return None
    
    # Import the AI context mapping
    from jpl.slim.best_practices.practice_mapping import get_ai_context_type
    
    # Fetch appropriate reference content based on best practice alias
    context_type = get_ai_context_type(best_practice_id)
    
    if context_type == 'governance':
        reference = fetch_readme(repo_path)
        additional_instruction = ""
    elif context_type == 'readme':
        reference = fetch_code_base(repo_path)
        additional_instruction = ""
    elif context_type == 'testing':
        reference1 = fetch_readme(repo_path)
        reference2 = "\n".join(fetch_relative_file_paths(repo_path))
        reference = "EXISTING README:\n" + reference1 + "\n\n" + "EXISTING DIRECTORY LISTING: " + reference2
        additional_instruction = "Within the provided testing template, only fill out the sections that plausibly have existing tests to fill out based on the directory listing provided (do not make up tests that do not exist)."
    else:
        reference = fetch_readme(repo_path)
        additional_instruction = ""
    
    if not reference:
        return None
        
    # Construct the prompt for the AI
    prompt = construct_prompt(template_content, best_practice, reference, additional_instruction if best_practice_id == 'SLIM-13.1' else "")
    
    # Generate and return the content using the specified model
    return generate_ai_content(prompt, model)


def construct_prompt(template_content, best_practice, reference, comment=""):
    """
    Construct a prompt for AI.
    
    Args:
        template_content: Content of the template
        best_practice: Best practice information
        reference: Reference content
        comment: Additional comment
        
    Returns:
        str: Constructed prompt
    """
    return (
        f"Fill out all blanks in the template below that start with INSERT. Use the provided context information to fill the blanks. Return the template with filled out values. {comment}\n\n"
        f"TEMPLATE:\n{template_content}\n\n"
        f"CONTEXT INFORMATION:\n{reference}\n\n"
    )


def enhance_content(content: str, practice_type: str, section_name: str, 
                   model: str, additional_context: Optional[str] = None) -> Optional[str]:
    """
    Enhance content using AI with centralized prompts and context.
    
    Args:
        content: Original content to enhance
        practice_type: Practice type (e.g., 'docgen', 'standard_practices')
        section_name: Section name (e.g., 'overview', 'installation') 
        model: AI model to use
        additional_context: Optional additional context
        
    Returns:
        Enhanced content, or original content if enhancement fails
    """
    try:
        # Get prompt with hierarchical context
        enhancement_prompt = get_prompt_with_context(practice_type, section_name, additional_context)
        
        if not enhancement_prompt:
            logging.warning(f"No prompt found for {practice_type}.{section_name}, using content as-is")
            return content
        
        # Combine prompt with content
        full_prompt = f"{enhancement_prompt}\n\nCONTENT TO ENHANCE:\n{content}"
        
        # Generate enhanced content
        enhanced = generate_ai_content(full_prompt, model)
        
        if enhanced:
            logging.debug(f"Successfully enhanced {section_name} content")
            return enhanced
        else:
            logging.warning(f"AI enhancement failed for {section_name}, using original content")
            return content
            
    except Exception as e:
        logging.error(f"Error during content enhancement: {str(e)}")
        return content


def generate_ai_content(prompt: str, model: str, **kwargs) -> Optional[str]:
    """
    Generate content using an AI model through a unified interface.
    
    Args:
        prompt: Prompt for the AI model
        model: Model name in format "provider/model" (e.g., "openai/gpt-4o", "anthropic/claude-3-5-sonnet-20241022")
        **kwargs: Additional parameters to pass to the model
        
    Returns:
        str: Generated content, or None if an error occurs
    """
    # Validate model format
    if '/' not in model:
        logging.error(f"Invalid model format: {model}. Expected format: 'provider/model'")
        return None
        
    provider, model_name = model.split('/', 1)
    
    # Use LiteLLM as the primary interface
    try:
        logging.debug(f"Generating with prompt: {prompt}")
        return generate_with_model(prompt, model, **kwargs)
    except Exception as e:
        logging.error(f"LiteLLM generation failed for {model}: {str(e)}")
        return None


def generate_with_model(prompt: str, model: str, **kwargs) -> Optional[str]:
    """
    Generate content using the primary AI interface (currently LiteLLM).
    
    Args:
        prompt: Prompt for the AI model
        model: Model name in format "provider/model" (e.g., "openai/gpt-4o", "anthropic/claude-3-5-sonnet-20241022")
        **kwargs: Additional parameters to pass to the model
        
    Returns:
        str: Generated content, or None if an error occurs
    """
    try:
        from litellm import completion
        import litellm
        
        # Apply LiteLLM logging configuration (in case it wasn't done at module level)
        _configure_litellm_logging()
        
        # Prepare messages
        messages = [{"role": "user", "content": prompt}]
        
        # Set default parameters
        completion_kwargs = {
            "model": model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "temperature": kwargs.get("temperature", 0.1),
        }
        
        # Add any additional kwargs
        completion_kwargs.update(kwargs)
        
        logging.debug(f"Generating content using model: {model}")
        
        response = completion(**completion_kwargs)
        
        if response and response.choices:
            content = response.choices[0].message.content
            logging.debug(f"Successfully generated {len(content)} characters with {model}")
            return content
        else:
            logging.error(f"No content returned from {model}")
            return None
            
    except ImportError:
        logging.error("AI library not available. Install with: pip install litellm")
        return None
    except Exception as e:
        logging.error(f"Error generating content with model ({model}): {str(e)}")
        return None


def get_model_recommendations(task: str = "documentation") -> Dict[str, str]:
    """
    Get guidance on choosing AI models for specific tasks.
    
    Instead of providing hard-coded recommendations that become outdated,
    this function guides users to authoritative sources for model selection.
    
    Args:
        task: The task type (currently ignored, kept for API compatibility)
        
    Returns:
        Dict with guidance URLs and instructions for model selection
    """
    return {
        "message": "To choose the best AI model for your task, please visit these resources:",
        "leaderboard_url": "https://www.vellum.ai/llm-leaderboard",
        "leaderboard_description": "Visit this URL to see current LLM rankings and performance metrics",
        "model_names_url": "https://models.litellm.ai/",
        "model_names_description": "Visit this URL to find the correct model name format to use with SLIM-CLI",
        "example_usage": "Example: if you want to use Claude 3.5 Sonnet, use 'anthropic/claude-3-5-sonnet-20241022'"
    }


def validate_model(model: str) -> tuple[bool, str]:
    """
    Validate model configuration and check if required environment variables are set.
    
    Args:
        model: Model name in format "provider/model"
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if '/' not in model:
        return False, f"Invalid model format: {model}. Expected format: 'provider/model'"
    
    provider, model_name = model.split('/', 1)
    
    # Check required environment variables by provider
    env_vars = {
        "openai": ["OPENAI_API_KEY"],
        "azure": ["AZURE_API_KEY", "AZURE_API_BASE", "AZURE_API_VERSION"],
        "anthropic": ["ANTHROPIC_API_KEY"],
        "google": ["GOOGLE_API_KEY"],
        "cohere": ["COHERE_API_KEY"],
        "mistral": ["MISTRAL_API_KEY"],
        "groq": ["GROQ_API_KEY"],
        "together": ["TOGETHER_API_KEY"],
        "huggingface": ["HUGGINGFACE_API_KEY"],
        "openrouter": ["OPENROUTER_API_KEY"],
        "replicate": ["REPLICATE_API_TOKEN"],
        "fireworks": ["FIREWORKS_API_KEY"],
        "deepinfra": ["DEEPINFRA_API_TOKEN"],
        "perplexity": ["PERPLEXITYAI_API_KEY"],
        "bedrock": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
        "vertex_ai": ["GOOGLE_APPLICATION_CREDENTIALS"],
        "ollama": [],  # No API key required for local Ollama
        "vllm": []     # No API key required for local VLLM
    }
    
    required_vars = env_vars.get(provider, [])
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        return False, f"Missing required environment variables for {provider}: {', '.join(missing_vars)}"
    
    return True, ""


# PlaceholderAIGenerator Framework
# Maximum attempts for AI generation retry
MAX_AI_GENERATION_ATTEMPTS = 3


class FileType:
    """File type constants for validation."""
    MARKDOWN = '.md'
    YAML = '.yaml'
    YML = '.yml'
    JSON = '.json'
    PYTHON = '.py'
    JAVASCRIPT = '.js'
    TYPESCRIPT = '.ts'
    ANY = 'ANY'  # For general validation only


@dataclass
class Section:
    """Represents a section of content from a file."""
    content: str
    index: int  # For maintaining order during reconstruction


@dataclass
class PlaceholderMapping:
    """Maps a placeholder pattern to its prompt and context."""
    pattern: re.Pattern
    prompt: str
    context: Optional[Dict[str, Any]] = None


@dataclass
class ValidationResult:
    """Result of content validation."""
    is_valid: bool
    errors: List[str]


@dataclass
class GenerationResult:
    """Result of AI generation."""
    success: bool
    processed_content: Optional[str] = None
    errors: List[str] = None


class PlaceholderAIGenerator:
    """
    Generic AI generator for processing files with placeholder patterns.
    
    This class can split files into sections and apply AI generation to specific
    placeholders, making it suitable for any file type or template structure.
    """
    
    def __init__(self, logger=None):
        """Initialize the generator with optional logger."""
        self.logger = logger or logging.getLogger(__name__)
    
    def generate_files(self, 
                      file_paths: List[str],
                      placeholder_mappings: List[PlaceholderMapping],
                      model: str,
                      delimiter_pattern: Optional[re.Pattern] = None,
                      file_type: str = FileType.ANY) -> GenerationResult:
        """
        Generate AI content for files based on placeholder patterns.
        
        Args:
            file_paths: Files to process
            placeholder_mappings: List of placeholder patterns with their prompts/context
            model: AI model to use
            delimiter_pattern: How to split files (optional - if None, process whole file)
            file_type: File type for validation
            
        Returns:
            GenerationResult with success status and processing summary
        """
        print("🤖 Starting AI generation...")
        print(f"  📚 Found {len(file_paths)} files to process")
        
        successful_files = []
        failed_files = []
        total_placeholders_filled = 0
        
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            
            try:
                # Read file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Split into sections or process as whole file
                if delimiter_pattern:
                    sections = self.detect_sections(content, delimiter_pattern)
                else:
                    sections = [Section(content=content, index=0)]
                
                # Count placeholders found
                placeholders_found = self._count_placeholders(sections, placeholder_mappings)
                if placeholders_found == 0:
                    # No placeholders to process in this file
                    continue
                
                print(f"  📝 Generating {file_name} ({placeholders_found} placeholders)...")
                
                # Process each section
                file_placeholders_filled = 0
                for section in sections:
                    # Find all applicable placeholder mappings for this section
                    applicable_mappings = []
                    for mapping in placeholder_mappings:
                        if mapping.pattern.search(section.content):
                            applicable_mappings.append(mapping)
                    
                    if applicable_mappings:
                        # Combine all applicable prompts and contexts
                        combined_prompt = self._combine_prompts(applicable_mappings)
                        combined_context = self._combine_contexts(applicable_mappings)
                        
                        # Process section with combined prompt
                        result = self.generate_section(
                            section=section,
                            prompt=combined_prompt,
                            context=combined_context,
                            model=model,
                            file_type=file_type
                        )
                        
                        if result.success:
                            section.content = result.processed_content
                            file_placeholders_filled += len(applicable_mappings)
                        else:
                            self.logger.warning(f"Failed to process placeholders in {file_name}: {result.errors}")
                
                # Reconstruct and save file
                final_content = self.reconstruct_content(sections)
                logging.debug(f"AI generated content for {file_name}:\n{final_content}")
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(final_content)
                
                successful_files.append(file_path)
                total_placeholders_filled += file_placeholders_filled
                
            except Exception as e:
                self.logger.error(f"Error processing file {file_name}: {str(e)}")
                failed_files.append({'path': file_path, 'error': str(e)})
        
        # Print summary
        print(f"\n📊 Generation Summary:")
        print(f"   ✅ Successfully processed: {len(successful_files)} files ({total_placeholders_filled} placeholders filled)")
        if failed_files:
            print(f"   ❌ Failed: {len(failed_files)} files")
            for failed in failed_files[:5]:
                print(f"      - {os.path.basename(failed['path'])}")
        
        return GenerationResult(
            success=len(successful_files) > 0,
            processed_content=f"Processed {len(successful_files)} files"
        )
    
    def detect_sections(self, content: str, delimiter_pattern: re.Pattern) -> List[Section]:
        """
        Split content into sections using a delimiter pattern.
        
        Args:
            content: The content to split
            delimiter_pattern: Compiled regex pattern to split by
            
        Returns:
            List of Section objects with content and index
        """
        sections = []
        last_end = 0
        index = 0
        
        # Find all delimiter matches
        matches = list(delimiter_pattern.finditer(content))
        
        # If no delimiters found, return the whole content as one section
        if not matches:
            return [Section(content=content, index=0)]
        
        # Add content before first delimiter as first section
        if matches[0].start() > 0:
            sections.append(Section(
                content=content[:matches[0].start()],
                index=index
            ))
            index += 1
        
        # Add each section starting with its delimiter
        for i, match in enumerate(matches):
            # Determine where this section ends
            if i + 1 < len(matches):
                # Ends at the start of the next delimiter
                section_end = matches[i + 1].start()
            else:
                # Last section - goes to end of content
                section_end = len(content)
            
            sections.append(Section(
                content=content[match.start():section_end],
                index=index
            ))
            index += 1
        
        return sections
    
    def generate_section(self,
                        section: Section,
                        prompt: str,
                        context: Dict[str, Any],
                        model: str,
                        file_type: str = FileType.ANY) -> GenerationResult:
        """
        Process a single section with AI, including retry logic and validation.
        
        Args:
            section: The section to process
            prompt: The prompt for this section
            context: Context for prompt formatting
            model: AI model to use
            file_type: File type for validation
            
        Returns:
            GenerationResult with success status and processed content
        """
        for attempt in range(1, MAX_AI_GENERATION_ATTEMPTS + 1):
            print(f"     Section {section.index} (attempt {attempt}/{MAX_AI_GENERATION_ATTEMPTS})...")
            
            try:
                # Format prompt with context and section content
                formatted_prompt = f"{prompt}\n\nCONTENT TO PROCESS:\n{section.content}"
                if context:
                    # Add context information to prompt
                    context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
                    formatted_prompt += f"\n\nCONTEXT:\n{context_str}"
                
                # Generate AI content with temperature based on attempt
                temperature = 0.7 + (attempt - 1) * 0.1
                generated_content = generate_ai_content(formatted_prompt, model, temperature=temperature)
                
                if not generated_content:
                    continue
                
                # Validate the generated content
                validation_result = self.validate_section(
                    content=generated_content,
                    file_type=file_type,
                    required_patterns=None,
                    forbidden_patterns=[re.compile(r'\[INSERT.*?\]')]
                )
                
                if validation_result.is_valid:
                    return GenerationResult(
                        success=True,
                        processed_content=generated_content
                    )
                else:
                    self.logger.debug(f"Validation failed for section {section.index}: {validation_result.errors}")
                    
            except Exception as e:
                self.logger.error(f"Error generating section {section.index}: {str(e)}")
        
        return GenerationResult(
            success=False,
            errors=[f"Failed to generate valid content after {MAX_AI_GENERATION_ATTEMPTS} attempts"]
        )
    
    def validate_section(self,
                        content: str,
                        file_type: str = FileType.ANY,
                        required_patterns: Optional[List[re.Pattern]] = None,
                        forbidden_patterns: Optional[List[re.Pattern]] = None) -> ValidationResult:
        """
        Validate section content.
        
        Args:
            content: Content to validate
            file_type: File type for specific linting
            required_patterns: Regex patterns that must be present
            forbidden_patterns: Regex patterns that must NOT be present
            
        Returns:
            ValidationResult with is_valid and error messages
        """
        errors = []
        
        # General validation - check for unresolved placeholders
        if '[INSERT' in content:
            errors.append("Contains unresolved [INSERT*] placeholders")
        
        # Pattern validation
        if forbidden_patterns:
            for pattern in forbidden_patterns:
                if pattern.search(content):
                    errors.append(f"Contains forbidden pattern: {pattern.pattern}")
        
        if required_patterns:
            for pattern in required_patterns:
                if not pattern.search(content):
                    errors.append(f"Missing required pattern: {pattern.pattern}")
        
        # File-type specific validation would go here
        # For now, just basic validation
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    def reconstruct_content(self, sections: List[Section]) -> str:
        """
        Reconstruct the full content from processed sections.
        
        Args:
            sections: List of Section objects (potentially with updated content)
            
        Returns:
            Reconstructed full content
        """
        # Sort by index to ensure correct order
        sorted_sections = sorted(sections, key=lambda s: s.index)
        
        # Concatenate all sections
        return ''.join(section.content for section in sorted_sections)
    
    def _count_placeholders(self, sections: List[Section], mappings: List[PlaceholderMapping]) -> int:
        """Count how many placeholders are found across all sections."""
        count = 0
        for section in sections:
            for mapping in mappings:
                if mapping.pattern.search(section.content):
                    count += 1
        return count
    
    def _combine_prompts(self, mappings: List[PlaceholderMapping]) -> str:
        """Combine multiple prompts into a single comprehensive prompt."""
        if len(mappings) == 1:
            return mappings[0].prompt
        
        combined = "You need to process multiple types of placeholders in this content:\n\n"
        for i, mapping in enumerate(mappings, 1):
            combined += f"{i}. {mapping.prompt}\n\n"
        
        combined += "IMPORTANT: Process ALL placeholder types mentioned above in a single pass. Return the COMPLETE content with ALL sections preserved, replacing only the specified placeholders."
        return combined
    
    def _combine_contexts(self, mappings: List[PlaceholderMapping]) -> Dict[str, Any]:
        """Combine contexts from multiple mappings."""
        combined_context = {}
        for mapping in mappings:
            if mapping.context:
                combined_context.update(mapping.context)
        return combined_context
