"""
MCP Client Component Tool Proxy.

This module implements the tool proxy functionality for the MCP Client component
using the SDK's JsonRpc class for tool execution.
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional, Callable, Union, Tuple

from mcp import JsonRpc, JsonRpcRequest, JsonRpcResponse, Tool

from .interfaces import IToolProxy


class ToolProxyManager(IToolProxy):
    """
    Manages tool proxies for the MCP Client component.
    
    This implementation uses the SDK's JsonRpc class for all tool operations,
    ensuring full protocol compliance.
    """
    
    def __init__(self, client: Any):
        """
        Initialize the ToolProxyManager.
        
        Args:
            client: The MCP Client instance
        """
        self.client = client
        self.proxies = {}
        
        # Initialize SDK Tool component if available
        self.tool_manager = None
        try:
            self.tool_manager = Tool.create_manager()
        except Exception as e:
            # Fall back to custom implementation if SDK component is not available
            pass
    
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
        
        # Use SDK Tool manager if available
        if self.tool_manager and hasattr(self.tool_manager, "create_proxy"):
            try:
                proxy = self.tool_manager.create_proxy(server_id, tool_name, tool_details)
                # Store the proxy function
                self.proxies[f"{server_id}:{tool_name}"] = proxy
                return proxy
            except Exception as e:
                # Fall back to custom implementation if SDK proxy creation fails
                pass
        
        # Create a proxy function
        def proxy_function(**kwargs):
            # Validate the arguments
            is_valid, validation_errors = self.validate_arguments(tool_details, kwargs)
            if not is_valid:
                error_message = f"Invalid arguments for tool {tool_name}"
                if validation_errors:
                    error_message += f": {', '.join(validation_errors)}"
                
                # Import here to avoid circular imports
                from .error_handler import ValidationError
                
                raise ValidationError(
                    message=error_message,
                    validation_errors=validation_errors,
                    data={
                        "tool_name": tool_name,
                        "server_id": server_id,
                        "arguments": kwargs
                    }
                )
            
            # Create a JSON-RPC request using the SDK's JsonRpc class
            params = {
                "name": tool_name,
                "arguments": kwargs
            }
            
            try:
                # Execute the tool
                response = self.client.send_request_to_server(
                    server_id=server_id,
                    method="tools/execute",
                    params=params
                )
                
                # Extract the result
                if "result" in response:
                    return response["result"]
                
                # Handle errors
                if "error" in response:
                    error = response["error"]
                    
                    # Import here to avoid circular imports
                    from .error_handler import ToolError
                    
                    raise ToolError(
                        message=f"Error executing tool: {error.get('message')} (code: {error.get('code')})",
                        tool_name=tool_name,
                        server_id=server_id,
                        data=error.get("data", {})
                    )
                
                return None
            except Exception as e:
                # If it's already a ToolError or ValidationError, re-raise it
                if isinstance(e, (ValidationError, ToolError)):
                    raise
                
                # Import here to avoid circular imports
                from .error_handler import ToolError
                
                # Wrap the exception in a ToolError
                raise ToolError(
                    message=f"Error executing tool {tool_name} on server {server_id}: {str(e)}",
                    tool_name=tool_name,
                    server_id=server_id,
                    original_exception=e
                )
        
        # Set the proxy function's name and docstring
        proxy_function.__name__ = tool_name
        proxy_function.__doc__ = tool_details.get("description", f"Proxy function for {tool_name}")
        
        # Add metadata for SDK compatibility
        proxy_function._mcp_tool_metadata = {
            "name": tool_name,
            "server_id": server_id,
            "description": tool_details.get("description", ""),
            "inputSchema": tool_details.get("inputSchema", {}),
            "dangerous": tool_details.get("dangerous", False)
        }
        
        # Store the proxy function
        self.proxies[f"{server_id}:{tool_name}"] = proxy_function
        
        return proxy_function
    
    def validate_arguments(self, tool_details: Dict[str, Any], arguments: Dict[str, Any]) -> Tuple[bool, Optional[List[str]]]:
        """
        Validate arguments against a tool's input schema.
        
        Args:
            tool_details: Details about the tool
            arguments: Arguments to validate
            
        Returns:
            Tuple[bool, Optional[List[str]]]: A tuple containing a boolean indicating whether the arguments are valid,
            and an optional list of validation error messages
        """
        validation_errors = []
        
        # Use SDK validation if available
        if hasattr(JsonRpc, "validate_tool_params"):
            input_schema = tool_details.get("inputSchema", {})
            validation_result = JsonRpc.validate_tool_params(tool_details.get("name", "unknown"), input_schema, arguments)
            if not validation_result["valid"]:
                return False, validation_result.get("errors", ["Unknown validation error"])
            return True, None
        
        # Fall back to custom validation
        # Get the input schema
        input_schema = tool_details.get("inputSchema", {})
        
        # Get the required properties
        required_properties = input_schema.get("required", [])
        
        # Check that all required properties are present
        for prop in required_properties:
            if prop not in arguments:
                validation_errors.append(f"Missing required property: {prop}")
        
        # Get the properties schema
        properties = input_schema.get("properties", {})
        
        # Check that all provided arguments are valid
        for arg_name, arg_value in arguments.items():
            # Check that the argument is defined in the schema
            if arg_name not in properties:
                validation_errors.append(f"Unknown property: {arg_name}")
                continue
            
            # Get the property schema
            prop_schema = properties[arg_name]
            
            # Check the type
            if "type" in prop_schema:
                prop_type = prop_schema["type"]
                
                # Check string type
                if prop_type == "string" and not isinstance(arg_value, str):
                    validation_errors.append(f"Property {arg_name} must be a string")
                
                # Check number type
                if prop_type == "number" and not isinstance(arg_value, (int, float)):
                    validation_errors.append(f"Property {arg_name} must be a number")
                
                # Check integer type
                if prop_type == "integer" and not isinstance(arg_value, int):
                    validation_errors.append(f"Property {arg_name} must be an integer")
                
                # Check boolean type
                if prop_type == "boolean" and not isinstance(arg_value, bool):
                    validation_errors.append(f"Property {arg_name} must be a boolean")
                
                # Check array type
                if prop_type == "array" and not isinstance(arg_value, list):
                    validation_errors.append(f"Property {arg_name} must be an array")
                
                # Check object type
                if prop_type == "object" and not isinstance(arg_value, dict):
                    validation_errors.append(f"Property {arg_name} must be an object")
            
            # Check enum values if present
            if "enum" in prop_schema and arg_value not in prop_schema["enum"]:
                validation_errors.append(f"Property {arg_name} must be one of: {', '.join(map(str, prop_schema['enum']))}")
            
            # Check minimum value for numbers
            if "minimum" in prop_schema and isinstance(arg_value, (int, float)) and arg_value < prop_schema["minimum"]:
                validation_errors.append(f"Property {arg_name} must be greater than or equal to {prop_schema['minimum']}")
            
            # Check maximum value for numbers
            if "maximum" in prop_schema and isinstance(arg_value, (int, float)) and arg_value > prop_schema["maximum"]:
                validation_errors.append(f"Property {arg_name} must be less than or equal to {prop_schema['maximum']}")
            
            # Check minLength for strings
            if "minLength" in prop_schema and isinstance(arg_value, str) and len(arg_value) < prop_schema["minLength"]:
                validation_errors.append(f"Property {arg_name} must have a minimum length of {prop_schema['minLength']}")
            
            # Check maxLength for strings
            if "maxLength" in prop_schema and isinstance(arg_value, str) and len(arg_value) > prop_schema["maxLength"]:
                validation_errors.append(f"Property {arg_name} must have a maximum length of {prop_schema['maxLength']}")
            
            # Check pattern for strings
            if "pattern" in prop_schema and isinstance(arg_value, str) and not re.match(prop_schema["pattern"], arg_value):
                validation_errors.append(f"Property {arg_name} must match the pattern: {prop_schema['pattern']}")
        
        return len(validation_errors) == 0, validation_errors if validation_errors else None
        
    def _ensure_capability_negotiation(self, server_id: str) -> None:
        """
        Ensure that capability negotiation has occurred with the server.
        
        Args:
            server_id: The ID of the server
            
        Raises:
            MCPError: If capability negotiation fails or the server doesn't support tools
        """
        # Import here to avoid circular imports
        from .error_handler import MCPError, ErrorCode
        
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
