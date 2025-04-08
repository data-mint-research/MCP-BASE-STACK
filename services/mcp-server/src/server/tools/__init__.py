"""
MCP Server Tools.

This package contains tools that can be provided by the MCP Server.
Tools are decorated with the @tool() decorator from the MCP SDK.
"""

from .shell.command import execute_shell_command

__all__ = ["execute_shell_command"]