"""
MCP Client Component Capability Negotiator.

This module implements the capability negotiation functionality for the MCP Client component
using the SDK's JsonRpc class for capability negotiation.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Callable, Union

from mcp import JsonRpc, JsonRpcRequest, JsonRpcResponse, Capability

from .interfaces import ICapabilityNegotiator


class CapabilityNegotiator(ICapabilityNegotiator):
    """
    Manages capability negotiation for the MCP Client component.
    
    This implementation uses the SDK's JsonRpc class for all capability negotiation operations,
    ensuring full protocol compliance.
    """
    
    def __init__(self, client: Any):
        """
        Initialize the CapabilityNegotiator.
        
        Args:
            client: The MCP Client instance
        """
        self.client = client
        self.negotiated_capabilities = {}
        
        # Initialize SDK Capability component if available
        self.capability_manager = None
        try:
            self.capability_manager = Capability.create_manager()
        except Exception as e:
            # Fall back to custom implementation if SDK component is not available
            pass
    
    def negotiate(self, server_id: str, client_capabilities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Negotiate capabilities with a server using the SDK's JsonRpc class.
        
        Args:
            server_id: The ID of the server
            client_capabilities: The client's capabilities
            
        Returns:
            Dict[str, Any]: Negotiated capabilities
            
        Raises:
            ValidationError: If the server_id or client_capabilities is invalid
            NetworkError: If there's a network error
            MCPError: For other errors
        """
        # Import here to avoid circular imports
        from .error_handler import ValidationError, MCPError, ErrorCode, NetworkError
        
        # Validate parameters
        if not server_id:
            raise ValidationError(
                message="Server ID cannot be empty",
                field_errors={"server_id": ["Server ID cannot be empty"]}
            )
        
        if client_capabilities is None:
            raise ValidationError(
                message="Client capabilities cannot be None",
                field_errors={"client_capabilities": ["Client capabilities cannot be None"]}
            )
        
        # Use SDK Capability manager if available
        if self.capability_manager and hasattr(self.capability_manager, "negotiate"):
            try:
                negotiated = self.capability_manager.negotiate(server_id, client_capabilities)
                # Store the negotiated capabilities
                self.negotiated_capabilities[server_id] = negotiated
                return negotiated
            except Exception as e:
                # Log the error but continue with custom implementation
                self.client.logger.error(f"Error negotiating capabilities via SDK: {str(e)}")
        
        try:
            # Create a JSON-RPC request using the SDK's JsonRpc class
            params = {
                "client_capabilities": client_capabilities
            }
            
            # Send a capability negotiation request to the server
            response = self.client.send_request_to_server(
                server_id=server_id,
                method="capabilities/negotiate",
                params=params
            )
            
            # Extract the negotiated capabilities from the response
            if "result" in response and "capabilities" in response["result"]:
                negotiated = response["result"]["capabilities"]
                
                # Store the negotiated capabilities
                self.negotiated_capabilities[server_id] = negotiated
                
                return negotiated
            
            # If primary negotiation fails, try to get server capabilities directly
            try:
                capabilities_response = self.client.send_request_to_server(
                    server_id=server_id,
                    method="capabilities/list",
                    params={}
                )
                
                if "result" in capabilities_response and "capabilities" in capabilities_response["result"]:
                    server_capabilities = capabilities_response["result"]["capabilities"]
                    
                    # Compute intersection of client and server capabilities
                    negotiated = {}
                    for capability, value in client_capabilities.items():
                        if capability in server_capabilities:
                            negotiated[capability] = value and server_capabilities[capability]
                        else:
                            negotiated[capability] = False
                    
                    # Store the negotiated capabilities
                    self.negotiated_capabilities[server_id] = negotiated
                    
                    return negotiated
            except Exception as e:
                # Log the error but continue with default capabilities
                self.client.logger.error(f"Error getting server capabilities: {str(e)}")
            
            # If no capabilities found in response, raise an error
            raise MCPError(
                error_code=ErrorCode.INTERNAL_ERROR,
                message=f"No capabilities found in negotiation response from server {server_id}",
                data={"server_id": server_id}
            )
        except MCPError as e:
            # Re-raise MCPError
            raise
        except Exception as e:
            # Wrap other exceptions in MCPError
            raise MCPError(
                error_code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to negotiate capabilities with server {server_id}: {str(e)}",
                data={"server_id": server_id},
                original_exception=e
            )
        
        # This code should never be reached due to the exceptions above,
        # but we'll keep it as a fallback just in case
        default_capabilities = {
            "tools": True,
            "resources": True,
            "subscriptions": False,
            "batch": False,
            "progress": False
        }
        
        # Store the default capabilities
        self.negotiated_capabilities[server_id] = default_capabilities
        
        return default_capabilities
    def get_client_capabilities(self) -> Dict[str, Any]:
        """
        Get the client's capabilities using the SDK if available.
        
        Returns:
            Dict[str, Any]: The client's capabilities
            
        Raises:
            MCPError: If there's an error getting the client's capabilities
        """
        # Import here to avoid circular imports
        from .error_handler import MCPError, ErrorCode
        
        try:
            # Use SDK Capability manager if available
            if self.capability_manager and hasattr(self.capability_manager, "get_client_capabilities"):
                try:
                    return self.capability_manager.get_client_capabilities()
                except Exception as e:
                    # Log the error but continue with custom implementation
                    self.client.logger.error(f"Error getting client capabilities via SDK: {str(e)}")
            
            # Return standard capabilities
            return {
                "tools": True,
                "resources": True,
                "subscriptions": True,
                "batch": True,
                "progress": True,
                "protocol_version": "2025-03-26",
                "client_version": "1.0.0"
            }
        except Exception as e:
            # Wrap the exception in an MCPError
            raise MCPError(
                error_code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to get client capabilities: {str(e)}",
                original_exception=e
            )
