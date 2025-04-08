"""
Test script for the MCP Client component.

This script tests the functionality of the MCP Client component,
including JSON-RPC message formatting, routing, subscription handling,
and protocol conformance.
"""

import logging
import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.client import MCPClient
from host.host import MCPHost, ConsentLevel
from server.server import MCPServer
from server.tools import execute_shell_command
from server.resources import FileResourceProvider


class TestMCPClient(unittest.TestCase):
    """Test cases for the MCP Client component."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("test_mcp_client")
        
        # Create a config dictionary
        self.config = {
            'mcp': {
                'server_id': 'test-server',
                'host_enabled': True,
                'client_enabled': True,
                'server_enabled': True,
            }
        }
        
        # Create a mock host
        self.host = MCPHost(logger=self.logger, config=self.config)
        
        # Create a mock server
        self.server = MCPServer(server_id='test-server', logger=self.logger, config=self.config)
        
        # Register the server with the host
        server_info = {
            "capabilities": self.server.capabilities,
            "server_id": "test-server"
        }
        self.host.register_server("test-server", server_info, self.server)
        
        # Create the client
        self.client = MCPClient(logger=self.logger, config=self.config)
        
        # Connect the client to the host
        self.client.connect_to_host(self.host)
        
    def test_create_jsonrpc_request(self):
        """Test creating a JSON-RPC request."""
        request = self.client.create_jsonrpc_request("test_method", {"param1": "value1"}, "test-id")
        
        self.assertEqual(request["jsonrpc"], "2.0")
        self.assertEqual(request["id"], "test-id")
        self.assertEqual(request["method"], "test_method")
        self.assertEqual(request["params"], {"param1": "value1"})
        
    def test_create_jsonrpc_notification(self):
        """Test creating a JSON-RPC notification."""
        notification = self.client.create_jsonrpc_notification("test_method", {"param1": "value1"})
        
        self.assertEqual(notification["jsonrpc"], "2.0")
        self.assertEqual(notification["method"], "test_method")
        self.assertEqual(notification["params"], {"param1": "value1"})
        self.assertNotIn("id", notification)
        
    def test_parse_jsonrpc_response(self):
        """Test parsing a JSON-RPC response."""
        response = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "result": {"status": "success"}
        }
        
        parsed = self.client.parse_jsonrpc_response(response)
        
        self.assertEqual(parsed["status"], "success")
        self.assertEqual(parsed["data"], {"status": "success"})
        
    def test_parse_jsonrpc_error_response(self):
        """Test parsing a JSON-RPC error response."""
        response = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "error": {
                "code": -32600,
                "message": "Invalid Request"
            }
        }
        
        with self.assertRaises(ValueError) as context:
            self.client.parse_jsonrpc_response(response)
            
        self.assertIn("JSON-RPC error -32600: Invalid Request", str(context.exception))
        
    @patch('server.server.MCPServer.handle_jsonrpc_request')
    def test_send_request_to_server(self, mock_handle_request):
        """Test sending a request to a server."""
        # Mock the server's handle_jsonrpc_request method
        mock_handle_request.return_value = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "result": {"status": "success"}
        }
        
        # Send a request to the server
        response = self.client.send_request_to_server("test-server", "test_method", {"param1": "value1"})
        
        # Check that the request was routed correctly
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], {"status": "success"})
        
    def test_negotiate_capabilities(self):
        """Test capability negotiation."""
        # Mock the server's handle_jsonrpc_request method to return capabilities
        with patch.object(self.server, 'handle_jsonrpc_request') as mock_handle_request:
            mock_handle_request.return_value = {
                "jsonrpc": "2.0",
                "id": "test-id",
                "result": {
                    "capabilities": {
                        "tools": True,
                        "resources": True,
                        "subscriptions": False
                    },
                    "server_id": "test-server"
                }
            }
            
            # Negotiate capabilities
            capabilities = self.client.negotiate_capabilities("test-server")
            
            # Check that the capabilities were negotiated correctly
            self.assertTrue(capabilities["tools"])
            self.assertTrue(capabilities["resources"])
            self.assertFalse(capabilities["subscriptions"])
            
    def test_create_tool_proxy(self):
        """Test creating a tool proxy."""
        # Mock the server's handle_jsonrpc_request method to return tool details
        with patch.object(self.server, 'handle_jsonrpc_request') as mock_handle_request:
            # First call for tool details
            mock_handle_request.side_effect = [
                {
                    "jsonrpc": "2.0",
                    "id": "test-id",
                    "result": {
                        "name": "test_tool",
                        "description": "Test tool",
                        "inputSchema": {
                            "type": "object",
                            "required": ["param1"],
                            "properties": {
                                "param1": {"type": "string"}
                            }
                        }
                    }
                },
                # Second call for tool execution
                {
                    "jsonrpc": "2.0",
                    "id": "test-id",
                    "result": {"status": "success"}
                }
            ]
            
            # Create a tool proxy
            tool_proxy = self.client.create_tool_proxy("test-server", "test_tool")
            
            # Check that the proxy was created correctly
            self.assertEqual(tool_proxy.__name__, "test_tool")
            self.assertEqual(tool_proxy.__doc__, "Test tool")
            
            # Execute the tool proxy
            result = tool_proxy(param1="value1")
            
            # Check that the tool was executed correctly
            self.assertEqual(result, {"status": "success"})
            
            # Check that the tool proxy validates parameters
            with self.assertRaises(ValueError) as context:
                tool_proxy()
                
            self.assertIn("Missing required parameter: param1", str(context.exception))
class TestMCPClientConformance(unittest.TestCase):
    """Test cases for MCP Client protocol conformance."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("test_mcp_client_conformance")
        
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

    def test_jsonrpc_request_conformance(self):
        """Test that JSON-RPC requests conform to the MCP specification."""
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

    def test_jsonrpc_notification_conformance(self):
        """Test that JSON-RPC notifications conform to the MCP specification."""
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

    def test_tool_execution_conformance(self):
        """Test that tool execution conforms to the MCP specification."""
        # Execute a tool
        result = self.client.execute_tool(
            server_id="test-server",
            tool_name="execute_shell_command",
            arguments={"command": "echo 'Hello, World!'"}
        )
        
        # Verify the result structure
        self.assertIn("status", result)
        self.assertIn("data", result)
        
        # Verify that the tool was executed successfully
        self.assertEqual(result["status"], "success")
        
        # Verify the tool execution result
        self.assertIn("output", result["data"])
        self.assertIn("Hello, World!", result["data"]["output"])

    def test_resource_uri_conformance(self):
        """Test that resource URIs conform to the MCP specification."""
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


if __name__ == "__main__":
    unittest.main()
if __name__ == "__main__":
    unittest.main()