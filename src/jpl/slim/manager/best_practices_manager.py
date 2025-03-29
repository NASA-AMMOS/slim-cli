"""
Best practices manager module.

This module contains the BestPracticeManager class for retrieving and managing best practices.
"""

import logging
from typing import Dict, List, Optional, Any, Union

from jpl.slim.best_practices import GovernancePractice
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
        self.registry_dict = registry
        
        # If registry is a list, convert it to a dictionary using create_slim_registry_dictionary
        if isinstance(registry, list):
            self.registry_dict = create_slim_registry_dictionary(registry)
    
    def get_best_practice(self, bp_id: str) -> Optional[GovernancePractice]:
        """
        Get a best practice by ID.
        
        Args:
            bp_id: ID of the best practice to retrieve (e.g., "SLIM-1.1")
            
        Returns:
            GovernancePractice: The best practice object if found, None otherwise
        """
        logging.debug(f"Retrieving best practice with ID: {bp_id}")
        
        # Check if the best practice ID exists in the registry
        if bp_id not in self.registry_dict:
            logging.warning(f"Best practice ID {bp_id} not found in registry")
            return None
        
        # Get the best practice information from the registry
        practice_info = self.registry_dict[bp_id]
        
        # Determine which asset URI to use based on the best practice ID
        uri = practice_info.get('asset_uri', '')
        
        # For SLIM-1.x practices, create a GovernancePractice
        if bp_id.startswith('SLIM-1.'):
            return GovernancePractice(
                best_practice_id=bp_id,
                uri=uri,
                title=practice_info.get('title', ''),
                description=practice_info.get('description', '')
            )
        
        # For other practice types, we would create the appropriate subclass here
        # For now, we only support GovernancePractice
        
        logging.warning(f"Unsupported best practice type for ID: {bp_id}")
        return None
