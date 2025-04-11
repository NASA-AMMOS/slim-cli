"""
Base class for SLIM best practices.

This module defines the abstract base class for all best practices
that can be applied to repositories.
"""

from abc import ABC, abstractmethod


class BestPractice(ABC):
    """
    Abstract base class for all best practices.

    All best practices must inherit from this class and implement
    the required abstract methods.
    """

    def __init__(self, best_practice_id, uri, title, description):
        """
        Initialize a best practice.

        Args:
            best_practice_id (str): Unique identifier for the best practice
            uri (str): URI where the best practice is defined
            title (str): Human-readable title of the best practice
            description (str): Detailed description of the best practice
        """
        self.best_practice_id = best_practice_id
        self.uri = uri
        self.title = title
        self.description = description

    @abstractmethod
    def apply(self, repo_path, use_ai=False, model=None, repo_url=None, target_dir_to_clone_to=None, branch=None, no_prompt=False):
        """
        Apply the best practice to a repository.

        Args:
            repo_path (str): Path to the repository
            use_ai (bool, optional): Whether to use AI assistance. Defaults to False.
            model (str, optional): AI model to use if use_ai is True. Defaults to None.
            repo_url (str, optional): Repository URL to apply to. Defaults to None.
            target_dir_to_clone_to (str, optional): Directory to clone repository to. Defaults to None.
            branch (str, optional): Git branch to use. Defaults to None.
            no_prompt (bool, optional): Skip user confirmation prompts for dependencies installation. Defaults to False.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass
        """
        pass

    @abstractmethod
    def deploy(self, repo_path, remote=None, commit_message=None):
        """
        Deploy changes made by applying the best practice.

        Args:
            repo_path (str): Path to the repository
            remote (str, optional): Remote repository to push changes to. Defaults to None.
            commit_message (str, optional): Commit message for the changes. Defaults to None.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass
        """
        pass