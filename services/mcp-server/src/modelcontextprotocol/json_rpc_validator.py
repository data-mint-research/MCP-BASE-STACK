"""
JSON-RPC 2.0 Validator for Model Context Protocol.

This module provides comprehensive validation for JSON-RPC 2.0 messages
according to the specification at https://www.jsonrpc.org/specification.

It ensures all messages include required fields and follow the correct structure.
"""

import json
from typing import Dict, Any, List, Optional, Union, Tuple

class JsonRpcValidator:
    """
    Validator for JSON-RPC 2.0 messages.
    
    This class provides methods for validating JSON-RPC 2.0 requests, responses,
    and batch requests according to the specification.
    """
    
    # JSON-RPC error codes as defined in the specification
    # JSON-RPC error codes as defined in the specification
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # MCP-specific error codes
    CONSENT_REQUIRED = -32000
    AUTHENTICATION_FAILED = -32001
    AUTHORIZATION_FAILED = -32002
    
    @staticmethod
    def validate_request(request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a JSON-RPC request according to the JSON-RPC 2.0 specification.
        
        Args:
            request: The request object to validate
            
        Returns:
            Dict[str, Any]: Validation result with 'valid' boolean and optional 'errors' list
        """
        errors = []
        
        # Check if request is a dictionary
        if not isinstance(request, dict):
            return {
                "valid": False,
                "errors": ["Request must be a JSON object"]
            }
        
        # Check jsonrpc version
        if "jsonrpc" not in request:
            errors.append("Missing 'jsonrpc' field")
        elif request["jsonrpc"] != "2.0":
            errors.append(f"Invalid jsonrpc version: {request['jsonrpc']}, expected '2.0'")
            
        # Check method
        if "method" not in request:
            errors.append("Missing 'method' field")
        elif not isinstance(request["method"], str):
            errors.append(f"Method must be a string, got {type(request['method']).__name__}")
        elif not request["method"]:
            errors.append("Method cannot be empty")
            
        # Check id for requests (not notifications)
        if "id" in request:
            if not isinstance(request["id"], (str, int, type(None))):
                errors.append(f"Id must be a string, number, or null, got {type(request['id']).__name__}")
                
        # Check params if present
        if "params" in request:
            if not isinstance(request["params"], (dict, list)):
                errors.append(f"Params must be an object or array, got {type(request['params']).__name__}")
                
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
        
    @staticmethod
    def validate_response(response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a JSON-RPC response according to the JSON-RPC 2.0 specification.
        
        Args:
            response: The response object to validate
            
        Returns:
            Dict[str, Any]: Validation result with 'valid' boolean and optional 'errors' list
        """
        errors = []
        
        # Check if response is a dictionary
        if not isinstance(response, dict):
            return {
                "valid": False,
                "errors": ["Response must be a JSON object"]
            }
        
        # Check jsonrpc version
        if "jsonrpc" not in response:
            errors.append("Missing 'jsonrpc' field")
        elif response["jsonrpc"] != "2.0":
            errors.append(f"Invalid jsonrpc version: {response['jsonrpc']}, expected '2.0'")
            
        # Check id
        if "id" not in response:
            errors.append("Missing 'id' field")
        elif not isinstance(response["id"], (str, int, type(None))):
            errors.append(f"Id must be a string, number, or null, got {type(response['id']).__name__}")
            
        # Check that response has either result or error, but not both
        has_result = "result" in response
        has_error = "error" in response
        
        if not has_result and not has_error:
            errors.append("Response must contain either 'result' or 'error'")
        elif has_result and has_error:
            errors.append("Response cannot contain both 'result' and 'error'")
            
        # Validate error structure if present
        if has_error:
            error = response["error"]
            if not isinstance(error, dict):
                errors.append("Error must be an object")
            else:
                if "code" not in error:
                    errors.append("Error object missing 'code' field")
                elif not isinstance(error["code"], int):
                    errors.append(f"Error code must be an integer, got {type(error['code']).__name__}")
                    
                if "message" not in error:
                    errors.append("Error object missing 'message' field")
                elif not isinstance(error["message"], str):
                    errors.append(f"Error message must be a string, got {type(error['message']).__name__}")
                    
                if "data" in error and not isinstance(error["data"], (dict, list, str, int, float, bool, type(None))):
                    errors.append(f"Error data must be a JSON value, got {type(error['data']).__name__}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
        
    @staticmethod
    def validate_batch_request(batch_request: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate a JSON-RPC batch request.
        
        Args:
            batch_request: The batch request to validate
            
        Returns:
            Dict[str, Any]: Validation result with 'valid' boolean and optional 'errors' list
        """
        errors = []
        
        # Check if batch_request is a list
        if not isinstance(batch_request, list):
            return {
                "valid": False,
                "errors": ["Batch request must be an array"]
            }
            
        # Check if batch_request is empty
        if len(batch_request) == 0:
            return {
                "valid": False,
                "errors": ["Batch request cannot be empty"]
            }
            
        # Validate each request in the batch
        request_errors = []
        for i, request in enumerate(batch_request):
            validation_result = JsonRpcValidator.validate_request(request)
            if not validation_result["valid"]:
                request_errors.append({
                    "index": i,
                    "errors": validation_result["errors"]
                })
                
        if request_errors:
            errors.append(f"Invalid requests in batch: {request_errors}")
            
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
        
    @staticmethod
    def validate_batch_response(batch_response: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate a JSON-RPC batch response.
        
        Args:
            batch_response: The batch response to validate
            
        Returns:
            Dict[str, Any]: Validation result with 'valid' boolean and optional 'errors' list
        """
            
        errors = []
        
        # Check if batch_response is a list
        if not isinstance(batch_response, list):
            return {
                "valid": False,
                "errors": ["Batch response must be an array"]
            }
            
        # Validate each response in the batch
        response_errors = []
        for i, response in enumerate(batch_response):
            validation_result = JsonRpcValidator.validate_response(response)
            if not validation_result["valid"]:
                response_errors.append({
                    "index": i,
                    "errors": validation_result["errors"]
                })
                
        if response_errors:
            errors.append(f"Invalid responses in batch: {response_errors}")
            
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
        
    @staticmethod
    def validate_tool_params(tool_name: str, input_schema: Dict[str, Any], arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate tool parameters against the tool's input schema.
        
        Args:
            tool_name: The name of the tool
            input_schema: The JSON Schema for the tool's input
            arguments: The arguments to validate
            
        Returns:
            Dict[str, Any]: Validation result with 'valid' boolean and optional 'errors' list
        """
        errors = []
        
        # Check required properties
        if "properties" in input_schema and "required" in input_schema:
            required_props = input_schema["required"]
            for prop in required_props:
                if prop not in arguments:
                    errors.append(f"Missing required parameter: {prop}")
                    
        # Check property types
        if "properties" in input_schema:
            properties = input_schema["properties"]
            for prop_name, prop_schema in properties.items():
                if prop_name in arguments:
                    arg_value = arguments[prop_name]
                    if "type" in prop_schema:
                        expected_type = prop_schema["type"]
                        if expected_type == "string" and not isinstance(arg_value, str):
                            errors.append(f"Parameter '{prop_name}' must be a string")
                        elif expected_type == "number" and not isinstance(arg_value, (int, float)):
                            errors.append(f"Parameter '{prop_name}' must be a number")
                        elif expected_type == "integer" and not isinstance(arg_value, int):
                            errors.append(f"Parameter '{prop_name}' must be an integer")
                        elif expected_type == "boolean" and not isinstance(arg_value, bool):
                            errors.append(f"Parameter '{prop_name}' must be a boolean")
                        elif expected_type == "array" and not isinstance(arg_value, list):
                            errors.append(f"Parameter '{prop_name}' must be an array")
                        elif expected_type == "object" and not isinstance(arg_value, dict):
                            errors.append(f"Parameter '{prop_name}' must be an object")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    @staticmethod
    def validate_resource_uri(uri: str) -> bool:
        """
        Validate a resource URI.
        
        Args:
            uri: The URI to validate
            
        Returns:
            bool: True if the URI is valid, False otherwise
        """
        # Basic validation: must be a string and follow the resource:// scheme
        if not isinstance(uri, str):
            return False
            
        # Check for resource:// scheme
        if not uri.startswith("resource://"):
            return False
            
        # Check for provider
        parts = uri.split("/")
        # The URI format should be resource://provider/path
        # When split by "/", we should have at least 3 parts:
        # ["resource:", "", "provider", ...]
        if len(parts) < 3 or parts[2] == "":
            return False
            
        return True
        
    @staticmethod
    def validate_json_string(json_str: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Validate a JSON string.
        
        Args:
            json_str: The JSON string to validate
            
        Returns:
            Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
                - Success flag
                - Parsed JSON object if successful, None otherwise
                - Error message if unsuccessful, None otherwise
        """
        try:
            parsed = json.loads(json_str)
            return True, parsed, None
        except json.JSONDecodeError as e:
            return False, None, f"Invalid JSON: {str(e)}"
            
    @staticmethod
    def create_error_response(request_id: Optional[Union[str, int]],
                             code: int,
                             message: str,
                             data: Any = None) -> Dict[str, Any]:
        """
        Create a JSON-RPC error response.
        
        Args:
            request_id: The request ID this response corresponds to
            code: The error code
            message: The error message
            data: Optional additional error data
            
        Returns:
            Dict[str, Any]: A valid JSON-RPC 2.0 error response object
        """
        error = {
            "code": code,
            "message": message
        }
        if data is not None:
            error["data"] = data
            
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": error
        }