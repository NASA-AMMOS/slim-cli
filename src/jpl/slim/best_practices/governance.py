"""
Governance best practice module.

This module contains the GovernanceBestPractice class for applying governance
best practices with enhanced AI customization that includes contributor statistics.
"""

import logging
import re

from jpl.slim.best_practices.standard import StandardPractice
from jpl.slim.utils.io_utils import read_file_content, fetch_repository_context
from jpl.slim.utils.prompt_utils import get_prompt_with_context, get_repository_context
from jpl.slim.utils.ai_utils import PlaceholderAIGenerator, PlaceholderMapping
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
        Apply AI customization to a governance file using PlaceholderAIGenerator.

        Args:
            git_repo (git.Repo): Git repository object
            file_path (str): Path to the file to customize
            model (str): AI model to use

        Returns:
            bool: True if AI customization was successful, False otherwise
        """
        try:
            # Get contributor stats from TARGET repository
            logging.debug(f"Getting contributor statistics from: {git_repo.working_tree_dir}")
            contributor_stats = get_contributor_stats(git_repo.working_tree_dir)
            
            # Format contributor stats for AI context
            contributor_context = {}
            contributor_stats_label = "Committer Statistics"
            if contributor_stats:
                # Prepare contributor info for AI prompts
                contributors_list = []
                for contributor in contributor_stats[:12]:  # Top 12 for large teams
                    contributors_list.append(f"{contributor['name']} ({contributor['email']}): {contributor['commits']} commits")
                contributor_context[contributor_stats_label] = "\n" + "\n".join(contributors_list)
                contributor_context['total_contributors'] = len(contributor_stats)
                logging.debug(f"Found {len(contributor_stats)} contributors, using top 12 for AI context")
            else:
                contributor_context[contributor_stats_label] = "No contributor statistics available"
                contributor_context['total_contributors'] = 0
                logging.warning("No contributor statistics found for repository")
            
            # Get repository context
            repo_context_config = get_repository_context('governance', self.best_practice_id)
            logging.debug(f"Repository context config for governance: {repo_context_config}")
            repo_context = fetch_repository_context(git_repo.working_tree_dir, repo_context_config)
            logging.debug(f"Fetched repository context, length: {len(repo_context) if repo_context else 0}")
            if repo_context:
                contributor_context['repository_info'] = repo_context
                logging.debug(f"Repository context preview: {repo_context[:200]}...")
            
            # Load prompts from YAML configuration
            title_prompt = get_prompt_with_context('governance', 'title')
            committers_prompt = None
            
            # Load prompts from nested structure in YAML using glom
            try:
                from glom import glom
                from jpl.slim.utils.prompt_utils import load_prompts
                prompts_dict = load_prompts()
                
                # Get the committers prompt based on practice ID
                if self.best_practice_id == 'governance-small':
                    committers_prompt = glom(prompts_dict, 'governance.governance-small.committers-small.prompt', default=None)
                elif self.best_practice_id == 'governance-medium':
                    committers_prompt = glom(prompts_dict, 'governance.governance-medium.committers-medium.prompt', default=None)
                elif self.best_practice_id == 'governance-large':
                    committers_prompt = glom(prompts_dict, 'governance.governance-large.committers-large.prompt', default=None)
                
                # Add contexts if prompt was found
                if committers_prompt:
                    global_context = glom(prompts_dict, 'context', default='')
                    governance_context = glom(prompts_dict, 'governance.context', default='')
                    
                    contexts = [ctx for ctx in [global_context, governance_context] if ctx]
                    if contexts:
                        committers_prompt = '\n\n'.join(contexts) + '\n\n' + committers_prompt
                        
            except ImportError:
                logging.error("glom library not installed. Please install with: pip install glom")
                committers_prompt = None
            except Exception as e:
                logging.error(f"Error loading nested prompts: {e}")
                committers_prompt = None
            
            if not title_prompt or not committers_prompt:
                logging.warning(f"Could not load prompts for {self.best_practice_id}, falling back to original method")
                from jpl.slim.utils.ai_utils import generate_with_ai
                return self._fallback_ai_generation(git_repo, file_path, model)
            
            # Create governance-specific patterns
            committer_pattern = None
            delimiter_pattern = None
            if self.best_practice_id == 'governance-small':
                # Small teams focus on basic committer info
                committer_pattern = re.compile(r'\[INSERT.*?(MEMBER|COMMITTER).*?\]')
                delimiter_pattern = re.compile(r'### Committer', re.MULTILINE)
            elif self.best_practice_id == 'governance-medium':
                # Medium teams include username links and org associations
                committer_pattern = re.compile(r'\[INSERT.*?(MEMBER|COMMITTER|USERNAME|ORG).*?\]')
                delimiter_pattern = re.compile(r'### Steering Committee', re.MULTILINE)
            elif self.best_practice_id == 'governance-large':
                # Large teams include all patterns plus committer lists
                committer_pattern = re.compile(r'\[List of current committers\]')
                delimiter_pattern = re.compile(r'### Technical Steering Committee Member', re.MULTILINE)
            else:
                # Fallback patterns
                committer_pattern = re.compile(r'\[INSERT.*?(MEMBER|COMMITTER|USERNAME|ORG).*?\]|\[List of current committers\]')
                delimiter_pattern = re.compile(r'^##\s+', re.MULTILINE)
            
            # Create placeholder mappings
            placeholder_mappings = [
                PlaceholderMapping(
                    pattern=re.compile(r'\[INSERT PROJECT NAME\]'),
                    prompt=title_prompt,
                    context=contributor_context
                ),
                PlaceholderMapping(
                    pattern=committer_pattern,
                    prompt=committers_prompt,
                    context=contributor_context
                )
            ]
            
            # Initialize PlaceholderAIGenerator
            generator = PlaceholderAIGenerator(logger=logging.getLogger(__name__))
            
            # Generate AI content for the file using section splitting
            # Split on ## headings to separate title, roles, acknowledgements, etc.
            # DELETE SOON: delimiter_pattern = re.compile(r'^##\s+', re.MULTILINE)
            
            result = generator.generate_files(
                file_paths=[file_path],
                placeholder_mappings=placeholder_mappings,
                model=model,
                delimiter_pattern=delimiter_pattern,
                file_type='.md'
            )
            
            if result.success:
                logging.debug(f"Successfully applied PlaceholderAIGenerator to {file_path}")
                return True
            else:
                logging.warning(f"PlaceholderAIGenerator failed for {file_path}: {result.errors}")
                return False
                
        except Exception as e:
            logging.error(f"Error applying AI customization: {e}")
            return False
    
    def _fallback_ai_generation(self, git_repo, file_path, model):
        """
        Fallback to original AI generation method if PlaceholderAIGenerator fails.
        """
        try:
            from jpl.slim.utils.ai_utils import generate_with_ai
            ai_content = generate_with_ai(self.best_practice_id, git_repo.working_tree_dir, file_path, model)
            
            if ai_content:
                with open(file_path, 'w') as f:
                    f.write(ai_content)
                logging.debug(f"Applied fallback AI-generated content to {file_path}")
                return True
            else:
                logging.warning(f"Fallback AI generation failed for {file_path}")
                return False
        except Exception as e:
            logging.error(f"Error in fallback AI generation: {e}")
            return False
