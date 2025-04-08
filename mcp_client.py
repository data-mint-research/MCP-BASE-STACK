"""
Simple MCP Client for connecting to our MCP server.

This client follows the MCP protocol and uses JSON-RPC for communication.
It can be used as a foundation for integrating with LibreChat.
"""

import json
import uuid
import requests
from typing import Dict, Any, List, Optional, Union

class MCPClient:
    """
    Simple MCP Client for connecting to our MCP server.
    
    This client follows the MCP protocol and uses JSON-RPC for communication.
    """
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        """
        Initialize the MCP client.
        
        Args:
            server_url: URL of the MCP server
        """
        self.server_url = server_url
        self.client_id = f"client-{uuid.uuid4()}"
        self.request_counter = 0
    
    def _get_request_id(self) -> str:
        """
        Get a unique request ID.
        
        Returns:
            str: Unique request ID
        """
        self.request_counter += 1
        return f"{self.client_id}-{self.request_counter}"
    
    def _create_jsonrpc_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a JSON-RPC request.
        
        Args:
            method: Method to call
            params: Method parameters
            
        Returns:
            Dict[str, Any]: JSON-RPC request
        """
        return {
            "jsonrpc": "2.0",
            "id": self._get_request_id(),
            "method": method,
            "params": params
        }
    
    def _send_jsonrpc_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a JSON-RPC request to the server.
        
        Args:
            method: Method to call
            params: Method parameters
            
        Returns:
            Dict[str, Any]: JSON-RPC response
        """
        request = self._create_jsonrpc_request(method, params)
        response = requests.post(
            f"{self.server_url}/jsonrpc",
            json=request,
            headers={"Content-Type": "application/json"}
        )
        return response.json()
    
    def get_capabilities(self) -> Dict[str, bool]:
        """
        Get server capabilities.
        
        Returns:
            Dict[str, bool]: Server capabilities
        """
        response = requests.get(f"{self.server_url}/mcp/capabilities")
        return response.json()
    
    def list_tools(self) -> List[str]:
        """
        List available tools.
        
        Returns:
            List[str]: List of available tools
        """
        response = self._send_jsonrpc_request("tools/list", {})
        return response.get("result", {}).get("tools", [])
    
    def get_tool_details(self, tool_name: str) -> Dict[str, Any]:
        """
        Get details about a tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Dict[str, Any]: Tool details
        """
        response = self._send_jsonrpc_request("tools/get", {"name": tool_name})
        return response.get("result", {})
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool.
        
        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            
        Returns:
            Dict[str, Any]: Tool execution result
        """
        response = self._send_jsonrpc_request(
            "tools/execute",
            {
                "name": tool_name,
                "arguments": arguments
            }
        )
        return response.get("result", {})
    
    def list_resources(self) -> List[str]:
        """
        List available resources.
        
        Returns:
            List[str]: List of available resources
        """
        response = self._send_jsonrpc_request("resources/list", {})
        return response.get("result", {}).get("resources", [])
    
    def get_resource(self, uri: str) -> Any:
        """
        Get a resource.
        
        Args:
            uri: Resource URI
            
        Returns:
            Any: Resource content
        """
        response = self._send_jsonrpc_request("resources/get", {"uri": uri})
        return response.get("result", {}).get("content")

# Example usage
if __name__ == "__main__":
    client = MCPClient()
    
    # Get server capabilities
    capabilities = client.get_capabilities()
    print(f"Server capabilities: {json.dumps(capabilities, indent=2)}")
    
    # List available tools
    tools = client.list_tools()
    print(f"Available tools: {tools}")
    
    # Get details about the mintycoder tool
    mintycoder_details = client.get_tool_details("mintycoder")
    print(f"MINTYcoder details: {json.dumps(mintycoder_details, indent=2)}")
    
    # Execute the mintycoder tool
    result = client.execute_tool(
        "mintycoder",
        {
            "prompt": "Create a function to calculate the factorial of a number",
            "language": "python"
        }
    )
    print(f"MINTYcoder result: {json.dumps(result, indent=2)}")
    
    # List available resources
    resources = client.list_resources()
    print(f"Available resources: {resources}")
    
    # Get a resource
    resource_content = client.get_resource("file://code_templates/python.py")
    print(f"Resource content: {resource_content}")
