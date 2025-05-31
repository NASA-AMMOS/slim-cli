# File: src/jpl/slim/docgen/enhancer/ai_enhancer.py
"""
AI enhancement functionality for documentation content.
"""
import logging
import os
import sys
from typing import Dict, Optional


class AIEnhancer:
    """
    Enhances documentation content using AI.
    """
    
    def __init__(self, model: str, logger: logging.Logger):
        """
        Initialize the AI enhancer.
        
        Args:
            model: AI model to use in format "provider/model_name"
            logger: Logger instance
        """
        self.model = model
        self.logger = logger
        
        # Parse provider and model name
        try:
            self.provider, self.model_name = model.split('/')
        except ValueError:
            self.logger.warning(f"Invalid model format: {model}. Expected format: 'provider/model_name'")
            self.provider = "openai"  # Default provider
            self.model_name = model
        
        # Validate provider
        if self.provider not in {"openai", "azure", "ollama"}:
            self.logger.warning(f"Unsupported provider: {self.provider}. Falling back to openai.")
            self.provider = "openai"
        
        self.logger.info(f"Initialized AI enhancer with {self.provider}/{self.model_name}")
    
    def enhance(self, content: str, section_name: str) -> str:
        """
        Enhance documentation content using AI.
        
        Args:
            content: Original content to enhance
            section_name: Name of the section being enhanced
            
        Returns:
            Enhanced content
        """
        try:
            self.logger.info(f"Enhancing {section_name} content with AI")
            
            # Get enhancement prompt for the section
            prompt = self._get_enhancement_prompt(content, section_name)
            
            # Generate enhanced content using selected provider/model
            if self.provider == "openai":
                enhanced_content = self._enhance_with_openai(prompt)
            elif self.provider == "azure":
                enhanced_content = self._enhance_with_azure(prompt)
            elif self.provider == "ollama":
                enhanced_content = self._enhance_with_ollama(prompt)
            else:
                self.logger.warning(f"Unsupported provider: {self.provider}")
                return content
            
            # If enhancement failed, return original content
            if not enhanced_content:
                self.logger.warning(f"AI enhancement failed. Using original content for {section_name}.")
                return content
            
            return enhanced_content
            
        except Exception as e:
            self.logger.error(f"Error during AI enhancement: {str(e)}")
            return content  # Return original content if enhancement fails
    
    def _get_enhancement_prompt(self, content: str, section_name: str) -> str:
        """
        Get the enhancement prompt for a specific section.
        
        Args:
            content: Original content to enhance
            section_name: Name of the section being enhanced
            
        Returns:
            Enhancement prompt
        """
        prompt_templates = {
            "overview": "Format markdown. Fix errors. Enhance this project overview to be more comprehensive and user-friendly "
                      "while maintaining accuracy. Add clear sections for features, use cases, and key "
                      "concepts if they're not already present: ",
            
            "installation": "Format markdown. Fix errors. Improve this installation guide by adding clear prerequisites, "
                          "troubleshooting tips, and platform-specific instructions while "
                          "maintaining accuracy: ",
            
            "api": "Format markdown. Fix errors. Enhance this API documentation by adding more detailed descriptions, usage "
                  "examples, and parameter explanations while maintaining technical accuracy: ",
            
            "development": "Format markdown. Fix errors. Improve this development guide by adding more context, best practices, "
                         "and workflow descriptions while maintaining accuracy: ",
            
            "contributing": "Format markdown. Fix errors. Enhance these contributing guidelines by adding more specific examples, "
                          "workflow descriptions, and best practices while maintaining accuracy: "
        }
        
        # Get specific prompt for the section, or use a generic one
        prompt = prompt_templates.get(
            section_name, 
            "Enhance this documentation while maintaining accuracy and improving clarity: "
        )
        
        # Add system context to the prompt
        system_context = (
            "You are a technical documentation specialist helping to improve software documentation. "
            "Your job is to enhance the provided documentation while maintaining factual accuracy. "
            "Improve clarity, organization, and comprehensiveness. "
            "Add examples where helpful. Format using markdown. "
            "Fix any error for docusaurus website."
        )
        
        # Return full prompt
        return f"{system_context}\n\n{prompt}\n\n{content}"
    
    def _enhance_with_openai(self, prompt: str) -> Optional[str]:
        """
        Enhance content using OpenAI API.
        
        Args:
            prompt: Enhancement prompt
            
        Returns:
            Enhanced content or None if enhancement failed
        """
        try:
            self.logger.debug("Using OpenAI for enhancement")
            
            # Use the existing SLIM CLI AI utils
            from jpl.slim.utils.ai_utils import generate_with_openai
            
            # Collect tokens from the generator
            collected_response = []
            for token in generate_with_openai(prompt, self.model_name):
                if token is not None:
                    collected_response.append(token)
                else:
                    self.logger.error("Error occurred during OpenAI generation")
                    return None
            
            return ''.join(collected_response)
            
        except Exception as e:
            self.logger.error(f"Error using OpenAI: {str(e)}")
            return None
    
    def _enhance_with_azure(self, prompt: str) -> Optional[str]:
        """
        Enhance content using Azure OpenAI API.
        
        Args:
            prompt: Enhancement prompt
            
        Returns:
            Enhanced content or None if enhancement failed
        """
        try:
            self.logger.debug("Using Azure OpenAI for enhancement")
            
            # Use the existing SLIM CLI AI utils
            from jpl.slim.utils.ai_utils import generate_with_azure
            
            return generate_with_azure(prompt, self.model_name)
            
        except Exception as e:
            self.logger.error(f"Error using Azure OpenAI: {str(e)}")
            return None
    
    def _enhance_with_ollama(self, prompt: str) -> Optional[str]:
        """
        Enhance content using Ollama (local models).
        
        Args:
            prompt: Enhancement prompt
            
        Returns:
            Enhanced content or None if enhancement failed
        """
        try:
            self.logger.debug("Using Ollama for enhancement")
            
            # Use the existing SLIM CLI AI utils
            from jpl.slim.utils.ai_utils import generate_with_ollama
            
            return generate_with_ollama(prompt, self.model_name)
            
        except Exception as e:
            self.logger.error(f"Error using Ollama: {str(e)}")
            return None