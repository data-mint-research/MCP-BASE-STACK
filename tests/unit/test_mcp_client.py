"""
Unit tests for the MCP Client component.

This module contains tests for the MCP Client component, focusing on:
1. Core functionality
2. Edge cases
3. Error scenarios
4. SDK integration
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
from client.error_handler import ValidationError, NetworkError, ResourceError, ToolError, MCPError
from host.host import MCPHost, ConsentLevel
from modelcontextprotocol.json_rpc import JsonRpc


class TestMCPClientCore(unittest.TestCase):
    """Test cases for the core functionality of the MCP Client component."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("test_mcp_client")
        
        # Create a config dictionary
        self.config = {
            'mcp': {
                'client_id': 'test-client',
                'client_name': 'Test Client'
            },
            'connection': {
                'retry_count': 3,
                'retry_delay': 0.1
            }
        }
        
        # Create a client
        self.client = MCPClient(logger=self.logger, config=self.config)
        
        # Create a mock host
        self.host = MagicMock()
        self.host.route_request.return_value = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "result": {"status": "success"}
        }
        
        # Connect the client to the host
        self.client.connect_to_host(self.host)
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Disconnect the client from the host
        if self.client.host:
            self.client.disconnect_from_host()
    
    def test_client_initialization(self):
        """Test client initialization."""
        # Test that the client was initialized correctly
        self.assertEqual(self.client.client_id, 'test-client')
        self.assertEqual(self.client.config['mcp']['client_name'], 'Test Client')
        self.assertEqual(self.client.connection_retry_count, 3)
        self.assertEqual(self.client.connection_retry_delay, 0.1)
        self.assertTrue(self.client.connected)
        self.assertIsNotNone(self.client.host)
    
    def test_connect_to_host(self):
        """Test connecting to a host."""
        # Disconnect first
        self.client.disconnect_from_host()
        
        # Test connecting to a host
        result = self.client.connect_to_host(self.host)
        self.assertTrue(result)
        self.assertTrue(self.client.connected)
        self.assertEqual(self.client.host, self.host)
    
    def test_disconnect_from_host(self):
        """Test disconnecting from a host."""
        # Test disconnecting from a host
        result = self.client.disconnect_from_host()
        self.assertTrue(result)
        self.assertFalse(self.client.connected)
        self.assertIsNone(self.client.host)
    
    def test_create_jsonrpc_request(self):
        """Test creating a JSON-RPC request."""
        # Test creating a request with a specific ID
        request = self.client.create_jsonrpc_request(
            method="test_method",
            params={"param1": "value1"},
            request_id="test-id"
        )
        
        self.assertEqual(request["jsonrpc"], "2.0")
        self.assertEqual(request["id"], "test-id")
        self.assertEqual(request["method"], "test_method")
        self.assertEqual(request["params"], {"param1": "value1"})
        
        # Test creating a request with an auto-generated ID
        request = self.client.create_jsonrpc_request(
            method="test_method",
            params={"param1": "value1"}
        )
        
        self.assertEqual(request["jsonrpc"], "2.0")
        self.assertIn("id", request)
        self.assertEqual(request["method"], "test_method")
        self.assertEqual(request["params"], {"param1": "value1"})
    
    def test_create_jsonrpc_notification(self):
        """Test creating a JSON-RPC notification."""
        # Test creating a notification
        notification = self.client.create_jsonrpc_notification(
            method="test_method",
            params={"param1": "value1"}
        )
        
        self.assertEqual(notification["jsonrpc"], "2.0")
        self.assertEqual(notification["method"], "test_method")
        self.assertEqual(notification["params"], {"param1": "value1"})
        self.assertNotIn("id", notification)
    
    def test_send_request_to_server(self):
        """Test sending a request to a server."""
        # Mock the host's route_request method
        self.host.route_request.return_value = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "result": {"data": "test_data"}
        }
        
        # Test sending a request
        response = self.client.send_request_to_server(
            server_id="test-server",
            method="test_method",
            params={"param1": "value1"},
            request_id="test-id"
        )
        
        # Check that the host's route_request method was called correctly
        self.host.route_request.assert_called_once()
        args, kwargs = self.host.route_request.call_args
        self.assertEqual(args[0], "test-server")
        self.assertEqual(args[2], "test-client")
        self.assertEqual(args[1]["jsonrpc"], "2.0")
        self.assertEqual(args[1]["id"], "test-id")
        self.assertEqual(args[1]["method"], "test_method")
        self.assertEqual(args[1]["params"], {"param1": "value1"})
        
        # Check the response
        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertEqual(response["id"], "test-id")
        self.assertEqual(response["result"], {"data": "test_data"})
    
    def test_send_notification_to_server(self):
        """Test sending a notification to a server."""
        # Test sending a notification
        self.client.send_notification_to_server(
            server_id="test-server",
            method="test_method",
            params={"param1": "value1"}
        )
        
        # Check that the host's route_request method was called correctly
        self.host.route_request.assert_called_once()
        args, kwargs = self.host.route_request.call_args
        self.assertEqual(args[0], "test-server")
        self.assertEqual(args[2], "test-client")
        self.assertEqual(args[1]["jsonrpc"], "2.0")
        self.assertEqual(args[1]["method"], "test_method")
        self.assertEqual(args[1]["params"], {"param1": "value1"})
        self.assertNotIn("id", args[1])


class TestMCPClientEdgeCases(unittest.TestCase):
    """Test cases for edge cases in the MCP Client component."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("test_mcp_client_edge_cases")
        
        # Create a config dictionary
        self.config = {
            'mcp': {
                'client_id': 'test-client',
                'client_name': 'Test Client'
            },
            'connection': {
                'retry_count': 3,
                'retry_delay': 0.1
            }
        }
        
        # Create a client
        self.client = MCPClient(logger=self.logger, config=self.config)
        
        # Create a mock host
        self.host = MagicMock()
        self.host.route_request.return_value = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "result": {"status": "success"}
        }
        
        # Connect the client to the host
        self.client.connect_to_host(self.host)
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Disconnect the client from the host
        if self.client.host:
            self.client.disconnect_from_host()
    
    def test_connect_to_none_host(self):
        """Test connecting to a None host."""
        # Disconnect first
        self.client.disconnect_from_host()
        
        # Test connecting to a None host
        with self.assertRaises(ValidationError):
            self.client.connect_to_host(None)
    
    def test_disconnect_when_not_connected(self):
        """Test disconnecting when not connected."""
        # Disconnect first
        self.client.disconnect_from_host()
        
        # Test disconnecting again
        result = self.client.disconnect_from_host()
        self.assertFalse(result)
    
    def test_create_jsonrpc_request_with_empty_method(self):
        """Test creating a JSON-RPC request with an empty method."""
        # Test creating a request with an empty method
        with self.assertRaises(ValidationError):
            self.client.create_jsonrpc_request(
                method="",
                params={"param1": "value1"}
            )
    
    def test_create_jsonrpc_request_with_non_dict_params(self):
        """Test creating a JSON-RPC request with non-dict params."""
        # Test creating a request with non-dict params
        with self.assertRaises(ValidationError):
            self.client.create_jsonrpc_request(
                method="test_method",
                params="not_a_dict"
            )
    
    def test_create_jsonrpc_notification_with_empty_method(self):
        """Test creating a JSON-RPC notification with an empty method."""
        # Test creating a notification with an empty method
        with self.assertRaises(ValidationError):
            self.client.create_jsonrpc_notification(
                method="",
                params={"param1": "value1"}
            )
    
    def test_create_jsonrpc_notification_with_non_dict_params(self):
        """Test creating a JSON-RPC notification with non-dict params."""
        # Test creating a notification with non-dict params
        with self.assertRaises(ValidationError):
            self.client.create_jsonrpc_notification(
                method="test_method",
                params="not_a_dict"
            )
    
    def test_send_request_with_empty_server_id(self):
        """Test sending a request with an empty server ID."""
        # Test sending a request with an empty server ID
        with self.assertRaises(ValidationError):
            self.client.send_request_to_server(
                server_id="",
                method="test_method",
                params={"param1": "value1"}
            )
    
    def test_send_request_when_not_connected(self):
        """Test sending a request when not connected."""
        # Disconnect first
        self.client.disconnect_from_host()
        
        # Test sending a request when not connected
        with self.assertRaises(NetworkError):
            self.client.send_request_to_server(
                server_id="test-server",
                method="test_method",
                params={"param1": "value1"}
            )
    
    def test_send_notification_with_empty_server_id(self):
        """Test sending a notification with an empty server ID."""
        # Test sending a notification with an empty server ID
        with self.assertRaises(ValidationError):
            self.client.send_notification_to_server(
                server_id="",
                method="test_method",
                params={"param1": "value1"}
            )
    
    def test_send_notification_when_not_connected(self):
        """Test sending a notification when not connected."""
        # Disconnect first
        self.client.disconnect_from_host()
        
        # Test sending a notification when not connected
        with self.assertRaises(NetworkError):
            self.client.send_notification_to_server(
                server_id="test-server",
                method="test_method",
                params={"param1": "value1"}
            )


class TestMCPClientErrorScenarios(unittest.TestCase):
    """Test cases for error scenarios in the MCP Client component."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("test_mcp_client_error_scenarios")
        
        # Create a config dictionary
        self.config = {
            'mcp': {
                'client_id': 'test-client',
                'client_name': 'Test Client'
            },
            'connection': {
                'retry_count': 3,
                'retry_delay': 0.1
            }
        }
        
        # Create a client
        self.client = MCPClient(logger=self.logger, config=self.config)
        
        # Create a mock host
        self.host = MagicMock()
        
        # Connect the client to the host
        self.client.connect_to_host(self.host)
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Disconnect the client from the host
        if self.client.host:
            self.client.disconnect_from_host()
    
    def test_send_request_with_invalid_response(self):
        """Test sending a request that receives an invalid response."""
        # Mock the host's route_request method to return an invalid response
        self.host.route_request.return_value = None
        
        # Test sending a request that receives an invalid response
        with self.assertRaises(NetworkError):
            self.client.send_request_to_server(
                server_id="test-server",
                method="test_method",
                params={"param1": "value1"}
            )
    
    def test_send_request_with_error_response(self):
        """Test sending a request that receives an error response."""
        # Mock the host's route_request method to return an error response
        self.host.route_request.return_value = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "error": {
                "code": -32600,
                "message": "Invalid Request"
            }
        }
        
        # Test sending a request that receives an error response
        with self.assertRaises(MCPError) as context:
            self.client.send_request_to_server(
                server_id="test-server",
                method="test_method",
                params={"param1": "value1"}
            )
        
        # Check the error
        self.assertEqual(context.exception.error_code, -32600)
        self.assertEqual(context.exception.message, "Invalid Request")
    
    def test_send_request_with_network_error(self):
        """Test sending a request that encounters a network error."""
        # Mock the host's route_request method to raise an exception
        self.host.route_request.side_effect = Exception("Network error")
        
        # Test sending a request that encounters a network error
        with self.assertRaises(NetworkError):
            self.client.send_request_to_server(
                server_id="test-server",
                method="test_method",
                params={"param1": "value1"}
            )
    
    def test_send_notification_with_network_error(self):
        """Test sending a notification that encounters a network error."""
        # Mock the host's route_request method to raise an exception
        self.host.route_request.side_effect = Exception("Network error")
        
        # Test sending a notification that encounters a network error
        with self.assertRaises(NetworkError):
            self.client.send_notification_to_server(
                server_id="test-server",
                method="test_method",
                params={"param1": "value1"}
            )


class TestMCPClientSDKIntegration(unittest.TestCase):
    """Test cases for SDK integration in the MCP Client component."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("test_mcp_client_sdk_integration")
        
        # Create a config dictionary
        self.config = {
            'mcp': {
                'client_id': 'test-client',
                'client_name': 'Test Client'
            },
            'connection': {
                'retry_count': 3,
                'retry_delay': 0.1
            }
        }
        
        # Create a mock SDK client
        self.mock_sdk_client = MagicMock()
        
        # Create a client with the mock SDK client
        self.client = MCPClient(
            logger=self.logger,
            config=self.config,
            mcp_client=self.mock_sdk_client
        )
        
        # Create a mock host
        self.host = MagicMock()
        
        # Connect the client to the host
        self.client.connect_to_host(self.host)
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Disconnect the client from the host
        if self.client.host:
            self.client.disconnect_from_host()
    
    def test_connect_to_host_with_sdk(self):
        """Test connecting to a host using the SDK."""
        # Disconnect first
        self.client.disconnect_from_host()
        
        # Add connect_to_host method to the mock SDK client
        self.mock_sdk_client.connect_to_host = MagicMock(return_value=True)
        
        # Test connecting to a host using the SDK
        result = self.client.connect_to_host(self.host)
        
        # Check that the SDK client's connect_to_host method was called
        self.mock_sdk_client.connect_to_host.assert_called_once_with(self.host)
        
        # Check the result
        self.assertTrue(result)
        self.assertTrue(self.client.connected)
        self.assertEqual(self.client.host, self.host)
    
    def test_disconnect_from_host_with_sdk(self):
        """Test disconnecting from a host using the SDK."""
        # Add disconnect_from_host method to the mock SDK client
        self.mock_sdk_client.disconnect_from_host = MagicMock(return_value=True)
        
        # Test disconnecting from a host using the SDK
        result = self.client.disconnect_from_host()
        
        # Check that the SDK client's disconnect_from_host method was called
        self.mock_sdk_client.disconnect_from_host.assert_called_once()
        
        # Check the result
        self.assertTrue(result)
        self.assertFalse(self.client.connected)
        self.assertIsNone(self.client.host)
    
    def test_send_request_with_sdk(self):
        """Test sending a request using the SDK."""
        # Add send_request method to the mock SDK client
        self.mock_sdk_client.send_request = MagicMock(return_value={
            "jsonrpc": "2.0",
            "id": "test-id",
            "result": {"data": "test_data"}
        })
        
        # Test sending a request using the SDK
        response = self.client.send_request_to_server(
            server_id="test-server",
            method="test_method",
            params={"param1": "value1"},
            request_id="test-id"
        )
        
        # Check that the SDK client's send_request method was called
        self.mock_sdk_client.send_request.assert_called_once()
        args, kwargs = self.mock_sdk_client.send_request.call_args
        self.assertEqual(args[0], "test-server")
        self.assertEqual(args[1]["jsonrpc"], "2.0")
        self.assertEqual(args[1]["id"], "test-id")
        self.assertEqual(args[1]["method"], "test_method")
        self.assertEqual(args[1]["params"], {"param1": "value1"})
        
        # Check the response
        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertEqual(response["id"], "test-id")
        self.assertEqual(response["result"], {"data": "test_data"})
    
    def test_send_notification_with_sdk(self):
        """Test sending a notification using the SDK."""
        # Add send_notification method to the mock SDK client
        self.mock_sdk_client.send_notification = MagicMock()
        
        # Test sending a notification using the SDK
        self.client.send_notification_to_server(
            server_id="test-server",
            method="test_method",
            params={"param1": "value1"}
        )
        
        # Check that the SDK client's send_notification method was called
        self.mock_sdk_client.send_notification.assert_called_once()
        args, kwargs = self.mock_sdk_client.send_notification.call_args
        self.assertEqual(args[0], "test-server")
        self.assertEqual(args[1]["jsonrpc"], "2.0")
        self.assertEqual(args[1]["method"], "test_method")
        self.assertEqual(args[1]["params"], {"param1": "value1"})
        self.assertNotIn("id", args[1])


if __name__ == "__main__":
    unittest.main()