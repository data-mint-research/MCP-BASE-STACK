"""
Model Context Protocol (MCP) implementation.

This package provides the core components for implementing the Model Context Protocol,
a standardized way for AI models to interact with external tools and resources.

The protocol is based on JSON-RPC 2.0 and provides a secure, extensible framework
for capability negotiation, tool execution, and resource access.
"""

from .json_rpc_validator import JsonRpcValidator

__all__ = ['JsonRpcValidator']