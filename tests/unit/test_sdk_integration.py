"""
Unit tests for SDK integration in the MCP components.

This module contains tests for SDK integration in the MCP components, focusing on:
1. Client SDK integration
2. Tool SDK integration
3. Resource SDK integration
4. Capability SDK integration
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
from client.tool_proxy import ToolProxyManager
from client.resource_subscriber import ResourceSubscriberManager
from client.capability_negotiator import CapabilityNegotiator
from client.error_handler import ValidationError, NetworkError, ResourceError, ToolError, MCPError


class TestClientSDKIntegration(unittest.TestCase):
    """Test cases for SDK integration in the Client component."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.INFO) 
        
        self.logger = logging.getLogger("test_client_sdk_integration")
        
        # Create a mock SDK client
        self.mock_sdk_client = MagicMock()
        
        # Create a client with the mock SDK client
        self.client = MCPClient(
            logger=self.logger,
            config={'mcp': {'client_id': 'test-client'}},
            mcp_client=self.mock_sdk_client
        )
        
        # Create a mock host
        self.host = MagicMock()
    
    def test_connect_to_host_with_sdk(self):
        """Test connecting to a host using the SDK."""
        # Add connect_to_host method to the mock SDK client
        self.mock_sdk_client.connect_to_host = MagicMock(return_value=True)
        
        # Connect to the host
        result = self.client.connect_to_host(self.host)
        
        # Check that the SDK client's connect_to_host method was called
        self.mock_sdk_client.connect_to_host.assert_called_once_with(self.host)
        
        # Check the result
        self.assertTrue(result)
        self.assertTrue(self.client.connected)
        self.assertEqual(self.client.host, self.host)
    
    def test_disconnect_from_host_with_sdk(self):
        """Test disconnecting from a host using the SDK."""
        # Add connect_to_host and disconnect_from_host methods to the mock SDK client
        self.mock_sdk_client.connect_to_host = MagicMock(return_value=True)
        self.mock_sdk_client.disconnect_from_host = MagicMock(return_value=True)
        
        # Connect to the host
        self.client.connect_to_host(self.host)
        
        # Disconnect from the host
        result = self.client.disconnect_from_host()
        
        # Check that the SDK client's disconnect_from_host method was called
        self.mock_sdk_client.disconnect_from_host.assert_called_once()
        
        # Check the result
        self.assertTrue(result)
        self.assertFalse(self.client.connected)
        self.assertIsNone(self.client.host)
    
    def test_send_request_with_sdk(self):
        """Test sending a request using the SDK."""
        # Add connect_to_host and send_request methods to the mock SDK client
        self.mock_sdk_client.connect_to_host = MagicMock(return_value=True)
        self.mock_sdk_client.send_request = MagicMock(return_value={
            "jsonrpc": "2.0",
            "id": "test-id",
            "result": {"status": "success"}
        })
        
        # Connect to the host
        self.client.connect_to_host(self.host)
        
        # Send a request
        response = self.client.send_request_to_server(
            server_id="test-server",
            method="test_method",
            params={"param1": "value1"}
        )
        
        # Check that the SDK client's send_request method was called
        self.mock_sdk_client.send_request.assert_called_once()
        args, kwargs = self.mock_sdk_client.send_request.call_args
        self.assertEqual(args[0], "test-server")
        self.assertEqual(args[1]["method"], "test_method")
        self.assertEqual(args[1]["params"], {"param1": "value1"})
        
        # Check the response
        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertEqual(response["id"], "test-id")
        self.assertEqual(response["result"], {"status": "success"})
    
    def test_send_notification_with_sdk(self):
        """Test sending a notification using the SDK."""
        # Add connect_to_host and send_notification methods to the mock SDK client
        self.mock_sdk_client.connect_to_host = MagicMock(return_value=True)
        self.mock_sdk_client.send_notification = MagicMock()
        
        # Connect to the host
        self.client.connect_to_host(self.host)
        
        # Send a notification
        self.client.send_notification_to_server(
            server_id="test-server",
            method="test_method",
            params={"param1": "value1"}
        )
        
        # Check that the SDK client's send_notification method was called
        self.mock_sdk_client.send_notification.assert_called_once()
        args, kwargs = self.mock_sdk_client.send_notification.call_args
        self.assertEqual(args[0], "test-server")
        self.assertEqual(args[1]["method"], "test_method")
        self.assertEqual(args[1]["params"], {"param1": "value1"})
    
    def test_list_tools_with_sdk(self):
        """Test listing tools using the SDK."""
        # Add connect_to_host and list_tools methods to the mock SDK client
        self.mock_sdk_client.connect_to_host = MagicMock(return_value=True)
        self.mock_sdk_client.list_tools = MagicMock(return_value=["tool1", "tool2"])
        
        # Connect to the host
        self.client.connect_to_host(self.host)
        
        # List tools
        tools = self.client.list_server_tools("test-server")
        
        # Check that the SDK client's list_tools method was called
        self.mock_sdk_client.list_tools.assert_called_once_with("test-server")
        
        # Check the result
        self.assertEqual(tools, ["tool1", "tool2"])
    
    def test_get_tool_details_with_sdk(self):
        """Test getting tool details using the SDK."""
        # Add connect_to_host and get_tool_details methods to the mock SDK client
        self.mock_sdk_client.connect_to_host = MagicMock(return_value=True)
        self.mock_sdk_client.get_tool_details = MagicMock(return_value={
            "name": "test_tool",
            "description": "A test tool",
            "inputSchema": {}
        })
        
        # Connect to the host
        self.client.connect_to_host(self.host)
        
        # Get tool details
        tool_details = self.client.get_tool_details("test-server", "test_tool")
        
        # Check that the SDK client's get_tool_details method was called
        self.mock_sdk_client.get_tool_details.assert_called_once_with("test-server", "test_tool")
        
        # Check the result
        self.assertEqual(tool_details["name"], "test_tool")
        self.assertEqual(tool_details["description"], "A test tool")
        self.assertEqual(tool_details["inputSchema"], {})
    
    def test_list_resources_with_sdk(self):
        """Test listing resources using the SDK."""
        # Add connect_to_host and list_resources methods to the mock SDK client
        self.mock_sdk_client.connect_to_host = MagicMock(return_value=True)
        self.mock_sdk_client.list_resources = MagicMock(return_value=["resource1", "resource2"])
        
        # Connect to the host
        self.client.connect_to_host(self.host)
        
        # List resources
        resources = self.client.list_resources("test-server", "file", "/")
        
        # Check that the SDK client's list_resources method was called
        self.mock_sdk_client.list_resources.assert_called_once_with("test-server", "file", "/")
        
        # Check the result
        self.assertEqual(resources, ["resource1", "resource2"])
    
    def test_access_resource_with_sdk(self):
        """Test accessing a resource using the SDK."""
        # Add connect_to_host and access_resource methods to the mock SDK client
        self.mock_sdk_client.connect_to_host = MagicMock(return_value=True)
        self.mock_sdk_client.access_resource = MagicMock(return_value={
            "content": "Resource content",
            "metadata": {"type": "text/plain"}
        })
        
        # Connect to the host
        self.client.connect_to_host(self.host)
        
        # Access a resource
        resource_data = self.client.access_resource("test-server", "resource://file/test")
        
        # Check that the SDK client's access_resource method was called
        self.mock_sdk_client.access_resource.assert_called_once_with("test-server", "resource://file/test")
        
        # Check the result
        self.assertEqual(resource_data["content"], "Resource content")
        self.assertEqual(resource_data["metadata"], {"type": "text/plain"})


class TestToolProxySDKIntegration(unittest.TestCase):
    """Test cases for SDK integration in the Tool Proxy component."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("test_tool_proxy_sdk_integration")
        
        # Create a mock client
        self.client = MagicMock()
        self.client.logger = self.logger
        
        # Create a mock SDK tool manager
        self.mock_sdk_tool_manager = MagicMock()
        
        # Create a tool proxy manager with the mock SDK tool manager
        self.tool_proxy_manager = ToolProxyManager(self.client)
        self.tool_proxy_manager.tool_manager = self.mock_sdk_tool_manager
        
        # Create sample tool details
        self.tool_details = {
            "name": "test_tool",
            "description": "A test tool",
            "inputSchema": {
                "type": "object",
                "required": ["required_param"],
                "properties": {
                    "required_param": {
                        "type": "string",
                        "description": "A required parameter"
                    }
                }
            }
        }
    
    def test_create_proxy_with_sdk(self):
        """Test creating a tool proxy using the SDK."""
        # Mock the SDK tool manager's create_proxy method
        mock_proxy = MagicMock()
        mock_proxy.__name__ = "test_tool"
        mock_proxy.__doc__ = "A test tool"
        self.mock_sdk_tool_manager.create_proxy = MagicMock(return_value=mock_proxy)
        
        # Create a proxy using the SDK
        proxy = self.tool_proxy_manager.create_proxy(
            server_id="test-server",
            tool_name="test_tool",
            tool_details=self.tool_details
        )
        
        # Check that the SDK tool manager's create_proxy method was called
        self.mock_sdk_tool_manager.create_proxy.assert_called_once_with(
            "test-server",
            "test_tool",
            self.tool_details
        )
        
        # Check that the proxy was returned
        self.assertEqual(proxy, mock_proxy)
        
        # Check that the proxy was stored
        self.assertIn("test-server:test_tool", self.tool_proxy_manager.proxies)
        self.assertEqual(self.tool_proxy_manager.proxies["test-server:test_tool"], mock_proxy)


class TestResourceSubscriberSDKIntegration(unittest.TestCase):
    """Test cases for SDK integration in the Resource Subscriber component."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("test_resource_subscriber_sdk_integration")
        
        # Create a mock client
        self.client = MagicMock()
        self.client.logger = self.logger
        
        # Create a mock SDK resource manager
        self.mock_sdk_resource_manager = MagicMock()
        
        # Create a resource subscriber manager with the mock SDK resource manager
        self.resource_subscriber = ResourceSubscriberManager(self.client)
        self.resource_subscriber.resource_manager = self.mock_sdk_resource_manager
        
        # Create a mock callback
        self.callback = MagicMock()
    
    def test_subscribe_with_sdk(self):
        """Test subscribing to a resource using the SDK."""
        # Mock the SDK resource manager's subscribe method
        sdk_subscription_id = str(uuid.uuid4())
        self.mock_sdk_resource_manager.subscribe = MagicMock(return_value=sdk_subscription_id)
        
        # Subscribe to a resource using the SDK
        subscription_id = self.resource_subscriber.subscribe(
            server_id="test-server",
            uri="resource://test/resource",
            callback=self.callback
        )
        
        # Check that the SDK resource manager's subscribe method was called
        self.mock_sdk_resource_manager.subscribe.assert_called_once_with(
            "test-server",
            "resource://test/resource",
            self.callback
        )
        
        # Check that the subscription was stored with the SDK subscription ID
        self.assertIn(subscription_id, self.resource_subscriber.subscriptions)
        self.assertEqual(
            self.resource_subscriber.subscriptions[subscription_id]["sdk_subscription_id"],
            sdk_subscription_id
        )
    
    def test_unsubscribe_with_sdk(self):
        """Test unsubscribing from a resource using the SDK."""
        # Mock the SDK resource manager's subscribe and unsubscribe methods
        sdk_subscription_id = str(uuid.uuid4())
        self.mock_sdk_resource_manager.subscribe = MagicMock(return_value=sdk_subscription_id)
        self.mock_sdk_resource_manager.unsubscribe = MagicMock(return_value=True)
        
        # Subscribe to a resource using the SDK
        subscription_id = self.resource_subscriber.subscribe(
            server_id="test-server",
            uri="resource://test/resource",
            callback=self.callback
        )
        
        # Unsubscribe from the resource using the SDK
        result = self.resource_subscriber.unsubscribe(subscription_id)
        
        # Check that the SDK resource manager's unsubscribe method was called
        self.mock_sdk_resource_manager.unsubscribe.assert_called_once_with(sdk_subscription_id)
        
        # Check the result
        self.assertTrue(result)
        
        # Check that the subscription was removed
        self.assertNotIn(subscription_id, self.resource_subscriber.subscriptions)
    
    def test_handle_update_with_sdk(self):
        """Test handling a resource update using the SDK."""
        # Mock the SDK resource manager's subscribe and handle_update methods
        sdk_subscription_id = str(uuid.uuid4())
        self.mock_sdk_resource_manager.subscribe = MagicMock(return_value=sdk_subscription_id)
        self.mock_sdk_resource_manager.handle_update = MagicMock()
        
        # Subscribe to a resource using the SDK
        subscription_id = self.resource_subscriber.subscribe(
            server_id="test-server",
            uri="resource://test/resource",
            callback=self.callback
        )
        
        # Create update data
        update_data = {
            "content": "Updated content",
            "timestamp": 123456789
        }
        
        # Handle the update using the SDK
        self.resource_subscriber.handle_update(subscription_id, update_data)
        
        # Check that the SDK resource manager's handle_update method was called
        self.mock_sdk_resource_manager.handle_update.assert_called_once_with(
            sdk_subscription_id,
            update_data
        )


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