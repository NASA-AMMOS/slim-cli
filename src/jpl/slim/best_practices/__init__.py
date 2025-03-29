"""
Best practices module for SLIM.

This module contains the base class and implementations for best practices
that can be applied to repositories.
"""

from jpl.slim.best_practices.base import BestPractice
from jpl.slim.best_practices.governance import GovernancePractice
from jpl.slim.manager.best_practices_manager import BestPracticeManager

__all__ = ["BestPractice", "GovernancePractice", "BestPracticeManager"]
