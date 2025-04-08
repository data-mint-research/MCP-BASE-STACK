"""
Unit tests for resource URI validation.

This module tests the resource URI validation functionality in the MCP client and resource subscriber.
"""

import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../services/mcp-server/src')))

from client.client import MCPClient
from client.resource_subscriber import ResourceSubscriberManager
from client.error_handler import ValidationError


class TestResourceUriValidation(unittest.TestCase):
    """Test cases for resource URI validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.logger_mock = MagicMock()
        self.config_mock = {}
        self.client = MCPClient(self.logger_mock, self.config_mock)
        self.resource_subscriber = ResourceSubscriberManager(self.client)

    def test_client_validate_resource_uri_valid(self):
        """Test that valid resource URIs are accepted by the client."""
        valid_uris = [
            "resource://file/path/to/file.txt",
            "resource://system/info",
            "resource://config/settings.json",
            "resource://user/profile",
            "resource://security/keys/public"
        ]
        
        for uri in valid_uris:
            self.assertTrue(
                self.client.validate_resource_uri(uri),
                f"URI '{uri}' should be valid"
            )

    def test_client_validate_resource_uri_invalid(self):
        """Test that invalid resource URIs are rejected by the client."""
        invalid_uris = [
            None,
            "",
            "file://path/to/file.txt",
            "http://example.com",
            "resource:/",
            "resource://",
            "resource:///path/to/file.txt"
        ]
        
        for uri in invalid_uris:
            self.assertFalse(
                self.client.validate_resource_uri(uri),
                f"URI '{uri}' should be invalid"
            )

    def test_subscriber_validate_resource_uri_valid(self):
        """Test that valid resource URIs are accepted by the resource subscriber."""
        valid_uris = [
            "resource://file/path/to/file.txt",
            "resource://system/info",
            "resource://config/settings.json",
            "resource://user/profile",
            "resource://security/keys/public"
        ]
        
        for uri in valid_uris:
            self.assertTrue(
                self.resource_subscriber.validate_resource_uri(uri),
                f"URI '{uri}' should be valid"
            )

    def test_subscriber_validate_resource_uri_invalid(self):
        """Test that invalid resource URIs are rejected by the resource subscriber."""
        invalid_uris = [
            None,
            "",
            "file://path/to/file.txt",
            "http://example.com",
            "resource:/",
            "resource://",
            "resource:///path/to/file.txt"
        ]
        
        for uri in invalid_uris:
            self.assertFalse(
                self.resource_subscriber.validate_resource_uri(uri),
                f"URI '{uri}' should be invalid"
            )

    @patch('client.client.MCPClient._ensure_capability_negotiation')
    @patch('client.client.MCPClient.send_request_to_server')
    def test_access_resource_validates_uri(self, mock_send_request, mock_ensure_capability):
        """Test that access_resource validates the URI before sending the request."""
        # Set up the mocks to return valid responses
        mock_send_request.return_value = {"result": {"content": "test content"}}
        mock_ensure_capability.return_value = None  # Mock the capability negotiation
        
        # Test with a valid URI
        self.client.access_resource("test-server", "resource://file/test.txt")
        mock_send_request.assert_called_once()
        mock_send_request.reset_mock()
        
        # Test with an invalid URI
        with self.assertRaises(ValidationError):
            self.client.access_resource("test-server", "file://test.txt")
        mock_send_request.assert_not_called()

    @patch('client.resource_subscriber.ResourceSubscriberManager._ensure_capability_negotiation')
    @patch('client.client.MCPClient.send_request_to_server')
    def test_subscribe_to_resource_validates_uri(self, mock_send_request, mock_ensure_capability):
        """Test that subscribe_to_resource validates the URI before sending the request."""
        # Set up the mock to return a valid response
        mock_send_request.return_value = {"result": {"subscription_id": "test-id"}}
        mock_callback = MagicMock()
        
        # Test with a valid URI
        self.resource_subscriber.subscribe("test-server", "resource://file/test.txt", mock_callback)
        
        # Test with an invalid URI
        with self.assertRaises(ValidationError):
            self.resource_subscriber.subscribe("test-server", "file://test.txt", mock_callback)


if __name__ == '__main__':
    unittest.main()