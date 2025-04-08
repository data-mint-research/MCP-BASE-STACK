"""
Tests for MCP batch processing implementation.

This module contains tests to verify that the batch processing implementation
works correctly and conforms to the MCP protocol specification.
"""

import unittest
import json
import logging
from typing import Dict, Any, List
from unittest.mock import MagicMock, patch

from ..server.server import MCPServer
from ..client.client import MCPClient
from ..host.host import MCPHost

# Configure logging for tests
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("test_batch_processing")


class TestBatchProcessing(unittest.TestCase):
    """Test cases for batch processing implementation."""

    def setUp(self):
        """Set up test environment before each test."""
        # Create a server with a unique ID
        self.server_id = "test-server"
        self.server_config = {
            "consent": {
                "max_violations_history": 100
            }
        }
        self.server = MCPServer(self.server_id, logger, self.server_config)
        
        # Register test tools
        @self.server.mcp_server.tool()
        def add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b
        
        @self.server.mcp_server.tool()
        def multiply(a: int, b: int) -> int:
            """Multiply two numbers."""
            return a * b
        
        @self.server.mcp_server.tool()
        def divide(a: int, b: int) -> float:
            """Divide two numbers."""
            if b == 0:
                raise ValueError("Cannot divide by zero")
            return a / b
        
        # Register the tools with the server
        self.server.register_tool(add)
        self.server.register_tool(multiply)
        self.server.register_tool(divide)
        
        # Create a host
        self.host_config = {
            "mcp": {
                "host_id": "test-host"
            },
            "auth": {
                "token_expiration": 3600
            }
        }
        self.host = MCPHost(logger, self.host_config)
        
        # Register the server with the host
        self.host.register_server(self.server_id, {"capabilities": self.server.capabilities}, self.server)
        
        # Create a client
        self.client_config = {
            "mcp": {
                "client_id": "test-client"
            }
        }
        self.client = MCPClient(logger, self.client_config)
        
        # Connect the client to the host
        self.client.connect_to_host(self.host)

    def test_server_batch_capability(self):
        """Test that the server has the batch capability."""
        self.assertTrue(self.server.capabilities.get("batch", False),
                        "Server should have batch capability")

    def test_create_batch_request(self):
        """Test creating a batch request."""
        # Create individual requests
        request1 = self.client.create_jsonrpc_request("tools/execute", {
            "name": "add",
            "arguments": {"a": 5, "b": 3}
        })
        
        request2 = self.client.create_jsonrpc_request("tools/execute", {
            "name": "multiply",
            "arguments": {"a": 5, "b": 3}
        })
        
        # Create a batch request
        batch_request = self.client.create_batch_request([request1, request2])
        
        # Verify the batch request
        self.assertIsInstance(batch_request, list,
                             "Batch request should be a list")
        self.assertEqual(len(batch_request), 2,
                        "Batch request should contain 2 requests")
        
        # Verify the individual requests in the batch
        self.assertEqual(batch_request[0]["method"], "tools/execute",
                        "First request should have method 'tools/execute'")
        self.assertEqual(batch_request[1]["method"], "tools/execute",
                        "Second request should have method 'tools/execute'")
        
        self.assertEqual(batch_request[0]["params"]["name"], "add",
                        "First request should be for the 'add' tool")
        self.assertEqual(batch_request[1]["params"]["name"], "multiply",
                        "Second request should be for the 'multiply' tool")

    def test_empty_batch_request(self):
        """Test that creating an empty batch request raises an error."""
        with self.assertRaises(ValueError):
            self.client.create_batch_request([])

    def test_invalid_batch_request(self):
        """Test that creating a batch request with invalid requests raises an error."""
        # Create an invalid request (missing method)
        invalid_request = {"params": {"name": "add", "arguments": {"a": 5, "b": 3}}}
        
        # Create a valid request
        valid_request = self.client.create_jsonrpc_request("tools/execute", {
            "name": "add",
            "arguments": {"a": 5, "b": 3}
        })
        
        # Try to create a batch request with the invalid request
        with self.assertRaises(ValueError):
            self.client.create_batch_request([invalid_request, valid_request])

    def test_server_handle_batch_request(self):
        """Test that the server can handle a batch request."""
        # Create individual requests
        request1 = self.client.create_jsonrpc_request("tools/execute", {
            "name": "add",
            "arguments": {"a": 5, "b": 3}
        })
        
        request2 = self.client.create_jsonrpc_request("tools/execute", {
            "name": "multiply",
            "arguments": {"a": 5, "b": 3}
        })
        
        # Create a batch request
        batch_request = self.client.create_batch_request([request1, request2])
        
        # Create a client context
        client_context = {
            "client_id": "test-client",
            "authenticated": False
        }
        
        # Handle the batch request
        batch_response = self.server.handle_batch_request(batch_request, client_context)
        
        # Verify the batch response
        self.assertIsInstance(batch_response, list,
                             "Batch response should be a list")
        self.assertEqual(len(batch_response), 2,
                        "Batch response should contain 2 responses")
        
        # Verify the individual responses in the batch
        self.assertEqual(batch_response[0]["id"], request1["id"],
                        "First response ID should match first request ID")
        self.assertEqual(batch_response[1]["id"], request2["id"],
                        "Second response ID should match second request ID")
        
        self.assertEqual(batch_response[0]["result"], 8,
                        "First response result should be 8 (5 + 3)")
        self.assertEqual(batch_response[1]["result"], 15,
                        "Second response result should be 15 (5 * 3)")

    def test_server_handle_batch_request_with_error(self):
        """Test that the server handles errors in batch requests correctly."""
        # Create individual requests
        request1 = self.client.create_jsonrpc_request("tools/execute", {
            "name": "add",
            "arguments": {"a": 5, "b": 3}
        })
        
        # This request will cause an error (divide by zero)
        request2 = self.client.create_jsonrpc_request("tools/execute", {
            "name": "divide",
            "arguments": {"a": 10, "b": 0}
        })
        
        request3 = self.client.create_jsonrpc_request("tools/execute", {
            "name": "multiply",
            "arguments": {"a": 5, "b": 3}
        })
        
        # Create a batch request
        batch_request = self.client.create_batch_request([request1, request2, request3])
        
        # Create a client context
        client_context = {
            "client_id": "test-client",
            "authenticated": False
        }
        
        # Handle the batch request
        batch_response = self.server.handle_batch_request(batch_request, client_context)
        
        # Verify the batch response
        self.assertIsInstance(batch_response, list,
                             "Batch response should be a list")
        self.assertEqual(len(batch_response), 3,
                        "Batch response should contain 3 responses")
        
        # Verify the individual responses in the batch
        self.assertEqual(batch_response[0]["id"], request1["id"],
                        "First response ID should match first request ID")
        self.assertEqual(batch_response[1]["id"], request2["id"],
                        "Second response ID should match second request ID")
        self.assertEqual(batch_response[2]["id"], request3["id"],
                        "Third response ID should match third request ID")
        
        # First request should succeed
        self.assertIn("result", batch_response[0],
                     "First response should have a result")
        self.assertEqual(batch_response[0]["result"], 8,
                        "First response result should be 8 (5 + 3)")
        
        # Second request should fail
        self.assertIn("error", batch_response[1],
                     "Second response should have an error")
        self.assertIn("Cannot divide by zero", batch_response[1]["error"]["message"],
                     "Error message should mention division by zero")
        
        # Third request should succeed
        self.assertIn("result", batch_response[2],
                     "Third response should have a result")
        self.assertEqual(batch_response[2]["result"], 15,
                        "Third response result should be 15 (5 * 3)")

    def test_host_route_batch_request(self):
        """Test that the host can route a batch request."""
        # Create individual requests
        request1 = self.client.create_jsonrpc_request("tools/execute", {
            "name": "add",
            "arguments": {"a": 5, "b": 3}
        })
        
        request2 = self.client.create_jsonrpc_request("tools/execute", {
            "name": "multiply",
            "arguments": {"a": 5, "b": 3}
        })
        
        # Create a batch request
        batch_request = self.client.create_batch_request([request1, request2])
        
        # Route the batch request
        batch_response = self.host.route_batch_request(
            self.server_id, batch_request, "test-client"
        )
        
        # Verify the batch response
        self.assertIsInstance(batch_response, list,
                             "Batch response should be a list")
        self.assertEqual(len(batch_response), 2,
                        "Batch response should contain 2 responses")
        
        # Verify the individual responses in the batch
        self.assertEqual(batch_response[0]["id"], request1["id"],
                        "First response ID should match first request ID")
        self.assertEqual(batch_response[1]["id"], request2["id"],
                        "Second response ID should match second request ID")
        
        self.assertEqual(batch_response[0]["result"], 8,
                        "First response result should be 8 (5 + 3)")
        self.assertEqual(batch_response[1]["result"], 15,
                        "Second response result should be 15 (5 * 3)")

    def test_client_send_batch_request(self):
        """Test that the client can send a batch request."""
        # Create individual requests
        request1 = self.client.create_jsonrpc_request("tools/execute", {
            "name": "add",
            "arguments": {"a": 5, "b": 3}
        })
        
        request2 = self.client.create_jsonrpc_request("tools/execute", {
            "name": "multiply",
            "arguments": {"a": 5, "b": 3}
        })
        
        # Create a batch request
        batch_request = self.client.create_batch_request([request1, request2])
        
        # Send the batch request
        batch_results = self.client.send_batch_request_to_server(
            self.server_id, batch_request
        )
        
        # Verify the batch results
        self.assertIsInstance(batch_results, list,
                             "Batch results should be a list")
        self.assertEqual(len(batch_results), 2,
                        "Batch results should contain 2 results")
        
        # Verify the individual results in the batch
        self.assertEqual(batch_results[0]["status"], "success",
                        "First result should have status 'success'")
        self.assertEqual(batch_results[1]["status"], "success",
                        "Second result should have status 'success'")
        
        self.assertEqual(batch_results[0]["data"], 8,
                        "First result data should be 8 (5 + 3)")
        self.assertEqual(batch_results[1]["data"], 15,
                        "Second result data should be 15 (5 * 3)")

    def test_client_send_batch_request_with_error(self):
        """Test that the client handles errors in batch requests correctly."""
        # Create individual requests
        request1 = self.client.create_jsonrpc_request("tools/execute", {
            "name": "add",
            "arguments": {"a": 5, "b": 3}
        })
        
        # This request will cause an error (divide by zero)
        request2 = self.client.create_jsonrpc_request("tools/execute", {
            "name": "divide",
            "arguments": {"a": 10, "b": 0}
        })
        
        request3 = self.client.create_jsonrpc_request("tools/execute", {
            "name": "multiply",
            "arguments": {"a": 5, "b": 3}
        })
        
        # Create a batch request
        batch_request = self.client.create_batch_request([request1, request2, request3])
        
        # Send the batch request and catch the exception
        with self.assertRaises(ValueError):
            batch_results = self.client.send_batch_request_to_server(
                self.server_id, batch_request
            )

    def test_fallback_to_individual_requests(self):
        """Test fallback to individual requests when batch processing is not supported."""
        # Temporarily disable batch processing in the server
        original_batch_capability = self.server.capabilities["batch"]
        self.server.capabilities["batch"] = False
        
        # Update the server registration with the host
        self.host.register_server(self.server_id, {"capabilities": self.server.capabilities}, self.server)
        
        # Create individual requests
        request1 = self.client.create_jsonrpc_request("tools/execute", {
            "name": "add",
            "arguments": {"a": 5, "b": 3}
        })
        
        request2 = self.client.create_jsonrpc_request("tools/execute", {
            "name": "multiply",
            "arguments": {"a": 5, "b": 3}
        })
        
        # Create a batch request
        batch_request = self.client.create_batch_request([request1, request2])
        
        # Send the batch request
        batch_results = self.client.send_batch_request_to_server(
            self.server_id, batch_request
        )
        
        # Verify the batch results
        self.assertIsInstance(batch_results, list,
                             "Batch results should be a list")
        self.assertEqual(len(batch_results), 2,
                        "Batch results should contain 2 results")
        
        # Verify the individual results in the batch
        self.assertEqual(batch_results[0]["status"], "success",
                        "First result should have status 'success'")
        self.assertEqual(batch_results[1]["status"], "success",
                        "Second result should have status 'success'")
        
        self.assertEqual(batch_results[0]["data"], 8,
                        "First result data should be 8 (5 + 3)")
        self.assertEqual(batch_results[1]["data"], 15,
                        "Second result data should be 15 (5 * 3)")
        
        # Restore the original batch capability
        self.server.capabilities["batch"] = original_batch_capability
        self.host.register_server(self.server_id, {"capabilities": self.server.capabilities}, self.server)

    def test_batch_request_with_notifications(self):
        """Test batch request with notifications (no response expected)."""
        # Create a regular request
        request = self.client.create_jsonrpc_request("tools/execute", {
            "name": "add",
            "arguments": {"a": 5, "b": 3}
        })
        
        # Create a notification (no id)
        notification = self.client.create_jsonrpc_notification("tools/execute", {
            "name": "multiply",
            "arguments": {"a": 5, "b": 3}
        })
        
        # Create a batch request with both
        batch_request = self.client.create_batch_request([request, notification])
        
        # Create a client context
        client_context = {
            "client_id": "test-client",
            "authenticated": False
        }
        
        # Handle the batch request
        batch_response = self.server.handle_batch_request(batch_request, client_context)
        
        # Verify the batch response
        self.assertIsInstance(batch_response, list,
                             "Batch response should be a list")
        self.assertEqual(len(batch_response), 1,
                        "Batch response should contain 1 response (for the request, not the notification)")
        
        # Verify the response
        self.assertEqual(batch_response[0]["id"], request["id"],
                        "Response ID should match request ID")
        self.assertEqual(batch_response[0]["result"], 8,
                        "Response result should be 8 (5 + 3)")

    def test_batch_request_performance(self):
        """Test that batch requests are more efficient than individual requests."""
        import time
        
        # Create 10 individual requests
        requests = []
        for i in range(10):
            request = self.client.create_jsonrpc_request("tools/execute", {
                "name": "add",
                "arguments": {"a": i, "b": i}
            })
            requests.append(request)
        
        # Measure time for individual requests
        start_time = time.time()
        for request in requests:
            self.server.handle_jsonrpc_request(request)
        individual_time = time.time() - start_time
        
        # Measure time for batch request
        batch_request = self.client.create_batch_request(requests)
        start_time = time.time()
        self.server.handle_batch_request(batch_request)
        batch_time = time.time() - start_time
        
        # Verify that batch processing is more efficient
        # Note: This is a simple test and may not always pass due to various factors
        # such as system load, but it should generally be true
        self.assertLessEqual(batch_time, individual_time,
                            "Batch processing should be at least as fast as individual requests")


if __name__ == "__main__":
    unittest.main()