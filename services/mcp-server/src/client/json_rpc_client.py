"""
JSON-RPC 2.0 Client for Model Context Protocol.

This module provides a client implementation that validates and processes
JSON-RPC 2.0 messages according to the specification.
"""

import json
import uuid
from typing import Dict, Any, List, Optional, Union, Callable

from modelcontextprotocol import JsonRpcValidator

class JsonRpcClient:
    """
    JSON-RPC 2.0 Client for Model Context Protocol.
    
    This class provides methods for creating and sending JSON-RPC 2.0 requests
    and ensuring they comply with the specification.
    """
    
    def __init__(self, client_id: str, transport: Callable[[str], str]):
        """
        Initialize a new JsonRpcClient instance.
        
        Args:
            client_id: The ID of this client
            transport: A function that sends a request and returns a response
        """
        self.client_id = client_id
        self.transport = transport
        
    def call(self, method: str, params: Dict[str, Any] = None, request_id: str = None) -> Dict[str, Any]:
        """
        Call a method on the server.
        
        Args:
            method: The method name
            params: The method parameters
            request_id: Optional request ID (generated if not provided)
            
        Returns:
            Dict[str, Any]: The response result
            
        Raises:
            JsonRpcError: If the server returns an error
        """
        # Create the request
        request = self.create_request(method, params, request_id)
        
        # Validate the request
        validation_result = JsonRpcValidator.validate_request(request)
        if not validation_result["valid"]:
            raise JsonRpcError(
                JsonRpcValidator.INVALID_REQUEST,
                "Invalid Request",
                validation_result["errors"]
            )
            
        # Send the request
        response_str = self.transport(json.dumps(request))
        
        # Parse the response
        validation_result = JsonRpcValidator.validate_json_string(response_str)
        if not validation_result[0]:
            raise JsonRpcError(
                JsonRpcValidator.PARSE_ERROR,
                "Parse error",
                validation_result[2]
            )
            
        response = validation_result[1]
        
        # Validate the response
        validation_result = JsonRpcValidator.validate_response(response)
        if not validation_result["valid"]:
            raise JsonRpcError(
                JsonRpcValidator.INVALID_REQUEST,
                "Invalid Response",
                validation_result["errors"]
            )
            
        # Check for error
        if "error" in response:
            error = response["error"]
            raise JsonRpcError(
                error["code"],
                error["message"],
                error.get("data")
            )
            
        # Return the result
        return response["result"]
        
    def notify(self, method: str, params: Dict[str, Any] = None) -> None:
        """
        Send a notification to the server.
        
        Args:
            method: The method name
            params: The method parameters
        """
        # Create the notification
        notification = self.create_notification(method, params)
        
        # Validate the notification
        validation_result = JsonRpcValidator.validate_request(notification)
        if not validation_result["valid"]:
            raise JsonRpcError(
                JsonRpcValidator.INVALID_REQUEST,
                "Invalid Request",
                validation_result["errors"]
            )
            
        # Send the notification
        self.transport(json.dumps(notification))
        
    def batch(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Send a batch of requests to the server.
        
        Args:
            requests: A list of requests
            
        Returns:
            List[Dict[str, Any]]: A list of responses
            
        Raises:
            JsonRpcError: If the server returns an error
        """
        # Validate the batch request
        validation_result = JsonRpcValidator.validate_batch_request(requests)
        if not validation_result["valid"]:
            raise JsonRpcError(
                JsonRpcValidator.INVALID_REQUEST,
                "Invalid Request",
                validation_result["errors"]
            )
            
        # Send the batch request
        response_str = self.transport(json.dumps(requests))
        
        # If all requests were notifications, there will be no response
        if not response_str:
            return []
            
        # Parse the response
        validation_result = JsonRpcValidator.validate_json_string(response_str)
        if not validation_result[0]:
            raise JsonRpcError(
                JsonRpcValidator.PARSE_ERROR,
                "Parse error",
                validation_result[2]
            )
            
        responses = validation_result[1]
        
        # Check if the response is a single error
        if isinstance(responses, dict) and "error" in responses:
            error = responses["error"]
            raise JsonRpcError(
                error["code"],
                error["message"],
                error.get("data")
            )
            
        # Validate each response in the batch
        for response in responses:
            validation_result = JsonRpcValidator.validate_response(response)
            if not validation_result["valid"]:
                raise JsonRpcError(
                    JsonRpcValidator.INVALID_REQUEST,
                    "Invalid Response",
                    validation_result["errors"]
                )
                
        return responses
        
    def create_request(self, method: str, params: Dict[str, Any] = None, request_id: str = None) -> Dict[str, Any]:
        """
        Create a new JSON-RPC request.
        
        Args:
            method: The method name
            params: The method parameters
            request_id: Optional request ID (generated if not provided)
            
        Returns:
            Dict[str, Any]: A valid JSON-RPC 2.0 request object
        """
        request = {
            "jsonrpc": "2.0",
            "method": method
        }
        
        if params is not None:
            request["params"] = params
            
        # Add ID if provided or generated (not a notification)
        if request_id is not None:
            request["id"] = request_id
        else:
            request["id"] = str(uuid.uuid4())
            
        return request
        
    def create_notification(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a new JSON-RPC notification (request without ID).
        
        Args:
            method: The method name
            params: The method parameters
            
        Returns:
            Dict[str, Any]: A valid JSON-RPC 2.0 notification object
        """
        notification = {
            "jsonrpc": "2.0",
            "method": method
        }
        
        if params is not None:
            notification["params"] = params
            
        return notification


class JsonRpcError(Exception):
    """
    JSON-RPC Error.
    
    This class represents a JSON-RPC error.
    """
    
    def __init__(self, code: int, message: str, data: Any = None):
        """
        Initialize a new JsonRpcError instance.
        
        Args:
            code: The error code
            message: The error message
            data: Optional additional error data
        """
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"{message} (code: {code})")
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to a dictionary.
        
        Returns:
            Dict[str, Any]: A dictionary representation of this error
        """
        error = {
            "code": self.code,
            "message": self.message
        }
        
        if self.data is not None:
            error["data"] = self.data
            
        return error