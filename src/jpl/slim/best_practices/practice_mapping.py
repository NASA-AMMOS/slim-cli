"""
Practice mapping module for SLIM best practices.

This module defines the mapping between aliases and practice classes,
following DRY principles for consistent alias-to-implementation mapping
across the SLIM CLI codebase.
"""

# Practice class names as strings to avoid circular imports
PRACTICE_CLASS_STANDARD = 'StandardPractice'
PRACTICE_CLASS_SECRETS = 'SecretsDetection'
PRACTICE_CLASS_DOCSWEBSITE = 'DocsWebsiteBestPractice'

# Mapping from aliases to practice class names
ALIAS_TO_PRACTICE_CLASS = {
    # Governance practices (StandardPractice)
    'governance-small': PRACTICE_CLASS_STANDARD,
    'governance-medium': PRACTICE_CLASS_STANDARD,
    'governance-large': PRACTICE_CLASS_STANDARD,
    'code-of-conduct': PRACTICE_CLASS_STANDARD,
    'code-of-conduct-collab': PRACTICE_CLASS_STANDARD,
    'contributing': PRACTICE_CLASS_STANDARD,
    'issue-bug-md': PRACTICE_CLASS_STANDARD,
    'issue-bug-form': PRACTICE_CLASS_STANDARD,
    'issue-feature-md': PRACTICE_CLASS_STANDARD,
    'issue-feature-form': PRACTICE_CLASS_STANDARD,
    'pull-request': PRACTICE_CLASS_STANDARD,
    'codeowners': PRACTICE_CLASS_STANDARD,
    'license-apache-jpl': PRACTICE_CLASS_STANDARD,
    'license-mit-jpl': PRACTICE_CLASS_STANDARD,
    'license-apache': PRACTICE_CLASS_STANDARD,
    'license-mit': PRACTICE_CLASS_STANDARD,
    
    # Documentation practices (StandardPractice)
    'readme': PRACTICE_CLASS_STANDARD,
    'changelog': PRACTICE_CLASS_STANDARD,
    'testing-plan': PRACTICE_CLASS_STANDARD,
    
    # Security practices (SecretsDetection)
    'secrets-github': PRACTICE_CLASS_SECRETS,
    'secrets-precommit': PRACTICE_CLASS_SECRETS,
    
    # Testing practices (StandardPractice)
    'static-tests-precommit': PRACTICE_CLASS_STANDARD,
    'container-scan-precommit': PRACTICE_CLASS_STANDARD,
    
    # Documentation generation (DocsWebsiteBestPractice)
    'docs-website': PRACTICE_CLASS_DOCSWEBSITE,
}

# Mapping for StandardPractice file paths based on aliases
ALIAS_TO_FILE_PATH = {
    'governance-small': 'GOVERNANCE.md',
    'governance-medium': 'GOVERNANCE.md',
    'governance-large': 'GOVERNANCE.md',
    'readme': 'README.md',
    'issue-bug-md': '.github/ISSUE_TEMPLATE/bug_report.md',
    'issue-bug-form': '.github/ISSUE_TEMPLATE/bug_report.yml',
    'issue-feature-md': '.github/ISSUE_TEMPLATE/new_feature.md',
    'issue-feature-form': '.github/ISSUE_TEMPLATE/new_feature.yml',
    'changelog': 'CHANGELOG.md',
    'pull-request': '.github/PULL_REQUEST_TEMPLATE.md',
    'codeowners': '.github/CODEOWNERS',
    'code-of-conduct': 'CODE_OF_CONDUCT.md',
    'code-of-conduct-collab': 'CODE_OF_COLLAB.md',
    'license-apache-jpl': 'LICENSE',
    'license-mit-jpl': 'LICENSE',
    'license-apache': 'LICENSE',
    'license-mit': 'LICENSE',
    'contributing': 'CONTRIBUTING.md',
    'testing-plan': 'TESTING.md',
    'static-tests-precommit': '.pre-commit-config.yaml',
    'container-scan-precommit': '.pre-commit-config.yml',
}

# AI generation mapping for aliases (for ai_utils.py)
ALIAS_AI_CONTEXT = {
    'governance-small': 'governance',
    'governance-medium': 'governance', 
    'governance-large': 'governance',
    'readme': 'readme',
    'testing-plan': 'testing',
    # Other aliases use default context
}

def get_practice_class_name(alias: str):
    """
    Get the practice class name for a given alias.
    
    Args:
        alias: The practice alias
        
    Returns:
        The practice class name as string, or None if not found
    """
    return ALIAS_TO_PRACTICE_CLASS.get(alias)

def get_file_path(alias: str):
    """
    Get the file path for a StandardPractice alias.
    
    Args:
        alias: The practice alias
        
    Returns:
        The file path, or None if not found
    """
    return ALIAS_TO_FILE_PATH.get(alias)

def get_ai_context_type(alias: str):
    """
    Get the AI context type for a given alias.
    
    Args:
        alias: The practice alias
        
    Returns:
        The AI context type, or 'default' if not specified
    """
    return ALIAS_AI_CONTEXT.get(alias, 'default')

def is_secrets_detection_practice(alias: str):
    """
    Check if an alias is for a secrets detection practice.
    
    Args:
        alias: The practice alias
        
    Returns:
        True if it's a secrets detection practice, False otherwise
    """
    return ALIAS_TO_PRACTICE_CLASS.get(alias) == PRACTICE_CLASS_SECRETS

def is_docgen_practice(alias: str):
    """
    Check if an alias is for a documentation generation practice.
    
    Args:
        alias: The practice alias
        
    Returns:
        True if it's a documentation generation practice, False otherwise
    """
    return ALIAS_TO_PRACTICE_CLASS.get(alias) == PRACTICE_CLASS_DOCSWEBSITE

def get_all_aliases():
    """
    Get all available aliases.
    
    Returns:
        List of all available aliases
    """
    return list(ALIAS_TO_PRACTICE_CLASS.keys())