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
        # Add doc-gen practice to the local copy of the registry
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
            self.registry_dict.update(create_slim_registry_dictionary(registry))
        else:
            # If it's already a dictionary, update our registry with it
            self.registry_dict.update(registry)

    def get_best_practice(self, bp_id: str) -> Optional[Union[StandardPractice, SecretsDetection, DocGenPractice]]:
        """
        Get a best practice by ID.

        Args:
            bp_id: ID of the best practice to retrieve (e.g., "SLIM-1.1")

        Returns:
            Union[StandardPractice, SecretsDetection, DocGenPractice]: The best practice object if found, None otherwise
        """
        logging.debug(f"Retrieving best practice with ID: {bp_id}")

        # Special case for doc-gen
        if bp_id == 'doc-gen':
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