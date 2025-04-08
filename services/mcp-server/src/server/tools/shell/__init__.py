"""
Shell Command Tools.

This package contains tools for executing shell commands.
These tools are decorated with the @tool() decorator from the MCP SDK.
"""

from .command import execute_shell_command

__all__ = ["execute_shell_command"]