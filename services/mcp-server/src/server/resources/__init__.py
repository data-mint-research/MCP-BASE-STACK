"""
MCP Server Resource Providers.

This package contains resource providers for the MCP Server.
Resources are exposed via the resource:// URI scheme.
"""

from .file_resource import FileResourceProvider

__all__ = ["FileResourceProvider"]