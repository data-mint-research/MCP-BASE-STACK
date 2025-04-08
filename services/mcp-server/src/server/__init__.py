"""
MCP Server Component.

This package contains the Server component of the MCP implementation.
The Server is responsible for providing tools and resources to the Client.
"""

from .server import MCPServer
from .resources import FileResourceProvider

__all__ = ["MCPServer", "FileResourceProvider"]