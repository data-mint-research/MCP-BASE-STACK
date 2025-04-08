"""
MCP Client Component.

This package contains the Client component of the MCP implementation.
The Client is responsible for communicating with the LLM and handling client-side operations.
"""

from .client import MCPClient
from .interfaces import IClient, IToolProxy, IResourceSubscriber, ICapabilityNegotiator

__all__ = [
    'MCPClient',
    'IClient',
    'IToolProxy',
    'IResourceSubscriber',
    'ICapabilityNegotiator'
]
