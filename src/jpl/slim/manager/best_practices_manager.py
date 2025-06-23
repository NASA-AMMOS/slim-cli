"""
Best practices manager module.

This module contains the BestPracticeManager class for retrieving and managing best practices.
"""

import logging
from typing import Dict, List, Optional, Any, Union

from jpl.slim.best_practices.standard import StandardPractice
from jpl.slim.best_practices.secrets_detection import SecretsDetection
from jpl.slim.best_practices.docs_website import DocsWebsiteBestPractice
from jpl.slim.best_practices.practice_mapping import (
    get_practice_class_name,
    is_docgen_practice,
    get_all_aliases,
    PRACTICE_CLASS_STANDARD,
    PRACTICE_CLASS_SECRETS,
    PRACTICE_CLASS_DOCSWEBSITE
)
from jpl.slim.utils.io_utils import create_slim_registry_dictionary


class BestPracticeManager:
    """
    Manager for retrieving and handling best practices.

    This class provides methods to retrieve best practices by ID and manage
    the registry of available best practices.
    """

    def __init__(self, registry: Union[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]):
        """
        Initialize a BestPracticeManager.

        Args:
            registry: Either a list of practice dictionaries from the SLIM registry JSON,
                     or a pre-processed dictionary from create_slim_registry_dictionary.
        """
        # If registry is a list, convert it to a dictionary using create_slim_registry_dictionary
        if isinstance(registry, list):
            self.registry_dict = create_slim_registry_dictionary(registry)
        else:
            # If it's already a dictionary, use it directly
            self.registry_dict = registry

    def get_best_practice(self, alias: str) -> Optional[Union[StandardPractice, SecretsDetection, DocsWebsiteBestPractice]]:
        """
        Get a best practice by alias.

        Args:
            alias: Alias of the best practice to retrieve (e.g., "readme", "secrets-github", "docs-website")

        Returns:
            Union[StandardPractice, SecretsDetection, DocsWebsiteBestPractice]: The best practice object if found, None otherwise
        """
        logging.debug(f"Retrieving best practice with alias: {alias}")

        # Handle docs-website as a special case for DocsWebsiteBestPractice
        if is_docgen_practice(alias):
            return DocsWebsiteBestPractice()

        # Check if the alias exists in the registry
        if alias not in self.registry_dict:
            logging.warning(f"Best practice alias {alias} not found in registry")
            return None

        # Get the best practice information from the registry
        practice_info = self.registry_dict[alias]

        # Get metadata
        uri = practice_info.get('asset_uri', '')
        title = practice_info.get('title', '')
        description = practice_info.get('description', '')

        # Determine the appropriate practice class based on the alias
        practice_class_name = get_practice_class_name(alias)
        if not practice_class_name:
            logging.warning(f"No practice class found for alias: {alias}")
            return None

        # Create and return the appropriate practice instance
        if practice_class_name == PRACTICE_CLASS_STANDARD:
            return StandardPractice(
                best_practice_id=alias,
                uri=uri,
                title=title,
                description=description
            )
        elif practice_class_name == PRACTICE_CLASS_SECRETS:
            return SecretsDetection(
                best_practice_id=alias,
                uri=uri,
                title=title,
                description=description
            )
        elif practice_class_name == PRACTICE_CLASS_DOCSWEBSITE:
            return DocsWebsiteBestPractice()
        else:
            logging.warning(f"Unknown practice class: {practice_class_name}")
            return None

    def list_available_practices(self) -> Dict[str, Dict[str, str]]:
        """
        List all available best practices.
        
        Returns:
            Dictionary mapping practice IDs to their metadata
        """
        return {bp_id: {
            'title': info.get('title', ''),
            'description': info.get('description', ''),
            'asset_name': info.get('asset_name', ''),
            'uri': info.get('asset_uri', '')
        } for bp_id, info in self.registry_dict.items()}

    def is_documentation_practice(self, alias: str) -> bool:
        """
        Check if a best practice alias is for documentation generation.
        
        Args:
            alias: Best practice alias to check
            
        Returns:
            True if it's a documentation practice, False otherwise
        """
        return is_docgen_practice(alias)