"""
Governance best practice module.

This module contains the GovernanceBestPractice class for applying governance
best practices with enhanced AI customization that includes contributor statistics.
"""

import logging

from jpl.slim.best_practices.standard import StandardPractice
from jpl.slim.utils.io_utils import read_file_content, fetch_repository_context
from jpl.slim.utils.prompt_utils import get_prompt_with_context, get_repository_context
from jpl.slim.utils.ai_utils import generate_ai_content
from jpl.slim.utils.git_utils import get_contributor_stats


class GovernanceBestPractice(StandardPractice):
    """
    Best practice for governance templates (governance-small, governance-medium, governance-large).

    This class handles downloading and customizing governance documentation
    with enhanced AI assistance that includes contributor statistics to help
    fill in committer information in governance templates.
    """

    def _apply_ai_customization(self, git_repo, file_path, model):
        """
        Apply AI customization to a governance file with contributor statistics.

        Args:
            git_repo (git.Repo): Git repository object
            file_path (str): Path to the file to customize
            model (str): AI model to use

        Returns:
            bool: True if AI customization was successful, False otherwise
        """
        try:
            # Read current file content
            current_content = read_file_content(file_path)
            if not current_content:
                logging.warning(f"Could not read content from {file_path}")
                return False
            
            # Get contributor stats from TARGET repository (not current SLIM CLI repo)
            logging.debug(f"Getting contributor statistics from: {git_repo.working_tree_dir}")
            contributor_stats = get_contributor_stats(git_repo.working_tree_dir)
            
            # Format contributor stats for AI context
            contributor_context = "CONTRIBUTOR STATISTICS:\n"
            if contributor_stats:
                for contributor in contributor_stats[:10]:  # Top 10 contributors
                    contributor_context += f"- {contributor['name']} ({contributor['email']}): {contributor['commits']} commits\n"
                logging.debug(f"Found {len(contributor_stats)} contributors, using top 10 for AI context")
            else:
                contributor_context += "No contributor statistics available.\n"
                logging.warning("No contributor statistics found for repository")
            
            # Get governance-specific prompt using dedicated category
            prompt_with_context = get_prompt_with_context('governance', self.best_practice_id)
            
            if not prompt_with_context:
                logging.warning(f"No AI prompt found for governance practice {self.best_practice_id}, falling back to original method")
                # Fall back to original AI generation method
                ai_content = generate_with_ai(self.best_practice_id, git_repo.working_tree_dir, file_path, model)
            else:
                # Use governance-specific prompt system with repository context
                logging.debug(f"Fetching repository context from: {git_repo.working_tree_dir}")
                
                # Get repository context configuration for governance practices
                repo_context_config = get_repository_context('governance', self.best_practice_id)
                logging.debug(f"Repository context config: {repo_context_config}")
                
                # Fetch repository context using the new system
                repo_context = fetch_repository_context(git_repo.working_tree_dir, repo_context_config)
                context_info = f"REPOSITORY CONTEXT:\n{repo_context}" if repo_context else "No repository context found."
                logging.debug(f"Fetched repository context, length: {len(repo_context) if repo_context else 0}")
                
                # Construct full prompt with contributor statistics
                full_prompt = f"{prompt_with_context}\n\nTEMPLATE TO ENHANCE:\n{current_content}\n\nCONTEXT INFORMATION:\n{context_info}\n\n{contributor_context}"
                
                # Generate AI content using the centralized AI utilities
                ai_content = generate_ai_content(full_prompt, model)
            
            if ai_content:
                logging.debug(f"AI-generated content for {file_path}:\n{ai_content}")
                with open(file_path, 'w') as f:
                    f.write(ai_content)
                logging.debug(f"Applied AI-generated content to {file_path}")
                return True
            else:
                logging.warning(f"AI generation failed for governance practice {self.best_practice_id}")
                return False
        except Exception as e:
            logging.error(f"Error applying AI customization: {e}")
            return False