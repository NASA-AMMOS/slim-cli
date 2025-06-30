"""
CLI utilities for the SLIM CLI application.

This module provides various utilities for command-line interface functionality,
including spinner management, user interaction, and terminal display utilities.
"""

import sys
from contextlib import contextmanager
from typing import Optional, Any
from rich.console import Console
from rich.progress import Progress


class SpinnerManager:
    """
    Manager for controlling Rich progress spinners during user interaction.
    
    This class provides methods to pause and resume spinners when user input
    is required, ensuring the terminal display remains clean and functional.
    """
    
    def __init__(self):
        self._current_progress: Optional[Progress] = None
        self._paused = False
        self._console = Console()
    
    def set_progress(self, progress: Progress):
        """Set the current progress context for management."""
        self._current_progress = progress
        self._paused = False
    
    def clear_progress(self):
        """Clear the current progress context."""
        self._current_progress = None
        self._paused = False
    
    def pause_spinner(self):
        """
        Pause the current spinner and clear the line.
        
        This method temporarily stops the spinner animation and clears
        the terminal line to prepare for clean user input.
        """
        if self._current_progress and not self._paused:
            # Stop the progress context temporarily
            self._current_progress.stop()
            # Clear the current line
            self._console.print("\r" + " " * 80 + "\r", end="")
            self._paused = True
    
    def resume_spinner(self):
        """
        Resume the spinner after user input is complete.
        
        This method restarts the spinner animation after user interaction
        has finished.
        """
        if self._current_progress and self._paused:
            # Restart the progress context
            self._current_progress.start()
            self._paused = False
    
    @contextmanager
    def pause_for_input(self):
        """
        Context manager for pausing spinner during user input.
        
        Usage:
            with spinner_manager.pause_for_input():
                response = input("Enter your choice: ")
        """
        was_paused = self._paused
        if not was_paused:
            self.pause_spinner()
        try:
            yield
        finally:
            if not was_paused:
                self.resume_spinner()


# Global spinner manager instance
_spinner_manager = SpinnerManager()


def get_spinner_manager() -> SpinnerManager:
    """Get the global spinner manager instance."""
    return _spinner_manager


def spinner_safe_input(prompt: str) -> str:
    """
    Get user input while safely managing any active spinner.
    
    This function automatically pauses any active spinner, displays the prompt,
    gets user input, and then resumes the spinner.
    
    Args:
        prompt: The prompt to display to the user
        
    Returns:
        str: The user's input response
    """
    manager = get_spinner_manager()
    with manager.pause_for_input():
        return input(prompt)


@contextmanager
def managed_progress(progress: Progress):
    """
    Context manager for automatically managing a Progress instance with the spinner manager.
    
    This ensures the spinner manager knows about the active progress context
    and can properly pause/resume it during user interaction.
    
    Args:
        progress: The Rich Progress instance to manage
        
    Usage:
        with Progress(...) as progress:
            with managed_progress(progress):
                # Your code that might need user input
                pass
    """
    manager = get_spinner_manager()
    manager.set_progress(progress)
    try:
        yield progress
    finally:
        manager.clear_progress()