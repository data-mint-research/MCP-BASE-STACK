"""
Unit tests for the MCP Tool Proxy component.

This module contains tests for the MCP Tool Proxy component, focusing on:
1. Proxy creation
2. Argument validation
3. Error handling
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
from client.tool_proxy import ToolProxyManager
from client.error_handler import ValidationError, ToolError


class TestToolProxyCore(unittest.TestCase):
    """Test cases for the core functionality of the Tool Proxy component."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("test_tool_proxy")
        
        # Create a mock client
        self.client = MagicMock()
        self.client.logger = self.logger
        self.client.send_request_to_server.return_value = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "result": {"status": "success", "data": "test_result"}
        }
        
        # Create a tool proxy manager
        self.tool_proxy_manager = ToolProxyManager(self.client)
        
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
                    },
                    "optional_param": {
                        "type": "integer",
                        "description": "An optional parameter"
                    },
                    "enum_param": {
                        "type": "string",
                        "enum": ["option1", "option2", "option3"],
                        "description": "A parameter with enum values"
                    }
                }
            }
        }
    
    def test_create_proxy(self):
        """Test creating a tool proxy."""
        # Create a proxy
        proxy = self.tool_proxy_manager.create_proxy(
            server_id="test-server",
            tool_name="test_tool",
            tool_details=self.tool_details
        )
        
        # Check that the proxy was created correctly
        self.assertEqual(proxy.__name__, "test_tool")
        self.assertEqual(proxy.__doc__, "A test tool")
        self.assertTrue(callable(proxy))
        
        # Check that the proxy was stored
        self.assertIn("test-server:test_tool", self.tool_proxy_manager.proxies)
        self.assertEqual(self.tool_proxy_manager.proxies["test-server:test_tool"], proxy)
    
    def test_proxy_execution(self):
        """Test executing a tool proxy."""
        # Create a proxy
        proxy = self.tool_proxy_manager.create_proxy(
            server_id="test-server",
            tool_name="test_tool",
            tool_details=self.tool_details
        )
        
        # Execute the proxy
        result = proxy(required_param="test_value")
        
        # Check that the client's send_request_to_server method was called correctly
        self.client.send_request_to_server.assert_called_once()
        args, kwargs = self.client.send_request_to_server.call_args
        self.assertEqual(kwargs["server_id"], "test-server")
        self.assertEqual(kwargs["method"], "tools/execute")
        self.assertEqual(kwargs["params"]["name"], "test_tool")
        self.assertEqual(kwargs["params"]["arguments"]["required_param"], "test_value")
        
        # Check the result
        self.assertEqual(result, {"status": "success", "data": "test_result"})
    
    def test_validate_arguments_success(self):
        """Test validating arguments successfully."""
        # Validate arguments
        is_valid, errors = self.tool_proxy_manager.validate_arguments(
            tool_details=self.tool_details,
            arguments={
                "required_param": "test_value",
                "optional_param": 42,
                "enum_param": "option1"
            }
        )
        
        # Check the result
        self.assertTrue(is_valid)
        self.assertIsNone(errors)
    
    def test_validate_arguments_missing_required(self):
        """Test validating arguments with a missing required parameter."""
        # Validate arguments
        is_valid, errors = self.tool_proxy_manager.validate_arguments(
            tool_details=self.tool_details,
            arguments={
                "optional_param": 42
            }
        )
        
        # Check the result
        self.assertFalse(is_valid)
        self.assertIsNotNone(errors)
        self.assertIn("Missing required property: required_param", errors)
    
    def test_validate_arguments_wrong_type(self):
        """Test validating arguments with a wrong type."""
        # Validate arguments
        is_valid, errors = self.tool_proxy_manager.validate_arguments(
            tool_details=self.tool_details,
            arguments={
                "required_param": "test_value",
                "optional_param": "not_an_integer"
            }
        )
        
        # Check the result
        self.assertFalse(is_valid)
        self.assertIsNotNone(errors)
        self.assertIn("Property optional_param must be an integer", errors)
    
    def test_validate_arguments_invalid_enum(self):
        """Test validating arguments with an invalid enum value."""
        # Validate arguments
        is_valid, errors = self.tool_proxy_manager.validate_arguments(
            tool_details=self.tool_details,
            arguments={
                "required_param": "test_value",
                "enum_param": "invalid_option"
            }
        )
        
        # Check the result
        self.assertFalse(is_valid)
        self.assertIsNotNone(errors)
        self.assertIn("Property enum_param must be one of: option1, option2, option3", errors)


class TestToolProxyEdgeCases(unittest.TestCase):
    """Test cases for edge cases in the Tool Proxy component."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("test_tool_proxy_edge_cases")
        
        # Create a mock client
        self.client = MagicMock()
        self.client.logger = self.logger
        self.client.send_request_to_server.return_value = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "result": {"status": "success", "data": "test_result"}
        }
        
        # Create a tool proxy manager
        self.tool_proxy_manager = ToolProxyManager(self.client)
    
    def test_create_proxy_with_minimal_details(self):
        """Test creating a tool proxy with minimal details."""
        # Create minimal tool details
        minimal_details = {
            "name": "minimal_tool"
        }
        
        # Create a proxy
        proxy = self.tool_proxy_manager.create_proxy(
            server_id="test-server",
            tool_name="minimal_tool",
            tool_details=minimal_details
        )
        
        # Check that the proxy was created correctly
        self.assertEqual(proxy.__name__, "minimal_tool")
        self.assertEqual(proxy.__doc__, "Proxy function for minimal_tool")
        self.assertTrue(callable(proxy))
    
    def test_create_proxy_with_empty_schema(self):
        """Test creating a tool proxy with an empty input schema."""
        # Create tool details with an empty schema
        empty_schema_details = {
            "name": "empty_schema_tool",
            "description": "A tool with an empty schema",
            "inputSchema": {}
        }
        
        # Create a proxy
        proxy = self.tool_proxy_manager.create_proxy(
            server_id="test-server",
            tool_name="empty_schema_tool",
            tool_details=empty_schema_details
        )
        
        # Execute the proxy with no arguments
        result = proxy()
        
        # Check the result
        self.assertEqual(result, {"status": "success", "data": "test_result"})
    
    def test_validate_arguments_with_empty_schema(self):
        """Test validating arguments with an empty input schema."""
        # Create tool details with an empty schema
        empty_schema_details = {
            "name": "empty_schema_tool",
            "inputSchema": {}
        }
        
        # Validate arguments
        is_valid, errors = self.tool_proxy_manager.validate_arguments(
            tool_details=empty_schema_details,
            arguments={
                "some_param": "some_value"
            }
        )
        
        # Check the result
        self.assertTrue(is_valid)
        self.assertIsNone(errors)
    
    def test_validate_arguments_with_no_schema(self):
        """Test validating arguments with no input schema."""
        # Create tool details with no schema
        no_schema_details = {
            "name": "no_schema_tool"
        }
        
        # Validate arguments
        is_valid, errors = self.tool_proxy_manager.validate_arguments(
            tool_details=no_schema_details,
            arguments={
                "some_param": "some_value"
            }
        )
        
        # Check the result
        self.assertTrue(is_valid)
        self.assertIsNone(errors)


class TestToolProxyErrorScenarios(unittest.TestCase):
    """Test cases for error scenarios in the Tool Proxy component."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("test_tool_proxy_error_scenarios")
        
        # Create a mock client
        self.client = MagicMock()
        self.client.logger = self.logger
        
        # Create a tool proxy manager
        self.tool_proxy_manager = ToolProxyManager(self.client)
        
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
    
    def test_proxy_execution_with_validation_error(self):
        """Test executing a tool proxy with a validation error."""
        # Create a proxy
        proxy = self.tool_proxy_manager.create_proxy(
            server_id="test-server",
            tool_name="test_tool",
            tool_details=self.tool_details
        )
        
        # Execute the proxy with missing required parameter
        with self.assertRaises(ValidationError) as context:
            proxy()
        
        # Check the error
        self.assertIn("Missing required property: required_param", str(context.exception))
    
    def test_proxy_execution_with_tool_error(self):
        """Test executing a tool proxy with a tool error."""
        # Mock the client's send_request_to_server method to return an error
        self.client.send_request_to_server.return_value = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "error": {
                "code": -32000,
                "message": "Tool execution error"
            }
        }
        
        # Create a proxy
        proxy = self.tool_proxy_manager.create_proxy(
            server_id="test-server",
            tool_name="test_tool",
            tool_details=self.tool_details
        )
        
        # Execute the proxy
        with self.assertRaises(ToolError) as context:
            proxy(required_param="test_value")
        
        # Check the error
        self.assertIn("Tool execution error", str(context.exception))
    
    def test_proxy_execution_with_network_error(self):
        """Test executing a tool proxy with a network error."""
        # Mock the client's send_request_to_server method to raise an exception
        self.client.send_request_to_server.side_effect = Exception("Network error")
        
        # Create a proxy
        proxy = self.tool_proxy_manager.create_proxy(
            server_id="test-server",
            tool_name="test_tool",
            tool_details=self.tool_details
        )
        
        # Execute the proxy
        with self.assertRaises(ToolError) as context:
            proxy(required_param="test_value")
        
        # Check the error
        self.assertIn("Network error", str(context.exception))


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
    
    def test_validate_arguments_with_sdk(self):
        """Test validating arguments using the SDK."""
        # Add validate_tool_params method to JsonRpc
        from modelcontextprotocol.json_rpc import JsonRpc
        original_validate_tool_params = getattr(JsonRpc, 'validate_tool_params', None)
        
        try:
            # Mock JsonRpc.validate_tool_params
            JsonRpc.validate_tool_params = MagicMock(return_value={"valid": True})
            
            # Validate arguments using the SDK
            is_valid, errors = self.tool_proxy_manager.validate_arguments(
                tool_details=self.tool_details,
                arguments={
                    "required_param": "test_value"
                }
            )
            
            # Check that JsonRpc.validate_tool_params was called
            JsonRpc.validate_tool_params.assert_called_once()
            args, kwargs = JsonRpc.validate_tool_params.call_args
            self.assertEqual(args[0], "test_tool")
            self.assertEqual(args[1], self.tool_details.get("inputSchema", {}))
            self.assertEqual(args[2], {"required_param": "test_value"})
            
            # Check the result
            self.assertTrue(is_valid)
            self.assertIsNone(errors)
            
            # Test with validation errors
            JsonRpc.validate_tool_params.reset_mock()
            JsonRpc.validate_tool_params.return_value = {
                "valid": False,
                "errors": ["Missing required parameter: required_param"]
            }
            
            # Validate arguments using the SDK
            is_valid, errors = self.tool_proxy_manager.validate_arguments(
                tool_details=self.tool_details,
                arguments={}
            )
            
            # Check the result
            self.assertFalse(is_valid)
            self.assertIsNotNone(errors)
            self.assertIn("Missing required parameter: required_param", errors)
            
        finally:
            # Restore original method
            if original_validate_tool_params:
                JsonRpc.validate_tool_params = original_validate_tool_params
            else:
                delattr(JsonRpc, 'validate_tool_params')


if __name__ == "__main__":
    unittest.main()