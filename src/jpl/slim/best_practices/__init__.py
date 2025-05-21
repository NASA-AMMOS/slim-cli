"""
Best practices module for SLIM.

This module contains the base class and implementations for best practices
that can be applied to repositories.
"""

from jpl.slim.best_practices.base import BestPractice
from jpl.slim.best_practices.standard import StandardPractice
from jpl.slim.best_practices.secrets_detection import SecretsDetection
from jpl.slim.best_practices.docgen import DocGenPractice

__all__ = ["BestPractice", "StandardPractice", "SecretsDetection", "DocGenPractice"]
