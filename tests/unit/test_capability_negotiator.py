"""
Unit tests for the MCP Capability Negotiator component.

This module contains tests for the MCP Capability Negotiator component, focusing on:
1. Capability negotiation
2. Client capability retrieval
3. Error handling
4. SDK integration
"""

import unittest
import logging
import json
from unittest.mock import MagicMock, patch
import sys
import os

# Add the services directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "services", "mcp-server", "src"))

# Import MCP components
from client.capability_negotiator import CapabilityNegotiator
from client.error_handler import ValidationError, MCPError


class TestCapabilityNegotiatorCore(unittest.TestCase):
    """Test cases for the core functionality of the Capability Negotiator component."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("test_capability_negotiator")
        
        # Create a mock client
        self.client = MagicMock()
        self.client.logger = self.logger
        self.client.send_request_to_server.return_value = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "result": {
                "capabilities": {
                    "tools": True,
                    "resources": True,
                    "subscriptions": True,
                    "batch": False,
                    "progress": False
                }
            }
        }
        
        # Create a capability negotiator
        self.capability_negotiator = CapabilityNegotiator(self.client)
    
    def test_negotiate(self):
        """Test negotiating capabilities with a server."""
        # Create client capabilities
        client_capabilities = {
            "tools": True,
            "resources": True,
            "subscriptions": True,
            "batch": True,
            "progress": True
        }
        
        # Negotiate capabilities
        capabilities = self.capability_negotiator.negotiate(
            server_id="test-server",
            client_capabilities=client_capabilities
        )
        
        # Check that the client's send_request_to_server method was called correctly
        self.client.send_request_to_server.assert_called_once()
        args, kwargs = self.client.send_request_to_server.call_args
        self.assertEqual(kwargs["server_id"], "test-server")
        self.assertEqual(kwargs["method"], "capabilities/negotiate")
        self.assertEqual(kwargs["params"]["client_capabilities"], client_capabilities)
        
        # Check the negotiated capabilities
        self.assertEqual(capabilities["tools"], True)
        self.assertEqual(capabilities["resources"], True)
        self.assertEqual(capabilities["subscriptions"], True)
        self.assertEqual(capabilities["batch"], False)
        self.assertEqual(capabilities["progress"], False)
        
        # Check that the negotiated capabilities were stored
        self.assertIn("test-server", self.capability_negotiator.negotiated_capabilities)
        self.assertEqual(
            self.capability_negotiator.negotiated_capabilities["test-server"],
            capabilities
        )
    
    def test_get_client_capabilities(self):
        """Test getting client capabilities."""
        # Get client capabilities
        capabilities = self.capability_negotiator.get_client_capabilities()
        
        # Check the client capabilities
        self.assertIsInstance(capabilities, dict)
        self.assertIn("tools", capabilities)
        self.assertIn("resources", capabilities)
        self.assertIn("subscriptions", capabilities)
        self.assertIn("batch", capabilities)
        self.assertIn("progress", capabilities)
        self.assertIn("protocol_version", capabilities)
        self.assertIn("client_version", capabilities)
        
        # Check the values
        self.assertTrue(capabilities["tools"])
        self.assertTrue(capabilities["resources"])
        self.assertTrue(capabilities["subscriptions"])
        self.assertTrue(capabilities["batch"])
        self.assertTrue(capabilities["progress"])
        self.assertEqual(capabilities["protocol_version"], "2025-03-26")
        self.assertEqual(capabilities["client_version"], "1.0.0")


class TestCapabilityNegotiatorEdgeCases(unittest.TestCase):
    """Test cases for edge cases in the Capability Negotiator component."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("test_capability_negotiator_edge_cases")
        
        # Create a mock client
        self.client = MagicMock()
        self.client.logger = self.logger
        
        # Create a capability negotiator
        self.capability_negotiator = CapabilityNegotiator(self.client)
    
    def test_negotiate_with_empty_server_id(self):
        """Test negotiating capabilities with an empty server ID."""
        # Negotiate with an empty server ID
        with self.assertRaises(ValidationError):
            self.capability_negotiator.negotiate(
                server_id="",
                client_capabilities={"tools": True}
            )
    
    def test_negotiate_with_none_client_capabilities(self):
        """Test negotiating capabilities with None as client capabilities."""
        # Negotiate with None as client capabilities
        with self.assertRaises(ValidationError):
            self.capability_negotiator.negotiate(
                server_id="test-server",
                client_capabilities=None
            )
    
    def test_negotiate_with_no_capabilities_in_response(self):
        """Test negotiating capabilities with no capabilities in the response."""
        # Mock the client's send_request_to_server method to return a response with no capabilities
        self.client.send_request_to_server.return_value = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "result": {}
        }
        
        # Create a second mock for the capabilities/list method
        self.client.send_request_to_server.side_effect = [
            # First call (capabilities/negotiate) returns no capabilities
            {
                "jsonrpc": "2.0",
                "id": "test-id",
                "result": {}
            },
            # Second call (capabilities/list) returns capabilities
            {
                "jsonrpc": "2.0",
                "id": "test-id",
                "result": {
                    "capabilities": {
                        "tools": True,
                        "resources": True,
                        "subscriptions": False,
                        "batch": False,
                        "progress": False
                    }
                }
            }
        ]
        
        # Negotiate capabilities
        capabilities = self.capability_negotiator.negotiate(
            server_id="test-server",
            client_capabilities={
                "tools": True,
                "resources": True,
                "subscriptions": True,
                "batch": True,
                "progress": True
            }
        )
        
        # Check that the client's send_request_to_server method was called twice
        self.assertEqual(self.client.send_request_to_server.call_count, 2)
        
        # Check the first call (capabilities/negotiate)
        args, kwargs = self.client.send_request_to_server.call_args_list[0]
        self.assertEqual(kwargs["server_id"], "test-server")
        self.assertEqual(kwargs["method"], "capabilities/negotiate")
        
        # Check the second call (capabilities/list)
        args, kwargs = self.client.send_request_to_server.call_args_list[1]
        self.assertEqual(kwargs["server_id"], "test-server")
        self.assertEqual(kwargs["method"], "capabilities/list")
        
        # Check the negotiated capabilities
        self.assertEqual(capabilities["tools"], True)
        self.assertEqual(capabilities["resources"], True)
        self.assertEqual(capabilities["subscriptions"], False)
        self.assertEqual(capabilities["batch"], False)
        self.assertEqual(capabilities["progress"], False)
    
    def test_negotiate_with_no_capabilities_in_list_response(self):
        """Test negotiating capabilities with no capabilities in the list response."""
        # Mock the client's send_request_to_server method to return responses with no capabilities
        self.client.send_request_to_server.side_effect = [
            # First call (capabilities/negotiate) returns no capabilities
            {
                "jsonrpc": "2.0",
                "id": "test-id",
                "result": {}
            },
            # Second call (capabilities/list) also returns no capabilities
            {
                "jsonrpc": "2.0",
                "id": "test-id",
                "result": {}
            }
        ]
        
        # Negotiate capabilities
        capabilities = self.capability_negotiator.negotiate(
            server_id="test-server",
            client_capabilities={
                "tools": True,
                "resources": True,
                "subscriptions": True,
                "batch": True,
                "progress": True
            }
        )
        
        # Check that the client's send_request_to_server method was called twice
        self.assertEqual(self.client.send_request_to_server.call_count, 2)
        
        # Check the negotiated capabilities (should be default capabilities)
        self.assertEqual(capabilities["tools"], True)
        self.assertEqual(capabilities["resources"], True)
        self.assertEqual(capabilities["subscriptions"], False)
        self.assertEqual(capabilities["batch"], False)
        self.assertEqual(capabilities["progress"], False)


class TestCapabilityNegotiatorErrorScenarios(unittest.TestCase):
    """Test cases for error scenarios in the Capability Negotiator component."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("test_capability_negotiator_error_scenarios")
        
        # Create a mock client
        self.client = MagicMock()
        self.client.logger = self.logger
        
        # Create a capability negotiator
        self.capability_negotiator = CapabilityNegotiator(self.client)
    
    def test_negotiate_with_network_error(self):
        """Test negotiating capabilities with a network error."""
        # Mock the client's send_request_to_server method to raise an exception
        self.client.send_request_to_server.side_effect = Exception("Network error")
        
        # Negotiate with a network error
        with self.assertRaises(MCPError) as context:
            self.capability_negotiator.negotiate(
                server_id="test-server",
                client_capabilities={"tools": True}
            )
        
        # Check the error
        self.assertIn("Network error", str(context.exception))
    
    def test_get_client_capabilities_with_error(self):
        """Test getting client capabilities with an error."""
        # Create a capability negotiator that raises an exception when getting client capabilities
        with patch.object(CapabilityNegotiator, 'get_client_capabilities', side_effect=Exception("Error getting capabilities")):
            capability_negotiator = CapabilityNegotiator(self.client)
            
            # Get client capabilities with an error
            with self.assertRaises(MCPError) as context:
                capability_negotiator.get_client_capabilities()
            
            # Check the error
            self.assertIn("Error getting capabilities", str(context.exception))


class TestCapabilityNegotiatorSDKIntegration(unittest.TestCase):
    """Test cases for SDK integration in the Capability Negotiator component."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("test_capability_negotiator_sdk_integration")
        
        # Create a mock client
        self.client = MagicMock()
        self.client.logger = self.logger
        
        # Create a mock SDK capability manager
        self.mock_sdk_capability_manager = MagicMock()
        
        # Create a capability negotiator with the mock SDK capability manager
        self.capability_negotiator = CapabilityNegotiator(self.client)
        self.capability_negotiator.capability_manager = self.mock_sdk_capability_manager
    
    def test_negotiate_with_sdk(self):
        """Test negotiating capabilities using the SDK."""
        # Mock the SDK capability manager's negotiate method
        negotiated_capabilities = {
            "tools": True,
            "resources": True,
            "subscriptions": False,
            "batch": False,
            "progress": False
        }
        self.mock_sdk_capability_manager.negotiate = MagicMock(return_value=negotiated_capabilities)
        
        # Create client capabilities
        client_capabilities = {
            "tools": True,
            "resources": True,
            "subscriptions": True,
            "batch": True,
            "progress": True
        }
        
        # Negotiate capabilities using the SDK
        capabilities = self.capability_negotiator.negotiate(
            server_id="test-server",
            client_capabilities=client_capabilities
        )
        
        # Check that the SDK capability manager's negotiate method was called
        self.mock_sdk_capability_manager.negotiate.assert_called_once_with(
            "test-server",
            client_capabilities
        )
        
        # Check the negotiated capabilities
        self.assertEqual(capabilities, negotiated_capabilities)
        
        # Check that the negotiated capabilities were stored
        self.assertIn("test-server", self.capability_negotiator.negotiated_capabilities)
        self.assertEqual(
            self.capability_negotiator.negotiated_capabilities["test-server"],
            negotiated_capabilities
        )
    
    def test_get_client_capabilities_with_sdk(self):
        """Test getting client capabilities using the SDK."""
        # Mock the SDK capability manager's get_client_capabilities method
        sdk_client_capabilities = {
            "tools": True,
            "resources": True,
            "subscriptions": True,
            "batch": True,
            "progress": True,
            "protocol_version": "2025-03-26",
            "client_version": "1.0.0",
            "sdk_specific_capability": "value"
        }
        self.mock_sdk_capability_manager.get_client_capabilities = MagicMock(return_value=sdk_client_capabilities)
        
        # Get client capabilities using the SDK
        capabilities = self.capability_negotiator.get_client_capabilities()
        
        # Check that the SDK capability manager's get_client_capabilities method was called
        self.mock_sdk_capability_manager.get_client_capabilities.assert_called_once()
        
        # Check the client capabilities
        self.assertEqual(capabilities, sdk_client_capabilities)


if __name__ == "__main__":
    unittest.main()