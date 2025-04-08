"""
Unit tests for the MCP Resource Subscriber component.

This module contains tests for the MCP Resource Subscriber component, focusing on:
1. Resource subscription
2. Resource unsubscription
3. Update handling
4. SDK integration
"""

import unittest
import logging
import json
from unittest.mock import MagicMock, patch
import sys
import os
import uuid
import time

# Add the services directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "services", "mcp-server", "src"))

# Import MCP components
from client.resource_subscriber import ResourceSubscriberManager
from client.error_handler import ValidationError, ResourceError


class TestResourceSubscriberCore(unittest.TestCase):
    """Test cases for the core functionality of the Resource Subscriber component."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("test_resource_subscriber")
        
        # Create a mock client
        self.client = MagicMock()
        self.client.logger = self.logger
        self.client.send_request_to_server.return_value = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "result": {"status": "success"}
        }
        
        # Create a resource subscriber manager
        self.resource_subscriber = ResourceSubscriberManager(self.client)
        
        # Create a mock callback
        self.callback = MagicMock()
    
    def test_subscribe(self):
        """Test subscribing to a resource."""
        # Subscribe to a resource
        subscription_id = self.resource_subscriber.subscribe(
            server_id="test-server",
            uri="resource://test/resource",
            callback=self.callback
        )
        
        # Check that the client's send_request_to_server method was called correctly
        self.client.send_request_to_server.assert_called_once()
        args, kwargs = self.client.send_request_to_server.call_args
        self.assertEqual(kwargs["server_id"], "test-server")
        self.assertEqual(kwargs["method"], "resources/subscribe")
        self.assertEqual(kwargs["params"]["uri"], "resource://test/resource")
        self.assertEqual(kwargs["params"]["subscription_id"], subscription_id)
        
        # Check that the subscription was stored
        self.assertIn(subscription_id, self.resource_subscriber.subscriptions)
        self.assertEqual(self.resource_subscriber.subscriptions[subscription_id]["server_id"], "test-server")
        self.assertEqual(self.resource_subscriber.subscriptions[subscription_id]["uri"], "resource://test/resource")
        
        # Check that the callback was stored
        self.assertIn(subscription_id, self.resource_subscriber.callbacks)
        self.assertEqual(self.resource_subscriber.callbacks[subscription_id], self.callback)
    
    def test_unsubscribe(self):
        """Test unsubscribing from a resource."""
        # Subscribe to a resource
        subscription_id = self.resource_subscriber.subscribe(
            server_id="test-server",
            uri="resource://test/resource",
            callback=self.callback
        )
        
        # Reset the mock
        self.client.send_request_to_server.reset_mock()
        
        # Unsubscribe from the resource
        result = self.resource_subscriber.unsubscribe(subscription_id)
        
        # Check that the client's send_request_to_server method was called correctly
        self.client.send_request_to_server.assert_called_once()
        args, kwargs = self.client.send_request_to_server.call_args
        self.assertEqual(kwargs["server_id"], "test-server")
        self.assertEqual(kwargs["method"], "resources/unsubscribe")
        self.assertEqual(kwargs["params"]["subscription_id"], subscription_id)
        
        # Check the result
        self.assertTrue(result)
        
        # Check that the subscription was removed
        self.assertNotIn(subscription_id, self.resource_subscriber.subscriptions)
        
        # Check that the callback was removed
        self.assertNotIn(subscription_id, self.resource_subscriber.callbacks)
    
    def test_handle_update(self):
        """Test handling a resource update."""
        # Subscribe to a resource
        subscription_id = self.resource_subscriber.subscribe(
            server_id="test-server",
            uri="resource://test/resource",
            callback=self.callback
        )
        
        # Create update data
        update_data = {
            "content": "Updated content",
            "timestamp": time.time()
        }
        
        # Handle the update
        self.resource_subscriber.handle_update(subscription_id, update_data)
        
        # Check that the callback was called with the update data
        self.callback.assert_called_once_with(update_data)


class TestResourceSubscriberEdgeCases(unittest.TestCase):
    """Test cases for edge cases in the Resource Subscriber component."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("test_resource_subscriber_edge_cases")
        
        # Create a mock client
        self.client = MagicMock()
        self.client.logger = self.logger
        self.client.send_request_to_server.return_value = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "result": {"status": "success"}
        }
        
        # Create a resource subscriber manager
        self.resource_subscriber = ResourceSubscriberManager(self.client)
        
        # Create a mock callback
        self.callback = MagicMock()
    
    def test_subscribe_with_empty_server_id(self):
        """Test subscribing with an empty server ID."""
        # Subscribe with an empty server ID
        with self.assertRaises(ValidationError):
            self.resource_subscriber.subscribe(
                server_id="",
                uri="resource://test/resource",
                callback=self.callback
            )
    
    def test_subscribe_with_empty_uri(self):
        """Test subscribing with an empty URI."""
        # Subscribe with an empty URI
        with self.assertRaises(ValidationError):
            self.resource_subscriber.subscribe(
                server_id="test-server",
                uri="",
                callback=self.callback
            )
    
    def test_subscribe_with_invalid_callback(self):
        """Test subscribing with an invalid callback."""
        # Subscribe with a non-callable callback
        with self.assertRaises(ValidationError):
            self.resource_subscriber.subscribe(
                server_id="test-server",
                uri="resource://test/resource",
                callback="not_a_callable"
            )
        
        # Subscribe with None as callback
        with self.assertRaises(ValidationError):
            self.resource_subscriber.subscribe(
                server_id="test-server",
                uri="resource://test/resource",
                callback=None
            )
    
    def test_unsubscribe_with_empty_subscription_id(self):
        """Test unsubscribing with an empty subscription ID."""
        # Unsubscribe with an empty subscription ID
        with self.assertRaises(ValidationError):
            self.resource_subscriber.unsubscribe("")
    
    def test_unsubscribe_with_nonexistent_subscription_id(self):
        """Test unsubscribing with a nonexistent subscription ID."""
        # Unsubscribe with a nonexistent subscription ID
        with self.assertRaises(ResourceError):
            self.resource_subscriber.unsubscribe("nonexistent_id")
    
    def test_handle_update_with_empty_subscription_id(self):
        """Test handling an update with an empty subscription ID."""
        # Handle an update with an empty subscription ID
        with self.assertRaises(ValidationError):
            self.resource_subscriber.handle_update("", {"content": "Updated content"})
    
    def test_handle_update_with_none_update_data(self):
        """Test handling an update with None as update data."""
        # Subscribe to a resource
        subscription_id = self.resource_subscriber.subscribe(
            server_id="test-server",
            uri="resource://test/resource",
            callback=self.callback
        )
        
        # Handle an update with None as update data
        with self.assertRaises(ValidationError):
            self.resource_subscriber.handle_update(subscription_id, None)
    
    def test_handle_update_with_nonexistent_subscription_id(self):
        """Test handling an update with a nonexistent subscription ID."""
        # Handle an update with a nonexistent subscription ID
        with self.assertRaises(ResourceError):
            self.resource_subscriber.handle_update("nonexistent_id", {"content": "Updated content"})


class TestResourceSubscriberErrorScenarios(unittest.TestCase):
    """Test cases for error scenarios in the Resource Subscriber component."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("test_resource_subscriber_error_scenarios")
        
        # Create a mock client
        self.client = MagicMock()
        self.client.logger = self.logger
        
        # Create a resource subscriber manager
        self.resource_subscriber = ResourceSubscriberManager(self.client)
        
        # Create a mock callback
        self.callback = MagicMock()
    
    def test_subscribe_with_network_error(self):
        """Test subscribing with a network error."""
        # Mock the client's send_request_to_server method to raise an exception
        self.client.send_request_to_server.side_effect = Exception("Network error")
        
        # Subscribe with a network error
        with self.assertRaises(ResourceError) as context:
            self.resource_subscriber.subscribe(
                server_id="test-server",
                uri="resource://test/resource",
                callback=self.callback
            )
        
        # Check the error
        self.assertIn("Network error", str(context.exception))
    
    def test_unsubscribe_with_network_error(self):
        """Test unsubscribing with a network error."""
        # Subscribe to a resource
        self.client.send_request_to_server.return_value = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "result": {"status": "success"}
        }
        subscription_id = self.resource_subscriber.subscribe(
            server_id="test-server",
            uri="resource://test/resource",
            callback=self.callback
        )
        
        # Mock the client's send_request_to_server method to raise an exception
        self.client.send_request_to_server.side_effect = Exception("Network error")
        
        # Unsubscribe with a network error
        with self.assertRaises(ResourceError) as context:
            self.resource_subscriber.unsubscribe(subscription_id)
        
        # Check the error
        self.assertIn("Network error", str(context.exception))
    
    def test_handle_update_with_callback_error(self):
        """Test handling an update with a callback that raises an error."""
        # Subscribe to a resource
        self.client.send_request_to_server.return_value = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "result": {"status": "success"}
        }
        subscription_id = self.resource_subscriber.subscribe(
            server_id="test-server",
            uri="resource://test/resource",
            callback=self.callback
        )
        
        # Mock the callback to raise an exception
        self.callback.side_effect = Exception("Callback error")
        
        # Handle an update with a callback that raises an error
        with self.assertRaises(ResourceError) as context:
            self.resource_subscriber.handle_update(
                subscription_id,
                {"content": "Updated content"}
            )
        
        # Check the error
        self.assertIn("Callback error", str(context.exception))


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
            "timestamp": time.time()
        }
        
        # Handle the update using the SDK
        self.resource_subscriber.handle_update(subscription_id, update_data)
        
        # Check that the SDK resource manager's handle_update method was called
        self.mock_sdk_resource_manager.handle_update.assert_called_once_with(
            sdk_subscription_id,
            update_data
        )


if __name__ == "__main__":
    unittest.main()