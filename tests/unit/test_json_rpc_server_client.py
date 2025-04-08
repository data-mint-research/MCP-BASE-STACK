"""
Unit tests for JSON-RPC server and client implementations.

These tests verify that the JSON-RPC server and client implementations
correctly handle JSON-RPC 2.0 messages according to the specification.
"""

import sys
import os
import unittest
import json
from typing import Dict, Any, List, Optional, Union

# Add the services directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "services", "mcp-server", "src"))

# Import the server and client classes
from server.json_rpc_server import JsonRpcServer
from client.json_rpc_client import JsonRpcClient, JsonRpcError

class TestJsonRpcServerClient(unittest.TestCase):
    """Test cases for JSON-RPC server and client implementations."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a server
        self.server = JsonRpcServer("test-server")
        
        # Register some methods
        self.server.register_method("echo", lambda params: params)
        self.server.register_method("add", lambda params: params["a"] + params["b"])
        self.server.register_method("subtract", lambda params: params["a"] - params["b"])
        self.server.register_method("multiply", lambda params: params["a"] * params["b"])
        self.server.register_method("divide", lambda params: params["a"] / params["b"])
        
        # Create a client with a transport function that sends requests to the server
        self.client = JsonRpcClient("test-client", self._transport)
        
    def _transport(self, request_str: str) -> str:
        """
        Transport function that sends requests to the server.
        
        Args:
            request_str: The request string
            
        Returns:
            str: The response string
        """
        return self.server.process_request(request_str)
        
    def test_call_method(self):
        """Test calling a method."""
        # Call the echo method
        result = self.client.call("echo", {"message": "Hello, World!"})
        self.assertEqual(result, {"message": "Hello, World!"})
        
        # Call the add method
        result = self.client.call("add", {"a": 2, "b": 3})
        self.assertEqual(result, 5)
        
        # Call the subtract method
        result = self.client.call("subtract", {"a": 5, "b": 3})
        self.assertEqual(result, 2)
        
        # Call the multiply method
        result = self.client.call("multiply", {"a": 2, "b": 3})
        self.assertEqual(result, 6)
        
        # Call the divide method
        result = self.client.call("divide", {"a": 6, "b": 3})
        self.assertEqual(result, 2)
        
    def test_call_nonexistent_method(self):
        """Test calling a nonexistent method."""
        with self.assertRaises(JsonRpcError) as context:
            self.client.call("nonexistent_method")
            
        self.assertEqual(context.exception.code, -32601)
        self.assertEqual(context.exception.message, "Method not found")
        
    def test_call_method_with_invalid_params(self):
        """Test calling a method with invalid parameters."""
        with self.assertRaises(JsonRpcError) as context:
            self.client.call("divide", {"a": 6, "b": 0})
            
        self.assertEqual(context.exception.code, -32603)
        self.assertEqual(context.exception.message, "Internal error")
        
    def test_notification(self):
        """Test sending a notification."""
        # Send a notification
        self.client.notify("echo", {"message": "Hello, World!"})
        
        # There's no response to check, but we can verify that no exception was raised
        
    def test_batch_request(self):
        """Test sending a batch request."""
        # Create a batch of requests
        requests = [
            self.client.create_request("add", {"a": 2, "b": 3}, "1"),
            self.client.create_request("subtract", {"a": 5, "b": 3}, "2"),
            self.client.create_request("multiply", {"a": 2, "b": 3}, "3"),
            self.client.create_request("divide", {"a": 6, "b": 3}, "4"),
            self.client.create_notification("echo", {"message": "Hello, World!"})
        ]
        
        # Send the batch request
        responses = self.client.batch(requests)
        
        # Check the responses
        self.assertEqual(len(responses), 4)  # 4 responses (not including the notification)
        
        # Check each response
        for response in responses:
            self.assertEqual(response["jsonrpc"], "2.0")
            self.assertIn("id", response)
            self.assertIn("result", response)
            
        # Check the results
        results = {response["id"]: response["result"] for response in responses}
        self.assertEqual(results["1"], 5)
        self.assertEqual(results["2"], 2)
        self.assertEqual(results["3"], 6)
        self.assertEqual(results["4"], 2)
        
    def test_batch_with_invalid_request(self):
        """Test sending a batch with an invalid request."""
        # Create a batch of requests with one invalid request
        requests = [
            self.client.create_request("add", {"a": 2, "b": 3}, "1"),
            {"jsonrpc": "2.0", "method": "", "id": "2"},  # Invalid method
            self.client.create_request("multiply", {"a": 2, "b": 3}, "3")
        ]
        
        # Send the batch request
        with self.assertRaises(JsonRpcError) as context:
            self.client.batch(requests)
            
        self.assertEqual(context.exception.code, -32600)
        self.assertEqual(context.exception.message, "Invalid Request")
        
    def test_invalid_json(self):
        """Test sending invalid JSON."""
        # Create an invalid JSON string
        invalid_json = "{"
        
        # Create a client with a transport function that returns invalid JSON
        client = JsonRpcClient("test-client", lambda request_str: invalid_json)
        
        # Send a request and expect an error
        with self.assertRaises(JsonRpcError) as context:
            client.call("echo", {"message": "Hello, World!"})
            
        self.assertEqual(context.exception.code, -32700)
        self.assertEqual(context.exception.message, "Parse error")
        
    def test_invalid_response(self):
        """Test receiving an invalid response."""
        # Create a transport function that returns an invalid response
        def invalid_transport(request_str: str) -> str:
            return json.dumps({"jsonrpc": "2.0", "id": "1"})  # Missing result or error
            
        # Create a client with the invalid transport
        client = JsonRpcClient("test-client", invalid_transport)
        
        # Call a method
        with self.assertRaises(JsonRpcError) as context:
            client.call("echo", {"message": "Hello, World!"})
            
        self.assertEqual(context.exception.code, -32600)
        self.assertEqual(context.exception.message, "Invalid Response")

if __name__ == "__main__":
    unittest.main()