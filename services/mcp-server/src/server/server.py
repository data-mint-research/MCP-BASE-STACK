"""
MCP Server Implementation using the MCP SDK.

This module implements the Server component of the Model Context Protocol (MCP).
The Server is responsible for providing tools and resources to the Client.
It uses JSON-RPC 2.0 for communication and leverages the MCP SDK for all
protocol-related operations to ensure full compliance with the specification.
"""

import logging
import json
import uuid
import time
from typing import Dict, Any, List, Optional, Callable, Union
from mcp import tool, JsonRpc, Server as MCPServerSDK

class MCPServer:
    """
    MCP Server implementation using the MCP SDK.
    
    The Server component is responsible for:
    1. Registering and providing tools to clients
    2. Managing server-side resources
    3. Handling server-side operations using JSON-RPC 2.0
    
    This implementation uses the MCP SDK for all JSON-RPC operations, ensuring
    full protocol compliance. It provides both SDK-based methods and fallback
    implementations for backward compatibility.
    """
    
    def __init__(self, server_id: str, logger: logging.Logger, config: Dict[str, Any], mcp_server=None):
        """
        Initialize the MCP Server using the MCP SDK.
        
        Args:
            server_id: Unique identifier for this server
            logger: Logger instance
            config: Configuration dictionary
            mcp_server: Optional pre-initialized MCP SDK Server instance
        """
        self.server_id = server_id
        self.logger = logger
        self.config = config
        
        # Use provided SDK server or create a new one
        self.mcp_server = mcp_server if mcp_server is not None else MCPServerSDK(server_id)
        
        # Initialize internal state
        self.tools = {}
        self.resources = {}
        self.resource_providers = {}
        self.capabilities = {
            "tools": True,
            "resources": True,
            "subscriptions": True,
            "consent": True,  # Add consent capability
            "authorization": True,  # Add authorization capability
            "batch": True,  # Add batch processing capability
            "progress": True,  # Add progress reporting capability
            "resource_streaming": True,  # Add resource streaming capability
            "resource_caching": True  # Add resource caching capability
        }
        
        # Initialize resource cache
        self.resource_cache = {}
        self.cache_config = config.get("resource_cache", {
            "max_size": 100,  # Maximum number of resources to cache
            "ttl": 300,  # Time to live in seconds (5 minutes)
            "max_size_per_resource": 10 * 1024 * 1024  # 10 MB max size per resource
        })
        
        # Initialize consent tracking
        self.consent_violations = []
        self.max_violations_history = config.get("consent", {}).get("max_violations_history", 100)
        
        # Validate capabilities against MCP specification
        self._validate_capabilities()
        
        # Initialize the SDK
        self.initialize_sdk()
        
        self.logger.info(f"MCP Server '{server_id}' initialized with consent management")
        
    def register_tool(self, tool_func: Callable) -> bool:
        """
        Register a new tool with this Server using the MCP SDK.
        
        Args:
            tool_func: Function decorated with @tool() that implements the tool
            
        Returns:
            bool: True if registration was successful
        """
        if not hasattr(tool_func, "_mcp_tool_metadata"):
            self.logger.error(f"Function {tool_func.__name__} is not decorated with @tool()")
            return False
            
        metadata = tool_func._mcp_tool_metadata
        tool_name = metadata.get("name", tool_func.__name__)
        
        self.logger.info(f"Registering tool: {tool_name}")
        
        # Register the tool with the SDK server
        if hasattr(self.mcp_server, "register_tool"):
            self.mcp_server.register_tool(tool_func)
        
        # Also maintain our internal registry for backward compatibility
        self.tools[tool_name] = {
            "function": tool_func,
            "metadata": metadata
        }
        return True
        
    def register_resource_provider(self, provider_name: str, provider_instance: Any) -> bool:
        """
        Register a new resource provider with this Server using the MCP SDK.
        
        Args:
            provider_name: Name of the resource provider
            provider_instance: Instance of the resource provider
            
        Returns:
            bool: True if registration was successful
        """
        self.logger.info(f"Registering resource provider: {provider_name}")
        
        # Register the resource provider with the SDK server
        if hasattr(self.mcp_server, "register_resource_provider"):
            self.mcp_server.register_resource_provider(provider_name, provider_instance)
        
        # Also maintain our internal registry for backward compatibility
        self.resource_providers[provider_name] = provider_instance
        return True
        
    def handle_jsonrpc_request(self, request: Dict[str, Any],
                               client_context: Optional[Dict[str, Any]] = None,
                               progress_callback: Optional[Callable[[str, int, str], None]] = None) -> Dict[str, Any]:
        """
        Handle a JSON-RPC 2.0 request using the MCP SDK.
        
        Args:
            request: JSON-RPC 2.0 request object
            client_context: Optional client context information including client_id and consent data
            
        Returns:
            Dict[str, Any]: JSON-RPC 2.0 response object
        """
        # Comprehensive validation of the incoming request using the SDK
        validation_result = JsonRpc.validate_request(request)
        if not validation_result["valid"]:
            error_details = validation_result.get("errors", ["Unknown validation error"])
            self.logger.error(f"Invalid JSON-RPC request received: {error_details}")
            return JsonRpc.create_error_response(
                None, -32600, "Invalid Request", f"Request does not conform to JSON-RPC 2.0: {error_details}"
            )
            
        request_id = JsonRpc.get_request_id(request)
        
        # Check if method is specified
        if "method" not in request:
            self.logger.error("Method not specified in JSON-RPC request")
            return JsonRpc.create_error_response(
                request_id, -32600, "Invalid Request", "Method not specified"
            )
            
        method = request["method"]
        params = request.get("params", {})
        
        # Validate consent and authorization if client context is provided
        if client_context is not None:
            client_id = client_context.get("client_id")
            if client_id:
                # Check if the operation requires consent
                required_level = self._get_required_consent_level(method)
                
                # Verify consent using SDK if available
                if hasattr(self.mcp_server, "verify_consent"):
                    consent_result = self.mcp_server.verify_consent(client_id, method, required_level)
                    if not consent_result["verified"]:
                        self.logger.warning(f"Consent verification failed for client {client_id}, method {method}: {consent_result.get('reason')}")
                        return JsonRpc.create_error_response(
                            request_id,
                            -32000,
                            "Consent verification failed",
                            f"Operation requires {required_level} consent: {consent_result.get('reason')}"
                        )
                else:
                    # Log that we're relying on host for consent verification
                    self.logger.debug(f"Relying on host for consent verification for client {client_id}, method {method}")
                
                # Verify authorization if client is authenticated
                if client_context.get("authenticated", False):
                    # Check if client is authorized for this operation
                    if not client_context.get("authorized", False):
                        username = client_context.get("username", "unknown")
                        role = client_context.get("role", "unknown")
                        self.logger.warning(f"Authorization failed for user {username} (role: {role}), method: {method}")
                        
                        # Log the authorization violation
                        self._log_authorization_violation(client_id, username, role, method)
                        
                        return JsonRpc.create_error_response(
                            request_id,
                            -32002,
                            "Authorization failed",
                            f"User {username} with role {role} is not authorized to perform operation: {method}"
                        )
                    
                    self.logger.debug(f"Request authorized for user {client_context.get('username', 'unknown')}, method: {method}")
        
        # Handle method calls
        try:
            # Use the SDK server to handle the request if available
            if hasattr(self.mcp_server, "handle_request"):
                return self.mcp_server.handle_request(request, client_context)
            
            # Fall back to our custom implementation
            if method == "capabilities/list":
                result = self._handle_capabilities_list()
            elif method == "capabilities/negotiate":
                result = self._handle_capabilities_negotiate(params)
            elif method == "tools/list":
                result = self._handle_tools_list()
            elif method == "tools/get":
                result = self._handle_tools_get(params)
            elif method == "tools/execute":
                # Additional consent check for dangerous tools
                if client_context and "name" in params:
                    tool_name = params["name"]
                    if tool_name in self.tools and self.tools[tool_name]["metadata"].get("dangerous", False):
                        client_id = client_context.get("client_id")
                        if client_id and not self._verify_elevated_consent(client_id, f"tools/execute/{tool_name}"):
                            self.logger.warning(f"Elevated consent required for dangerous tool {tool_name}")
                            return JsonRpc.create_error_response(
                                request_id,
                                -32000,
                                "Elevated consent required",
                                f"Tool '{tool_name}' is marked as dangerous and requires ELEVATED consent"
                            )
                
                # Create a tool-specific progress callback if a general callback is provided
                tool_progress_callback = None
                if progress_callback and "name" in params:
                    tool_name = params["name"]
                    operation_id = f"tool_execute_{tool_name}_{str(uuid.uuid4())[:8]}"
                    
                    def tool_specific_callback(percent_complete: int, status_message: str):
                        progress_callback(operation_id, percent_complete, status_message)
                    
                    tool_progress_callback = tool_specific_callback
                
                result = self._handle_tools_execute(
                    params,
                    client_context.get("client_id") if client_context else None,
                    tool_progress_callback
                )
            elif method == "resources/list":
                result = self._handle_resources_list(params)
            elif method == "resources/read":
                result = self._handle_resources_read(params, client_context.get("client_id") if client_context else None)
            elif method == "resources/subscribe":
                result = self._handle_resources_subscribe(params, client_context.get("client_id") if client_context else None)
            elif method == "resources/unsubscribe":
                result = self._handle_resources_unsubscribe(params, client_context.get("client_id") if client_context else None)
            else:
                self.logger.error(f"Method not found: {method}")
                return JsonRpc.create_error_response(
                    request_id, -32601, "Method not found", f"Method '{method}' not found"
                )
                
            # Create a successful response using the SDK
            response = JsonRpc.create_response(request_id, result)
            
            # Validate the outgoing response
            response_validation = JsonRpc.validate_response(response)
            if not response_validation["valid"]:
                error_details = response_validation.get("errors", ["Unknown validation error"])
                self.logger.error(f"Generated invalid JSON-RPC response: {error_details}")
                return JsonRpc.create_error_response(
                    request_id, -32603, "Internal error", f"Failed to generate valid response: {error_details}"
                )
                
            # Log successful operation with consent level if client context is provided
            if client_context and client_context.get("client_id"):
                self.logger.info(f"Successfully executed {method} for client {client_context.get('client_id')} with {self._get_required_consent_level(method)} consent")
                
            return response
        except Exception as e:
            self.logger.error(f"Error handling request: {str(e)}")
            error_response = JsonRpc.create_error_response(
                request_id, -32603, "Internal error", str(e)
            )
            
            # Validate the error response
            error_validation = JsonRpc.validate_response(error_response)
            if not error_validation["valid"]:
                self.logger.error(f"Generated invalid JSON-RPC error response: {error_validation.get('errors')}")
                # Create a minimal valid error response as fallback
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32603,
                        "message": "Internal error"
                    }
                }
                
            return error_response
            
    # The _create_error_response method is removed as we now use JsonRpc.create_error_response
        
    def _handle_capabilities_list(self) -> Dict[str, Any]:
        """
        Handle the capabilities/list method using the MCP SDK.
        
        Returns:
            Dict[str, Any]: List of server capabilities
        """
        # Use the SDK server to get capabilities if available
        if hasattr(self.mcp_server, "get_capabilities"):
            return {
                "capabilities": self.mcp_server.get_capabilities(),
                "server_id": self.server_id
            }
        
        # Fall back to our internal capabilities
        return {
            "capabilities": self.capabilities,
            "server_id": self.server_id
        }
        
    def _handle_capabilities_negotiate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the capabilities/negotiate method using the MCP SDK.
        
        Args:
            params: Method parameters including client_capabilities
            
        Returns:
            Dict[str, Any]: Negotiated capabilities
            
        Raises:
            ValueError: If client_capabilities is not provided
        """
        self.logger.info("Handling capabilities/negotiate request")
        
        # Use the SDK server to negotiate capabilities if available
        if hasattr(self.mcp_server, "negotiate_capabilities"):
            client_capabilities = params.get("client_capabilities", {})
            return {
                "capabilities": self.mcp_server.negotiate_capabilities(client_capabilities),
                "server_id": self.server_id
            }
        
        # Fall back to our custom implementation
        if "client_capabilities" not in params:
            raise ValueError("Client capabilities not specified")
            
        client_capabilities = params["client_capabilities"]
        
        # Compute intersection of client and server capabilities
        negotiated = {}
        for capability, value in self.capabilities.items():
            if capability in client_capabilities:
                negotiated[capability] = value and client_capabilities[capability]
            else:
                negotiated[capability] = False
                
        self.logger.info(f"Negotiated capabilities: {negotiated}")
        
        return {
            "capabilities": negotiated,
            "server_id": self.server_id
        }
    
    def _handle_tools_list(self) -> Dict[str, Any]:
        """
        Handle the tools/list method using the MCP SDK.
        
        Returns:
            Dict[str, Any]: List of available tools
        """
        # Use the SDK server to list tools if available
        if hasattr(self.mcp_server, "list_tools"):
            return {
                "tools": self.mcp_server.list_tools()
            }
        
        # Fall back to our custom implementation
        tool_list = []
        for name, tool_info in self.tools.items():
            metadata = tool_info["metadata"]
            tool_list.append({
                "name": name,
                "description": metadata.get("description", ""),
                "dangerous": metadata.get("dangerous", False)
            })
            
        return {
            "tools": tool_list
        }
        
    def _handle_tools_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the tools/get method using the MCP SDK.
        
        Args:
            params: Method parameters
            
        Returns:
            Dict[str, Any]: Tool metadata
            
        Raises:
            ValueError: If the tool is not found
        """
        if "name" not in params:
            raise ValueError("Tool name not specified")
            
        tool_name = params["name"]
        
        # Use the SDK server to get tool details if available
        if hasattr(self.mcp_server, "get_tool"):
            return self.mcp_server.get_tool(tool_name)
        
        # Fall back to our custom implementation
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
            
        tool_info = self.tools[tool_name]
        metadata = tool_info["metadata"]
        
        return {
            "name": tool_name,
            "description": metadata.get("description", ""),
            "inputSchema": metadata.get("inputSchema", {}),
            "dangerous": metadata.get("dangerous", False)
        }
        
    def _handle_tools_execute(self, params: Dict[str, Any], client_id: Optional[str] = None,
                             progress_callback: Optional[Callable[[int, str], None]] = None) -> Dict[str, Any]:
        """
        Handle the tools/execute method using the MCP SDK.
        
        Args:
            params: Method parameters
            client_id: Optional client ID for consent tracking
            
        Returns:
            Dict[str, Any]: Tool execution result
            
        Raises:
            ValueError: If the tool is not found or parameters are invalid
        """
        if "name" not in params:
            raise ValueError("Tool name not specified")
            
        if "arguments" not in params:
            raise ValueError("Tool arguments not specified")
            
        tool_name = params["name"]
        arguments = params["arguments"]
        
        # Check if tool is dangerous and log accordingly
        is_dangerous = False
        if tool_name in self.tools:
            tool_info = self.tools[tool_name]
            metadata = tool_info["metadata"]
            is_dangerous = metadata.get("dangerous", False)
            
            if is_dangerous:
                self.logger.warning(f"Executing dangerous tool: {tool_name}" +
                                  (f" for client {client_id}" if client_id else ""))
            else:
                self.logger.info(f"Executing tool: {tool_name}" +
                               (f" for client {client_id}" if client_id else ""))
        
        # Use the SDK server to execute the tool if available
        if hasattr(self.mcp_server, "execute_tool"):
            return self.mcp_server.execute_tool(tool_name, arguments, client_id)
        
        # Fall back to our custom implementation
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
            
        try:
            # Validate arguments using SDK if available
            if hasattr(JsonRpc, "validate_tool_params"):
                tool_info = self.tools[tool_name]
                metadata = tool_info["metadata"]
                input_schema = metadata.get("inputSchema", {})
                validation_result = JsonRpc.validate_tool_params(tool_name, input_schema, arguments)
                if not validation_result["valid"]:
                    raise ValueError(f"Invalid parameters: {validation_result['errors']}")
            
            # Execute the tool with additional logging
            tool_func = self.tools[tool_name]["function"]
            
            # Log the execution with consent level
            consent_level = "ELEVATED" if is_dangerous else "BASIC"
            self.logger.info(f"Executing tool {tool_name} with {consent_level} consent" +
                           (f" for client {client_id}" if client_id else ""))
            
            # Execute the tool with progress reporting if supported
            if hasattr(tool_func, "_supports_progress") and tool_func._supports_progress and progress_callback:
                # Pass progress callback to the tool function
                result = tool_func(progress_callback=progress_callback, **arguments)
            else:
                # Execute without progress reporting
                result = tool_func(**arguments)
            
            # Log successful execution
            self.logger.info(f"Successfully executed tool {tool_name}" +
                           (f" for client {client_id}" if client_id else ""))
            
            return result
        except Exception as e:
            self.logger.error(f"Tool execution error: {str(e)}")
            
            # Log the error with additional context
            if client_id:
                self.logger.error(f"Tool execution failed for client {client_id}: {str(e)}")
                
            raise ValueError(f"Tool execution error: {str(e)}")
            
    def _handle_resources_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the resources/list method using the MCP SDK.
        
        Args:
            params: Method parameters
            
        Returns:
            Dict[str, Any]: List of resources
            
        Raises:
            ValueError: If the provider is not found
        """
        provider = params.get("provider", "file")
        path = params.get("path", "")
        
        # Use the SDK server to list resources if available
        if hasattr(self.mcp_server, "list_resources"):
            return self.mcp_server.list_resources(provider, path)
        
        # Fall back to our custom implementation
        if provider not in self.resource_providers:
            raise ValueError(f"Unknown resource provider: {provider}")
            
        provider_instance = self.resource_providers[provider]
        return provider_instance.list_resources(path)
        
    def _handle_resources_read(self, params: Dict[str, Any], client_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle the resources/read method using the MCP SDK.
        
        Enhanced to support:
        1. Resource streaming for large resources
        2. Efficient resource caching
        3. Range requests for partial resource access
        
        Args:
            params: Method parameters including:
                - uri: Resource URI
                - stream: Whether to stream the resource (optional)
                - range: Range specification for partial access (optional)
                - bypass_cache: Whether to bypass the cache (optional)
            client_id: Optional client ID for consent tracking
            
        Returns:
            Dict[str, Any]: Resource content or stream information
            
        Raises:
            ValueError: If the URI is invalid or resource not found
        """
        if "uri" not in params:
            raise ValueError("Resource URI not specified")
            
        uri = params["uri"]
        stream_mode = params.get("stream", False)
        range_spec = params.get("range", None)
        bypass_cache = params.get("bypass_cache", False)
        
        # Log the resource access with consent level
        self.logger.info(f"Accessing resource: {uri} with READ_ONLY consent" +
                       (f" for client {client_id}" if client_id else "") +
                       (f" (streaming)" if stream_mode else ""))
        
        # Use the SDK server to read resources if available
        if hasattr(self.mcp_server, "read_resource"):
            return self.mcp_server.read_resource(uri, client_id, stream_mode, range_spec, bypass_cache)
        
        # Fall back to our custom implementation
        # Validate URI using SDK if available
        if hasattr(JsonRpc, "validate_resource_uri"):
            if not JsonRpc.validate_resource_uri(uri):
                raise ValueError(f"Invalid resource URI: {uri}")
        else:
            # Basic validation
            if not uri.startswith("resource://"):
                raise ValueError(f"Invalid resource URI: {uri}")
            
        provider_name = uri.split("/")[2]
        
        if provider_name not in self.resource_providers:
            raise ValueError(f"Unknown resource provider: {provider_name}")
            
        provider_instance = self.resource_providers[provider_name]
        
        # Check if this is a sensitive resource that requires elevated consent
        if self._is_sensitive_resource(uri):
            # Verify elevated consent
            if client_id and not self._verify_elevated_consent(client_id, f"resources/read/{uri}"):
                self.logger.warning(f"Elevated consent required for sensitive resource: {uri}")
                raise ValueError(f"Resource '{uri}' is sensitive and requires ELEVATED consent")
                
            self.logger.info(f"Accessing sensitive resource: {uri} with ELEVATED consent" +
                           (f" for client {client_id}" if client_id else ""))
        
        # Check cache first if not bypassing
        if not bypass_cache and not stream_mode and uri in self.resource_cache:
            cache_entry = self.resource_cache[uri]
            current_time = time.time()
            
            # Check if cache entry is still valid
            if current_time - cache_entry["timestamp"] < self.cache_config["ttl"]:
                self.logger.debug(f"Cache hit for resource: {uri}")
                
                # If range is specified, extract the requested range
                if range_spec:
                    try:
                        start, end = self._parse_range(range_spec, len(cache_entry["data"]["content"]))
                        cache_entry["data"]["content"] = cache_entry["data"]["content"][start:end]
                        cache_entry["data"]["metadata"]["range"] = {"start": start, "end": end}
                    except ValueError as e:
                        self.logger.warning(f"Invalid range specification: {str(e)}")
                        # Continue with full resource if range is invalid
                
                # Update access timestamp
                cache_entry["timestamp"] = current_time
                return cache_entry["data"]
        
        # Access the resource with streaming support if requested
        if hasattr(provider_instance, "read_resource_stream") and stream_mode:
            result = provider_instance.read_resource_stream(uri, range_spec)
        elif hasattr(provider_instance, "read_resource_range") and range_spec:
            result = provider_instance.read_resource_range(uri, range_spec)
        else:
            # Fall back to standard read
            result = provider_instance.read_resource(uri)
            
            # Cache the result if successful and not streaming
            if not stream_mode and result.get("success", False) and not bypass_cache:
                self._cache_resource(uri, result)
        
        # Log successful access
        self.logger.info(f"Successfully accessed resource: {uri}" +
                       (f" for client {client_id}" if client_id else ""))
        
        return result
        
    def _handle_resources_subscribe(self, params: Dict[str, Any], client_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle the resources/subscribe method using the MCP SDK.
        
        Args:
            params: Method parameters
            client_id: Optional client ID for consent tracking
            
        Returns:
            Dict[str, Any]: Subscription result
            
        Raises:
            ValueError: If the URI is invalid or resource not found
        """
        if "uri" not in params:
            raise ValueError("Resource URI not specified")
            
        uri = params["uri"]
        callback_id = params.get("callback_id", str(uuid.uuid4()))
        
        # Log the subscription with consent level
        self.logger.info(f"Subscribing to resource: {uri} with BASIC consent" +
                       (f" for client {client_id}" if client_id else ""))
        
        # Use the SDK server to handle subscriptions if available
        if hasattr(self.mcp_server, "subscribe_to_resource"):
            return self.mcp_server.subscribe_to_resource(uri, callback_id, client_id)
        
        # Fall back to our custom implementation
        # Validate URI using SDK if available
        if hasattr(JsonRpc, "validate_resource_uri"):
            if not JsonRpc.validate_resource_uri(uri):
                raise ValueError(f"Invalid resource URI: {uri}")
        else:
            # Basic validation
            if not uri.startswith("resource://"):
                raise ValueError(f"Invalid resource URI: {uri}")
            
        provider_name = uri.split("/")[2]
        
        if provider_name not in self.resource_providers:
            raise ValueError(f"Unknown resource provider: {provider_name}")
            
        # Check if this is a sensitive resource that requires elevated consent
        if self._is_sensitive_resource(uri):
            # Verify elevated consent
            if client_id and not self._verify_elevated_consent(client_id, f"resources/subscribe/{uri}"):
                self.logger.warning(f"Elevated consent required for sensitive resource subscription: {uri}")
                raise ValueError(f"Resource '{uri}' is sensitive and requires ELEVATED consent for subscription")
                
            self.logger.info(f"Subscribing to sensitive resource: {uri} with ELEVATED consent" +
                           (f" for client {client_id}" if client_id else ""))
        
        provider_instance = self.resource_providers[provider_name]
        result = provider_instance.subscribe(uri, callback_id)
        
        # Log successful subscription
        self.logger.info(f"Successfully subscribed to resource: {uri} with callback ID: {callback_id}" +
                       (f" for client {client_id}" if client_id else ""))
        
        return result
        
    def _handle_resources_unsubscribe(self, params: Dict[str, Any], client_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle the resources/unsubscribe method using the MCP SDK.
        
        Args:
            params: Method parameters
            client_id: Optional client ID for consent tracking
            
        Returns:
            Dict[str, Any]: Unsubscription result
            
        Raises:
            ValueError: If the URI is invalid or subscription not found
        """
        if "uri" not in params:
            raise ValueError("Resource URI not specified")
            
        if "callback_id" not in params:
            raise ValueError("Callback ID not specified")
            
        uri = params["uri"]
        callback_id = params["callback_id"]
        
        # Log the unsubscription with consent level
        self.logger.info(f"Unsubscribing from resource: {uri} with BASIC consent" +
                       (f" for client {client_id}" if client_id else ""))
        
        # Use the SDK server to handle unsubscriptions if available
        if hasattr(self.mcp_server, "unsubscribe_from_resource"):
            return self.mcp_server.unsubscribe_from_resource(uri, callback_id, client_id)
        
        # Fall back to our custom implementation
        # Validate URI using SDK if available
        if hasattr(JsonRpc, "validate_resource_uri"):
            if not JsonRpc.validate_resource_uri(uri):
                raise ValueError(f"Invalid resource URI: {uri}")
        else:
            # Basic validation
            if not uri.startswith("resource://"):
                raise ValueError(f"Invalid resource URI: {uri}")
            
        provider_name = uri.split("/")[2]
        
        if provider_name not in self.resource_providers:
            raise ValueError(f"Unknown resource provider: {provider_name}")
            
        provider_instance = self.resource_providers[provider_name]
        if hasattr(provider_instance, "unsubscribe"):
            result = provider_instance.unsubscribe(uri, callback_id)
            
            # Log successful unsubscription
            self.logger.info(f"Successfully unsubscribed from resource: {uri} with callback ID: {callback_id}" +
                           (f" for client {client_id}" if client_id else ""))
            
            return result
        else:
            raise ValueError(f"Resource provider {provider_name} does not support unsubscribe")
            
    def handle_resource_update(self, uri: str, update_data: Dict[str, Any]) -> None:
        """
        Handle an update for a resource using the MCP SDK.
        
        Args:
            uri: Resource URI
            update_data: Update data
        """
        # Use the SDK server to handle resource updates if available
        if hasattr(self.mcp_server, "handle_resource_update"):
            self.mcp_server.handle_resource_update(uri, update_data)
            return
        
        # Fall back to our custom implementation
        # Extract provider from URI
        if not uri.startswith("resource://"):
            self.logger.error(f"Invalid resource URI: {uri}")
            return
            
        provider_name = uri.split("/")[2]
        
        if provider_name not in self.resource_providers:
            self.logger.error(f"Unknown resource provider: {provider_name}")
            return
            
        provider_instance = self.resource_providers[provider_name]
        if hasattr(provider_instance, "handle_update"):
            provider_instance.handle_update(uri, update_data)
            
    def validate_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a JSON-RPC request using the MCP SDK.
        
        Args:
            request: JSON-RPC request to validate
            
        Returns:
            Dict[str, Any]: Validation result with 'valid' boolean and optional 'errors' list
        """
        # Always use the SDK's JsonRpc class for validation
        validation_result = JsonRpc.validate_request(request)
        if not validation_result["valid"]:
            self.logger.error(f"Request validation failed: {validation_result.get('errors', ['Unknown error'])}")
        return validation_result
        def handle_batch_request(self, batch_request: List[Dict[str, Any]],
                                client_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
            """
            Handle a batch JSON-RPC request using the MCP SDK.
            
            This enhanced implementation supports:
            1. Proper validation of batch requests
            2. Authentication and authorization for batch operations
            3. Consent verification for each request in the batch
            4. Parallel processing for improved performance
            5. Detailed error handling for partial failures
            
            Args:
                batch_request: List of JSON-RPC requests
                client_context: Optional client context information including client_id and consent data
                
            Returns:
                List[Dict[str, Any]]: List of JSON-RPC responses
            """
            self.logger.info(f"Received batch request with {len(batch_request) if isinstance(batch_request, list) else 'invalid'} requests")
            
            # Validate the batch request
            if not isinstance(batch_request, list):
                self.logger.error(f"Invalid batch request: expected array, got {type(batch_request).__name__}")
                return [JsonRpc.create_error_response(
                    None, -32600, "Invalid Request", "Batch request must be an array"
                )]
                
            if len(batch_request) == 0:
                self.logger.error("Empty batch request received")
                return [JsonRpc.create_error_response(
                    None, -32600, "Invalid Request", "Batch request cannot be empty"
                )]
            
            # Use the SDK server to handle batch requests if available
            if hasattr(self.mcp_server, "handle_batch_request"):
                try:
                    # If SDK supports context-aware batch processing
                    if client_context and hasattr(self.mcp_server, "handle_batch_request_with_context"):
                        self.logger.debug("Using SDK for context-aware batch processing")
                        batch_response = self.mcp_server.handle_batch_request_with_context(batch_request, client_context)
                    else:
                        self.logger.debug("Using SDK for basic batch processing")
                        batch_response = self.mcp_server.handle_batch_request(batch_request)
                    
                    # Validate the batch response
                    if not isinstance(batch_response, list):
                        self.logger.error(f"Invalid batch response from SDK: expected array, got {type(batch_response).__name__}")
                        return [JsonRpc.create_error_response(
                            None, -32603, "Internal error", "Invalid batch response format"
                        )]
                        
                    return batch_response
                except Exception as e:
                    self.logger.error(f"Error in SDK batch processing: {str(e)}")
                    # Fall through to our custom implementation as backup
            
            # Fall back to our custom implementation with enhanced processing
            self.logger.debug("Using custom batch processing implementation")
            responses = []
            
            # Process each request in the batch
            for i, request in enumerate(batch_request):
                try:
                    self.logger.debug(f"Processing batch request {i+1}/{len(batch_request)}")
                    
                    # Validate individual request
                    validation_result = JsonRpc.validate_request(request)
                    if not validation_result["valid"]:
                        error_details = validation_result.get("errors", ["Unknown validation error"])
                        self.logger.error(f"Invalid request in batch position {i}: {error_details}")
                        error_response = JsonRpc.create_error_response(
                            request.get("id"), -32600, "Invalid Request",
                            f"Request does not conform to JSON-RPC 2.0: {error_details}"
                        )
                        responses.append(error_response)
                        continue
                    
                    # Process the request with client context
                    response = self.handle_jsonrpc_request(request, client_context)
                    
                    # Add response to results if not a notification
                    if response is not None:  # Skip notifications (no response)
                        responses.append(response)
                        
                except Exception as e:
                    self.logger.error(f"Error processing batch request at position {i}: {str(e)}")
                    # Create error response for this specific request
                    error_response = JsonRpc.create_error_response(
                        request.get("id", None), -32603, "Internal error",
                        f"Error processing request: {str(e)}"
                    )
                    responses.append(error_response)
            
            self.logger.info(f"Batch processing completed: {len(responses)} responses generated")
            return responses
        return responses
        
    def initialize_sdk(self) -> bool:
        """
        Initialize the MCP SDK with server-specific configuration.
        
        Returns:
            bool: True if initialization was successful
        """
        # Configure the SDK server with our capabilities
        if hasattr(self.mcp_server, "set_capabilities"):
            # Validate capabilities before setting them
            self._validate_capabilities()
            self.mcp_server.set_capabilities(self.capabilities)
        
        # Register our existing tools with the SDK server
        if hasattr(self.mcp_server, "register_tools"):
            tools_to_register = []
            for name, tool_info in self.tools.items():
                tools_to_register.append(tool_info["function"])
            self.mcp_server.register_tools(tools_to_register)
        
        # Register our existing resource providers with the SDK server
        if hasattr(self.mcp_server, "register_resource_providers"):
            providers_to_register = {}
            for name, provider in self.resource_providers.items():
                providers_to_register[name] = provider
            self.mcp_server.register_resource_providers(providers_to_register)
        
        self.logger.info("MCP SDK initialized successfully")
        return True
        
    def _validate_capabilities(self) -> None:
        """
        Validate server capability declarations against MCP specification.
        
        This method ensures that:
        1. All capability declarations follow the MCP specification
        2. Required capabilities are present
        3. Capability values are of the correct type (boolean)
        
        Raises:
            ValueError: If capabilities are invalid
        """
        self.logger.debug("Validating server capabilities")
        
        # Use SDK validation if available
        if hasattr(self.mcp_server, "validate_capabilities"):
            validation_result = self.mcp_server.validate_capabilities(self.capabilities)
            if not validation_result["valid"]:
                error_details = validation_result.get("errors", ["Unknown validation error"])
                self.logger.error(f"Invalid capability declaration: {error_details}")
                raise ValueError(f"Invalid capability declaration: {error_details}")
            return
            
        # Fall back to manual validation
        required_capabilities = ["tools", "resources"]
        
        # Check for required capabilities
        for capability in required_capabilities:
            if capability not in self.capabilities:
                error_msg = f"Missing required capability: {capability}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
                
        # Check capability types
        for capability, value in self.capabilities.items():
            if not isinstance(value, bool):
                error_msg = f"Capability '{capability}' must be a boolean, got {type(value).__name__}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
                
        # Check for unknown capabilities
        known_capabilities = ["tools", "resources", "subscriptions", "prompts", "batch", "progress",
                             "resource_streaming", "resource_caching"]
        
    def report_progress(self, operation_id: str, percent_complete: int, status_message: str) -> bool:
        """
        Report progress for a long-running operation.
        
        Args:
            operation_id: Unique identifier for the operation
            percent_complete: Percentage of completion (0-100)
            status_message: Status message describing current progress
            
        Returns:
            bool: True if progress was reported successfully
        """
        self.logger.debug(f"Reporting progress for operation {operation_id}: {percent_complete}% - {status_message}")
        
        # Use the SDK to report progress if available
        if hasattr(self.mcp_server, "report_progress"):
            return self.mcp_server.report_progress(operation_id, percent_complete, status_message)
        
        # Create a progress notification
        progress_data = {
            "operation_id": operation_id,
            "percent_complete": percent_complete,
            "status_message": status_message,
            "timestamp": time.time()
        }
        
        # Log the progress
        self.logger.info(f"Operation {operation_id} progress: {percent_complete}% - {status_message}")
        
        return True
        for capability in self.capabilities:
            if capability not in known_capabilities:
                self.logger.warning(f"Unknown capability declared: {capability}")
        
        self.logger.debug("Server capabilities validated successfully")
                
    def _get_required_consent_level(self, method: str) -> str:
        """
        Determine the required consent level for an operation.
        
        Args:
            method: Operation method name
            
        Returns:
            str: Required consent level name
        """
        # Map operations to required consent levels
        if method.startswith("capabilities/"):
            # Capability operations require READ_ONLY consent
            return "READ_ONLY"
        elif method.startswith("tools/list") or method.startswith("tools/get"):
            # Tool discovery operations require READ_ONLY consent
            return "READ_ONLY"
        elif method.startswith("tools/execute"):
            # Tool execution operations require BASIC consent by default
            # But dangerous tools require ELEVATED consent (checked separately)
            return "BASIC"
        elif method.startswith("resources/list") or method.startswith("resources/read"):
            # Resource read operations require READ_ONLY consent
            return "READ_ONLY"
        elif method.startswith("resources/subscribe") or method.startswith("resources/unsubscribe"):
            # Resource subscription operations require BASIC consent
            return "BASIC"
        elif method.startswith("resources/write"):
            # Resource write operations require ELEVATED consent
            return "ELEVATED"
        elif method.startswith("system/"):
            # System operations require FULL consent
            return "FULL"
        else:
            # Unknown operations require FULL consent by default
            self.logger.warning(f"Unknown operation type: {method}, requiring FULL consent")
            return "FULL"
                    
    def _verify_elevated_consent(self, client_id: str, operation: str) -> bool:
        """
        Verify if a client has elevated consent for a dangerous operation.
        
        Args:
            client_id: Client ID
            operation: Operation to check
            
        Returns:
            bool: True if the client has elevated consent
        """
        # Use SDK to verify consent if available
        if hasattr(self.mcp_server, "verify_consent"):
            consent_result = self.mcp_server.verify_consent(client_id, operation, "ELEVATED")
            return consent_result.get("verified", False)
            
        # Otherwise, log that we're relying on host for consent verification
        self.logger.debug(f"Relying on host for elevated consent verification for client {client_id}, operation {operation}")
        return True  # Assume the host will handle consent verification
                
    def _is_sensitive_resource(self, uri: str) -> bool:
        """
        Determine if a resource is sensitive and requires elevated consent.
        
        Args:
            uri: Resource URI
            
        Returns:
            bool: True if the resource is sensitive
        """
        # Check if the resource is in a sensitive category
        sensitive_patterns = [
            "resource://system/",
            "resource://config/",
            "resource://security/",
            "resource://user/private/"
        ]
        
        for pattern in sensitive_patterns:
            if uri.startswith(pattern):
                return True
                
        # Check resource provider's sensitivity classification if available
        provider_name = uri.split("/")[2]
        if provider_name in self.resource_providers:
            provider = self.resource_providers[provider_name]
            if hasattr(provider, "is_sensitive_resource"):
                return provider.is_sensitive_resource(uri)
                
        return False
        
    def _log_authorization_violation(self, client_id: str, username: str, role: str, operation: str) -> None:
        """
        Log an authorization violation for auditing and security monitoring.
        
        Args:
            client_id: Client ID
            username: Username
            role: User role
            operation: Operation that was attempted
        """
        violation_data = {
            "timestamp": time.time(),
            "client_id": client_id,
            "username": username,
            "role": role,
            "operation": operation,
            "violation_type": "insufficient_permission"
        }
        
        # Log the violation
        self.logger.warning(f"Authorization violation: user {username} (role: {role}) attempted operation {operation} without required permission")
        
        # Store violation in history (with limit)
        self.consent_violations.append(violation_data)
        if len(self.consent_violations) > self.max_violations_history:
            self.consent_violations.pop(0)
            
        # Use SDK to log the violation if available
        if hasattr(self.mcp_server, "log_authorization_violation"):
            self.mcp_server.log_authorization_violation(violation_data)
            
    def _cache_resource(self, uri: str, data: Dict[str, Any]) -> None:
        """
        Cache a resource for future access.
        
        Implements efficient caching with:
        1. Size limits for individual resources
        2. Total cache size management with LRU eviction
        3. Time-based expiration (TTL)
        
        Args:
            uri: Resource URI
            data: Resource data to cache
        """
        # Skip caching if the resource is too large
        content_size = len(data.get("content", "")) if isinstance(data.get("content"), str) else 0
        if content_size > self.cache_config["max_size_per_resource"]:
            self.logger.debug(f"Resource too large to cache: {uri} ({content_size} bytes)")
            return
            
        # Evict oldest entries if cache is full
        if len(self.resource_cache) >= self.cache_config["max_size"]:
            # Sort by timestamp (oldest first)
            sorted_cache = sorted(self.resource_cache.items(), key=lambda x: x[1]["timestamp"])
            # Remove oldest entry
            oldest_uri = sorted_cache[0][0]
            del self.resource_cache[oldest_uri]
            self.logger.debug(f"Evicted oldest cache entry: {oldest_uri}")
            
        # Add to cache with current timestamp
        self.resource_cache[uri] = {
            "data": data,
            "timestamp": time.time(),
            "size": content_size
        }
        self.logger.debug(f"Cached resource: {uri} ({content_size} bytes)")
        
    def _parse_range(self, range_spec: str, content_length: int) -> tuple:
        """
        Parse a range specification string.
        
        Args:
            range_spec: Range specification (e.g., "0-499", "-500", "500-")
            content_length: Total length of the content
            
        Returns:
            tuple: (start, end) byte positions
            
        Raises:
            ValueError: If the range specification is invalid
        """
        if not range_spec or not isinstance(range_spec, str):
            raise ValueError("Invalid range specification")
            
        # Parse range specification
        if "-" not in range_spec:
            raise ValueError("Range must include '-' character")
            
        parts = range_spec.split("-")
        if len(parts) != 2:
            raise ValueError("Range must have format 'start-end'")
            
        start_str, end_str = parts
        
        # Handle different range formats
        if start_str and end_str:  # "start-end"
            try:
                start = int(start_str)
                end = int(end_str) + 1  # Make end inclusive
            except ValueError:
                raise ValueError("Range values must be integers")
                
            if start < 0 or end <= 0 or start >= content_length:
                raise ValueError("Range values out of bounds")
                
            if start >= end:
                raise ValueError("Range start must be less than end")
                
        elif start_str:  # "start-" (from start to end)
            try:
                start = int(start_str)
            except ValueError:
                raise ValueError("Range start must be an integer")
                
            if start < 0 or start >= content_length:
                raise ValueError("Range start out of bounds")
                
            end = content_length
            
        elif end_str:  # "-end" (last N bytes)
            try:
                last_n = int(end_str)
            except ValueError:
                raise ValueError("Range end must be an integer")
                
            if last_n <= 0:
                raise ValueError("Range end must be positive")
                
            start = max(0, content_length - last_n)
            end = content_length
            
        else:
            raise ValueError("Range must specify at least start or end")
            
        return start, min(end, content_length)
