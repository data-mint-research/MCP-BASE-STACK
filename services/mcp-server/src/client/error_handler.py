"""
MCP Client Component Error Handler.

This module implements a centralized error handling mechanism for the MCP Client component,
ensuring consistent error responses and proper exception handling across all components.
"""

import logging
import json
import traceback
from enum import Enum
from typing import Dict, Any, Optional, Union, List, Tuple, Callable

from mcp import JsonRpcError


class ErrorCategory(Enum):
    """Enumeration of error categories."""
    CLIENT_ERROR = "client_error"  # 400-499 range
    SERVER_ERROR = "server_error"  # 500-599 range
    VALIDATION_ERROR = "validation_error"  # Input validation errors
    PROTOCOL_ERROR = "protocol_error"  # JSON-RPC protocol errors
    NETWORK_ERROR = "network_error"  # Network-related errors
    AUTHENTICATION_ERROR = "authentication_error"  # Authentication errors
    AUTHORIZATION_ERROR = "authorization_error"  # Authorization errors
    RESOURCE_ERROR = "resource_error"  # Resource-related errors
    TOOL_ERROR = "tool_error"  # Tool-related errors
    UNKNOWN_ERROR = "unknown_error"  # Uncategorized errors


class ErrorCode(Enum):
    """Enumeration of error codes with their corresponding HTTP status codes and messages."""
    # Client errors (400-499)
    INVALID_REQUEST = (400, "Invalid request")
    INVALID_PARAMETERS = (400, "Invalid parameters")
    INVALID_METHOD = (405, "Method not allowed")
    RESOURCE_NOT_FOUND = (404, "Resource not found")
    TOOL_NOT_FOUND = (404, "Tool not found")
    SERVER_NOT_FOUND = (404, "Server not found")
    UNAUTHORIZED = (401, "Unauthorized")
    FORBIDDEN = (403, "Forbidden")
    CONFLICT = (409, "Conflict")
    TOO_MANY_REQUESTS = (429, "Too many requests")
    
    # Server errors (500-599)
    INTERNAL_SERVER_ERROR = (500, "Internal server error")
    NOT_IMPLEMENTED = (501, "Not implemented")
    SERVICE_UNAVAILABLE = (503, "Service unavailable")
    TIMEOUT = (504, "Gateway timeout")
    
    # Protocol errors
    PARSE_ERROR = (-32700, "Parse error")
    INVALID_JSON_RPC = (-32600, "Invalid JSON-RPC")
    METHOD_NOT_FOUND = (-32601, "Method not found")
    INVALID_PARAMS = (-32602, "Invalid params")
    INTERNAL_ERROR = (-32603, "Internal error")
    
    # Custom error codes
    VALIDATION_ERROR = (1000, "Validation error")
    NETWORK_ERROR = (1001, "Network error")
    AUTHENTICATION_ERROR = (1002, "Authentication error")
    AUTHORIZATION_ERROR = (1003, "Authorization error")
    RESOURCE_ERROR = (1004, "Resource error")
    TOOL_ERROR = (1005, "Tool error")
    SDK_ERROR = (1006, "SDK error")
    UNKNOWN_ERROR = (9999, "Unknown error")
    
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message


class MCPError(Exception):
    """
    Base exception class for MCP errors.
    
    This class provides a standardized way to create and handle errors in the MCP client component.
    It includes error code, message, category, and additional data.
    """
    
    def __init__(
        self,
        error_code: Union[ErrorCode, int],
        message: Optional[str] = None,
        category: Optional[ErrorCategory] = None,
        data: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        """
        Initialize an MCP error.
        
        Args:
            error_code: The error code, either as an ErrorCode enum or an integer
            message: The error message (will use the default message for the error code if not provided)
            category: The error category (will be inferred from the error code if not provided)
            data: Additional data related to the error
            original_exception: The original exception that caused this error
        """
        self.error_code = error_code.code if isinstance(error_code, ErrorCode) else error_code
        self.error_name = error_code.name if isinstance(error_code, ErrorCode) else "CUSTOM_ERROR"
        self.message = message or (error_code.message if isinstance(error_code, ErrorCode) else "Unknown error")
        self.original_exception = original_exception
        self.data = data or {}
        
        # Add stack trace to data if there's an original exception
        if original_exception:
            self.data["stack_trace"] = traceback.format_exception(
                type(original_exception),
                original_exception,
                original_exception.__traceback__
            )
        
        # Infer category from error code if not provided
        if category:
            self.category = category
        else:
            if isinstance(error_code, ErrorCode):
                if error_code in [
                    ErrorCode.INVALID_REQUEST, ErrorCode.INVALID_PARAMETERS,
                    ErrorCode.INVALID_METHOD, ErrorCode.RESOURCE_NOT_FOUND,
                    ErrorCode.TOOL_NOT_FOUND, ErrorCode.SERVER_NOT_FOUND,
                    ErrorCode.UNAUTHORIZED, ErrorCode.FORBIDDEN,
                    ErrorCode.CONFLICT, ErrorCode.TOO_MANY_REQUESTS
                ]:
                    self.category = ErrorCategory.CLIENT_ERROR
                elif error_code in [
                    ErrorCode.INTERNAL_SERVER_ERROR, ErrorCode.NOT_IMPLEMENTED,
                    ErrorCode.SERVICE_UNAVAILABLE, ErrorCode.TIMEOUT
                ]:
                    self.category = ErrorCategory.SERVER_ERROR
                elif error_code in [
                    ErrorCode.PARSE_ERROR, ErrorCode.INVALID_JSON_RPC,
                    ErrorCode.METHOD_NOT_FOUND, ErrorCode.INVALID_PARAMS,
                    ErrorCode.INTERNAL_ERROR
                ]:
                    self.category = ErrorCategory.PROTOCOL_ERROR
                elif error_code == ErrorCode.VALIDATION_ERROR:
                    self.category = ErrorCategory.VALIDATION_ERROR
                elif error_code == ErrorCode.NETWORK_ERROR:
                    self.category = ErrorCategory.NETWORK_ERROR
                elif error_code == ErrorCode.AUTHENTICATION_ERROR:
                    self.category = ErrorCategory.AUTHENTICATION_ERROR
                elif error_code == ErrorCode.AUTHORIZATION_ERROR:
                    self.category = ErrorCategory.AUTHORIZATION_ERROR
                elif error_code == ErrorCode.RESOURCE_ERROR:
                    self.category = ErrorCategory.RESOURCE_ERROR
                elif error_code == ErrorCode.TOOL_ERROR:
                    self.category = ErrorCategory.TOOL_ERROR
                else:
                    self.category = ErrorCategory.UNKNOWN_ERROR
            else:
                # For custom error codes, use the range to determine category
                if 400 <= self.error_code < 500:
                    self.category = ErrorCategory.CLIENT_ERROR
                elif 500 <= self.error_code < 600:
                    self.category = ErrorCategory.SERVER_ERROR
                else:
                    self.category = ErrorCategory.UNKNOWN_ERROR
        
        # Initialize the base Exception with the message
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the error to a dictionary.
        
        Returns:
            Dict[str, Any]: The error as a dictionary
        """
        error_dict = {
            "code": self.error_code,
            "message": self.message,
            "category": self.category.value,
            "name": self.error_name
        }
        
        if self.data:
            error_dict["data"] = self.data
        
        return error_dict
    
    def to_json_rpc_error(self) -> Dict[str, Any]:
        """
        Convert the error to a JSON-RPC error object.
        
        Returns:
            Dict[str, Any]: The error as a JSON-RPC error object
        """
        error_dict = {
            "code": self.error_code,
            "message": self.message
        }
        
        if self.data:
            error_dict["data"] = {
                "category": self.category.value,
                "name": self.error_name,
                **self.data
            }
        else:
            error_dict["data"] = {
                "category": self.category.value,
                "name": self.error_name
            }
        
        return error_dict
    
    def to_json_rpc_response(self, request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert the error to a JSON-RPC response.
        
        Args:
            request_id: The ID of the request that caused the error
            
        Returns:
            Dict[str, Any]: The error as a JSON-RPC response
        """
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": self.to_json_rpc_error()
        }
    
    def __str__(self) -> str:
        """
        Get a string representation of the error.
        
        Returns:
            str: The error as a string
        """
        return f"{self.error_name} ({self.error_code}): {self.message}"


class ValidationError(MCPError):
    """Exception raised for validation errors."""
    
    def __init__(
        self,
        message: str,
        validation_errors: Optional[List[str]] = None,
        field_errors: Optional[Dict[str, List[str]]] = None,
        data: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        """
        Initialize a validation error.
        
        Args:
            message: The error message
            validation_errors: List of validation error messages
            field_errors: Dictionary mapping field names to lists of error messages
            data: Additional data related to the error
            original_exception: The original exception that caused this error
        """
        error_data = data or {}
        if validation_errors:
            error_data["validation_errors"] = validation_errors
        if field_errors:
            error_data["field_errors"] = field_errors
        
        super().__init__(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=message,
            category=ErrorCategory.VALIDATION_ERROR,
            data=error_data,
            original_exception=original_exception
        )


class NetworkError(MCPError):
    """Exception raised for network errors."""
    
    def __init__(
        self,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        """
        Initialize a network error.
        
        Args:
            message: The error message
            data: Additional data related to the error
            original_exception: The original exception that caused this error
        """
        super().__init__(
            error_code=ErrorCode.NETWORK_ERROR,
            message=message,
            category=ErrorCategory.NETWORK_ERROR,
            data=data,
            original_exception=original_exception
        )


class AuthenticationError(MCPError):
    """Exception raised for authentication errors."""
    
    def __init__(
        self,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        """
        Initialize an authentication error.
        
        Args:
            message: The error message
            data: Additional data related to the error
            original_exception: The original exception that caused this error
        """
        super().__init__(
            error_code=ErrorCode.AUTHENTICATION_ERROR,
            message=message,
            category=ErrorCategory.AUTHENTICATION_ERROR,
            data=data,
            original_exception=original_exception
        )


class AuthorizationError(MCPError):
    """Exception raised for authorization errors."""
    
    def __init__(
        self,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        """
        Initialize an authorization error.
        
        Args:
            message: The error message
            data: Additional data related to the error
            original_exception: The original exception that caused this error
        """
        super().__init__(
            error_code=ErrorCode.AUTHORIZATION_ERROR,
            message=message,
            category=ErrorCategory.AUTHORIZATION_ERROR,
            data=data,
            original_exception=original_exception
        )


class ResourceError(MCPError):
    """Exception raised for resource errors."""
    
    def __init__(
        self,
        message: str,
        resource_uri: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        """
        Initialize a resource error.
        
        Args:
            message: The error message
            resource_uri: The URI of the resource that caused the error
            data: Additional data related to the error
            original_exception: The original exception that caused this error
        """
        error_data = data or {}
        if resource_uri:
            error_data["resource_uri"] = resource_uri
        
        super().__init__(
            error_code=ErrorCode.RESOURCE_ERROR,
            message=message,
            category=ErrorCategory.RESOURCE_ERROR,
            data=error_data,
            original_exception=original_exception
        )


class ToolError(MCPError):
    """Exception raised for tool errors."""
    
    def __init__(
        self,
        message: str,
        tool_name: Optional[str] = None,
        server_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        """
        Initialize a tool error.
        
        Args:
            message: The error message
            tool_name: The name of the tool that caused the error
            server_id: The ID of the server that hosts the tool
            data: Additional data related to the error
            original_exception: The original exception that caused this error
        """
        error_data = data or {}
        if tool_name:
            error_data["tool_name"] = tool_name
        if server_id:
            error_data["server_id"] = server_id
        
        super().__init__(
            error_code=ErrorCode.TOOL_ERROR,
            message=message,
            category=ErrorCategory.TOOL_ERROR,
            data=error_data,
            original_exception=original_exception
        )


class ErrorHandler:
    """
    Centralized error handler for the MCP Client component.
    
    This class provides methods for handling errors consistently across all components.
    """
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize the error handler.
        
        Args:
            logger: The logger to use for logging errors
        """
        self.logger = logger
    
    def handle_exception(
        self,
        exception: Exception,
        context: Optional[str] = None,
        error_code: Optional[Union[ErrorCode, int]] = None,
        category: Optional[ErrorCategory] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> MCPError:
        """
        Handle an exception and convert it to an MCPError.
        
        Args:
            exception: The exception to handle
            context: Optional context information about where the exception occurred
            error_code: Optional error code to use (will be inferred if not provided)
            category: Optional error category to use (will be inferred if not provided)
            data: Optional additional data to include in the error
            
        Returns:
            MCPError: The handled error
        """
        # If the exception is already an MCPError, just log it and return it
        if isinstance(exception, MCPError):
            self._log_error(exception, context)
            return exception
        
        # If it's a JsonRpcError, convert it to an MCPError
        if isinstance(exception, JsonRpcError):
            mcp_error = self._convert_jsonrpc_error(exception, data)
            self._log_error(mcp_error, context)
            return mcp_error
        
        # For other exceptions, create a new MCPError
        if error_code is None:
            error_code = ErrorCode.UNKNOWN_ERROR
        
        error_message = str(exception)
        mcp_error = MCPError(
            error_code=error_code,
            message=error_message,
            category=category,
            data=data,
            original_exception=exception
        )
        
        self._log_error(mcp_error, context)
        return mcp_error
    
    def create_error(
        self,
        error_code: Union[ErrorCode, int],
        message: Optional[str] = None,
        category: Optional[ErrorCategory] = None,
        data: Optional[Dict[str, Any]] = None,
        context: Optional[str] = None
    ) -> MCPError:
        """
        Create a new MCPError.
        
        Args:
            error_code: The error code
            message: Optional error message (will use the default message for the error code if not provided)
            category: Optional error category (will be inferred from the error code if not provided)
            data: Optional additional data to include in the error
            context: Optional context information about where the error occurred
            
        Returns:
            MCPError: The created error
        """
        mcp_error = MCPError(
            error_code=error_code,
            message=message,
            category=category,
            data=data
        )
        
        self._log_error(mcp_error, context)
        return mcp_error
    
    def create_validation_error(
        self,
        message: str,
        validation_errors: Optional[List[str]] = None,
        field_errors: Optional[Dict[str, List[str]]] = None,
        data: Optional[Dict[str, Any]] = None,
        context: Optional[str] = None
    ) -> ValidationError:
        """
        Create a new ValidationError.
        
        Args:
            message: The error message
            validation_errors: Optional list of validation error messages
            field_errors: Optional dictionary mapping field names to lists of error messages
            data: Optional additional data to include in the error
            context: Optional context information about where the error occurred
            
        Returns:
            ValidationError: The created error
        """
        validation_error = ValidationError(
            message=message,
            validation_errors=validation_errors,
            field_errors=field_errors,
            data=data
        )
        
        self._log_error(validation_error, context)
        return validation_error
    
    def _convert_jsonrpc_error(
        self,
        jsonrpc_error: JsonRpcError,
        data: Optional[Dict[str, Any]] = None
    ) -> MCPError:
        """
        Convert a JsonRpcError to an MCPError.
        
        Args:
            jsonrpc_error: The JsonRpcError to convert
            data: Optional additional data to include in the error
            
        Returns:
            MCPError: The converted error
        """
        error_code = jsonrpc_error.code
        error_message = jsonrpc_error.message
        error_data = jsonrpc_error.data or {}
        
        if data:
            error_data.update(data)
        
        # Map JSON-RPC error codes to MCPError categories
        if error_code == -32700:  # Parse error
            category = ErrorCategory.PROTOCOL_ERROR
        elif error_code == -32600:  # Invalid JSON-RPC
            category = ErrorCategory.PROTOCOL_ERROR
        elif error_code == -32601:  # Method not found
            category = ErrorCategory.PROTOCOL_ERROR
        elif error_code == -32602:  # Invalid params
            category = ErrorCategory.VALIDATION_ERROR
        elif error_code == -32603:  # Internal error
            category = ErrorCategory.SERVER_ERROR
        elif -32099 <= error_code <= -32000:  # Server error
            category = ErrorCategory.SERVER_ERROR
        else:
            category = ErrorCategory.UNKNOWN_ERROR
        
        return MCPError(
            error_code=error_code,
            message=error_message,
            category=category,
            data=error_data,
            original_exception=jsonrpc_error
        )
    
    def _log_error(self, error: MCPError, context: Optional[str] = None):
        """
        Log an error with the appropriate severity level.
        
        Args:
            error: The error to log
            context: Optional context information about where the error occurred
        """
        log_message = f"{context + ': ' if context else ''}{str(error)}"
        
        # Determine the appropriate log level based on the error category
        if error.category in [ErrorCategory.CLIENT_ERROR, ErrorCategory.VALIDATION_ERROR]:
            self.logger.warning(log_message)
        elif error.category in [ErrorCategory.SERVER_ERROR, ErrorCategory.NETWORK_ERROR, ErrorCategory.UNKNOWN_ERROR]:
            self.logger.error(log_message)
        elif error.category in [ErrorCategory.AUTHENTICATION_ERROR, ErrorCategory.AUTHORIZATION_ERROR]:
            self.logger.warning(log_message)
        elif error.category in [ErrorCategory.PROTOCOL_ERROR]:
            self.logger.error(log_message)
        elif error.category in [ErrorCategory.RESOURCE_ERROR, ErrorCategory.TOOL_ERROR]:
            self.logger.warning(log_message)
        else:
            self.logger.error(log_message)
        
        # Log the stack trace for server errors and unknown errors
        if error.category in [ErrorCategory.SERVER_ERROR, ErrorCategory.UNKNOWN_ERROR] and error.original_exception:
            self.logger.debug(f"Stack trace: {error.data.get('stack_trace', 'No stack trace available')}")


def create_error_response(
    error: Union[MCPError, Exception],
    request_id: Optional[str] = None,
    error_handler: Optional[ErrorHandler] = None,
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        error: The error to convert to a response
        request_id: The ID of the request that caused the error
        error_handler: Optional error handler to use for handling the error
        logger: Optional logger to use for logging the error
        
    Returns:
        Dict[str, Any]: The error response
    """
    # If the error is already an MCPError, use it directly
    if isinstance(error, MCPError):
        return error.to_json_rpc_response(request_id)
    
    # If an error handler is provided, use it to handle the error
    if error_handler:
        mcp_error = error_handler.handle_exception(error)
        return mcp_error.to_json_rpc_response(request_id)
    
    # If a logger is provided, log the error
    if logger:
        logger.error(f"Error in request {request_id}: {str(error)}")
    
    # Create a generic error response
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": -32603,  # Internal error
            "message": str(error),
            "data": {
                "category": ErrorCategory.UNKNOWN_ERROR.value,
                "name": "UNKNOWN_ERROR"
            }
        }
    }


def validate_request(
    request: Dict[str, Any],
    required_params: Optional[List[str]] = None,
    optional_params: Optional[List[str]] = None,
    param_types: Optional[Dict[str, Union[type, Tuple[type, ...]]]] = None,
    param_validators: Optional[Dict[str, Callable[[Any], Tuple[bool, Optional[str]]]]] = None
) -> Tuple[bool, Optional[ValidationError]]:
    """
    Validate a request against a schema.
    
    Args:
        request: The request to validate
        required_params: Optional list of required parameter names
        optional_params: Optional list of optional parameter names
        param_types: Optional dictionary mapping parameter names to expected types
        param_validators: Optional dictionary mapping parameter names to validator functions
        
    Returns:
        Tuple[bool, Optional[ValidationError]]: A tuple containing a boolean indicating whether the request is valid,
        and an optional ValidationError if the request is invalid
    """
    validation_errors = []
    field_errors = {}
    
    # Check that the request is a dictionary
    if not isinstance(request, dict):
        return False, ValidationError(
            message="Request must be a dictionary",
            validation_errors=["Request must be a dictionary"]
        )
    
    # Check for required JSON-RPC fields
    if "jsonrpc" not in request:
        validation_errors.append("Missing 'jsonrpc' field")
    elif request["jsonrpc"] != "2.0":
        validation_errors.append("Invalid 'jsonrpc' version, must be '2.0'")
    
    if "method" not in request:
        validation_errors.append("Missing 'method' field")
    elif not isinstance(request["method"], str):
        validation_errors.append("'method' field must be a string")
    
    # Check for params field
    if "params" not in request:
        if required_params:
            validation_errors.append("Missing 'params' field")
            params = {}
        else:
            params = {}
    elif not isinstance(request["params"], dict):
        validation_errors.append("'params' field must be a dictionary")
        params = {}
    else:
        params = request["params"]
    
    # Check for required parameters
    if required_params:
        for param in required_params:
            if param not in params:
                if param not in field_errors:
                    field_errors[param] = []
                field_errors[param].append(f"Missing required parameter: {param}")
    
    # Check parameter types
    if param_types:
        for param, expected_type in param_types.items():
            if param in params:
                if not isinstance(params[param], expected_type):
                    if param not in field_errors:
                        field_errors[param] = []
                    
                    if isinstance(expected_type, tuple):
                        type_names = " or ".join([t.__name__ for t in expected_type])
                        field_errors[param].append(f"Parameter '{param}' must be of type {type_names}")
                    else:
                        field_errors[param].append(f"Parameter '{param}' must be of type {expected_type.__name__}")
    
    # Run custom validators
    if param_validators:
        for param, validator in param_validators.items():
            if param in params:
                is_valid, error_message = validator(params[param])
                if not is_valid:
                    if param not in field_errors:
                        field_errors[param] = []
                    field_errors[param].append(error_message or f"Invalid value for parameter '{param}'")
    
    # Check for unknown parameters
    if optional_params or required_params:
        allowed_params = set(optional_params or []) | set(required_params or [])
        for param in params:
            if param not in allowed_params:
                validation_errors.append(f"Unknown parameter: {param}")
    
    # If there are any validation errors, return False and a ValidationError
    if validation_errors or field_errors:
        return False, ValidationError(
            message="Request validation failed",
            validation_errors=validation_errors,
            field_errors=field_errors
        )
    
    return True, None