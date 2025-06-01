"""
Best practices manager module.

This module contains the BestPracticeManager class for retrieving and managing best practices.
"""

import logging
from typing import Dict, List, Optional, Any, Union

from jpl.slim.best_practices.standard import StandardPractice
from jpl.slim.best_practices.secrets_detection import SecretsDetection
from jpl.slim.best_practices.docgen import DocGenPractice
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
        # Initialize with doc-gen practice as a special case for backward compatibility
        self.registry_dict = {
            'doc-gen': {
                'title': 'Documentation Generator',
                'description': 'Generates comprehensive documentation sites for software projects using the SLIM docsite template and AI enhancement',
                'asset_name': 'SLIM Docsite Template',
                'asset_uri': 'https://github.com/NASA-AMMOS/slim-docsite-template.git'
            }
        }

        # If registry is a list, convert it to a dictionary using create_slim_registry_dictionary
        if isinstance(registry, list):
            registry_dict = create_slim_registry_dictionary(registry)
            self.registry_dict.update(registry_dict)
            
            # Add SLIM-17.1 as an alias for the documentation template
            # This maps the official registry entry to our doc-gen implementation
            if 'SLIM-17.1' in registry_dict:
                # Copy SLIM-17.1 to doc-gen for compatibility
                slim_17_1 = registry_dict['SLIM-17.1'].copy()
                slim_17_1['title'] = 'Documentation Generator'
                slim_17_1['description'] = 'Generates comprehensive documentation sites for software projects using the SLIM docsite template and AI enhancement'
                self.registry_dict['doc-gen'] = slim_17_1
            else:
                # If SLIM-17.1 doesn't exist, create it as an alias to doc-gen
                self.registry_dict['SLIM-17.1'] = self.registry_dict['doc-gen'].copy()
        else:
            # If it's already a dictionary, update our registry with it
            self.registry_dict.update(registry)
            
            # Ensure both doc-gen and SLIM-17.1 exist and point to the same implementation
            if 'SLIM-17.1' in registry and 'doc-gen' not in registry:
                self.registry_dict['doc-gen'] = registry['SLIM-17.1'].copy()
            elif 'doc-gen' in registry and 'SLIM-17.1' not in registry:
                self.registry_dict['SLIM-17.1'] = registry['doc-gen'].copy()

    def get_best_practice(self, bp_id: str) -> Optional[Union[StandardPractice, SecretsDetection, DocGenPractice]]:
        """
        Get a best practice by ID.

        Args:
            bp_id: ID of the best practice to retrieve (e.g., "SLIM-1.1", "doc-gen", "SLIM-17.1")

        Returns:
            Union[StandardPractice, SecretsDetection, DocGenPractice]: The best practice object if found, None otherwise
        """
        logging.debug(f"Retrieving best practice with ID: {bp_id}")

        # Handle both doc-gen and SLIM-17.1 as aliases for the documentation generator
        if bp_id in ['doc-gen', 'SLIM-17.1']:
            return DocGenPractice()

        # Check if the best practice ID exists in the registry
        if bp_id not in self.registry_dict:
            logging.warning(f"Best practice ID {bp_id} not found in registry")
            return None

        # Get the best practice information from the registry
        practice_info = self.registry_dict[bp_id]

        # Determine which asset URI to use based on the best practice ID
        uri = practice_info.get('asset_uri', '')
        title = practice_info.get('title', '')
        description = practice_info.get('description', '')

        # Determine the appropriate practice type based on the best practice ID
        if bp_id in ['SLIM-1.1', 'SLIM-1.2', 'SLIM-1.3', 'SLIM-3.1', 'SLIM-4.1', 'SLIM-4.2', 'SLIM-4.3', 'SLIM-4.4',
                      'SLIM-5.1', 'SLIM-7.1', 'SLIM-8.1', 'SLIM-9.1', 'SLIM-13.1']:
            return StandardPractice(
                best_practice_id=bp_id,
                uri=uri,
                title=title,
                description=description
            )
        elif bp_id in ['SLIM-2.1', 'SLIM-2.2']:
            return SecretsDetection(
                best_practice_id=bp_id,
                uri=uri,
                title=title,
                description=description
            )

        logging.warning(f"Unsupported best practice type for ID: {bp_id}")
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

    def is_documentation_practice(self, bp_id: str) -> bool:
        """
        Check if a best practice ID is for documentation generation.
        
        Args:
            bp_id: Best practice ID to check
            
        Returns:
            True if it's a documentation practice, False otherwise
        """
        return bp_id in ['doc-gen', 'SLIM-17.1']