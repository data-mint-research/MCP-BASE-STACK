# Capability Negotiation in MCP

This document describes the implementation of capability negotiation in the MCP-BASE-STACK project.

## Overview

Capability negotiation is a critical part of the Model Context Protocol (MCP) that ensures clients and servers can communicate effectively by agreeing on which features they both support. The MCP Compliance Checklist explicitly states that "Capabilities negotiated before usage" is a requirement for MCP compliance.

## Implementation

The implementation of capability negotiation in the MCP-BASE-STACK project consists of the following components:

1. **Server-side capability declaration**: The server declares its capabilities in the `MCPServer` class.
2. **Server-side capability negotiation**: The server implements a `capabilities/negotiate` method that computes the intersection of client and server capabilities.
3. **Client-side capability negotiation**: The client ensures that capability negotiation occurs before tool usage or resource operations.

### Server-side Capability Declaration

The server declares its capabilities in the `MCPServer` class:

```python
self.capabilities = {
    "tools": True,
    "resources": True,
    "subscriptions": True,
    "consent": True,
    "authorization": True,
    "batch": True,
    "progress": True,
    "resource_streaming": True,
    "resource_caching": True
}
```

### Server-side Capability Negotiation

The server implements a `capabilities/negotiate` method that computes the intersection of client and server capabilities:

```python
def _handle_capabilities_negotiate(self, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle the capabilities/negotiate method using the MCP SDK.
    
    Args:
        params: Method parameters including client_capabilities
        
    Returns:
        Dict[str, Any]: Negotiated capabilities
        
    Raises:
        ValueError: If client_capabilities is not provided
    """
    self.logger.info("Handling capabilities/negotiate request")
    
    # Use the SDK server to negotiate capabilities if available
    if hasattr(self.mcp_server, "negotiate_capabilities"):
        client_capabilities = params.get("client_capabilities", {})
        return {
            "capabilities": self.mcp_server.negotiate_capabilities(client_capabilities),
            "server_id": self.server_id
        }
    
    # Fall back to our custom implementation
    if "client_capabilities" not in params:
        raise ValueError("Client capabilities not specified")
        
    client_capabilities = params["client_capabilities"]
    
    # Compute intersection of client and server capabilities
    negotiated = {}
    for capability, value in self.capabilities.items():
        if capability in client_capabilities:
            negotiated[capability] = value and client_capabilities[capability]
        else:
            negotiated[capability] = False
            
    self.logger.info(f"Negotiated capabilities: {negotiated}")
    
    return {
        "capabilities": negotiated,
        "server_id": self.server_id
    }
```

### Client-side Capability Negotiation

The client ensures that capability negotiation occurs before tool usage or resource operations by adding capability negotiation checks to the following methods:

1. `create_proxy` in the `ToolProxyManager` class
2. `access_resource` in the `MCPClient` class
3. `subscribe_to_resource` in the `MCPClient` class
4. `unsubscribe_from_resource` in the `MCPClient` class

For example, the `create_proxy` method in the `ToolProxyManager` class now includes a capability negotiation check:

```python
def create_proxy(self, server_id: str, tool_name: str, tool_details: Dict[str, Any]) -> Callable:
    """
    Create a proxy function for a tool using the SDK's JsonRpc class.
    
    This method ensures that capability negotiation occurs before tool usage.
    It checks if capabilities have been negotiated with the server, and if not,
    it negotiates them first.
    
    Args:
        server_id: The ID of the server
        tool_name: The name of the tool
        tool_details: Details about the tool
        
    Returns:
        Callable: A function that can be called to execute the tool
        
    Raises:
        ValidationError: If the server_id or tool_name is invalid
        ToolError: If the tool is not found or there's an error creating the proxy
        NetworkError: If there's a network error
        MCPError: If capability negotiation fails or the server doesn't support tools
    """
    # Ensure capability negotiation has occurred
    self._ensure_capability_negotiation(server_id)
    
    # ... rest of the method ...
```

The `_ensure_capability_negotiation` method checks if capabilities have been negotiated with the server, and if not, it negotiates them and checks if the required capability is supported:

```python
def _ensure_capability_negotiation(self, server_id: str) -> None:
    """
    Ensure that capability negotiation has occurred with the server.
    
    Args:
        server_id: The ID of the server
        
    Raises:
        MCPError: If capability negotiation fails or the server doesn't support tools
    """
    # Check if capabilities have been negotiated
    if server_id not in self.client.capability_negotiator.negotiated_capabilities:
        self.client.logger.info(f"Negotiating capabilities with server {server_id} before tool usage")
        
        try:
            # Get client capabilities
            client_capabilities = self.client.capability_negotiator.get_client_capabilities()
            
            # Negotiate capabilities
            negotiated = self.client.capability_negotiator.negotiate(server_id, client_capabilities)
            
            # Check if the server supports tools
            if not negotiated.get("tools", False):
                raise MCPError(
                    error_code=ErrorCode.CAPABILITY_NOT_SUPPORTED,
                    message=f"Server {server_id} does not support tools",
                    data={"server_id": server_id, "capability": "tools"}
                )
        except Exception as e:
            # If it's already an MCPError, re-raise it
            if isinstance(e, MCPError):
                raise
            
            # Wrap the exception in an MCPError
            raise MCPError(
                error_code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to negotiate capabilities with server {server_id}: {str(e)}",
                data={"server_id": server_id},
                original_exception=e
            )
```

Similar capability negotiation checks have been added to the `access_resource`, `subscribe_to_resource`, and `unsubscribe_from_resource` methods in the `MCPClient` class.

## Conclusion

With these changes, the MCP-BASE-STACK project now properly implements capability negotiation as required by the MCP Compliance Checklist. Capability negotiation occurs before tool usage or resource operations, ensuring that clients and servers can communicate effectively by agreeing on which features they both support.