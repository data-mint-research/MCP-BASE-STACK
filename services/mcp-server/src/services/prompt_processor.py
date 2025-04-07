"""
Prompt Processor Service.

This service is responsible for processing user prompts and determining
whether they should be handled by a tool or sent to the LLM.
"""

import logging
from typing import Tuple, Optional, Callable


class PromptProcessor:
    """
    Service for processing user prompts.
    
    This service analyzes user prompts to determine if they should be
    handled by a tool (like shell commands) or sent to the LLM for processing.
    """
    
    def __init__(
        self,
        logger: logging.Logger,
        shell_command_executor: Callable[[str, int], Tuple[bool, str]]
    ):
        """
        Initialize the prompt processor.
        
        Args:
            logger: Logger instance
            shell_command_executor: Function to execute shell commands
        """
        self.logger = logger
        self.shell_command_executor = shell_command_executor
        
    def process(self, prompt: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Process a user prompt.
        
        Args:
            prompt: The user prompt to process
            
        Returns:
            Tuple[Optional[str], Optional[str]]: A tuple containing:
                - The prompt to send to the LLM (or None if handled by a tool)
                - The output from a tool (or None if no tool was used)
        """
        prompt_stripped = prompt.strip()
        self.logger.info(f"Processing prompt: {prompt_stripped[:50]}...")
        
        # If prompt starts with "!shell", treat the rest as a shell command
        if prompt_stripped.startswith("!shell"):
            command = prompt_stripped[len("!shell"):].strip()
            if command:
                # Use the injected shell_command_executor
                success, output = self.shell_command_executor(command)
                return None, output
            else:
                return None, "Error: No command provided."
                
        # Otherwise, no tool invocation, treat entire prompt as LLM query
        return prompt, None