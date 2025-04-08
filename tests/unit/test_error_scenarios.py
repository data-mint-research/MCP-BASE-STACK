"""
Unit tests for error scenarios in the MCP components.

This module contains tests for error scenarios in the MCP components, focusing on:
1. Invalid requests
2. Invalid parameters
3. Server errors
4. Consent enforcement
"""

import unittest
import logging
import json
from unittest.mock import MagicMock, patch
import sys
import os
import uuid

# Add the services directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "services", "mcp-server", "src"))

# Import MCP components
from client.client import MCPClient
from client.error_handler import ValidationError, NetworkError, ResourceError, ToolError, MCPError, ErrorCode
from host.host import MCPHost, ConsentLevel
from server.server import MCPServer


class TestInvalidRequests(unittest.TestCase):
    """Test cases for handling invalid requests."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("test_invalid_requests")
        
        # Create a host
        self.host = MCPHost(
            logger=self.logger,
            config={'mcp': {'host_id': 'test-host'}}
        )
        
        # Create a server
        self.server = MCPServer(
            server_id='test-server',
            logger=self.logger,
            config={'mcp': {'server_id': 'test-server'}}
        )
        
        # Register the server with the host
        server_info = {
            "capabilities": self.server.capabilities,
            "server_id": "test-server"
        }
        self.host.register_server("test-server", server_info, self.server)
        
        # Create a client
        self.client = MCPClient(
            logger=self.logger,
            config={'mcp': {'client_id': 'test-client'}}
        )
        
        # Connect the client to the host
        self.client.connect_to_host(self.host)
        
        # Register consent
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
    
    def test_missing_jsonrpc_version(self):
        """Test handling a request with a missing JSON-RPC version."""
        # Create a request with a missing JSON-RPC version
        request = {
            "id": "test-id",
            "method": "test_method",
            "params": {}
        }
        
        # Route the request
        response = self.host.route_request("test-server", request, "test-client")
        
        # Check the error response
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], -32600)
        self.assertEqual(response["error"]["message"], "Invalid Request")
    
    def test_invalid_jsonrpc_version(self):
        """Test handling a request with an invalid JSON-RPC version."""
        # Create a request with an invalid JSON-RPC version
        request = {
            "jsonrpc": "1.0",
            "id": "test-id",
            "method": "test_method",
            "params": {}
        }
        
        # Route the request
        response = self.host.route_request("test-server", request, "test-client")
        
        # Check the error response
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], -32600)
        self.assertEqual(response["error"]["message"], "Invalid Request")
    
    def test_missing_method(self):
        """Test handling a request with a missing method."""
        # Create a request with a missing method
        request = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "params": {}
        }
        
        # Route the request
        response = self.host.route_request("test-server", request, "test-client")
        
        # Check the error response
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], -32600)
        self.assertEqual(response["error"]["message"], "Invalid Request")
    
    def test_missing_params(self):
        """Test handling a request with missing params."""
        # Create a request with missing params
        request = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "method": "test_method"
        }
        
        # Route the request
        response = self.host.route_request("test-server", request, "test-client")
        
        # Check the error response
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], -32600)
        self.assertEqual(response["error"]["message"], "Invalid Request")
    
    def test_non_object_params(self):
        """Test handling a request with non-object params."""
        # Create a request with non-object params
        request = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "method": "test_method",
            "params": "not_an_object"
        }
        
        # Route the request
        response = self.host.route_request("test-server", request, "test-client")
        
        # Check the error response
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], -32600)
        self.assertEqual(response["error"]["message"], "Invalid Request")


class TestInvalidParameters(unittest.TestCase):
    """Test cases for handling invalid parameters."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("test_invalid_parameters")
        
        # Create a mock client
        self.client = MagicMock()
        self.client.logger = self.logger
        
        # Create a mock host
        self.host = MagicMock()
        
        # Connect the client to the host
        self.client.host = self.host
        self.client.connected = True
    
    def test_create_jsonrpc_request_with_empty_method(self):
        """Test creating a JSON-RPC request with an empty method."""
        # Create a real client for this test
        real_client = MCPClient(
            logger=self.logger,
            config={'mcp': {'client_id': 'test-client'}}
        )
        
        # Test creating a request with an empty method
        with self.assertRaises(ValidationError) as context:
            real_client.create_jsonrpc_request(
                method="",
                params={"param1": "value1"}
            )
        
        # Check the error
        self.assertIn("Method cannot be empty", str(context.exception))
    
    def test_create_jsonrpc_request_with_non_dict_params(self):
        """Test creating a JSON-RPC request with non-dict params."""
        # Create a real client for this test
        real_client = MCPClient(
            logger=self.logger,
            config={'mcp': {'client_id': 'test-client'}}
        )
        
        # Test creating a request with non-dict params
        with self.assertRaises(ValidationError) as context:
            real_client.create_jsonrpc_request(
                method="test_method",
                params="not_a_dict"
            )
        
        # Check the error
        self.assertIn("Params must be a dictionary", str(context.exception))
    
    def test_send_request_with_empty_server_id(self):
        """Test sending a request with an empty server ID."""
        # Create a real client for this test
        real_client = MCPClient(
            logger=self.logger,
            config={'mcp': {'client_id': 'test-client'}}
        )
        
        # Connect to a mock host
        real_client.connect_to_host(self.host)
        
        # Test sending a request with an empty server ID
        with self.assertRaises(ValidationError) as context:
            real_client.send_request_to_server(
                server_id="",
                method="test_method",
                params={"param1": "value1"}
            )
        
        # Check the error
        self.assertIn("Server ID cannot be empty", str(context.exception))
        
        # Disconnect from the host
        real_client.disconnect_from_host()
    
    def test_list_resources_with_invalid_parameters(self):
        """Test listing resources with invalid parameters."""
        # Create a real client for this test
        real_client = MCPClient(
            logger=self.logger,
            config={'mcp': {'client_id': 'test-client'}}
        )
        
        # Connect to a mock host
        real_client.connect_to_host(self.host)
        
        # Test listing resources with an empty server ID
        with self.assertRaises(ValidationError) as context:
            real_client.list_resources(
                server_id="",
                provider="file",
                path="/"
            )
        
        # Check the error
        self.assertIn("Server ID cannot be empty", str(context.exception))
        
        # Test listing resources with an empty provider
        with self.assertRaises(ValidationError) as context:
            real_client.list_resources(
                server_id="test-server",
                provider="",
                path="/"
            )
        
        # Check the error
        self.assertIn("Provider cannot be empty", str(context.exception))
        
        # Test listing resources with None as path
        with self.assertRaises(ValidationError) as context:
            real_client.list_resources(
                server_id="test-server",
                provider="file",
                path=None
            )
        
        # Check the error
        self.assertIn("Path cannot be None", str(context.exception))
        
        # Disconnect from the host
        real_client.disconnect_from_host()


class TestServerErrors(unittest.TestCase):
    """Test cases for handling server errors."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("test_server_errors")
        
        # Create a host
        self.host = MCPHost(
            logger=self.logger,
            config={'mcp': {'host_id': 'test-host'}}
        )
        
        # Create a server that raises an exception
        self.error_server = MagicMock()
        self.error_server.handle_jsonrpc_request.side_effect = Exception("Test server error")
        
        # Register the server with the host
        server_info = {
            "capabilities": {
                "tools": True,
                "resources": True,
                "subscriptions": True
            },
            "server_id": "error-server"
        }
        self.host.register_server("error-server", server_info, self.error_server)
        
        # Create a client
        self.client = MCPClient(
            logger=self.logger,
            config={'mcp': {'client_id': 'test-client'}}
        )
        
        # Connect the client to the host
        self.client.connect_to_host(self.host)
        
        # Register consent
        self.consent_id = self.host.register_consent(
            client_id="test-client",
            server_id="error-server",
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
        self.host.unregister_server("error-server")
        
        # Revoke consent
        if hasattr(self, 'consent_id'):
            self.host.revoke_consent(self.consent_id)
    
    def test_server_exception(self):
        """Test handling a server exception."""
        # Create a request
        request = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "method": "test_method",
            "params": {}
        }
        
        # Route the request
        response = self.host.route_request("error-server", request, "test-client")
        
        # Check the error response
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], -32000)
        self.assertEqual(response["error"]["message"], "Server error")
        self.assertIn("data", response["error"])
        self.assertIn("Test server error", str(response["error"]["data"]))
    
    def test_client_handling_server_error(self):
        """Test client handling of a server error."""
        # Mock the host's route_request method to return an error
        self.host.route_request.return_value = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "error": {
                "code": -32000,
                "message": "Server error",
                "data": "Test server error"
            }
        }
        
        # Send a request
        with self.assertRaises(MCPError) as context:
            self.client.send_request_to_server(
                server_id="error-server",
                method="test_method",
                params={}
            )
        
        # Check the error
        self.assertEqual(context.exception.error_code, -32000)
        self.assertEqual(context.exception.message, "Server error")
        self.assertIn("Test server error", str(context.exception.data))


class TestConsentEnforcement(unittest.TestCase):
    """Test cases for consent enforcement."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("test_consent_enforcement")
        
        # Create a host
        self.host = MCPHost(
            logger=self.logger,
            config={'mcp': {'host_id': 'test-host'}}
        )
        
        # Create a server
        self.server = MCPServer(
            server_id='test-server',
            logger=self.logger,
            config={'mcp': {'server_id': 'test-server'}}
        )
        
        # Register the server with the host
        server_info = {
            "capabilities": self.server.capabilities,
            "server_id": "test-server"
        }
        self.host.register_server("test-server", server_info, self.server)
        
        # Create a client
        self.client = MCPClient(
            logger=self.logger,
            config={'mcp': {'client_id': 'test-client'}}
        )
        
        # Connect the client to the host
        self.client.connect_to_host(self.host)
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Disconnect the client from the host
        self.client.disconnect_from_host()
        
        # Unregister the client
        self.host.unregister_client("test-client")
        
        # Unregister the server
        self.host.unregister_server("test-server")
        
        # Revoke consent if it exists
        if hasattr(self, 'consent_id'):
            self.host.revoke_consent(self.consent_id)
    
    def test_no_consent(self):
        """Test handling a request without consent."""
        # Create a request
        request = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "method": "test_method",
            "params": {}
        }
        
        # Route the request without consent
        response = self.host.route_request("test-server", request, "test-client")
        
        # Check the error response
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], -32001)
        self.assertEqual(response["error"]["message"], "Consent required")
    
    def test_partial_consent(self):
        """Test handling a request with partial consent."""
        # Register consent for tools only
        self.consent_id = self.host.register_consent(
            client_id="test-client",
            server_id="test-server",
            operation_pattern="tools/*",
            consent_level=ConsentLevel.BASIC
        )
        
        # Create a tools request
        tools_request = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "method": "tools/list",
            "params": {}
        }
        
        # Route the tools request with consent
        tools_response = self.host.route_request("test-server", tools_request, "test-client")
        
        # Check that the tools request was processed
        self.assertNotIn("error", tools_response)
        self.assertIn("result", tools_response)
        
        # Create a resources request
        resources_request = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "method": "resources/list",
            "params": {"provider": "file", "path": "/"}
        }
        
        # Route the resources request without consent
        resources_response = self.host.route_request("test-server", resources_request, "test-client")
        
        # Check the error response
        self.assertIn("error", resources_response)
        self.assertEqual(resources_response["error"]["code"], -32001)
        self.assertEqual(resources_response["error"]["message"], "Consent required")
    
    def test_full_consent(self):
        """Test handling a request with full consent."""
        # Register full consent
        self.consent_id = self.host.register_consent(
            client_id="test-client",
            server_id="test-server",
            operation_pattern="*",
            consent_level=ConsentLevel.FULL
        )
        
        # Create a request
        request = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "method": "tools/list",
            "params": {}
        }
        
        # Route the request with full consent
        response = self.host.route_request("test-server", request, "test-client")
        
        # Check that the request was processed
        self.assertNotIn("error", response)
        self.assertIn("result", response)
    
    def test_consent_revocation(self):
        """Test handling a request after consent revocation."""
        # Register consent
        self.consent_id = self.host.register_consent(
            client_id="test-client",
            server_id="test-server",
            operation_pattern="*",
            consent_level=ConsentLevel.FULL
        )
        
        # Create a request
        request = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "method": "tools/list",
            "params": {}
        }
        
        # Route the request with consent
        response_with_consent = self.host.route_request("test-server", request, "test-client")
        
        # Check that the request was processed
        self.assertNotIn("error", response_with_consent)
        self.assertIn("result", response_with_consent)
        
        # Revoke consent
        self.host.revoke_consent(self.consent_id)
        
        # Route the request after consent revocation
        response_without_consent = self.host.route_request("test-server", request, "test-client")
        
        # Check the error response
        self.assertIn("error", response_without_consent)
        self.assertEqual(response_without_consent["error"]["code"], -32001)
        self.assertEqual(response_without_consent["error"]["message"], "Consent required")


if __name__ == "__main__":
    unittest.main()