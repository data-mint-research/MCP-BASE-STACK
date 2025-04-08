"""
Unit tests for JSON-RPC message structure validation.

These tests verify that the JSON-RPC validation implementation correctly validates
JSON-RPC 2.0 messages according to the specification.
"""

import sys
import os
import unittest
from typing import Dict, Any, List

# Add the services directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "services", "mcp-server", "src"))

# Import the validation classes
from modelcontextprotocol import JsonRpcValidator
from mcp import JsonRpc

class TestJsonRpcValidation(unittest.TestCase):
    """Test cases for JSON-RPC message structure validation."""

    def test_valid_request(self):
        """Test validation of a valid JSON-RPC request."""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/execute",
            "params": {
                "name": "execute_shell_command",
                "arguments": {
                    "command": "echo 'Hello, World!'"
                }
            },
            "id": "request-1"
        }
        
        # Test JsonRpc validation
        result = JsonRpc.validate_request(request)
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)
        
        # Test JsonRpcValidator validation
        result = JsonRpcValidator.validate_request(request)
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)

    def test_valid_notification(self):
        """Test validation of a valid JSON-RPC notification (request without ID)."""
        notification = {
            "jsonrpc": "2.0",
            "method": "progress/update",
            "params": {
                "operation_id": "op-1",
                "percent_complete": 50,
                "status_message": "Processing..."
            }
        }
        
        # Test JsonRpc validation
        result = JsonRpc.validate_request(notification)
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)
        
        # Test JsonRpcValidator validation
        result = JsonRpcValidator.validate_request(notification)
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)

    def test_valid_response(self):
        """Test validation of a valid JSON-RPC response."""
        response = {
            "jsonrpc": "2.0",
            "id": "request-1",
            "result": {
                "success": True,
                "output": "Hello, World!\n"
            }
        }
        
        # Test JsonRpc validation
        result = JsonRpc.validate_response(response)
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)
        
        # Test JsonRpcValidator validation
        result = JsonRpcValidator.validate_response(response)
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)

    def test_valid_error_response(self):
        """Test validation of a valid JSON-RPC error response."""
        error_response = {
            "jsonrpc": "2.0",
            "id": "request-1",
            "error": {
                "code": -32601,
                "message": "Method not found",
                "data": {
                    "method": "non_existent_method"
                }
            }
        }
        
        # Test JsonRpc validation
        result = JsonRpc.validate_response(error_response)
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)
        
        # Test JsonRpcValidator validation
        result = JsonRpcValidator.validate_response(error_response)
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)

    def test_invalid_request_missing_jsonrpc(self):
        """Test validation of an invalid JSON-RPC request missing the jsonrpc field."""
        request = {
            "method": "tools/execute",
            "params": {
                "name": "execute_shell_command",
                "arguments": {
                    "command": "echo 'Hello, World!'"
                }
            },
            "id": "request-1"
        }
        
        # Test JsonRpc validation
        result = JsonRpc.validate_request(request)
        self.assertFalse(result["valid"])
        self.assertIn("Missing 'jsonrpc' field", result["errors"])
        
        # Test JsonRpcValidator validation
        result = JsonRpcValidator.validate_request(request)
        self.assertFalse(result["valid"])
        self.assertIn("Missing 'jsonrpc' field", result["errors"])

    def test_invalid_request_wrong_jsonrpc_version(self):
        """Test validation of an invalid JSON-RPC request with wrong jsonrpc version."""
        request = {
            "jsonrpc": "1.0",
            "method": "tools/execute",
            "params": {
                "name": "execute_shell_command",
                "arguments": {
                    "command": "echo 'Hello, World!'"
                }
            },
            "id": "request-1"
        }
        
        # Test JsonRpc validation
        result = JsonRpc.validate_request(request)
        self.assertFalse(result["valid"])
        self.assertTrue(any("Invalid jsonrpc version" in error for error in result["errors"]))
        
        # Test JsonRpcValidator validation
        result = JsonRpcValidator.validate_request(request)
        self.assertFalse(result["valid"])
        self.assertTrue(any("Invalid jsonrpc version" in error for error in result["errors"]))

    def test_invalid_request_missing_method(self):
        """Test validation of an invalid JSON-RPC request missing the method field."""
        request = {
            "jsonrpc": "2.0",
            "params": {
                "name": "execute_shell_command",
                "arguments": {
                    "command": "echo 'Hello, World!'"
                }
            },
            "id": "request-1"
        }
        
        # Test JsonRpc validation
        result = JsonRpc.validate_request(request)
        self.assertFalse(result["valid"])
        self.assertIn("Missing 'method' field", result["errors"])
        
        # Test JsonRpcValidator validation
        result = JsonRpcValidator.validate_request(request)
        self.assertFalse(result["valid"])
        self.assertIn("Missing 'method' field", result["errors"])

    def test_invalid_request_empty_method(self):
        """Test validation of an invalid JSON-RPC request with empty method."""
        request = {
            "jsonrpc": "2.0",
            "method": "",
            "params": {
                "name": "execute_shell_command",
                "arguments": {
                    "command": "echo 'Hello, World!'"
                }
            },
            "id": "request-1"
        }
        
        # Test JsonRpc validation
        result = JsonRpc.validate_request(request)
        self.assertFalse(result["valid"])
        self.assertIn("Method cannot be empty", result["errors"])
        
        # Test JsonRpcValidator validation
        result = JsonRpcValidator.validate_request(request)
        self.assertFalse(result["valid"])
        self.assertIn("Method cannot be empty", result["errors"])

    def test_invalid_request_invalid_params(self):
        """Test validation of an invalid JSON-RPC request with invalid params."""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/execute",
            "params": "invalid_params",
            "id": "request-1"
        }
        
        # Test JsonRpc validation
        result = JsonRpc.validate_request(request)
        self.assertFalse(result["valid"])
        self.assertTrue(any("Params must be an object or array" in error for error in result["errors"]))
        
        # Test JsonRpcValidator validation
        result = JsonRpcValidator.validate_request(request)
        self.assertFalse(result["valid"])
        self.assertTrue(any("Params must be an object or array" in error for error in result["errors"]))

    def test_invalid_response_missing_id(self):
        """Test validation of an invalid JSON-RPC response missing the id field."""
        response = {
            "jsonrpc": "2.0",
            "result": {
                "success": True,
                "output": "Hello, World!\n"
            }
        }
        
        # Test JsonRpc validation
        result = JsonRpc.validate_response(response)
        self.assertFalse(result["valid"])
        self.assertIn("Missing 'id' field", result["errors"])
        
        # Test JsonRpcValidator validation
        result = JsonRpcValidator.validate_response(response)
        self.assertFalse(result["valid"])
        self.assertIn("Missing 'id' field", result["errors"])

    def test_invalid_response_missing_result_and_error(self):
        """Test validation of an invalid JSON-RPC response missing both result and error."""
        response = {
            "jsonrpc": "2.0",
            "id": "request-1"
        }
        
        # Test JsonRpc validation
        result = JsonRpc.validate_response(response)
        self.assertFalse(result["valid"])
        self.assertIn("Response must contain either 'result' or 'error'", result["errors"])
        
        # Test JsonRpcValidator validation
        result = JsonRpcValidator.validate_response(response)
        self.assertFalse(result["valid"])
        self.assertIn("Response must contain either 'result' or 'error'", result["errors"])

    def test_invalid_response_both_result_and_error(self):
        """Test validation of an invalid JSON-RPC response with both result and error."""
        response = {
            "jsonrpc": "2.0",
            "id": "request-1",
            "result": {
                "success": True
            },
            "error": {
                "code": -32603,
                "message": "Internal error"
            }
        }
        
        # Test JsonRpc validation
        result = JsonRpc.validate_response(response)
        self.assertFalse(result["valid"])
        self.assertIn("Response cannot contain both 'result' and 'error'", result["errors"])
        
        # Test JsonRpcValidator validation
        result = JsonRpcValidator.validate_response(response)
        self.assertFalse(result["valid"])
        self.assertIn("Response cannot contain both 'result' and 'error'", result["errors"])

    def test_invalid_error_response_missing_code(self):
        """Test validation of an invalid JSON-RPC error response missing the code field."""
        error_response = {
            "jsonrpc": "2.0",
            "id": "request-1",
            "error": {
                "message": "Method not found"
            }
        }
        
        # Test JsonRpc validation
        result = JsonRpc.validate_response(error_response)
        self.assertFalse(result["valid"])
        self.assertIn("Error object missing 'code' field", result["errors"])
        
        # Test JsonRpcValidator validation
        result = JsonRpcValidator.validate_response(error_response)
        self.assertFalse(result["valid"])
        self.assertIn("Error object missing 'code' field", result["errors"])

    def test_invalid_error_response_missing_message(self):
        """Test validation of an invalid JSON-RPC error response missing the message field."""
        error_response = {
            "jsonrpc": "2.0",
            "id": "request-1",
            "error": {
                "code": -32601
            }
        }
        
        # Test JsonRpc validation
        result = JsonRpc.validate_response(error_response)
        self.assertFalse(result["valid"])
        self.assertIn("Error object missing 'message' field", result["errors"])
        
        # Test JsonRpcValidator validation
        result = JsonRpcValidator.validate_response(error_response)
        self.assertFalse(result["valid"])
        self.assertIn("Error object missing 'message' field", result["errors"])

    def test_valid_batch_request(self):
        """Test validation of a valid JSON-RPC batch request."""
        batch_request = [
            {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": "request-1"
            },
            {
                "jsonrpc": "2.0",
                "method": "resources/list",
                "params": {
                    "provider": "file",
                    "path": "/"
                },
                "id": "request-2"
            }
        ]
        
        # Test JsonRpc validation
        result = JsonRpc.validate_batch_request(batch_request)
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)
        
        # Test JsonRpcValidator validation
        result = JsonRpcValidator.validate_batch_request(batch_request)
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)

    def test_invalid_batch_request_empty(self):
        """Test validation of an invalid JSON-RPC batch request that is empty."""
        batch_request = []
        
        # Test JsonRpc validation
        result = JsonRpc.validate_batch_request(batch_request)
        self.assertFalse(result["valid"])
        self.assertIn("Batch request cannot be empty", result["errors"])
        
        # Test JsonRpcValidator validation
        result = JsonRpcValidator.validate_batch_request(batch_request)
        self.assertFalse(result["valid"])
        self.assertIn("Batch request cannot be empty", result["errors"])

    def test_invalid_batch_request_not_array(self):
        """Test validation of an invalid JSON-RPC batch request that is not an array."""
        batch_request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": "request-1"
        }
        
        # Test JsonRpc validation
        result = JsonRpc.validate_batch_request(batch_request)
        self.assertFalse(result["valid"])
        self.assertIn("Batch request must be an array", result["errors"])
        
        # Test JsonRpcValidator validation
        result = JsonRpcValidator.validate_batch_request(batch_request)
        self.assertFalse(result["valid"])
        self.assertIn("Batch request must be an array", result["errors"])

    def test_invalid_batch_request_invalid_request(self):
        """Test validation of an invalid JSON-RPC batch request containing an invalid request."""
        batch_request = [
            {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": "request-1"
            },
            {
                "method": "resources/list",  # Missing jsonrpc field
                "params": {
                    "provider": "file",
                    "path": "/"
                },
                "id": "request-2"
            }
        ]
        
        # Test JsonRpc validation
        result = JsonRpc.validate_batch_request(batch_request)
        self.assertFalse(result["valid"])
        self.assertTrue(any("Invalid requests in batch" in error for error in result["errors"]))
        
        # Test JsonRpcValidator validation
        result = JsonRpcValidator.validate_batch_request(batch_request)
        self.assertFalse(result["valid"])
        self.assertTrue(any("Invalid requests in batch" in error for error in result["errors"]))

    def test_tool_params_validation(self):
        """Test validation of tool parameters against a schema."""
        tool_name = "execute_shell_command"
        input_schema = {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Maximum execution time in seconds",
                    "default": 60
                }
            },
            "required": ["command"]
        }
        
        # Valid arguments
        valid_arguments = {
            "command": "echo 'Hello, World!'",
            "timeout": 30
        }
        
        # Test JsonRpc validation
        result = JsonRpc.validate_tool_params(tool_name, input_schema, valid_arguments)
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)
        
        # Test JsonRpcValidator validation
        result = JsonRpcValidator.validate_tool_params(tool_name, input_schema, valid_arguments)
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)
        
        # Invalid arguments - missing required parameter
        invalid_arguments_missing = {
            "timeout": 30
        }
        
        # Test JsonRpc validation
        result = JsonRpc.validate_tool_params(tool_name, input_schema, invalid_arguments_missing)
        self.assertFalse(result["valid"])
        self.assertIn("Missing required parameter: command", result["errors"])
        
        # Test JsonRpcValidator validation
        result = JsonRpcValidator.validate_tool_params(tool_name, input_schema, invalid_arguments_missing)
        self.assertFalse(result["valid"])
        self.assertIn("Missing required parameter: command", result["errors"])
        
        # Invalid arguments - wrong type
        invalid_arguments_type = {
            "command": "echo 'Hello, World!'",
            "timeout": "30"  # Should be an integer
        }
        
        # Test JsonRpc validation
        result = JsonRpc.validate_tool_params(tool_name, input_schema, invalid_arguments_type)
        self.assertFalse(result["valid"])
        self.assertTrue(any("Parameter 'timeout' must be an integer" in error for error in result["errors"]))
        
        # Test JsonRpcValidator validation
        result = JsonRpcValidator.validate_tool_params(tool_name, input_schema, invalid_arguments_type)
        self.assertFalse(result["valid"])
        self.assertTrue(any("Parameter 'timeout' must be an integer" in error for error in result["errors"]))

    def test_resource_uri_validation(self):
        """Test validation of resource URIs."""
        # Valid URI
        valid_uri = "resource://file/path/to/file.txt"
        
        # Test JsonRpc validation
        self.assertTrue(JsonRpc.validate_resource_uri(valid_uri))
        
        # Test JsonRpcValidator validation
        self.assertTrue(JsonRpcValidator.validate_resource_uri(valid_uri))
        
        # Invalid URI - not a string
        invalid_uri_not_string = 123
        
        # Test JsonRpc validation
        self.assertFalse(JsonRpc.validate_resource_uri(invalid_uri_not_string))
        
        # Test JsonRpcValidator validation
        self.assertFalse(JsonRpcValidator.validate_resource_uri(invalid_uri_not_string))
        
        # Invalid URI - wrong scheme
        invalid_uri_wrong_scheme = "http://example.com"
        
        # Test JsonRpc validation
        self.assertFalse(JsonRpc.validate_resource_uri(invalid_uri_wrong_scheme))
        
        # Test JsonRpcValidator validation
        self.assertFalse(JsonRpcValidator.validate_resource_uri(invalid_uri_wrong_scheme))
        
        # Invalid URI - missing provider
        invalid_uri_missing_provider = "resource://"
        
        # Test JsonRpc validation
        self.assertFalse(JsonRpc.validate_resource_uri(invalid_uri_missing_provider))
        
        # Test JsonRpcValidator validation
        self.assertFalse(JsonRpcValidator.validate_resource_uri(invalid_uri_missing_provider))

if __name__ == "__main__":
    unittest.main()