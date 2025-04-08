"""
JSON-RPC 2.0 Server for Model Context Protocol.

This module provides a server implementation that validates and processes
JSON-RPC 2.0 messages according to the specification.
"""

import json
from typing import Dict, Any, List, Optional, Union, Callable

from modelcontextprotocol import JsonRpcValidator

class JsonRpcServer:
    """
    JSON-RPC 2.0 Server for Model Context Protocol.
    
    This class provides methods for handling JSON-RPC 2.0 requests and
    ensuring they comply with the specification.
    """
    
    def __init__(self, server_id: str):
        """
        Initialize a new JsonRpcServer instance.
        
        Args:
            server_id: The ID of this server
        """
        self.server_id = server_id
        self.methods = {}
        
    def register_method(self, method_name: str, handler: Callable):
        """
        Register a method handler.
        
        Args:
            method_name: The name of the method
            handler: The function to handle the method
        """
        self.methods[method_name] = handler
        
    def process_request(self, request_data: str) -> str:
        """
        Process a JSON-RPC request.
        
        Args:
            request_data: The JSON-RPC request data as a string
            
        Returns:
            str: The JSON-RPC response data as a string
        """
        # Parse the request
        validation_result = JsonRpcValidator.validate_json_string(request_data)
        if not validation_result[0]:
            # Invalid JSON
            error_response = JsonRpcValidator.create_error_response(
                None,
                JsonRpcValidator.PARSE_ERROR,
                "Parse error",
                validation_result[2]
            )
            return json.dumps(error_response)
            
        request = validation_result[1]
        
        # Check if it's a batch request
        if isinstance(request, list):
            return self._process_batch_request(request)
        else:
            return self._process_single_request(request)
            
    def _process_single_request(self, request: Dict[str, Any]) -> str:
        """
        Process a single JSON-RPC request.
        
        Args:
            request: The JSON-RPC request object
            
        Returns:
            str: The JSON-RPC response data as a string
        """
        # Validate the request
        validation_result = JsonRpcValidator.validate_request(request)
        if not validation_result["valid"]:
            # Invalid request
            error_response = JsonRpcValidator.create_error_response(
                request.get("id"),
                JsonRpcValidator.INVALID_REQUEST,
                "Invalid Request",
                validation_result["errors"]
            )
            return json.dumps(error_response)
            
        # Check if it's a notification (no ID)
        is_notification = "id" not in request
        
        # Get the method
        method = request.get("method")
        
        # Check if the method exists
        if method not in self.methods:
            if is_notification:
                # Notifications don't get a response
                return ""
                
            error_response = JsonRpcValidator.create_error_response(
                request.get("id"),
                JsonRpcValidator.METHOD_NOT_FOUND,
                "Method not found",
                {"method": method}
            )
            return json.dumps(error_response)
            
        # Get the parameters
        params = request.get("params", {})
        
        try:
            # Call the method
            result = self.methods[method](params)
            
            if is_notification:
                # Notifications don't get a response
                return ""
                
            # Create the response
            response = {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": result
            }
            return json.dumps(response)
        except Exception as e:
            if is_notification:
                # Notifications don't get a response
                return ""
                
            # Create an error response
            error_response = JsonRpcValidator.create_error_response(
                request.get("id"),
                JsonRpcValidator.INTERNAL_ERROR,
                "Internal error",
                str(e)
            )
            return json.dumps(error_response)
            
    def _process_batch_request(self, batch_request: List[Dict[str, Any]]) -> str:
        """
        Process a batch JSON-RPC request.
        
        Args:
            batch_request: The batch JSON-RPC request
            
        Returns:
            str: The JSON-RPC response data as a string
        """
        # Validate the batch request
        validation_result = JsonRpcValidator.validate_batch_request(batch_request)
        if not validation_result["valid"]:
            # Invalid batch request
            error_response = JsonRpcValidator.create_error_response(
                None,
                JsonRpcValidator.INVALID_REQUEST,
                "Invalid Request",
                validation_result["errors"]
            )
            return json.dumps(error_response)
            
        # Process each request in the batch
        responses = []
        for request in batch_request:
            # Process the request
            response_str = self._process_single_request(request)
            if response_str:  # Skip notifications (empty responses)
                responses.append(json.loads(response_str))
                
        # If all requests were notifications, return an empty string
        if not responses:
            return ""
            
        # Return the batch response
        return json.dumps(responses)