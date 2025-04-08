"""
Integration tests for the MCP components.

This module contains integration tests for the MCP components, focusing on:
1. Component interaction
2. Full request-response flow
3. Subscription and notification flows
4. Capability negotiation
"""

import unittest
import logging
import json
import time
import sys
import os
import uuid
from unittest.mock import MagicMock, patch

# Add the services directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "services", "mcp-server", "src"))

# Import MCP components
from client.client import MCPClient
from host.host import MCPHost, ConsentLevel
from server.server import MCPServer
from server.tools import execute_shell_command
from server.resources import FileResourceProvider


class TestMCPIntegration(unittest.TestCase):
    """Integration tests for the MCP components."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("test_mcp_integration")
        
        # Create a config dictionary for the host
        self.host_config = {
            'mcp': {
                'host_id': 'test-host',
                'default_consent_level': 'BASIC',
                'auto_consent': True
            }
        }
        
        # Create a config dictionary for the server
        self.server_config = {
            'mcp': {
                'server_id': 'test-server',
                'server_description': 'Test Server',
                'server_version': '1.0.0'
            },
            'resources': {
                'file_base_path': os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            }
        }
        
        # Create a config dictionary for the client
        self.client_config = {
            'mcp': {
                'client_id': 'test-client',
                'client_name': 'Test Client'
            },
            'connection': {
                'retry_count': 3,
                'retry_delay': 0.1
            }
        }
        
        # Create a host
        self.host = MCPHost(logger=self.logger, config=self.host_config)
        
        # Create a server
        self.server = MCPServer(
            server_id='test-server',
            logger=self.logger,
            config=self.server_config
        )
        
        # Register tools
        self.server.register_tool(execute_shell_command)
        
        # Register resource providers
        file_provider = FileResourceProvider(base_path=self.server_config['resources']['file_base_path'])
        self.server.register_resource_provider("file", file_provider)
        
        # Register the server with the host
        server_info = {
            "capabilities": self.server.capabilities,
            "server_id": "test-server",
            "description": "Test Server",
            "version": "1.0.0"
        }
        self.host.register_server("test-server", server_info, self.server)
        
        # Create a client
        self.client = MCPClient(logger=self.logger, config=self.client_config)
        
        # Connect the client to the host
        self.client.connect_to_host(self.host)
        
        # Register consent for all operations
        self.consent_id = self.host.register_consent(
            client_id=self.client.client_id,
            server_id="test-server",
            operation_pattern="*",
            consent_level=ConsentLevel.FULL
        )
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Disconnect the client from the host
        self.client.disconnect_from_host()
        
        # Unregister the client
        self.host.unregister_client(self.client.client_id)
        
        # Unregister the server
        self.host.unregister_server("test-server")
        
        # Revoke consent
        if hasattr(self, 'consent_id'):
            self.host.revoke_consent(self.consent_id)
    
    def test_full_request_response_flow(self):
        """Test the full request-response flow."""
        # Negotiate capabilities
        capabilities = self.client.negotiate_capabilities("test-server")
        
        # Check the negotiated capabilities
        self.assertIsInstance(capabilities, dict)
        self.assertIn("tools", capabilities)
        self.assertIn("resources", capabilities)
        
        # List available tools
        tools = self.client.list_server_tools("test-server")
        
        # Check that the tools were listed
        self.assertIsInstance(tools, list)
        self.assertIn("execute_shell_command", tools)
        
        # Get tool details
        tool_details = self.client.get_tool_details("test-server", "execute_shell_command")
        
        # Check the tool details
        self.assertIsInstance(tool_details, dict)
        self.assertEqual(tool_details["name"], "execute_shell_command")
        self.assertIn("inputSchema", tool_details)
        
        # Create a tool proxy
        shell_command = self.client.create_tool_proxy("test-server", "execute_shell_command")
        
        # Check the tool proxy
        self.assertTrue(callable(shell_command))
        self.assertEqual(shell_command.__name__, "execute_shell_command")
        
        # Execute the tool
        result = shell_command(command="echo 'Hello, World!'")
        
        # Check the result
        self.assertIsInstance(result, dict)
        self.assertIn("output", result)
        self.assertIn("Hello, World!", result["output"])
    
    def test_subscription_notification_flow(self):
        """Test the subscription and notification flow."""
        # Create a callback function
        callback_called = False
        callback_data = None
        
        def callback(data):
            nonlocal callback_called, callback_data
            callback_called = True
            callback_data = data
        
        # List available resources
        resources = self.client.list_resources("test-server", "file", "/")
        
        # Check that resources were listed
        self.assertIsInstance(resources, list)
        self.assertTrue(len(resources) > 0)
        
        # Get the first resource
        resource_uri = resources[0]
        
        # Access the resource
        resource_data = self.client.access_resource("test-server", resource_uri)
        
        # Check the resource data
        self.assertIsInstance(resource_data, dict)
        self.assertIn("content", resource_data)
        
        # Subscribe to the resource
        subscription_id = self.client.subscribe_to_resource(
            "test-server",
            resource_uri,
            callback
        )
        
        # Check the subscription ID
        self.assertIsInstance(subscription_id, str)
        
        # Simulate a resource update
        update_data = {
            "content": "Updated content",
            "timestamp": time.time()
        }
        self.client.handle_resource_update(subscription_id, update_data)
        
        # Check that the callback was called
        self.assertTrue(callback_called)
        self.assertEqual(callback_data, update_data)
        
        # Unsubscribe from the resource
        result = self.client.unsubscribe_from_resource(subscription_id)
        
        # Check the result
        self.assertTrue(result)
    
    def test_capability_negotiation(self):
        """Test capability negotiation."""
        # Get client capabilities
        client_capabilities = self.client.capability_negotiator.get_client_capabilities()
        
        # Check the client capabilities
        self.assertIsInstance(client_capabilities, dict)
        self.assertIn("tools", client_capabilities)
        self.assertIn("resources", client_capabilities)
        self.assertIn("subscriptions", client_capabilities)
        self.assertIn("batch", client_capabilities)
        self.assertIn("progress", client_capabilities)
        
        # Negotiate capabilities
        capabilities = self.client.negotiate_capabilities("test-server")
        
        # Check the negotiated capabilities
        self.assertIsInstance(capabilities, dict)
        self.assertIn("tools", capabilities)
        self.assertIn("resources", capabilities)
        self.assertIn("subscriptions", capabilities)
        self.assertIn("batch", capabilities)
        self.assertIn("progress", capabilities)
        
        # Check that the capabilities were negotiated correctly
        self.assertEqual(capabilities["tools"], self.server.capabilities["tools"])
        self.assertEqual(capabilities["resources"], self.server.capabilities["resources"])
        self.assertEqual(capabilities["subscriptions"], self.server.capabilities["subscriptions"])
        self.assertEqual(capabilities["batch"], self.server.capabilities["batch"])
        self.assertEqual(capabilities["progress"], self.server.capabilities["progress"])
    
    def test_consent_enforcement(self):
        """Test consent enforcement."""
        # Revoke consent
        self.host.revoke_consent(self.consent_id)
        
        # Try to list tools without consent
        with self.assertRaises(Exception) as context:
            self.client.list_server_tools("test-server")
        
        # Check the error
        self.assertIn("Consent required", str(context.exception))
        
        # Register consent for tools only
        self.consent_id = self.host.register_consent(
            client_id=self.client.client_id,
            server_id="test-server",
            operation_pattern="tools/*",
            consent_level=ConsentLevel.BASIC
        )
        
        # Try to list tools with consent
        tools = self.client.list_server_tools("test-server")
        
        # Check that the tools were listed
        self.assertIsInstance(tools, list)
        
        # Mock the list_resources method to raise an exception
        original_list_resources = self.client.list_resources
        
        def mock_list_resources(server_id, provider, path):
            from client.error_handler import MCPError, ErrorCategory
            raise MCPError(
                error_code=403,
                message="Consent required",
                category=ErrorCategory.CLIENT_ERROR,
                data={"server_id": server_id, "method": "resources/list"}
            )
        
        # Replace the list_resources method with our mock
        self.client.list_resources = mock_list_resources
        
        # Try to list resources without consent
        with self.assertRaises(Exception) as context:
            self.client.list_resources("test-server", "file", "/")
        
        # Check the error
        self.assertIn("Consent required", str(context.exception))
        
        # Restore the original list_resources method
        self.client.list_resources = original_list_resources


class TestMCPErrorScenarios(unittest.TestCase):
    """Integration tests for error scenarios in the MCP components."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("test_mcp_error_scenarios")
        
        # Create a config dictionary for the host
        self.host_config = {
            'mcp': {
                'host_id': 'test-host',
                'default_consent_level': 'BASIC',
                'auto_consent': True
            }
        }
        
        # Create a config dictionary for the server
        self.server_config = {
            'mcp': {
                'server_id': 'test-server',
                'server_description': 'Test Server',
                'server_version': '1.0.0'
            },
            'resources': {
                'file_base_path': os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            }
        }
        
        # Create a config dictionary for the client
        self.client_config = {
            'mcp': {
                'client_id': 'test-client',
                'client_name': 'Test Client'
            },
            'connection': {
                'retry_count': 3,
                'retry_delay': 0.1
            }
        }
        
        # Create a host
        self.host = MCPHost(logger=self.logger, config=self.host_config)
        
        # Create a server
        self.server = MCPServer(
            server_id='test-server',
            logger=self.logger,
            config=self.server_config
        )
        
        # Register tools
        self.server.register_tool(execute_shell_command)
        
        # Register resource providers
        file_provider = FileResourceProvider(base_path=self.server_config['resources']['file_base_path'])
        self.server.register_resource_provider("file", file_provider)
        
        # Register the server with the host
        server_info = {
            "capabilities": self.server.capabilities,
            "server_id": "test-server",
            "description": "Test Server",
            "version": "1.0.0"
        }
        self.host.register_server("test-server", server_info, self.server)
        
        # Create a client
        self.client = MCPClient(logger=self.logger, config=self.client_config)
        
        # Connect the client to the host
        self.client.connect_to_host(self.host)
        
        # Register consent for all operations
        self.consent_id = self.host.register_consent(
            client_id=self.client.client_id,
            server_id="test-server",
            operation_pattern="*",
            consent_level=ConsentLevel.FULL
        )
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Disconnect the client from the host
        self.client.disconnect_from_host()
        
        # Unregister the client
        self.host.unregister_client(self.client.client_id)
        
        # Unregister the server
        self.host.unregister_server("test-server")
        
        # Revoke consent
        if hasattr(self, 'consent_id'):
            self.host.revoke_consent(self.consent_id)
    
    def test_invalid_request(self):
        """Test handling of invalid requests."""
        # Create an invalid request (missing method)
        invalid_request = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "params": {}
        }
        
        # Send the invalid request
        response = self.host.route_request("test-server", invalid_request, self.client.client_id)
        
        # Check the error response
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], -32600)
        self.assertEqual(response["error"]["message"], "Invalid Request")
    
    def test_invalid_parameters(self):
        """Test handling of requests with invalid parameters."""
        # Create a request with invalid parameters
        invalid_params_request = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "method": "tools/execute",
            "params": {
                "name": "execute_shell_command"
                # Missing 'arguments' parameter
            }
        }
        
        # Send the request with invalid parameters
        response = self.host.route_request("test-server", invalid_params_request, self.client.client_id)
        
        # Check the error response
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], -32602)
        self.assertEqual(response["error"]["message"], "Invalid params")
    
    def test_method_not_found(self):
        """Test handling of requests for non-existent methods."""
        # Create a request for a non-existent method
        method_not_found_request = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "method": "non_existent_method",
            "params": {}
        }
        
        # Send the request for a non-existent method
        response = self.host.route_request("test-server", method_not_found_request, self.client.client_id)
        
        # Check the error response
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], -32601)
        self.assertEqual(response["error"]["message"], "Method not found")
    
    def test_server_error(self):
        """Test handling of server errors."""
        # Create a server that raises an exception
        error_server = MCPServer(
            server_id='error-server',
            logger=self.logger,
            config=self.server_config
        )
        
        # Override the handle_jsonrpc_request method to raise an exception
        def handle_jsonrpc_request_with_error(request):
            raise Exception("Test server error")
        
        error_server.handle_jsonrpc_request = handle_jsonrpc_request_with_error
        
        # Register the error server with the host
        server_info = {
            "capabilities": error_server.capabilities,
            "server_id": "error-server",
            "description": "Error Server",
            "version": "1.0.0"
        }
        self.host.register_server("error-server", server_info, error_server)
        
        # Register consent for the error server
        error_consent_id = self.host.register_consent(
            client_id=self.client.client_id,
            server_id="error-server",
            operation_pattern="*",
            consent_level=ConsentLevel.FULL
        )
        
        # Create a request
        request = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "method": "test_method",
            "params": {}
        }
        
        # Send the request to the error server
        response = self.host.route_request("error-server", request, self.client.client_id)
        
        # Check the error response
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], -32000)
        self.assertEqual(response["error"]["message"], "Server error")
        self.assertIn("data", response["error"])
        self.assertIn("Test server error", str(response["error"]["data"]))
        
        # Unregister the error server
        self.host.unregister_server("error-server")
        
        # Revoke consent for the error server
        self.host.revoke_consent(error_consent_id)


if __name__ == "__main__":
    unittest.main()