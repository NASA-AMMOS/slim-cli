"""
Best practices module for SLIM.

This module contains the base class and implementations for best practices
that can be applied to repositories.
"""

from jpl.slim.best_practices.base import BestPractice
from jpl.slim.best_practices.governance import GovernancePractice
from jpl.slim.best_practices.standard import StandardPractice

__all__ = ["BestPractice", "GovernancePractice", "StandardPractice"]
