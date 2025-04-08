#!/usr/bin/env python3
"""
MCP Client Test Script

This script tests the MCP Client component by:
1. Creating a mock MCP server
2. Running the client implementation
3. Testing basic client-server interactions
4. Validating protocol compliance

Usage:
    python test_mcp_client_integration.py
"""

import os
import sys
import json
import logging
import argparse
import time
from typing import Dict, Any, List, Optional, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp_client_test")

# Add the services directory to the Python path
sys.path.append(os.path.abspath("services/mcp-server/src"))

# Import MCP components
try:
    from client import MCPClient
    from host import MCPHost
except ImportError as e:
    logger.error(f"Error importing MCP components: {str(e)}")
    logger.error("Make sure you've run the implement_client_component.py and implement_host_component.py scripts")
    sys.exit(1)


class MockMCPServer:
    """A mock MCP server for testing the client component."""
    
    def __init__(self, server_id: str):
        """
        Initialize the mock server.
        
        Args:
            server_id: The ID of the server
        """
        self.server_id = server_id
        self.logger = logging.getLogger(f"mock_server_{server_id}")
        self.tools = {
            "echo": {
                "name": "echo",
                "description": "Echo back the input",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Message to echo"
                        }
                    },
                    "required": ["message"]
                }
            },
            "add": {
                "name": "add",
                "description": "Add two numbers",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "a": {
                            "type": "number",
                            "description": "First number"
                        },
                        "b": {
                            "type": "number",
                            "description": "Second number"
                        }
                    },
                    "required": ["a", "b"]
                }
            }
        }
        self.resources = {
            "test://data/sample": {
                "content": "This is a sample resource",
                "metadata": {
                    "type": "text/plain",
                    "created_at": time.time()
                }
            }
        }
        self.subscriptions = {}
        self.logger.info(f"Mock server {server_id} initialized")
    
    def handle_request(self, request: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """
        Handle a JSON-RPC request from a client.
        
        Args:
            request: The JSON-RPC request
            client_id: The ID of the client making the request
            
        Returns:
            Dict[str, Any]: The JSON-RPC response
        """
        self.logger.info(f"Received request from client {client_id}: {json.dumps(request)}")
        
        # Check if this is a notification (no ID)
        is_notification = "id" not in request
        
        # Get the method and params
        method = request.get("method", "")
        params = request.get("params", {})
        
        # Handle different methods
        if method == "capabilities/negotiate":
            return self._handle_capabilities_negotiate(request, params)
        elif method == "tools/list":
            return self._handle_tools_list(request)
        elif method == "tools/get":
            return self._handle_tools_get(request, params)
        elif method == "tools/execute":
            return self._handle_tools_execute(request, params)
        elif method == "resources/list":
            return self._handle_resources_list(request, params)
        elif method == "resources/read":
            return self._handle_resources_read(request, params)
        elif method == "resources/subscribe":
            return self._handle_resources_subscribe(request, params, client_id)
        elif method == "resources/unsubscribe":
            return self._handle_resources_unsubscribe(request, params)
        else:
            # Unknown method
            if is_notification:
                return {}
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
    
    def _handle_capabilities_negotiate(self, request: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle capabilities/negotiate method."""
        client_capabilities = params.get("client_capabilities", {})
        
        # Negotiate capabilities (simple intersection)
        negotiated = {
            "tools": client_capabilities.get("tools", True),
            "resources": client_capabilities.get("resources", True),
            "subscriptions": client_capabilities.get("subscriptions", False),
            "protocol_version": "2025-03-26",
            "server_version": "1.0.0"
        }
        
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "capabilities": negotiated
            }
        }
    
    def _handle_tools_list(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list method."""
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "tools": list(self.tools.keys())
            }
        }
    
    def _handle_tools_get(self, request: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/get method."""
        tool_name = params.get("name", "")
        
        if tool_name in self.tools:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "tool": self.tools[tool_name]
                }
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32602,
                    "message": f"Tool not found: {tool_name}"
                }
            }
    
    def _handle_tools_execute(self, request: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/execute method."""
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        
        if tool_name not in self.tools:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32602,
                    "message": f"Tool not found: {tool_name}"
                }
            }
        
        # Execute the tool
        if tool_name == "echo":
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "output": arguments.get("message", "")
                }
            }
        elif tool_name == "add":
            a = arguments.get("a", 0)
            b = arguments.get("b", 0)
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "output": a + b
                }
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error executing tool: {tool_name}"
                }
            }
    
    def _handle_resources_list(self, request: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/list method."""
        provider = params.get("provider", "")
        path = params.get("path", "")
        
        # In a real implementation, we would filter by provider and path
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "resources": list(self.resources.keys())
            }
        }
    
    def _handle_resources_read(self, request: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read method."""
        uri = params.get("uri", "")
        
        if uri in self.resources:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "data": self.resources[uri]
                }
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32602,
                    "message": f"Resource not found: {uri}"
                }
            }
    
    def _handle_resources_subscribe(self, request: Dict[str, Any], params: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Handle resources/subscribe method."""
        uri = params.get("uri", "")
        subscription_id = params.get("subscription_id", "")
        
        if not uri or not subscription_id:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32602,
                    "message": "Missing required parameters: uri, subscription_id"
                }
            }
        
        if uri not in self.resources:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32602,
                    "message": f"Resource not found: {uri}"
                }
            }
        
        # Store the subscription
        self.subscriptions[subscription_id] = {
            "uri": uri,
            "client_id": client_id,
            "created_at": time.time()
        }
        
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "subscription_id": subscription_id,
                "status": "subscribed"
            }
        }
    
    def _handle_resources_unsubscribe(self, request: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/unsubscribe method."""
        subscription_id = params.get("subscription_id", "")
        
        if not subscription_id:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32602,
                    "message": "Missing required parameter: subscription_id"
                }
            }
        
        if subscription_id not in self.subscriptions:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32602,
                    "message": f"Subscription not found: {subscription_id}"
                }
            }
        
        # Remove the subscription
        del self.subscriptions[subscription_id]
        
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "status": "unsubscribed"
            }
        }


class TestMCPClient:
    """Test the MCP Client component."""
    
    def __init__(self):
        """Initialize the test."""
        self.logger = logger
        
        # Create a mock server
        self.mock_server = MockMCPServer("test-server-1")
        
        # Create a host
        self.host = MCPHost(
            logger=self.logger,
            config={}
        )
        
        # Register the mock server with the host
        self.host.register_server_handler(
            server_id=self.mock_server.server_id,
            handler=self.mock_server.handle_request
        )
        
        # Create a client
        self.client = MCPClient(
            logger=self.logger,
            config={
                "mcp": {
                    "client_id": "test-client-1"
                },
                "connection": {
                    "retry_count": 3,
                    "retry_delay": 1
                }
            }
        )
        
        # Connect the client to the host
        success = self.client.connect_to_host(self.host)
        if not success:
            raise RuntimeError("Failed to connect client to host")
    
    def run_tests(self):
        """Run the tests."""
        self.logger.info("Running MCP Client tests")
        
        # Test capability negotiation
        self.test_capability_negotiation()
        
        # Test tool listing
        self.test_tool_listing()
        
        # Test tool execution
        self.test_tool_execution()
        
        # Test resource listing
        self.test_resource_listing()
        
        # Test resource access
        self.test_resource_access()
        
        # Test resource subscription
        self.test_resource_subscription()
        
        # Disconnect the client
        self.client.disconnect_from_host()
        
        self.logger.info("All tests completed successfully")
    
    def test_capability_negotiation(self):
        """Test capability negotiation."""
        self.logger.info("Testing capability negotiation")
        
        capabilities = self.client.negotiate_capabilities(self.mock_server.server_id)
        
        assert "tools" in capabilities, "Missing 'tools' capability"
        assert "resources" in capabilities, "Missing 'resources' capability"
        assert "protocol_version" in capabilities, "Missing 'protocol_version' capability"
        
        self.logger.info("Capability negotiation test passed")
    
    def test_tool_listing(self):
        """Test tool listing."""
        self.logger.info("Testing tool listing")
        
        tools = self.client.list_server_tools(self.mock_server.server_id)
        
        assert "echo" in tools, "Missing 'echo' tool"
        assert "add" in tools, "Missing 'add' tool"
        
        self.logger.info("Tool listing test passed")
    
    def test_tool_execution(self):
        """Test tool execution."""
        self.logger.info("Testing tool execution")
        
        # Get the echo tool
        echo_tool = self.client.create_tool_proxy(self.mock_server.server_id, "echo")
        
        # Execute the echo tool
        result = echo_tool(message="Hello, world!")
        
        assert result["output"] == "Hello, world!", f"Unexpected result: {result}"
        
        # Get the add tool
        add_tool = self.client.create_tool_proxy(self.mock_server.server_id, "add")
        
        # Execute the add tool
        result = add_tool(a=2, b=3)
        
        assert result["output"] == 5, f"Unexpected result: {result}"
        
        self.logger.info("Tool execution test passed")
    
    def test_resource_listing(self):
        """Test resource listing."""
        self.logger.info("Testing resource listing")
        
        resources = self.client.list_resources(self.mock_server.server_id, "test", "/")
        
        assert "test://data/sample" in resources, "Missing 'test://data/sample' resource"
        
        self.logger.info("Resource listing test passed")
    
    def test_resource_access(self):
        """Test resource access."""
        self.logger.info("Testing resource access")
        
        resource_data = self.client.access_resource(self.mock_server.server_id, "test://data/sample")
        
        assert "content" in resource_data, "Missing 'content' in resource data"
        assert resource_data["content"] == "This is a sample resource", f"Unexpected content: {resource_data['content']}"
        
        self.logger.info("Resource access test passed")
    
    def test_resource_subscription(self):
        """Test resource subscription."""
        self.logger.info("Testing resource subscription")
        
        # Create a callback
        updates_received = []
        
        def update_callback(update_data):
            updates_received.append(update_data)
        
        # Subscribe to the resource
        subscription_id = self.client.subscribe_to_resource(
            server_id=self.mock_server.server_id,
            uri="test://data/sample",
            callback=update_callback
        )
        
        assert subscription_id, "Failed to get subscription ID"
        
        # Unsubscribe
        success = self.client.unsubscribe_from_resource(subscription_id)
        
        assert success, "Failed to unsubscribe"
        
        self.logger.info("Resource subscription test passed")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test the MCP Client component")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    try:
        # Run the tests
        test_client = TestMCPClient()
        test_client.run_tests()
        
        return 0
    except Exception as e:
        logger.error(f"Error during testing: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())