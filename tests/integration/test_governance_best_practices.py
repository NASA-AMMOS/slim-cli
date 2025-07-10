"""
Integration tests for governance best practices.

This module contains integration tests for governance best practices that test
end-to-end functionality including AI enhancement with contributor statistics,
git repository operations, and file generation.
"""

import pytest
import logging
import re
from jpl.slim.app import app
from tests.conftest import (
    BestPracticeTestEnvironment, 
    verify_repository_setup,
    verify_branch_creation
)


class TestGovernanceBestPractices:
    """Integration tests for governance best practices with AI enhancement."""
    
    @pytest.mark.slow
    @pytest.mark.integration
    @pytest.mark.ai
    def test_governance_small_best_practice_for_correct_ai_output(self, caplog):
        """
        Test governance-small best practice with AI generated content.
        Checks to ensure contributor statistics are used and content is project-adapted.
        """
        with BestPracticeTestEnvironment(use_ai=True) as env:
            # Set the logging level to capture debug logs
            caplog.set_level(logging.DEBUG)
            
            # Suppress noisy loggers to clean up caplog
            noisy_loggers = ["LiteLLM", "litellm", "httpx", "httpcore", "urllib3", "requests"]
            for logger_name in noisy_loggers:
                logging.getLogger(logger_name).setLevel(logging.WARNING)
            
            # Execute command using centralized AI model config
            args = [
                'apply',
                '--best-practice-ids', 'governance-small', 
                '--repo-urls', 'https://github.com/NASA-AMMOS/MMTC',
                '--clone-to-dir', env.target_dir,
                '--use-ai', env.ai_model,
                '--logging', 'DEBUG'
            ]
            result = env.runner.invoke(app, args)
            
            # Custom assertions for this specific test
            assert result.exit_code == 0, f"Command failed with output: {result.output}"
            assert "Successfully applied" in result.output
            
            # Filter to capture AI generated content logs from ai_utils.py
            ai_content_logs = '\n'.join([
                record.getMessage() for record in caplog.records 
                if record.filename == 'ai_utils.py' and 'AI generated content for' in record.getMessage()
            ])
            
            #print(f"AI Content Logs:\n{ai_content_logs}")
            assert "john.lage@jhuapl.edu" in ai_content_logs, f"Committer information not found in AI content logs: {ai_content_logs}"
            assert re.search(r"MMTC.*Project Governance", ai_content_logs), f"'MMTC.*Project Governance' pattern not found in AI content logs: {ai_content_logs}"
            #assert "RiverM" not in ai_content_logs, f"RiverM information found in AI content logs: {ai_content_logs}"
            assert "[INSERT PROJECT NAME]" not in ai_content_logs, f"Template placeholder found in AI content logs: {ai_content_logs}"
            assert "completed template" not in ai_content_logs, f"AI chat text found in AI content logs: {ai_content_logs}"
            
            # Verify repository setup
            repo_path = verify_repository_setup(env.target_dir, 'GOVERNANCE.md')
            
            # Verify branch creation
            verify_branch_creation(repo_path, 'governance-small')

    @pytest.mark.slow
    @pytest.mark.integration
    @pytest.mark.ai
    def test_governance_medium_best_practice_for_correct_ai_output(self, caplog):
        """
        Test governance-medium best practice with AI generated content.
        Checks to ensure contributor statistics are used for committers section.
        """
        with BestPracticeTestEnvironment(use_ai=True) as env:
            # Set the logging level to capture debug logs
            caplog.set_level(logging.DEBUG)
            
            # Suppress LiteLLM debug logging to avoid test interference
            litellm_loggers = ["LiteLLM", "litellm", "httpx", "httpcore"]
            for logger_name in litellm_loggers:
                logging.getLogger(logger_name).setLevel(logging.WARNING)
            
            # Execute command using centralized AI model config
            args = [
                'apply',
                '--best-practice-ids', 'governance-medium', 
                '--repo-urls', 'https://github.com/NASA-AMMOS/MMTC',
                '--clone-to-dir', env.target_dir,
                '--use-ai', env.ai_model,
                '--logging', 'DEBUG'
            ]
            result = env.runner.invoke(app, args)
            
            # Custom assertions for this specific test
            assert result.exit_code == 0, f"Command failed with output: {result.output}"
            assert "Successfully applied" in result.output
            
            # Filter to capture AI generated content logs from ai_utils.py
            ai_content_logs = '\n'.join([
                record.getMessage() for record in caplog.records 
                if record.filename == 'ai_utils.py' and 'AI generated content for' in record.getMessage()
            ])
            
            assert "john.lage@jhuapl.edu" in ai_content_logs, f"Committer information not found in AI content logs: {ai_content_logs}"
            assert re.search(r"MMTC.*Project Governance", ai_content_logs), f"'MMTC.*Project Governance' pattern not found in AI content logs: {ai_content_logs}"
            assert "[INSERT PROJECT NAME]" not in ai_content_logs, f"Template placeholder found in AI content logs: {ai_content_logs}"
            assert "completed template" not in ai_content_logs, f"AI chat text found in AI content logs: {ai_content_logs}"
            
            # Verify repository setup
            repo_path = verify_repository_setup(env.target_dir, 'GOVERNANCE.md')
            
            # Verify branch creation
            verify_branch_creation(repo_path, 'governance-medium')

    @pytest.mark.slow
    @pytest.mark.integration
    @pytest.mark.ai
    def test_governance_large_best_practice_for_correct_ai_output(self, caplog):
        """
        Test governance-large best practice with AI generated content.
        Checks to ensure contributor statistics are used for committers information.
        """
        with BestPracticeTestEnvironment(use_ai=True) as env:
            # Set the logging level to capture debug logs
            caplog.set_level(logging.DEBUG)
            
            # Suppress LiteLLM debug logging to avoid test interference
            litellm_loggers = ["LiteLLM", "litellm", "httpx", "httpcore"]
            for logger_name in litellm_loggers:
                logging.getLogger(logger_name).setLevel(logging.WARNING)
            
            # Execute command using centralized AI model config
            args = [
                'apply',
                '--best-practice-ids', 'governance-large', 
                '--repo-urls', 'https://github.com/NASA-AMMOS/MMTC',
                '--clone-to-dir', env.target_dir,
                '--use-ai', env.ai_model,
                '--logging', 'DEBUG'
            ]
            result = env.runner.invoke(app, args)
            
            # Custom assertions for this specific test
            assert result.exit_code == 0, f"Command failed with output: {result.output}"
            assert "Successfully applied" in result.output
            
            # Filter to capture AI generated content logs from ai_utils.py
            ai_content_logs = '\n'.join([
                record.getMessage() for record in caplog.records 
                if record.filename == 'ai_utils.py' and 'AI generated content for' in record.getMessage()
            ])
            
            assert "john.lage@jhuapl.edu" in ai_content_logs, f"Committer information not found in AI content logs: {ai_content_logs}"
            assert re.search(r"MMTC.*Project Governance", ai_content_logs), f"'MMTC.*Project Governance' pattern not found in AI content logs: {ai_content_logs}"
            assert "[INSERT PROJECT NAME]" not in ai_content_logs, f"Template placeholder found in AI content logs: {ai_content_logs}"
            assert "completed template" not in ai_content_logs, f"AI chat text found in AI content logs: {ai_content_logs}"
            
            # Verify repository setup
            repo_path = verify_repository_setup(env.target_dir, 'GOVERNANCE.md')
            
            # Verify branch creation
            verify_branch_creation(repo_path, 'governance-large')
