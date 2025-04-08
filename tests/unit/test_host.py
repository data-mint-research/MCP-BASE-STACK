"""
Test script for the MCP Host component.

This script tests the functionality of the MCP Host component,
including server and client management, request routing, consent handling,
and protocol conformance.
"""

import unittest
import logging
import json
import uuid
from unittest.mock import MagicMock, patch

import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from host.host import MCPHost, ConsentLevel
from server.server import MCPServer
from client.client import MCPClient
from server.tools import execute_shell_command
from server.resources import FileResourceProvider


class TestMCPHost(unittest.TestCase):
    """Test cases for the MCP Host component."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("test_mcp_host")
        
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
            }
        }
        
        # Create a host
        self.host = MCPHost(logger=self.logger, config=self.config)
        
        # Create a server
        self.server = MCPServer(server_id='test-server', logger=self.logger, config=self.config)
        
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
        
    def test_server_registration(self):
        """Test server registration and listing."""
        # Check that the server was registered
        servers = self.host.get_available_servers()
        self.assertIn("test-server", servers)
        
        # Get server info
        server_info = self.host.get_server_info("test-server")
        self.assertIsNotNone(server_info)
        self.assertEqual(server_info["server_id"], "test-server")
        self.assertEqual(server_info["description"], "Test Server")
        
        # Unregister the server
        result = self.host.unregister_server("test-server")
        self.assertTrue(result)
        
        # Check that the server was unregistered
        servers = self.host.get_available_servers()
        self.assertNotIn("test-server", servers)
        
    def test_client_registration(self):
        """Test client registration and listing."""
        # Check that the client was registered
        clients = self.host.get_registered_clients()
        self.assertIn("test-client", clients)
        
        # Get client info
        client_info = self.host.get_client_info("test-client")
        self.assertIsNotNone(client_info)
        self.assertEqual(client_info["client_id"], "test-client")
        self.assertEqual(client_info["name"], "Test Client")
        
        # Unregister the client
        result = self.host.unregister_client("test-client")
        self.assertTrue(result)
        
        # Check that the client was unregistered
        clients = self.host.get_registered_clients()
        self.assertNotIn("test-client", clients)
        
    def test_request_routing(self):
        """Test request routing."""
        # Create a mock server instance
        mock_server = MagicMock()
        mock_server.handle_jsonrpc_request.return_value = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "result": {"status": "success"}
        }
        
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
        
        # Create a request
        request = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "method": "test_method",
            "params": {"param1": "value1"}
        }
        
        # Route the request
        response = self.host.route_request("mock-server", request, "test-client")
        
        # Check that the request was routed correctly
        mock_server.handle_jsonrpc_request.assert_called_once_with(request)
        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertEqual(response["id"], "test-id")
        self.assertEqual(response["result"]["status"], "success")
        
    def test_consent_management(self):
        """Test consent management."""
        # Register consent
        consent_id = self.host.register_consent(
            client_id="test-client",
            server_id="test-server",
            operation_pattern="tools/*",
            consent_level=ConsentLevel.BASIC
        )
        
        # Check that consent was registered
        self.assertIsNotNone(consent_id)
        
        # Check operation consent
        has_consent = self.host._check_operation_consent(
            client_id="test-client",
            server_id="test-server",
            operation="tools/execute"
        )
        self.assertTrue(has_consent)
        
        # Check operation without consent
        has_consent = self.host._check_operation_consent(
            client_id="test-client",
            server_id="test-server",
            operation="resources/read"
        )
        self.assertFalse(has_consent)
        
        # Revoke consent
        result = self.host.revoke_consent(consent_id)
        self.assertTrue(result)
        
        # Check that consent was revoked
        has_consent = self.host._check_operation_consent(
            client_id="test-client",
            server_id="test-server",
            operation="tools/execute"
        )
        self.assertFalse(has_consent)
        
    def test_authentication(self):
        """Test authentication and session management."""
        # Authenticate user
        session_id = self.host.authenticate_user(
            username="test-user",
            credentials={"password": "test-password"}
        )
        
        # Check that session was created
        self.assertIsNotNone(session_id)
        
        # Validate session
        is_valid = self.host.validate_session(session_id)
        self.assertTrue(is_valid)
        
        # Check permission
        has_permission = self.host.check_permission(session_id, "basic")
        self.assertTrue(has_permission)
        
        # Grant permission
        result = self.host.grant_permission(session_id, "admin")
        self.assertTrue(result)
        
        # Check granted permission
        has_permission = self.host.check_permission(session_id, "admin")
        self.assertTrue(has_permission)
        
        # Revoke permission
        result = self.host.revoke_permission(session_id, "admin")
        self.assertTrue(result)
        
        # Check revoked permission
        has_permission = self.host.check_permission(session_id, "admin")
        self.assertFalse(has_permission)
        
        # End session
        result = self.host.end_session(session_id)
        self.assertTrue(result)
        
        # Check that session was ended
        is_valid = self.host.validate_session(session_id)
        self.assertFalse(is_valid)
        
    def test_event_system(self):
        """Test event system."""
        # Create a mock callback
        callback = MagicMock()
        
        # Subscribe to events
        subscription_id = self.host.subscribe_to_events("test_event", callback)
        
        # Check that subscription was created
        self.assertIsNotNone(subscription_id)
        
        # Publish an event
        event_data = {"test": "data"}
        self.host._publish_event("test_event", event_data)
        
        # Check that callback was called
        callback.assert_called_once_with(event_data)
        
        # Unsubscribe from events
        result = self.host.unsubscribe_from_events(subscription_id)
        self.assertTrue(result)
        
        # Reset the mock
        callback.reset_mock()
        
        # Publish another event
        self.host._publish_event("test_event", event_data)
        
        # Check that callback was not called
        callback.assert_not_called()
        
    def test_client_coordination(self):
        """Test client coordination."""
        # Create a mock client instance
        mock_client = MagicMock()
        
        # Register the mock client
        client_info = {
            "capabilities": {
                "tools": True,
                "resources": True,
                "subscriptions": True
            },
            "client_id": "mock-client"
        }
        self.host.register_client("mock-client", client_info, mock_client)
        
        # Broadcast a message
        message = {"test": "message"}
        results = self.host.broadcast_to_clients(message)
        
        # Check that the message was broadcast
        self.assertIn("mock-client", results)
        self.assertTrue(results["mock-client"])
        
        # Get client status
        status = self.host.get_client_status("mock-client")
        
        # Check that status was returned
        self.assertEqual(status["status"], "active")
        
        # Clean up inactive clients
        inactive_clients = self.host.cleanup_inactive_clients(max_idle_time=0)
        
        # Check that the client was cleaned up
        self.assertIn("mock-client", inactive_clients)
        
        # Check that the client was unregistered
        clients = self.host.get_registered_clients()
        self.assertNotIn("mock-client", clients)
class TestMCPHostConformance(unittest.TestCase):
    """Test cases for MCP Host protocol conformance."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("test_mcp_host_conformance")
        
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

    def test_request_routing_conformance(self):
        """Test that request routing conforms to the MCP specification."""
        # Create a request
        request = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "method": "tools/list",
            "params": {}
        }
        
        # Route the request
        response = self.host.route_request("test-server", request, "test-client")
        
        # Verify the response structure
        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertEqual(response["id"], "test-id")
        self.assertIn("result", response)
        
        # Verify that the response contains the expected data
        self.assertIsInstance(response["result"], list)
        self.assertTrue(any(tool["name"] == "execute_shell_command" for tool in response["result"]))

    def test_error_response_conformance(self):
        """Test that error responses conform to the MCP specification."""
        # Create an invalid request (missing method)
        invalid_request = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "params": {}
        }
        
        # Route the invalid request
        response = self.host.route_request("test-server", invalid_request, "test-client")
        
        # Verify the error response structure
        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertEqual(response["id"], "test-id")
        self.assertIn("error", response)
        self.assertIn("code", response["error"])
        self.assertIn("message", response["error"])
        
        # Verify the error code and message
        self.assertEqual(response["error"]["code"], -32600)
        self.assertEqual(response["error"]["message"], "Invalid Request")

    def test_method_not_found_conformance(self):
        """Test that method not found errors conform to the MCP specification."""
        # Create a request with a non-existent method
        request = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "method": "non_existent_method",
            "params": {}
        }
        
        # Route the request
        response = self.host.route_request("test-server", request, "test-client")
        
        # Verify the error response structure
        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertEqual(response["id"], "test-id")
        self.assertIn("error", response)
        self.assertIn("code", response["error"])
        self.assertIn("message", response["error"])
        
        # Verify the error code and message
        self.assertEqual(response["error"]["code"], -32601)
        self.assertEqual(response["error"]["message"], "Method not found")

    def test_consent_enforcement_conformance(self):
        """Test that consent enforcement conforms to the MCP specification."""
        # Revoke all consent
        self.host.revoke_consent(self.consent_id)
        
        # Create a request
        request = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "method": "tools/list",
            "params": {}
        }
        
        # Route the request without consent
        response = self.host.route_request("test-server", request, "test-client")
        
        # Verify the error response structure
        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertEqual(response["id"], "test-id")
        self.assertIn("error", response)
        self.assertIn("code", response["error"])
        self.assertIn("message", response["error"])
        
        # Verify the error code and message
        self.assertEqual(response["error"]["code"], -32001)
        self.assertEqual(response["error"]["message"], "Consent required")
        
        # Register consent for tools only
        self.consent_id = self.host.register_consent(
            client_id="test-client",
            server_id="test-server",
            operation_pattern="tools/*",
            consent_level=ConsentLevel.BASIC
        )
        
        # Route the request with consent
        response = self.host.route_request("test-server", request, "test-client")
        
        # Verify the response structure
        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertEqual(response["id"], "test-id")
        self.assertIn("result", response)


if __name__ == "__main__":
    unittest.main()
if __name__ == "__main__":
    unittest.main()