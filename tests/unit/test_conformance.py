"""
Conformance testing for the MCP implementation.

This module contains tests that verify the conformance of the MCP implementation
to the MCP specification. It tests all message types and flows, including:

1. JSON-RPC message structure validation
2. Message flow validation
3. Capability negotiation
4. Tool and resource handling
5. Subscription management
6. Error handling

These tests ensure that the implementation follows the MCP protocol specification
and can interoperate with other MCP-compliant implementations.
"""

import unittest
import logging
import json
import uuid
import sys
import os
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List, Optional

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.client import MCPClient
from host.host import MCPHost, ConsentLevel
from server.server import MCPServer
from server.tools import execute_shell_command
from server.resources import FileResourceProvider


class TestMCPConformance(unittest.TestCase):
    """Test cases for MCP protocol conformance."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("test_mcp_conformance")
        
        # Create a config dictionary
        self.config = {
            'mcp': {
                'host_id': 'test-host',
                'server_id': 'test-server',
                'client_id': 'test-client',
                'default_consent_level': 'BASIC',
                'auto_consent': True
            },
            'auth': {
                'provider': 'basic',
                'session_timeout': 3600  # 1 hour
            },
            'context': {
                'storage': 'memory',
                'cleanup_interval': 3600  # 1 hour
            },
            'resources': {
                'file_base_path': os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            }
        }
        
        # Create a host
        self.host = MCPHost(logger=self.logger, config=self.config)
        
        # Create a server
        self.server = MCPServer(server_id='test-server', logger=self.logger, config=self.config)
        
        # Register tools
        self.server.register_tool(execute_shell_command)
        
        # Register resource providers
        file_provider = FileResourceProvider(base_path=self.config['resources']['file_base_path'])
        self.server.register_resource_provider("file", file_provider)
        
        # Create a client
        self.client = MCPClient(logger=self.logger, config=self.config)
        
        # Register the server with the host
        server_info = {
            "capabilities": self.server.capabilities,
            "server_id": "test-server",
            "description": "Test Server",
            "version": "1.0.0",
            "primitives": {
                "tools": True,
                "resources": True,
                "prompts": False
            }
        }
        self.host.register_server("test-server", server_info, self.server)
        
        # Register the client with the host
        client_info = {
            "capabilities": {
                "tools": True,
                "resources": True,
                "subscriptions": True
            },
            "client_id": "test-client",
            "name": "Test Client"
        }
        self.host.register_client("test-client", client_info, self.client)
        
        # Connect the client to the host
        self.client.connect_to_host(self.host)
        
        # Register consent for all operations
        self.consent_id = self.host.register_consent(
            client_id="test-client",
            server_id="test-server",
            operation_pattern="*",
            consent_level=ConsentLevel.FULL
        )

    def tearDown(self):
        """Tear down test fixtures."""
        # Disconnect the client from the host
        self.client.disconnect_from_host()
        
        # Unregister the client
        self.host.unregister_client("test-client")
        
        # Unregister the server
        self.host.unregister_server("test-server")
        
        # Revoke consent
        if hasattr(self, 'consent_id'):
            self.host.revoke_consent(self.consent_id)

    # =========================================================================
    # JSON-RPC Message Structure Tests
    # =========================================================================
    
    def test_jsonrpc_request_structure(self):
        """Test that JSON-RPC requests have the correct structure."""
        # Create a request
        request = self.client.create_jsonrpc_request(
            method="test_method",
            params={"param1": "value1"},
            request_id="test-id"
        )
        
        # Verify the request structure
        self.assertEqual(request["jsonrpc"], "2.0")
        self.assertEqual(request["id"], "test-id")
        self.assertEqual(request["method"], "test_method")
        self.assertEqual(request["params"], {"param1": "value1"})
        
        # Verify that all required fields are present
        self.assertIn("jsonrpc", request)
        self.assertIn("id", request)
        self.assertIn("method", request)
        self.assertIn("params", request)

    def test_jsonrpc_notification_structure(self):
        """Test that JSON-RPC notifications have the correct structure."""
        # Create a notification
        notification = self.client.create_jsonrpc_notification(
            method="test_method",
            params={"param1": "value1"}
        )
        
        # Verify the notification structure
        self.assertEqual(notification["jsonrpc"], "2.0")
        self.assertEqual(notification["method"], "test_method")
        self.assertEqual(notification["params"], {"param1": "value1"})
        
        # Verify that the id field is not present
        self.assertNotIn("id", notification)
        
        # Verify that all required fields are present
        self.assertIn("jsonrpc", notification)
        self.assertIn("method", notification)
        self.assertIn("params", notification)

    def test_jsonrpc_response_structure(self):
        """Test that JSON-RPC responses have the correct structure."""
        # Create a response
        response = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "result": {"status": "success"}
        }
        
        # Verify the response structure
        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertEqual(response["id"], "test-id")
        self.assertEqual(response["result"], {"status": "success"})
        
        # Verify that all required fields are present
        self.assertIn("jsonrpc", response)
        self.assertIn("id", response)
        self.assertIn("result", response)
        
        # Verify that the error field is not present
        self.assertNotIn("error", response)

    def test_jsonrpc_error_response_structure(self):
        """Test that JSON-RPC error responses have the correct structure."""
        # Create an error response
        error_response = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "error": {
                "code": -32600,
                "message": "Invalid Request"
            }
        }
        
        # Verify the error response structure
        self.assertEqual(error_response["jsonrpc"], "2.0")
        self.assertEqual(error_response["id"], "test-id")
        self.assertEqual(error_response["error"]["code"], -32600)
        self.assertEqual(error_response["error"]["message"], "Invalid Request")
        
        # Verify that all required fields are present
        self.assertIn("jsonrpc", error_response)
        self.assertIn("id", error_response)
        self.assertIn("error", error_response)
        self.assertIn("code", error_response["error"])
        self.assertIn("message", error_response["error"])
        
        # Verify that the result field is not present
        self.assertNotIn("result", error_response)

    # =========================================================================
    # Message Flow Tests
    # =========================================================================
    
    def test_request_response_flow(self):
        """Test the request-response flow between client and server."""
        # Send a request to the server
        response = self.client.send_request_to_server(
            server_id="test-server",
            method="tools/list",
            params={}
        )
        
        # Verify that a response was received
        self.assertIsNotNone(response)
        self.assertIn("status", response)
        self.assertEqual(response["status"], "success")
        self.assertIn("data", response)
        
        # Verify that the response contains the expected data
        self.assertIsInstance(response["data"], list)
        self.assertIn("execute_shell_command", [tool["name"] for tool in response["data"]])

    def test_notification_flow(self):
        """Test the notification flow from client to server."""
        # Create a mock server to track notifications
        mock_server = MagicMock()
        mock_server.handle_jsonrpc_notification = MagicMock()
        
        # Register the mock server
        server_info = {
            "capabilities": {
                "tools": True,
                "resources": True,
                "subscriptions": True
            },
            "server_id": "mock-server"
        }
        self.host.register_server("mock-server", server_info, mock_server)
        
        # Send a notification to the server
        self.client.send_notification_to_server(
            server_id="mock-server",
            method="test_notification",
            params={"param1": "value1"}
        )
        
        # Verify that the notification was received by the server
        mock_server.handle_jsonrpc_notification.assert_called_once()
        
        # Get the notification that was received
        args, _ = mock_server.handle_jsonrpc_notification.call_args
        notification = args[0]
        
        # Verify the notification structure
        self.assertEqual(notification["jsonrpc"], "2.0")
        self.assertEqual(notification["method"], "test_notification")
        self.assertEqual(notification["params"], {"param1": "value1"})
        self.assertNotIn("id", notification)

    def test_batch_request_flow(self):
        """Test the batch request flow between client and server."""
        # Create a batch of requests
        batch = [
            self.client.create_jsonrpc_request(
                method="tools/list",
                params={},
                request_id="request-1"
            ),
            self.client.create_jsonrpc_request(
                method="resources/list",
                params={"provider": "file", "path": "examples"},
                request_id="request-2"
            )
        ]
        
        # Send the batch request to the server
        responses = self.client.send_batch_request_to_server(
            server_id="test-server",
            batch=batch
        )
        
        # Verify that responses were received
        self.assertIsNotNone(responses)
        self.assertIsInstance(responses, list)
        self.assertEqual(len(responses), 2)
        
        # Verify the first response
        self.assertEqual(responses[0]["id"], "request-1")
        self.assertIn("result", responses[0])
        
        # Verify the second response
        self.assertEqual(responses[1]["id"], "request-2")
        self.assertIn("result", responses[1])

    # =========================================================================
    # Capability Negotiation Tests
    # =========================================================================
    
    def test_capability_negotiation(self):
        """Test capability negotiation between client and server."""
        # Negotiate capabilities
        capabilities = self.client.negotiate_capabilities("test-server")
        
        # Verify that capabilities were negotiated
        self.assertIsNotNone(capabilities)
        self.assertIn("tools", capabilities)
        self.assertIn("resources", capabilities)
        self.assertIn("subscriptions", capabilities)
        
        # Verify that the capabilities match the server's capabilities
        self.assertEqual(capabilities["tools"], self.server.capabilities["tools"])
        self.assertEqual(capabilities["resources"], self.server.capabilities["resources"])
        self.assertEqual(capabilities["subscriptions"], self.server.capabilities["subscriptions"])

    def test_capability_mismatch_handling(self):
        """Test handling of capability mismatches between client and server."""
        # Create a server with limited capabilities
        limited_server = MCPServer(server_id='limited-server', logger=self.logger, config=self.config)
        
        # Modify the server's capabilities
        limited_server.capabilities["tools"] = False
        limited_server.capabilities["resources"] = False
        
        # Register the server with the host
        server_info = {
            "capabilities": limited_server.capabilities,
            "server_id": "limited-server"
        }
        self.host.register_server("limited-server", server_info, limited_server)
        
        # Negotiate capabilities
        capabilities = self.client.negotiate_capabilities("limited-server")
        
        # Verify that capabilities were negotiated
        self.assertIsNotNone(capabilities)
        self.assertIn("tools", capabilities)
        self.assertIn("resources", capabilities)
        self.assertIn("subscriptions", capabilities)
        
        # Verify that the capabilities reflect the limitations
        self.assertFalse(capabilities["tools"])
        self.assertFalse(capabilities["resources"])
        self.assertTrue(capabilities["subscriptions"])
        
        # Attempt to use a tool (should fail)
        with self.assertRaises(Exception):
            self.client.send_request_to_server(
                server_id="limited-server",
                method="tools/list",
                params={}
            )

    # =========================================================================
    # Tool Handling Tests
    # =========================================================================
    
    def test_tool_listing(self):
        """Test listing available tools from a server."""
        # List tools
        tools = self.client.list_server_tools("test-server")
        
        # Verify that tools were listed
        self.assertIsNotNone(tools)
        self.assertIsInstance(tools, list)
        
        # Verify that the expected tool is in the list
        self.assertIn("execute_shell_command", [tool["name"] for tool in tools])

    def test_tool_details(self):
        """Test getting details for a specific tool."""
        # Get tool details
        tool_details = self.client.get_tool_details("test-server", "execute_shell_command")
        
        # Verify that tool details were retrieved
        self.assertIsNotNone(tool_details)
        self.assertEqual(tool_details["name"], "execute_shell_command")
        
        # Verify that the tool details include the required fields
        self.assertIn("description", tool_details)
        self.assertIn("inputSchema", tool_details)
        
        # Verify the input schema
        self.assertIn("type", tool_details["inputSchema"])
        self.assertIn("required", tool_details["inputSchema"])
        self.assertIn("properties", tool_details["inputSchema"])
        
        # Verify that the command parameter is required
        self.assertIn("command", tool_details["inputSchema"]["required"])
        
        # Verify the command parameter properties
        self.assertIn("command", tool_details["inputSchema"]["properties"])
        self.assertEqual(tool_details["inputSchema"]["properties"]["command"]["type"], "string")

    def test_tool_execution(self):
        """Test executing a tool on a server."""
        # Execute the tool
        result = self.client.execute_tool(
            server_id="test-server",
            tool_name="execute_shell_command",
            arguments={"command": "echo 'Hello, World!'"}
        )
        
        # Verify that the tool was executed successfully
        self.assertIsNotNone(result)
        self.assertIn("status", result)
        self.assertEqual(result["status"], "success")
        self.assertIn("data", result)
        
        # Verify the tool execution result
        self.assertIn("output", result["data"])
        self.assertIn("Hello, World!", result["data"]["output"])

    def test_tool_proxy(self):
        """Test creating and using a tool proxy."""
        # Create a tool proxy
        shell_command = self.client.create_tool_proxy("test-server", "execute_shell_command")
        
        # Verify that the proxy was created
        self.assertIsNotNone(shell_command)
        self.assertEqual(shell_command.__name__, "execute_shell_command")
        
        # Execute the tool using the proxy
        result = shell_command(command="echo 'Hello, World!'")
        
        # Verify that the tool was executed successfully
        self.assertIsNotNone(result)
        self.assertIn("status", result)
        self.assertEqual(result["status"], "success")
        self.assertIn("data", result)
        
        # Verify the tool execution result
        self.assertIn("output", result["data"])
        self.assertIn("Hello, World!", result["data"]["output"])

    def test_tool_validation(self):
        """Test validation of tool parameters."""
        # Create a tool proxy
        shell_command = self.client.create_tool_proxy("test-server", "execute_shell_command")
        
        # Attempt to execute the tool with missing required parameters
        with self.assertRaises(ValueError) as context:
            shell_command()
            
        # Verify that the validation error message is correct
        self.assertIn("Missing required parameter: command", str(context.exception))
        
        # Attempt to execute the tool with invalid parameter types
        with self.assertRaises(ValueError) as context:
            shell_command(command=123)
            
        # Verify that the validation error message is correct
        self.assertIn("Invalid parameter type", str(context.exception))

    # =========================================================================
    # Resource Handling Tests
    # =========================================================================
    
    def test_resource_listing(self):
        """Test listing available resources from a server."""
        # List resources
        resources = self.client.list_resources("test-server", "file", "examples")
        
        # Verify that resources were listed
        self.assertIsNotNone(resources)
        self.assertIsInstance(resources, list)
        
        # Verify that the expected resource is in the list
        self.assertIn("client_example.py", [resource["name"] for resource in resources])

    def test_resource_access(self):
        """Test accessing a resource from a server."""
        # Access a resource
        resource_data = self.client.access_resource(
            server_id="test-server",
            uri="resource://file/examples/client_example.py"
        )
        
        # Verify that the resource was accessed
        self.assertIsNotNone(resource_data)
        self.assertIn("content", resource_data)
        self.assertIn("metadata", resource_data)
        
        # Verify the resource content
        self.assertIn("Example script demonstrating the use of the MCP Client component", resource_data["content"])
        
        # Verify the resource metadata
        self.assertIn("mime_type", resource_data["metadata"])
        self.assertIn("size", resource_data["metadata"])
        self.assertIn("last_modified", resource_data["metadata"])

    def test_resource_uri_validation(self):
        """Test validation of resource URIs."""
        # Test with a valid URI
        valid_uri = "resource://file/examples/client_example.py"
        self.assertTrue(self.client.validate_resource_uri(valid_uri))
        
        # Test with an invalid URI (missing scheme)
        invalid_uri_1 = "file/examples/client_example.py"
        self.assertFalse(self.client.validate_resource_uri(invalid_uri_1))
        
        # Test with an invalid URI (wrong scheme)
        invalid_uri_2 = "http://file/examples/client_example.py"
        self.assertFalse(self.client.validate_resource_uri(invalid_uri_2))
        
        # Test with an invalid URI (missing provider)
        invalid_uri_3 = "resource:///examples/client_example.py"
        self.assertFalse(self.client.validate_resource_uri(invalid_uri_3))

    # =========================================================================
    # Subscription Management Tests
    # =========================================================================
    
    def test_resource_subscription(self):
        """Test subscribing to a resource."""
        # Create a callback function
        callback = MagicMock()
        
        # Subscribe to a resource
        subscription_id = self.client.subscribe_to_resource(
            server_id="test-server",
            uri="resource://file/examples/client_example.py",
            callback=callback
        )
        
        # Verify that the subscription was created
        self.assertIsNotNone(subscription_id)
        
        # Simulate a resource update
        update_data = {"content": "Updated content", "timestamp": 123456789}
        self.client.handle_resource_update(subscription_id, update_data)
        
        # Verify that the callback was called with the update data
        callback.assert_called_once_with(update_data)
        
        # Unsubscribe from the resource
        result = self.client.unsubscribe_from_resource(subscription_id)
        
        # Verify that the unsubscription was successful
        self.assertTrue(result)
        
        # Reset the mock
        callback.reset_mock()
        
        # Simulate another resource update
        self.client.handle_resource_update(subscription_id, update_data)
        
        # Verify that the callback was not called
        callback.assert_not_called()

    # =========================================================================
    # Error Handling Tests
    # =========================================================================
    
    def test_invalid_request_handling(self):
        """Test handling of invalid requests."""
        # Create an invalid request (missing method)
        invalid_request = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "params": {"param1": "value1"}
        }
        
        # Send the invalid request to the server
        with self.assertRaises(Exception) as context:
            self.host.route_request("test-server", invalid_request, "test-client")
            
        # Verify that an appropriate error was raised
        self.assertIn("Invalid Request", str(context.exception))

    def test_method_not_found_handling(self):
        """Test handling of requests for non-existent methods."""
        # Create a request for a non-existent method
        request = self.client.create_jsonrpc_request(
            method="non_existent_method",
            params={},
            request_id="test-id"
        )
        
        # Send the request to the server
        response = self.host.route_request("test-server", request, "test-client")
        
        # Verify that an error response was returned
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], -32601)
        self.assertEqual(response["error"]["message"], "Method not found")

    def test_invalid_params_handling(self):
        """Test handling of requests with invalid parameters."""
        # Create a request with invalid parameters
        request = self.client.create_jsonrpc_request(
            method="tools/execute",
            params={"tool_name": "execute_shell_command"},  # Missing 'arguments' parameter
            request_id="test-id"
        )
        
        # Send the request to the server
        response = self.host.route_request("test-server", request, "test-client")
        
        # Verify that an error response was returned
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], -32602)
        self.assertEqual(response["error"]["message"], "Invalid params")

    def test_server_error_handling(self):
        """Test handling of server errors."""
        # Create a mock server that raises an exception
        mock_server = MagicMock()
        mock_server.handle_jsonrpc_request.side_effect = Exception("Test server error")
        
        # Register the mock server
        server_info = {
            "capabilities": {
                "tools": True,
                "resources": True,
                "subscriptions": True
            },
            "server_id": "error-server"
        }
        self.host.register_server("error-server", server_info, mock_server)
        
        # Create a request
        request = self.client.create_jsonrpc_request(
            method="test_method",
            params={},
            request_id="test-id"
        )
        
        # Send the request to the server
        response = self.host.route_request("error-server", request, "test-client")
        
        # Verify that an error response was returned
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], -32000)
        self.assertEqual(response["error"]["message"], "Server error")
        self.assertIn("data", response["error"])
        self.assertIn("Test server error", response["error"]["data"])

    # =========================================================================
    # Consent Management Tests
    # =========================================================================
    
    def test_consent_enforcement(self):
        """Test enforcement of consent for operations."""
        # Revoke all consent
        self.host.revoke_consent(self.consent_id)
        
        # Attempt to execute a tool without consent
        request = self.client.create_jsonrpc_request(
            method="tools/execute",
            params={"tool_name": "execute_shell_command", "arguments": {"command": "echo 'Hello'"}},
            request_id="test-id"
        )
        
        # Send the request to the server
        response = self.host.route_request("test-server", request, "test-client")
        
        # Verify that an error response was returned
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], -32001)
        self.assertEqual(response["error"]["message"], "Consent required")
        
        # Register consent for tools only
        self.consent_id = self.host.register_consent(
            client_id="test-client",
            server_id="test-server",
            operation_pattern="tools/*",
            consent_level=ConsentLevel.BASIC
        )
        
        # Attempt to execute a tool with consent
        response = self.host.route_request("test-server", request, "test-client")
        
        # Verify that the request was processed
        self.assertIn("result", response)
        
        # Attempt to access a resource without consent
        resource_request = self.client.create_jsonrpc_request(
            method="resources/access",
            params={"uri": "resource://file/examples/client_example.py"},
            request_id="test-id"
        )
        
        # Send the request to the server
        response = self.host.route_request("test-server", resource_request, "test-client")
        
        # Verify that an error response was returned
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], -32001)
        self.assertEqual(response["error"]["message"], "Consent required")


if __name__ == "__main__":
    unittest.main()