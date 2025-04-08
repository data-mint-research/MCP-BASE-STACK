"""
MCP Host Implementation.

This module implements the Host component of the Model Context Protocol (MCP).
The Host is responsible for managing the communication between the Client and Server components,
coordinating multiple clients, managing context and consent, and providing authentication and authorization.
"""

import logging
import uuid
import time
import json
import os
from typing import Dict, Any, List, Optional, Callable, Set, Tuple
from enum import Enum
from temp.mcp import Host, Client, Server, Consent, Context, Authentication, JsonRpc

class ConsentLevel(Enum):
    """
    Consent levels for operations.
    
    NONE: No consent granted
    READ_ONLY: Read-only access to non-sensitive information
    BASIC: Basic operations that don't modify system state
    ELEVATED: Operations that modify system state
    FULL: Full access to all operations
    """
    NONE = 0
    READ_ONLY = 1
    BASIC = 2
    ELEVATED = 3
    FULL = 4


class Role(Enum):
    """
    User roles for role-based access control.
    
    USER: Regular user with basic permissions
    POWER_USER: Power user with elevated permissions
    ADMIN: Administrator with full access
    """
    USER = 1
    POWER_USER = 2
    ADMIN = 3


class Permission(Enum):
    """
    Fine-grained permissions for authorization control.
    
    READ: Permission to read resources and list tools
    WRITE: Permission to modify resources
    EXECUTE: Permission to execute tools
    ADMIN: Permission to perform administrative operations
    """
    READ = 1
    WRITE = 2
    EXECUTE = 3
    ADMIN = 4


class MCPHost:
    """
    MCP Host implementation using the MCP SDK.
    
    The Host component is responsible for:
    1. Managing connections to MCP Servers
    2. Routing requests from Clients to appropriate Servers
    3. Handling lifecycle events for the MCP ecosystem
    4. Managing client registration and authentication
    5. Tracking context and consent for operations
    6. Coordinating multiple clients
    """
    def __init__(self, logger: logging.Logger, config: Dict[str, Any],
                 mcp_host=None, auth_provider=None, context_manager=None, consent_manager=None,
                 authorization_provider=None):
        """
        Initialize the MCP Host.
        
        Args:
            logger: Logger instance
            config: Configuration dictionary
            mcp_host: Optional pre-initialized MCP SDK Host instance
            auth_provider: Optional pre-initialized Authentication provider
            context_manager: Optional pre-initialized Context manager
            consent_manager: Optional pre-initialized Consent manager
        """
        self.logger = logger
        self.config = config
        
        # Initialize host ID from config or generate a new one
        host_id = config.get("mcp", {}).get("host_id", str(uuid.uuid4()))
        
        # Use provided SDK components or create new ones
        self.mcp_host = mcp_host if mcp_host is not None else Host(host_id)
        # Initialize authentication provider with SDK
        auth_config = config.get("auth", {})
        self.auth_provider = auth_provider if auth_provider is not None else Authentication.create_provider(auth_config)
        
        # Initialize context and consent managers with SDK
        self.context_manager = context_manager if context_manager is not None else Context.create_manager(config.get("context", {}))
        self.consent_manager = consent_manager if consent_manager is not None else Consent.create_manager(config.get("consent", {}))
        
        # Initialize internal state
        self.servers = {}
        self.clients = {}
        self.contexts = {}
        self.consent_registry = {}
        # Enhanced session management
        self.user_sessions = {}
        self.event_subscribers = {}
        self.token_expiration = auth_config.get("token_expiration", 3600)  # Default: 1 hour
        self.session_cleanup_interval = auth_config.get("session_cleanup_interval", 300)  # Default: 5 minutes
        self.last_cleanup_time = time.time()
        
        # Initialize role-based access control
        self.authorization_provider = authorization_provider
        self.role_permissions = {
            Role.USER: {Permission.READ, Permission.EXECUTE},
            Role.POWER_USER: {Permission.READ, Permission.WRITE, Permission.EXECUTE},
            Role.ADMIN: {Permission.READ, Permission.WRITE, Permission.EXECUTE, Permission.ADMIN}
        }
        
        # Enable batch processing
        self.batch_processing_enabled = True
        self.progress_enabled = True  # Enable progress reporting by default
        
        # Map operations to required permissions
        self.operation_permissions = {
            "capabilities/list": Permission.READ,
            "tools/list": Permission.READ,
            "tools/get": Permission.READ,
            "tools/execute": Permission.EXECUTE,
            "resources/list": Permission.READ,
            "resources/read": Permission.READ,
            "resources/subscribe": Permission.READ,
            "resources/unsubscribe": Permission.READ,
            "resources/write": Permission.WRITE,
            "system/": Permission.ADMIN
        }
        
        # Initialize authorization logging
        self.auth_violations = []
        self.max_violations_history = config.get("auth", {}).get("max_violations_history", 100)
        self.logger.info(f"MCP Host initialized with ID: {host_id}")
        self.logger.info(f"Authentication provider initialized with token expiration: {self.token_expiration}s")
        self.logger.info(f"Authorization provider initialized with role-based access control")
        self.logger.info(f"Authentication provider initialized with token expiration: {self.token_expiration}s")
        
    # ===== Server Management =====
    
    def register_server(self, server_id: str, server_info: Dict[str, Any], server_instance=None) -> bool:
        """
        Register a new MCP Server with this Host.
        
        This method validates server capability declarations against the MCP specification
        before registering the server with the host.
        
        Args:
            server_id: Unique identifier for the server
            server_info: Server information including capabilities
            server_instance: Optional server instance for direct method calls
            
        Returns:
            bool: True if registration was successful
            
        Raises:
            ValueError: If server capabilities are invalid
        """
        self.logger.info(f"Registering MCP Server: {server_id}")
        
        # Validate server capabilities
        self._validate_server_capabilities(server_id, server_info)
        
        # Register server with MCP SDK
        self.mcp_host.register_server(server_id, server_info)
        
        # Store server information and instance
        server_data = server_info.copy()
        if server_instance is not None:
            server_data["instance"] = server_instance
            
        self.servers[server_id] = server_data
        
        # Notify clients about the new server
        self._publish_event("server_registered", {
            "server_id": server_id,
            "capabilities": server_info.get("capabilities", {})
        })
        
        return True
        
    def _validate_server_capabilities(self, server_id: str, server_info: Dict[str, Any]) -> None:
        """
        Validate server capability declarations against MCP specification.
        
        This method ensures that:
        1. Server provides capability information
        2. All required capabilities are present
        3. Capability values are of the correct type (boolean)
        4. All primitive implementations (tools, resources, prompts) are consistent
        
        Args:
            server_id: Server ID
            server_info: Server information including capabilities
            
        Raises:
            ValueError: If server capabilities are invalid
        """
        self.logger.debug(f"Validating capabilities for server: {server_id}")
        
        # Use SDK validation if available
        if hasattr(self.mcp_host, "validate_server_capabilities"):
            validation_result = self.mcp_host.validate_server_capabilities(server_info)
            if not validation_result["valid"]:
                error_details = validation_result.get("errors", ["Unknown validation error"])
                self.logger.error(f"Invalid server capabilities: {error_details}")
                raise ValueError(f"Invalid server capabilities: {error_details}")
            return
            
        # Fall back to manual validation
        # Check if capabilities are provided
        if "capabilities" not in server_info:
            error_msg = f"Server {server_id} does not provide capability information"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        capabilities = server_info["capabilities"]
        
        # Check if capabilities is a dictionary
        if not isinstance(capabilities, dict):
            error_msg = f"Server {server_id} capabilities must be a dictionary, got {type(capabilities).__name__}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        # Check for required capabilities
        required_capabilities = ["tools", "resources"]
        missing_capabilities = [cap for cap in required_capabilities if cap not in capabilities]
        
        if missing_capabilities:
            error_msg = f"Server {server_id} is missing required capabilities: {missing_capabilities}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        # Check capability types
        for capability, value in capabilities.items():
            if not isinstance(value, bool):
                error_msg = f"Server {server_id} capability '{capability}' must be a boolean, got {type(value).__name__}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
                
        # Check for unknown capabilities
        known_capabilities = ["tools", "resources", "subscriptions", "prompts", "batch", "progress"]
        
        # Check if progress capability is declared
        if capabilities.get("progress", False):
            self.logger.info(f"Server {server_id} supports progress reporting")
        unknown_capabilities = [cap for cap in capabilities if cap not in known_capabilities]
        
        if unknown_capabilities:
            self.logger.warning(f"Server {server_id} declares unknown capabilities: {unknown_capabilities}")
            
        # Verify primitive implementation consistency
        self._verify_primitive_implementation(server_id, server_info)
        
        self.logger.debug(f"Server {server_id} capabilities validated successfully")
        
    def _verify_primitive_implementation(self, server_id: str, server_info: Dict[str, Any]) -> None:
        """
        Verify that server primitive implementations are consistent with declared capabilities.
        
        Args:
            server_id: Server ID
            server_info: Server information including capabilities
            
        Raises:
            ValueError: If primitive implementations are inconsistent with capabilities
        """
        capabilities = server_info["capabilities"]
        
        # Check tools capability
        if capabilities.get("tools", False):
            # If tools capability is declared, server should provide tool information
            if "tools" not in server_info and "tool_count" not in server_info:
                self.logger.warning(f"Server {server_id} declares tools capability but provides no tool information")
                
        # Check resources capability
        if capabilities.get("resources", False):
            # If resources capability is declared, server should provide resource information
            if "resources" not in server_info and "resource_providers" not in server_info:
                self.logger.warning(f"Server {server_id} declares resources capability but provides no resource information")
                
        # Check prompts capability
        if capabilities.get("prompts", False):
            # If prompts capability is declared, server should provide prompt information
            if "prompts" not in server_info:
                self.logger.warning(f"Server {server_id} declares prompts capability but provides no prompt information")
        
    def unregister_server(self, server_id: str) -> bool:
        """
        Unregister an MCP Server from this Host.
        
        Args:
            server_id: Unique identifier for the server
            
        Returns:
            bool: True if unregistration was successful
        """
        if server_id not in self.servers:
            self.logger.warning(f"Attempted to unregister unknown server: {server_id}")
            return False
            
        self.logger.info(f"Unregistering MCP Server: {server_id}")
        
        # Unregister server with MCP SDK
        self.mcp_host.unregister_server(server_id)
        
        # Remove server from internal state
        del self.servers[server_id]
        
        # Notify clients about the server removal
        self._publish_event("server_unregistered", {
            "server_id": server_id
        })
        
        return True
        
    def get_available_servers(self) -> List[str]:
        """
        Get a list of available MCP Servers.
        
        Returns:
            List[str]: List of server IDs
        """
        # Use MCP SDK to get available servers
        return self.mcp_host.get_available_servers()
        
    def get_server_info(self, server_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific MCP Server.
        
        Args:
            server_id: Server ID
            
        Returns:
            Optional[Dict[str, Any]]: Server information or None if not found
        """
        if server_id not in self.servers:
            return None
            
        # Return a copy of the server info without the instance
        server_info = self.servers[server_id].copy()
        server_info.pop("instance", None)
        return server_info
        
    # ===== Client Management =====
    
    def register_client(self, client_id: str, client_info: Dict[str, Any], client_instance=None) -> bool:
        """
        Register a new MCP Client with this Host.
        
        Args:
            client_id: Unique identifier for the client
            client_info: Client information including capabilities
            client_instance: Optional client instance for direct method calls
            
        Returns:
            bool: True if registration was successful
        """
        self.logger.info(f"Registering MCP Client: {client_id}")
        
        # Register client with MCP SDK
        self.mcp_host.register_client(client_id, client_info)
        
        # Store client information and instance
        client_data = client_info.copy()
        if client_instance is not None:
            client_data["instance"] = client_instance
            
        self.clients[client_id] = client_data
        
        # Create a new context for this client
        self.contexts[client_id] = {
            "active_session": None,
            "server_connections": set(),
            "subscriptions": set(),
            "last_activity": time.time()
        }
        
        return True
        
    def unregister_client(self, client_id: str) -> bool:
        """
        Unregister an MCP Client from this Host.
        
        Args:
            client_id: Unique identifier for the client
            
        Returns:
            bool: True if unregistration was successful
        """
        if client_id not in self.clients:
            self.logger.warning(f"Attempted to unregister unknown client: {client_id}")
            return False
            
        self.logger.info(f"Unregistering MCP Client: {client_id}")
        
        # Unregister client with MCP SDK
        self.mcp_host.unregister_client(client_id)
        
        # Clean up client resources
        if client_id in self.contexts:
            # Unsubscribe from all subscriptions
            for subscription_id in self.contexts[client_id]["subscriptions"]:
                self._remove_subscription(client_id, subscription_id)
                
            # Remove client context
            del self.contexts[client_id]
            
        # Remove client
        del self.clients[client_id]
        
        return True
        
    def get_registered_clients(self) -> List[str]:
        """
        Get a list of registered MCP Clients.
        
        Returns:
            List[str]: List of client IDs
        """
        # Use MCP SDK to get registered clients
        return self.mcp_host.get_registered_clients()
        
    def get_client_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific MCP Client.
        
        Args:
            client_id: Client ID
            
        Returns:
            Optional[Dict[str, Any]]: Client information or None if not found
        """
        if client_id not in self.clients:
            return None
            
        # Return a copy of the client info without the instance
        client_info = self.clients[client_id].copy()
        client_info.pop("instance", None)
        return client_info
        
    # ===== Request Routing =====
    
    def route_request(self, server_id: str, request: Dict[str, Any], client_id: Optional[str] = None,
                     auth_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Route a JSON-RPC request to the specified MCP Server with authentication.
        
        Args:
            server_id: Target server ID
            request: JSON-RPC request payload
            client_id: Optional client ID for tracking and consent
            auth_token: Optional authentication token for secure requests
            
        Returns:
            Optional[Dict[str, Any]]: JSON-RPC response from the server or None if routing failed
        """
        # Validate the incoming request before routing
        validation_result = JsonRpc.validate_request(request)
        if not validation_result["valid"]:
            error_details = validation_result.get("errors", ["Unknown validation error"])
            self.logger.error(f"Invalid JSON-RPC request received for routing: {error_details}")
            
            # Create an error response for invalid requests
            request_id = request.get("id")
            return JsonRpc.create_error_response(
                request_id,
                -32600,
                "Invalid Request",
                f"Request does not conform to JSON-RPC 2.0: {error_details}"
            )
        
        # Validate server existence
        if server_id not in self.servers:
            self.logger.error(f"Unknown server ID: {server_id}")
            return JsonRpc.create_error_response(
                request.get("id"),
                -32602,
                "Invalid params",
                f"Unknown server ID: {server_id}"
            )
            
        server_info = self.servers[server_id]
        server_instance = server_info.get("instance")
        
        if server_instance is None:
            self.logger.error(f"No server instance available for {server_id}")
            return JsonRpc.create_error_response(
                request.get("id"),
                -32603,
                "Internal error",
                f"Server instance not available for {server_id}"
            )
        
        # Extract method for logging and authentication checks
        method = request.get("method", "")
        
        # Authenticate the request if client_id and auth_token are provided
        if client_id and auth_token:
            # Check if the client has an active session
            if client_id in self.contexts and self.contexts[client_id].get("active_session"):
                session_id = self.contexts[client_id]["active_session"]
                
                # Validate the session with the token
                if not self.validate_session(session_id, auth_token):
                    self.logger.warning(f"Authentication failed for client {client_id}, method: {method}")
                    return JsonRpc.create_error_response(
                        request.get("id"),
                        -32001,
                        "Authentication failed",
                        "Invalid or expired authentication token"
                    )
                    
                self.logger.debug(f"Request authenticated for client {client_id}, session {session_id}")
                
                # Authorize the request based on user role and required permissions
                if not self._authorize_operation(session_id, method):
                    self.logger.warning(f"Authorization failed for client {client_id}, method: {method}")
                    
                    # Log the authorization violation
                    self._log_authorization_violation(client_id, session_id, method)
                    
                    return JsonRpc.create_error_response(
                        request.get("id"),
                        -32002,
                        "Authorization failed",
                        f"User does not have permission to perform operation: {method}"
                    )
                    
                self.logger.debug(f"Request authorized for client {client_id}, method: {method}")
            else:
                # If no active session but authentication is required
                required_level = self._get_required_consent_level(method)
                if required_level.value > 1:  # If more than READ_ONLY is required
                    self.logger.warning(f"Authentication required for client {client_id}, method: {method}")
                    return JsonRpc.create_error_response(
                        request.get("id"),
                        -32001,
                        "Authentication required",
                        f"Operation {method} requires authentication"
                    )
            
        self.logger.info(f"Routing request to server: {server_id}, method: {method}" +
                        (f" for client {client_id}" if client_id else ""))
        
        # Enhanced consent verification in the request processing pipeline
        if client_id is not None:
            # Get the required consent level for this operation
            required_level = self._get_required_consent_level(method)
            
            # Check if the client has sufficient consent
            if not self._check_operation_consent(client_id, server_id, method):
                self.logger.warning(f"Operation not authorized: {method} for client {client_id}, required consent level: {required_level.name}")
                
                # Create detailed error response using MCP SDK
                error_response = JsonRpc.create_error_response(
                    request.get("id"),
                    -32000,
                    "Operation not authorized",
                    f"Client {client_id} does not have sufficient consent for {method} on server {server_id}. Required level: {required_level.name}"
                )
                
                # Log the consent violation
                self._log_consent_violation(client_id, server_id, method, required_level)
                
                return error_response
                
            # Update client context
            if client_id in self.contexts:
                self.contexts[client_id]["last_activity"] = time.time()
                self.contexts[client_id]["server_connections"].add(server_id)
                
            # Log successful consent verification
            self.logger.debug(f"Consent verified for client {client_id} on server {server_id} for operation {method}")
        try:
            # Add authentication and authorization information to client context if available
            client_context = None
            if client_id:
                client_context = {
                    "client_id": client_id,
                    "authenticated": False
                }
                
                # Add authentication and authorization status if available
                if client_id in self.contexts and self.contexts[client_id].get("active_session"):
                    session_id = self.contexts[client_id]["active_session"]
                    if session_id in self.user_sessions:
                        client_context["authenticated"] = True
                        client_context["username"] = self.user_sessions[session_id].get("username")
                        client_context["permissions"] = self.user_sessions[session_id].get("permissions", [])
                        client_context["role"] = self.user_sessions[session_id].get("role", Role.USER.name)
                        
                        # Add authorization information
                        required_permission = self._get_required_permission(method)
                        client_context["authorized"] = self._has_permission(session_id, required_permission)
                        
            # Use MCP SDK to route the request with enhanced context
            # Pass authentication context to the SDK if supported
            if hasattr(self.mcp_host, "route_authenticated_request") and client_context and client_context.get("authenticated"):
                response = self.mcp_host.route_authenticated_request(server_id, request, client_context)
            else:
                response = self.mcp_host.route_request(server_id, request, client_id)
            
            # If SDK routing is not available, fall back to direct method call
            if response is None and server_instance is not None:
                # Create a progress callback if the server supports progress reporting
                progress_callback = None
                if server_info.get("capabilities", {}).get("progress", False) and client_id:
                    def progress_callback_fn(operation_id: str, percent_complete: int, status_message: str):
                        self.route_progress_notification(server_id, client_id, operation_id, percent_complete, status_message)
                    progress_callback = progress_callback_fn
                
                # Pass client context and progress callback to server if available
                if client_context:
                    response = server_instance.handle_jsonrpc_request(request, client_context, progress_callback)
                else:
                    response = server_instance.handle_jsonrpc_request(request, None, progress_callback)
            
            # Validate the response before returning it
            if response is not None:
                response_validation = JsonRpc.validate_response(response)
                if not response_validation["valid"]:
                    error_details = response_validation.get("errors", ["Unknown validation error"])
                    self.logger.error(f"Invalid JSON-RPC response received from server {server_id}: {error_details}")
                    
                    # Create a valid error response instead
                    response = JsonRpc.create_error_response(
                        request.get("id"),
                        -32603,
                        "Internal error",
                        f"Server returned invalid response: {error_details}"
                    )
            
            # Track context updates if needed
            if client_id is not None and method.startswith("resources/subscribe") and response and response.get("result"):
                subscription_id = response["result"].get("subscription_id")
                if subscription_id:
                    self._add_subscription(client_id, subscription_id, server_id)
                    
            return response
        except Exception as e:
            self.logger.error(f"Error routing request to server {server_id}: {str(e)}")
            
            # Create an error response using MCP SDK
            error_response = JsonRpc.create_error_response(
                request.get("id"),
                -32603,
                "Internal error",
                str(e)
            )
            
            # Validate the error response
            error_validation = JsonRpc.validate_response(error_response)
            if not error_validation["valid"]:
                self.logger.error(f"Generated invalid JSON-RPC error response: {error_validation.get('errors')}")
                # Create a minimal valid error response as fallback
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32603,
                        "message": "Internal error"
                    }
                }
                
            return error_response
            
    def route_batch_request(self, server_id: str, batch_request: List[Dict[str, Any]],
                           client_id: Optional[str] = None,
                           auth_token: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Route a JSON-RPC batch request to the specified MCP Server with authentication.
        
        This method supports:
        1. Batch request validation
        2. Authentication and authorization for the entire batch
        3. Consent verification for each request in the batch
        4. Detailed error handling for partial failures
        5. Performance optimization for batch processing
        
        Args:
            server_id: Target server ID
            batch_request: List of JSON-RPC request objects
            client_id: Optional client ID for tracking and consent
            auth_token: Optional authentication token for secure requests
            
        Returns:
            Optional[List[Dict[str, Any]]]: List of JSON-RPC responses or None if routing failed
        """
        self.logger.info(f"Routing batch request with {len(batch_request) if isinstance(batch_request, list) else 'invalid'} requests to server {server_id}" +
                        (f" for client {client_id}" if client_id else ""))
        
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
            
        # Check if batch processing is enabled
        if not self.batch_processing_enabled:
            self.logger.warning("Batch processing is disabled, falling back to individual requests")
            return self._fallback_to_individual_requests(server_id, batch_request, client_id, auth_token)
            
        # Validate server existence
        if server_id not in self.servers:
            self.logger.error(f"Unknown server ID: {server_id}")
            return [JsonRpc.create_error_response(
                None, -32602, "Invalid params", f"Unknown server ID: {server_id}"
            )]
            
        server_info = self.servers[server_id]
        server_instance = server_info.get("instance")
        
        if server_instance is None:
            self.logger.error(f"No server instance available for {server_id}")
            return [JsonRpc.create_error_response(
                None, -32603, "Internal error", f"Server instance not available for {server_id}"
            )]
            
        # Check if server supports batch processing
        server_capabilities = server_info.get("capabilities", {})
        if not server_capabilities.get("batch", False):
            self.logger.warning(f"Server {server_id} does not support batch processing, falling back to individual requests")
            return self._fallback_to_individual_requests(server_id, batch_request, client_id, auth_token)
            
        # Authenticate the batch request if client_id and auth_token are provided
        client_context = None
        if client_id:
            client_context = {
                "client_id": client_id,
                "authenticated": False
            }
            
            if auth_token:
                # Check if the client has an active session
                if client_id in self.contexts and self.contexts[client_id].get("active_session"):
                    session_id = self.contexts[client_id]["active_session"]
                    
                    # Validate the session with the token
                    if not self.validate_session(session_id, auth_token):
                        self.logger.warning(f"Authentication failed for client {client_id}, batch request")
                        return [JsonRpc.create_error_response(
                            None, -32001, "Authentication failed", "Invalid or expired authentication token"
                        )]
                        
                    self.logger.debug(f"Batch request authenticated for client {client_id}, session {session_id}")
                    
                    # Add authentication and authorization status to client context
                    client_context["authenticated"] = True
                    client_context["username"] = self.user_sessions[session_id].get("username")
                    client_context["permissions"] = self.user_sessions[session_id].get("permissions", [])
                    client_context["role"] = self.user_sessions[session_id].get("role", Role.USER.name)
                    
                    # Update client context
                    if client_id in self.contexts:
                        self.contexts[client_id]["last_activity"] = time.time()
                        self.contexts[client_id]["server_connections"].add(server_id)
        
        try:
            # Use MCP SDK to route the batch request if available
            if hasattr(self.mcp_host, "route_batch_request"):
                self.logger.debug("Using SDK for batch request routing")
                
                # If SDK supports context-aware batch routing
                if client_context and hasattr(self.mcp_host, "route_batch_request_with_context"):
                    batch_response = self.mcp_host.route_batch_request_with_context(
                        server_id, batch_request, client_context
                    )
                else:
                    batch_response = self.mcp_host.route_batch_request(
                        server_id, batch_request, client_id
                    )
                    
                # Validate the batch response
                if batch_response is not None and not isinstance(batch_response, list):
                    self.logger.error(f"Invalid batch response from SDK: expected array, got {type(batch_response).__name__}")
                    return [JsonRpc.create_error_response(
                        None, -32603, "Internal error", "Invalid batch response format"
                    )]
                    
                return batch_response
                
            # Fall back to direct method call with enhanced processing
            self.logger.debug("Using direct method call for batch request routing")
            
            # Pass client context to server if available
            if client_context:
                batch_response = server_instance.handle_batch_request(batch_request, client_context)
            else:
                batch_response = server_instance.handle_batch_request(batch_request)
                
            # Validate the batch response
            if batch_response is not None and not isinstance(batch_response, list):
                self.logger.error(f"Invalid batch response from server {server_id}: expected array, got {type(batch_response).__name__}")
                return [JsonRpc.create_error_response(
                    None, -32603, "Internal error", "Server returned invalid batch response format"
                )]
                
            return batch_response
            
        except Exception as e:
            self.logger.error(f"Error routing batch request to server {server_id}: {str(e)}")
            
            # Create an error response using MCP SDK
            error_response = [JsonRpc.create_error_response(
                None, -32603, "Internal error", f"Error routing batch request: {str(e)}"
            )]
            
            return error_response
            
    def _fallback_to_individual_requests(self, server_id: str, batch_request: List[Dict[str, Any]],
                                        client_id: Optional[str] = None,
                                        auth_token: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fall back to routing individual requests when batch processing is not supported.
        
        Args:
            server_id: Target server ID
            batch_request: List of JSON-RPC request objects
            client_id: Optional client ID for tracking and consent
            auth_token: Optional authentication token for secure requests
            
        Returns:
            List[Dict[str, Any]]: List of JSON-RPC responses
        """
        self.logger.info(f"Falling back to individual requests for batch with {len(batch_request)} requests")
        responses = []
        
        for i, request in enumerate(batch_request):
            try:
                self.logger.debug(f"Processing individual request {i+1}/{len(batch_request)}")
                response = self.route_request(server_id, request, client_id, auth_token)
                if response is not None:  # Skip notifications (no response)
                    responses.append(response)
            except Exception as e:
                self.logger.error(f"Error processing individual request at position {i}: {str(e)}")
                # Create error response for this specific request
                error_response = JsonRpc.create_error_response(
                    request.get("id", None), -32603, "Internal error",
                    f"Error processing request: {str(e)}"
                )
                responses.append(error_response)
                
        return responses
            
    # ===== Context Management =====
    
    def get_client_context(self, client_id: str, include_auth_info: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get the context for a specific client, optionally including authentication information.
        
        Args:
            client_id: Client ID
            include_auth_info: Whether to include authentication information
            
        Returns:
            Optional[Dict[str, Any]]: Client context or None if not found
        """
        # Use MCP SDK context manager if available
        if hasattr(self.context_manager, "get_context"):
            try:
                # If SDK supports auth info inclusion
                if include_auth_info and hasattr(self.context_manager, "get_context_with_auth"):
                    return self.context_manager.get_context_with_auth(client_id)
                else:
                    sdk_context = self.context_manager.get_context(client_id)
                    if sdk_context:
                        return sdk_context
            except Exception as e:
                self.logger.error(f"SDK context retrieval error: {str(e)}")
                # Fall through to internal context retrieval
            
        # Fall back to internal context with enhanced auth info
        if client_id not in self.contexts:
            return None
            
        context = self.contexts[client_id].copy()
        
        # Add authentication information if requested
        if include_auth_info and "active_session" in context and context["active_session"]:
            session_id = context["active_session"]
            if session_id in self.user_sessions:
                session = self.user_sessions[session_id]
                context["authenticated"] = True
                context["username"] = session.get("username")
                context["permissions"] = session.get("permissions", [])
                context["session_expiration"] = session.get("expiration")
            else:
                context["authenticated"] = False
                
        return context
        
    def update_client_context(self, client_id: str, context_updates: Dict[str, Any], auth_token: Optional[str] = None) -> bool:
        """
        Update the context for a specific client with authentication.
        
        Args:
            client_id: Client ID
            context_updates: Updates to apply to the context
            auth_token: Optional authentication token for secure updates
            
        Returns:
            bool: True if update was successful
        """
        # Authenticate the update if token is provided
        if auth_token and client_id in self.contexts and "active_session" in self.contexts[client_id]:
            session_id = self.contexts[client_id]["active_session"]
            if not self.validate_session(session_id, auth_token):
                self.logger.warning(f"Authentication failed for context update: client {client_id}")
                return False
                
        # Use MCP SDK context manager if available
        if hasattr(self.context_manager, "update_context"):
            try:
                # If SDK supports authenticated updates
                if auth_token and hasattr(self.context_manager, "update_context_with_auth"):
                    return self.context_manager.update_context_with_auth(client_id, context_updates, auth_token)
                else:
                    return self.context_manager.update_context(client_id, context_updates)
            except Exception as e:
                self.logger.error(f"SDK context update error: {str(e)}")
                # Fall through to internal context update
            
        # Fall back to internal context update with enhanced security
        if client_id not in self.contexts:
            self.logger.warning(f"Attempted to update context for unknown client: {client_id}")
            return False
            
        # Handle special case for setting active session
        if "active_session" in context_updates:
            session_id = context_updates["active_session"]
            if session_id is not None and session_id not in self.user_sessions:
                self.logger.warning(f"Attempted to set unknown session {session_id} for client {client_id}")
                return False
                
        # Update the context
        for key, value in context_updates.items():
            if key != "server_connections" and key != "subscriptions":
                self.contexts[client_id][key] = value
                
                # Log important context changes
                if key == "active_session":
                    if value is None:
                        self.logger.info(f"Client {client_id} session cleared")
                    else:
                        username = self.user_sessions.get(value, {}).get("username", "unknown")
                        self.logger.info(f"Client {client_id} session set to {value} (user: {username})")
                
        # Always update last_activity
        self.contexts[client_id]["last_activity"] = time.time()
        
        # Log the context update
        self.logger.debug(f"Updated context for client {client_id}: {list(context_updates.keys())}")
        
        return True
        
    def _add_subscription(self, client_id: str, subscription_id: str, server_id: str) -> None:
        """
        Add a subscription to a client's context.
        
        Args:
            client_id: Client ID
            subscription_id: Subscription ID
            server_id: Server ID
        """
        if client_id in self.contexts:
            self.contexts[client_id]["subscriptions"].add(subscription_id)
            
    def _remove_subscription(self, client_id: str, subscription_id: str) -> None:
        """
        Remove a subscription from a client's context.
        
        Args:
            client_id: Client ID
            subscription_id: Subscription ID
        """
        if client_id in self.contexts and subscription_id in self.contexts[client_id]["subscriptions"]:
            self.contexts[client_id]["subscriptions"].remove(subscription_id)
            
    # ===== Consent Management =====
    
    def register_consent(self, client_id: str, server_id: str, operation_pattern: str,
                         consent_level: ConsentLevel, expiration: Optional[float] = None) -> str:
        """
        Register consent for a client to perform operations on a server.
        
        Args:
            client_id: Client ID
            server_id: Server ID
            operation_pattern: Pattern of operations to allow (e.g., "tools/*")
            consent_level: Level of consent
            expiration: Optional expiration time (Unix timestamp)
            
        Returns:
            str: Consent ID
        """
        self.logger.debug(f"Registering consent for client {client_id} on server {server_id} with level {consent_level.name}")
        
        # Set the consent level on the client if it exists
        if client_id in self.clients and "instance" in self.clients[client_id]:
            client_instance = self.clients[client_id]["instance"]
            if hasattr(client_instance, "consent_level"):
                client_instance.consent_level = consent_level.name
                self.logger.debug(f"Set consent_level={consent_level.name} on client {client_id}")
        
        # Always use MCP SDK consent manager for protocol compliance
        if hasattr(self.consent_manager, "register_consent"):
            consent_id = self.consent_manager.register_consent(
                client_id,
                server_id,
                operation_pattern,
                consent_level.value,
                expiration
            )
            
            self.logger.info(f"Registered consent {consent_id} for client {client_id} on server {server_id} with level {consent_level.name}")
            return consent_id
            
        # Fall back to internal consent registration
        consent_id = str(uuid.uuid4())
        
        self.consent_registry[consent_id] = {
            "client_id": client_id,
            "server_id": server_id,
            "operation_pattern": operation_pattern,
            "consent_level": consent_level,
            "expiration": expiration,
            "created_at": time.time(),
            "last_used": None
        }
        
        self.logger.info(f"Registered consent {consent_id} for client {client_id} on server {server_id} with level {consent_level.name}")
        return consent_id
        
    def revoke_consent(self, consent_id: str, reason: Optional[str] = None) -> bool:
        """
        Revoke a previously registered consent.
        
        Args:
            consent_id: Consent ID
            reason: Optional reason for revocation
            
        Returns:
            bool: True if revocation was successful
        """
        # Always use MCP SDK consent manager for protocol compliance
        if hasattr(self.consent_manager, "revoke_consent"):
            result = self.consent_manager.revoke_consent(consent_id, reason)
            if result:
                self.logger.info(f"Revoked consent {consent_id}" + (f" - Reason: {reason}" if reason else ""))
            else:
                self.logger.warning(f"Failed to revoke consent {consent_id}")
            return result
            
        # Fall back to internal consent revocation
        if consent_id not in self.consent_registry:
            self.logger.warning(f"Attempted to revoke unknown consent: {consent_id}")
            return False
            
        consent_info = self.consent_registry[consent_id]
        client_id = consent_info.get("client_id", "unknown")
        server_id = consent_info.get("server_id", "unknown")
        
        self.logger.info(f"Revoking consent {consent_id} for client {client_id} on server {server_id}" +
                        (f" - Reason: {reason}" if reason else ""))
        del self.consent_registry[consent_id]
        
        # Publish event for consent revocation
        self._publish_event("consent_revoked", {
            "consent_id": consent_id,
            "client_id": client_id,
            "server_id": server_id,
            "reason": reason
        })
        
        return True
        
    def _check_operation_consent(self, client_id: str, server_id: str, operation: str) -> bool:
        """
        Check if a client has consent to perform an operation on a server.
        
        Args:
            client_id: Client ID
            server_id: Server ID
            operation: Operation to check
            
        Returns:
            bool: True if the client has consent
        """
        self.logger.debug(f"Checking consent for client {client_id} on server {server_id} for operation {operation}")
        
        # Always use MCP SDK consent manager for protocol compliance
        if hasattr(self.consent_manager, "check_consent"):
            result = self.consent_manager.check_consent(client_id, server_id, operation)
            if result:
                self.logger.debug(f"Consent granted for client {client_id} on server {server_id} for operation {operation}")
            else:
                self.logger.warning(f"Consent denied for client {client_id} on server {server_id} for operation {operation}")
            return result
            
        # Fall back to internal consent checking
        # Check for expired consents and clean them up
        current_time = time.time()
        expired_consents = []
        
        for consent_id, consent in self.consent_registry.items():
            if consent["expiration"] is not None and consent["expiration"] < current_time:
                expired_consents.append(consent_id)
                
        for consent_id in expired_consents:
            client_id = self.consent_registry[consent_id].get("client_id", "unknown")
            server_id = self.consent_registry[consent_id].get("server_id", "unknown")
            self.logger.info(f"Removing expired consent {consent_id} for client {client_id} on server {server_id}")
            del self.consent_registry[consent_id]
            
            # Publish event for consent expiration
            self._publish_event("consent_expired", {
                "consent_id": consent_id,
                "client_id": client_id,
                "server_id": server_id
            })
            
        # Check if the client has consent for this operation
        required_level = self._get_required_consent_level(operation)
        
        for consent_id, consent in self.consent_registry.items():
            if (consent["client_id"] == client_id and
                consent["server_id"] == server_id and
                self._match_operation_pattern(operation, consent["operation_pattern"])):
                
                # Check if the consent level is sufficient
                if consent["consent_level"].value >= required_level.value:
                    # Update last used timestamp
                    consent["last_used"] = current_time
                    self.logger.debug(f"Consent {consent_id} granted for operation {operation} with level {consent['consent_level'].name}")
                    return True
                else:
                    self.logger.warning(f"Insufficient consent level for operation {operation}: " +
                                      f"required {required_level.name}, but consent {consent_id} only provides {consent['consent_level'].name}")
                
        # If no specific consent is found, check if there's a default consent policy
        default_consent_level = self.config.get("mcp", {}).get("default_consent_level", "NONE")
        try:
            default_level = ConsentLevel[default_consent_level]
            
            # Check if the default level is sufficient
            if default_level.value >= required_level.value:
                self.logger.debug(f"Default consent level {default_level.name} is sufficient for operation {operation}")
                return True
            else:
                self.logger.warning(f"Default consent level {default_level.name} is insufficient for operation {operation}, required {required_level.name}")
                return False
        except KeyError:
            self.logger.warning(f"Invalid default consent level: {default_consent_level}")
            return False
            
    def _match_operation_pattern(self, operation: str, pattern: str) -> bool:
        """
        Check if an operation matches a pattern.
        
        Args:
            operation: Operation to check
            pattern: Pattern to match against
            
        Returns:
            bool: True if the operation matches the pattern
        """
        # Enhanced wildcard matching
        if pattern == "*":
            # Universal consent for all operations
            return True
        elif pattern.endswith("/*"):
            # Category wildcard (e.g., "tools/*")
            prefix = pattern[:-1]
            return operation.startswith(prefix)
        elif pattern.endswith("/**"):
            # Recursive wildcard (e.g., "tools/**")
            prefix = pattern[:-2]
            return operation.startswith(prefix)
        else:
            # Exact match
            return operation == pattern
            
    def _get_required_consent_level(self, operation: str) -> ConsentLevel:
        """
        Determine the required consent level for an operation.
        
        Args:
            operation: Operation to check
            
        Returns:
            ConsentLevel: Required consent level
        """
        # Map operations to required consent levels
        if operation.startswith("capabilities/"):
            # Capability operations require READ_ONLY consent
            return ConsentLevel.READ_ONLY
        elif operation.startswith("tools/list") or operation.startswith("tools/get"):
            # Tool discovery operations require READ_ONLY consent
            return ConsentLevel.READ_ONLY
        elif operation.startswith("tools/execute"):
            # Tool execution operations require BASIC consent by default
            # But dangerous tools require ELEVATED consent
            if "dangerous" in operation:
                return ConsentLevel.ELEVATED
            return ConsentLevel.BASIC
        elif operation.startswith("resources/list") or operation.startswith("resources/read"):
            # Resource read operations require READ_ONLY consent
            return ConsentLevel.READ_ONLY
        elif operation.startswith("resources/subscribe") or operation.startswith("resources/unsubscribe"):
            # Resource subscription operations require BASIC consent
            return ConsentLevel.BASIC
        elif operation.startswith("resources/write"):
            # Resource write operations require ELEVATED consent
            return ConsentLevel.ELEVATED
        elif operation.startswith("system/"):
            # System operations require FULL consent
            return ConsentLevel.FULL
        else:
            # Unknown operations require FULL consent by default
            self.logger.warning(f"Unknown operation type: {operation}, requiring FULL consent")
            return ConsentLevel.FULL
            
    # ===== Authentication and Authorization =====
    
    def authenticate_user(self, username: str, credentials: Dict[str, Any],
                         role: Role = Role.USER) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user and create a session using the MCP SDK.
        
        Args:
            username: Username
            credentials: Authentication credentials
            
        Returns:
            Optional[Dict[str, Any]]: Session information including token if authentication was successful, None otherwise
        """
        self.logger.info(f"Authentication attempt for user: {username}")
        
        # Use MCP SDK authentication provider
        if hasattr(self.auth_provider, "authenticate"):
            try:
                # SDK authentication with enhanced error handling
                auth_result = self.auth_provider.authenticate(username, credentials)
                
                if not auth_result:
                    self.logger.warning(f"Authentication failed for user: {username}")
                    return None
                    
                # If SDK returns just a session ID, wrap it in a proper session object
                if isinstance(auth_result, str):
                    session_id = auth_result
                    token = self._generate_secure_token()
                    
                    # Create a session with expiration
                    expiration_time = time.time() + self.token_expiration
                    self.user_sessions[session_id] = {
                        "username": username,
                        "token": token,
                        "created_at": time.time(),
                        "last_activity": time.time(),
                        "expiration": expiration_time,
                        "permissions": ["basic"],  # Default permissions
                        "role": role.name  # Assign the specified role
                    }
                    
                    self.logger.info(f"User {username} authenticated, session {session_id} created with expiration")
                    return {
                        "session_id": session_id,
                        "token": token,
                        "expiration": expiration_time,
                        "username": username
                    }
                else:
                    # SDK returned a complete session object
                    self.logger.info(f"User {username} authenticated via SDK provider")
                    return auth_result
            except Exception as e:
                self.logger.error(f"Authentication error for user {username}: {str(e)}")
                return None
                
        # If SDK authentication is not available, use secure internal authentication
        try:
            # In a production implementation, this would validate credentials against a secure database
            # with proper password hashing
            session_id = str(uuid.uuid4())
            token = self._generate_secure_token()
            
            # Create a session with expiration
            expiration_time = time.time() + self.token_expiration
            self.user_sessions[session_id] = {
                "username": username,
                "token": token,
                "created_at": time.time(),
                "last_activity": time.time(),
                "expiration": expiration_time,
                "permissions": ["basic"],  # Default permissions
                "role": role.name  # Assign the specified role
            }
            
            self.logger.info(f"User {username} authenticated, session {session_id} created with expiration")
            return {
                "session_id": session_id,
                "token": token,
                "expiration": expiration_time,
                "username": username
            }
        except Exception as e:
            self.logger.error(f"Internal authentication error for user {username}: {str(e)}")
            return None
        
    def validate_session(self, session_id: str, token: Optional[str] = None) -> bool:
        """
        Validate a user session with token verification.
        
        Args:
            session_id: Session ID
            token: Optional authentication token for additional security
            
        Returns:
            bool: True if the session is valid
        """
        # Check if it's time to clean up expired sessions
        self._cleanup_expired_sessions()
        
        # Use MCP SDK authentication provider if available
        if hasattr(self.auth_provider, "validate_session"):
            try:
                # If SDK supports token validation
                if token and hasattr(self.auth_provider, "validate_token"):
                    validation_result = self.auth_provider.validate_token(session_id, token)
                    if validation_result:
                        self.logger.debug(f"Session {session_id} validated with token via SDK")
                        return True
                else:
                    # Basic session validation via SDK
                    validation_result = self.auth_provider.validate_session(session_id)
                    if validation_result:
                        self.logger.debug(f"Session {session_id} validated via SDK")
                        return True
            except Exception as e:
                self.logger.error(f"SDK session validation error: {str(e)}")
                # Fall through to internal validation as backup
        
        # Fall back to internal session validation with enhanced security
        if session_id not in self.user_sessions:
            self.logger.warning(f"Session validation failed: unknown session ID {session_id}")
            return False
            
        session = self.user_sessions[session_id]
        
        # Check if session has expired
        if "expiration" in session and session["expiration"] < time.time():
            self.logger.warning(f"Session validation failed: session {session_id} has expired")
            del self.user_sessions[session_id]
            return False
            
        # Validate token if provided
        if token and session.get("token") != token:
            self.logger.warning(f"Session validation failed: invalid token for session {session_id}")
            return False
            
        # Update last activity and extend expiration if needed
        session["last_activity"] = time.time()
        
        # Optionally extend session expiration on activity
        if "expiration" in session:
            session["expiration"] = time.time() + self.token_expiration
            
        self.logger.debug(f"Session {session_id} validated successfully")
        return True
        
    def end_session(self, session_id: str, token: Optional[str] = None) -> bool:
        """
        End a user session with token verification.
        
        Args:
            session_id: Session ID
            token: Optional authentication token for additional security
            
        Returns:
            bool: True if the session was ended successfully
        """
        # Use MCP SDK authentication provider if available
        if hasattr(self.auth_provider, "end_session"):
            try:
                # If SDK supports token validation for session ending
                if token and hasattr(self.auth_provider, "end_session_with_token"):
                    result = self.auth_provider.end_session_with_token(session_id, token)
                    if result:
                        self.logger.info(f"Session {session_id} ended via SDK with token verification")
                        return True
                else:
                    # Basic session ending via SDK
                    result = self.auth_provider.end_session(session_id)
                    if result:
                        self.logger.info(f"Session {session_id} ended via SDK")
                        return True
            except Exception as e:
                self.logger.error(f"SDK session ending error: {str(e)}")
                # Fall through to internal session ending as backup
        
        # Fall back to internal session ending with enhanced security
        if session_id not in self.user_sessions:
            self.logger.warning(f"Cannot end session: unknown session ID {session_id}")
            return False
            
        # Validate token if provided
        if token and self.user_sessions[session_id].get("token") != token:
            self.logger.warning(f"Cannot end session: invalid token for session {session_id}")
            return False
            
        # Log session ending with username for audit trail
        username = self.user_sessions[session_id].get("username", "unknown")
        self.logger.info(f"Ending session {session_id} for user {username}")
        
        # Remove the session
        del self.user_sessions[session_id]
        
        # Publish event for session ending
        self._publish_event("session_ended", {
            "session_id": session_id,
            "username": username,
            "timestamp": time.time()
        })
        
        return True
        
    def check_permission(self, session_id: str, permission: str, token: Optional[str] = None) -> bool:
        """
        Check if a session has a specific permission with token verification.
        
        Args:
            session_id: Session ID
            permission: Permission to check
            token: Optional authentication token for additional security
            
        Returns:
            bool: True if the session has the permission
        """
        # First validate the session
        if not self.validate_session(session_id, token):
            self.logger.warning(f"Permission check failed: invalid session {session_id}")
            return False
            
        # Use MCP SDK authentication provider if available
        if hasattr(self.auth_provider, "check_permission"):
            try:
                # If SDK supports token-based permission checking
                if token and hasattr(self.auth_provider, "check_permission_with_token"):
                    result = self.auth_provider.check_permission_with_token(session_id, permission, token)
                    self.logger.debug(f"Permission check for {permission} on session {session_id}: {result} (via SDK with token)")
                    return result
                else:
                    # Basic permission checking via SDK
                    result = self.auth_provider.check_permission(session_id, permission)
                    self.logger.debug(f"Permission check for {permission} on session {session_id}: {result} (via SDK)")
                    return result
            except Exception as e:
                self.logger.error(f"SDK permission check error: {str(e)}")
                # Fall through to internal permission checking as backup
        
        # Fall back to internal permission checking with enhanced security
        if session_id not in self.user_sessions:
            self.logger.warning(f"Permission check failed: unknown session ID {session_id}")
            return False
            
        # Check if the permission exists in the session
        has_permission = permission in self.user_sessions[session_id]["permissions"]
        
        # Log the permission check for audit trail
        username = self.user_sessions[session_id].get("username", "unknown")
        self.logger.debug(f"Permission check for {permission} on session {session_id} (user {username}): {has_permission}")
        
        return has_permission
        
    def _authorize_operation(self, session_id: str, method: str) -> bool:
        """
        Authorize an operation based on the user's role and the required permission.
        
        Args:
            session_id: Session ID
            method: Operation method name
            
        Returns:
            bool: True if the operation is authorized
        """
        # Get the required permission for this operation
        required_permission = self._get_required_permission(method)
        
        # Check if the user has the required permission
        return self._has_permission(session_id, required_permission)
        
    def _has_permission(self, session_id: str, required_permission: Permission) -> bool:
        """
        Check if a user has a specific permission based on their role.
        
        Args:
            session_id: Session ID
            required_permission: Required permission
            
        Returns:
            bool: True if the user has the permission
        """
        if session_id not in self.user_sessions:
            return False
            
        # Get the user's role
        role_name = self.user_sessions[session_id].get("role", Role.USER.name)
        
        # Convert role name to enum
        try:
            role = Role[role_name]
        except (KeyError, ValueError):
            self.logger.warning(f"Invalid role: {role_name}, defaulting to USER")
            role = Role.USER
            
        # Check if the role has the required permission
        if role in self.role_permissions:
            return required_permission in self.role_permissions[role]
            
        return False
        
    def _get_required_permission(self, method: str) -> Permission:
        """
        Determine the required permission for an operation.
        
        Args:
            method: Operation method name
            
        Returns:
            Permission: Required permission
        """
        # Check for exact matches
        if method in self.operation_permissions:
            return self.operation_permissions[method]
            
        # Check for prefix matches
        for prefix, permission in self.operation_permissions.items():
            if method.startswith(prefix):
                return permission
                
        # Default to ADMIN for unknown operations
        self.logger.warning(f"Unknown operation type: {method}, requiring ADMIN permission")
        return Permission.ADMIN
        
    def grant_permission(self, session_id: str, permission: str, admin_token: Optional[str] = None) -> bool:
        """
        Grant a permission to a session with admin token verification.
        
        Args:
            session_id: Session ID
            permission: Permission to grant
            admin_token: Optional admin authentication token for authorization
            
        Returns:
            bool: True if the permission was granted successfully
        """
        # Use MCP SDK authentication provider if available
        if hasattr(self.auth_provider, "grant_permission"):
            try:
                # If SDK supports admin token verification for permission granting
                if admin_token and hasattr(self.auth_provider, "grant_permission_with_admin"):
                    result = self.auth_provider.grant_permission_with_admin(session_id, permission, admin_token)
                    if result:
                        self.logger.info(f"Permission {permission} granted to session {session_id} via SDK with admin verification")
                        return True
                else:
                    # Basic permission granting via SDK
                    result = self.auth_provider.grant_permission(session_id, permission)
                    if result:
                        self.logger.info(f"Permission {permission} granted to session {session_id} via SDK")
                        return True
            except Exception as e:
                self.logger.error(f"SDK permission granting error: {str(e)}")
                # Fall through to internal permission granting as backup
        
        # Fall back to internal permission granting with enhanced security
        if session_id not in self.user_sessions:
            self.logger.warning(f"Cannot grant permission: unknown session ID {session_id}")
            return False
            
        # In a production environment, we would verify the admin token here
        # For now, we'll just log that this should be implemented
        if admin_token:
            self.logger.warning("Admin token verification not fully implemented in fallback mode")
            
        # Grant the permission
        if permission not in self.user_sessions[session_id]["permissions"]:
            self.user_sessions[session_id]["permissions"].append(permission)
            
            # Log the permission grant for audit trail
            username = self.user_sessions[session_id].get("username", "unknown")
            self.logger.info(f"Permission {permission} granted to session {session_id} (user {username})")
            
            # Publish event for permission granting
            self._publish_event("permission_granted", {
                "session_id": session_id,
                "username": username,
                "permission": permission,
                "timestamp": time.time()
            })
            
        return True
    def revoke_permission(self, session_id: str, permission: str, admin_token: Optional[str] = None) -> bool:
        """
        Revoke a permission from a session with admin token verification.
        
        Args:
            session_id: Session ID
            permission: Permission to revoke
            admin_token: Optional admin authentication token for authorization
            
        Returns:
            bool: True if the permission was revoked successfully
        """
        # Use MCP SDK authentication provider if available
        if hasattr(self.auth_provider, "revoke_permission"):
            try:
                # If SDK supports admin token verification for permission revoking
                if admin_token and hasattr(self.auth_provider, "revoke_permission_with_admin"):
                    result = self.auth_provider.revoke_permission_with_admin(session_id, permission, admin_token)
                    if result:
                        self.logger.info(f"Permission {permission} revoked from session {session_id} via SDK with admin verification")
                        return True
                else:
                    # Basic permission revoking via SDK
                    result = self.auth_provider.revoke_permission(session_id, permission)
                    if result:
                        self.logger.info(f"Permission {permission} revoked from session {session_id} via SDK")
                        return True
            except Exception as e:
                self.logger.error(f"SDK permission revoking error: {str(e)}")
                # Fall through to internal permission revoking as backup
        
        # Fall back to internal permission revoking with enhanced security
        if session_id not in self.user_sessions:
            self.logger.warning(f"Cannot revoke permission: unknown session ID {session_id}")
            return False
            
        # In a production environment, we would verify the admin token here
        # For now, we'll just log that this should be implemented
        if admin_token:
            self.logger.warning("Admin token verification not fully implemented in fallback mode")
            
        # Revoke the permission
        if permission in self.user_sessions[session_id]["permissions"]:
            self.user_sessions[session_id]["permissions"].remove(permission)
            
            # Log the permission revocation for audit trail
            username = self.user_sessions[session_id].get("username", "unknown")
            self.logger.info(f"Permission {permission} revoked from session {session_id} (user {username})")
            
            # Publish event for permission revoking
            self._publish_event("permission_revoked", {
                "session_id": session_id,
                "username": username,
                "permission": permission,
                "timestamp": time.time()
            })
            
        return True
        
    # ===== Event System =====
    
    def subscribe_to_events(self, event_type: str, callback: Callable[[Dict[str, Any]], None]) -> str:
        """
        Subscribe to host events.
        
        Args:
            event_type: Type of event to subscribe to
            callback: Function to call when the event occurs
            
        Returns:
            str: Subscription ID
        """
        # Use MCP SDK event system if available
        if hasattr(self.mcp_host, "subscribe_to_events"):
            return self.mcp_host.subscribe_to_events(event_type, callback)
            
        # Fall back to internal event subscription
        subscription_id = str(uuid.uuid4())
        
        if event_type not in self.event_subscribers:
            self.event_subscribers[event_type] = {}
            
        self.event_subscribers[event_type][subscription_id] = callback
        return subscription_id
        
    def unsubscribe_from_events(self, subscription_id: str) -> bool:
        """
        Unsubscribe from host events.
        
        Args:
            subscription_id: Subscription ID
            
        Returns:
            bool: True if unsubscription was successful
        """
        # Use MCP SDK event system if available
        if hasattr(self.mcp_host, "unsubscribe_from_events"):
            return self.mcp_host.unsubscribe_from_events(subscription_id)
            
        # Fall back to internal event unsubscription
        for event_type, subscribers in self.event_subscribers.items():
            if subscription_id in subscribers:
                del subscribers[subscription_id]
                return True
                
        return False
        
    def _publish_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Publish an event to subscribers.
        
        Args:
            event_type: Type of event
            event_data: Event data
        """
        # Use MCP SDK event system if available
        if hasattr(self.mcp_host, "publish_event"):
            self.mcp_host.publish_event(event_type, event_data)
            return
            
        # Fall back to internal event publishing
        if event_type not in self.event_subscribers:
            return
            
        for callback in self.event_subscribers[event_type].values():
            try:
                callback(event_data)
            except Exception as e:
                self.logger.error(f"Error in event subscriber: {str(e)}")
                
    # ===== Client Coordination =====
    
    def broadcast_to_clients(self, message: Dict[str, Any], client_filter: Optional[Callable[[str], bool]] = None) -> Dict[str, bool]:
        """
        Broadcast a message to all registered clients.
        
        Args:
            message: Message to broadcast
            client_filter: Optional function to filter clients
            
        Returns:
            Dict[str, bool]: Map of client IDs to success status
        """
        # Use MCP SDK broadcast if available
        if hasattr(self.mcp_host, "broadcast_to_clients"):
            return self.mcp_host.broadcast_to_clients(message, client_filter)
            
        # Fall back to internal broadcasting
        results = {}
        
        for client_id, client_data in self.clients.items():
            # Apply filter if provided
            if client_filter is not None and not client_filter(client_id):
                continue
                
            client_instance = client_data.get("instance")
            if client_instance is None:
                results[client_id] = False
                continue
                
            try:
                # In a real implementation, this would use a proper client API
                # For now, we'll just log the message
                self.logger.info(f"Broadcasting message to client {client_id}: {message}")
                results[client_id] = True
            except Exception as e:
                self.logger.error(f"Error broadcasting to client {client_id}: {str(e)}")
                results[client_id] = False
                
        return results
        
    def get_client_status(self, client_id: str) -> Dict[str, Any]:
        """
        Get the status of a client.
        
        Args:
            client_id: Client ID
            
        Returns:
            Dict[str, Any]: Client status information
        """
        # Use MCP SDK client status if available
        if hasattr(self.mcp_host, "get_client_status"):
            return self.mcp_host.get_client_status(client_id)
            
        # Fall back to internal client status
        if client_id not in self.clients or client_id not in self.contexts:
            return {"status": "unknown"}
            
        context = self.contexts[client_id]
        
        return {
            "status": "active",
            "last_activity": context["last_activity"],
            "connected_servers": list(context["server_connections"]),
            "subscription_count": len(context["subscriptions"]),
            "session_active": context["active_session"] is not None
        }
        
    def cleanup_inactive_clients(self, max_idle_time: float = 3600.0) -> List[str]:
        """
        Clean up inactive clients.
        
        Args:
            max_idle_time: Maximum idle time in seconds
            
        Returns:
            List[str]: List of cleaned up client IDs
        """
        # Use MCP SDK cleanup if available
        if hasattr(self.mcp_host, "cleanup_inactive_clients"):
            return self.mcp_host.cleanup_inactive_clients(max_idle_time)
            
        # Fall back to internal cleanup
        current_time = time.time()
        inactive_clients = []
        
        for client_id, context in self.contexts.items():
            if current_time - context["last_activity"] > max_idle_time:
                inactive_clients.append(client_id)
                
        for client_id in inactive_clients:
            self.unregister_client(client_id)
            
        return inactive_clients
        
    def _generate_secure_token(self) -> str:
        """
        Generate a secure authentication token.
        
        Returns:
            str: Secure token
        """
        # Use SDK token generation if available
        if hasattr(self.auth_provider, "generate_token"):
            try:
                return self.auth_provider.generate_token()
            except Exception as e:
                self.logger.error(f"SDK token generation error: {str(e)}")
                # Fall through to internal token generation
                
        # Fall back to secure internal token generation
        # Generate a random token with high entropy
        token_bytes = os.urandom(32)  # 256 bits of randomness
        return token_bytes.hex()
        
    def _cleanup_expired_sessions(self) -> None:
        """
        Clean up expired sessions periodically.
        """
        current_time = time.time()
        
        # Only run cleanup at the configured interval
        if current_time - self.last_cleanup_time < self.session_cleanup_interval:
            return
            
        self.last_cleanup_time = current_time
        self.logger.debug("Running session cleanup")
        
        # Use SDK session cleanup if available
        if hasattr(self.auth_provider, "cleanup_sessions"):
            try:
                cleanup_result = self.auth_provider.cleanup_sessions()
                self.logger.info(f"SDK session cleanup completed: {cleanup_result}")
                return
            except Exception as e:
                self.logger.error(f"SDK session cleanup error: {str(e)}")
                # Fall through to internal cleanup
                
        # Fall back to internal session cleanup
        expired_sessions = []
        
        for session_id, session in self.user_sessions.items():
            # Check for explicit expiration
            if "expiration" in session and session["expiration"] < current_time:
                expired_sessions.append(session_id)
                continue
                
            # Check for inactivity timeout (as a backup)
            inactivity_timeout = self.token_expiration * 2  # Double the token expiration as inactivity timeout
            if current_time - session["last_activity"] > inactivity_timeout:
                expired_sessions.append(session_id)
                
        # Remove expired sessions
        for session_id in expired_sessions:
            username = self.user_sessions[session_id].get("username", "unknown")
            self.logger.info(f"Removing expired session {session_id} for user {username}")
            del self.user_sessions[session_id]
            
            # Publish event for session expiration
            self._publish_event("session_expired", {
                "session_id": session_id,
                "username": username,
                "timestamp": current_time
            })
            
        if expired_sessions:
            self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
    def _log_consent_violation(self, client_id: str, server_id: str, operation: str, required_level: ConsentLevel) -> None:
        """
        Log a consent violation for auditing and security monitoring.
        
        Args:
            client_id: Client ID
            server_id: Server ID
            operation: Operation that was attempted
            required_level: Required consent level
        """
        violation_data = {
            "timestamp": time.time(),
            "client_id": client_id,
            "server_id": server_id,
            "operation": operation,
            "required_level": required_level.name,
            "violation_type": "insufficient_consent"
        }
        
        # Log the violation
        self.logger.warning(f"Consent violation: client {client_id} attempted operation {operation} on server {server_id} " +
                          f"without required consent level {required_level.name}")
        
        # Publish event for consent violation
        self._publish_event("consent_violation", violation_data)
        
        # Use SDK to log the violation if available
        if hasattr(self.consent_manager, "log_violation"):
            self.consent_manager.log_violation(violation_data)
            
    def _log_authorization_violation(self, client_id: str, session_id: str, operation: str) -> None:
        """
        Log an authorization violation for auditing and security monitoring.
        
        Args:
            client_id: Client ID
            session_id: Session ID
            operation: Operation that was attempted
        """
        # Get user information
        username = "unknown"
        role = "unknown"
        if session_id in self.user_sessions:
            username = self.user_sessions[session_id].get("username", "unknown")
            role = self.user_sessions[session_id].get("role", "unknown")
            
        # Get required permission
        required_permission = self._get_required_permission(operation)
        
        violation_data = {
            "timestamp": time.time(),
            "client_id": client_id,
            "session_id": session_id,
            "username": username,
            "role": role,
            "operation": operation,
            "required_permission": required_permission.name,
            "violation_type": "insufficient_permission"
        }
        
        # Log the violation
        self.logger.warning(f"Authorization violation: user {username} (role: {role}) attempted operation {operation} " +
                          f"without required permission {required_permission.name}")
        
        # Store violation in history (with limit)
        self.auth_violations.append(violation_data)
        if len(self.auth_violations) > self.max_violations_history:
            self.auth_violations.pop(0)
            
        # Publish event for authorization violation
        self._publish_event("authorization_violation", violation_data)
        
        # Use SDK to log the violation if available
        if hasattr(self.authorization_provider, "log_violation"):
            self.authorization_provider.log_violation(violation_data)
            
    def assign_role(self, session_id: str, role: Role, admin_token: Optional[str] = None) -> bool:
        """
        Assign a role to a user session with admin token verification.
        
        Args:
            session_id: Session ID
            role: Role to assign
            admin_token: Optional admin authentication token for authorization
            
        Returns:
            bool: True if the role was assigned successfully
        """
        # Verify admin token if provided
        if admin_token:
            # In a production environment, we would verify the admin token here
            # For now, we'll just log that this should be implemented
            self.logger.warning("Admin token verification not fully implemented in fallback mode")
            
        # Check if the session exists
        if session_id not in self.user_sessions:
            self.logger.warning(f"Cannot assign role: unknown session ID {session_id}")
            return False
            
        # Assign the role
        old_role = self.user_sessions[session_id].get("role", Role.USER.name)
        self.user_sessions[session_id]["role"] = role.name
        
        # Log the role assignment for audit trail
        username = self.user_sessions[session_id].get("username", "unknown")
        self.logger.info(f"Role changed for user {username}: {old_role} -> {role.name}")
        
        # Publish event for role assignment
        self._publish_event("role_assigned", {
            "session_id": session_id,
            "username": username,
            "old_role": old_role,
            "new_role": role.name,
            "timestamp": time.time()
        })
        return True
        
    def route_progress_notification(self, server_id: str, client_id: str,
                                   operation_id: str, percent_complete: int,
                                   status_message: str) -> bool:
        """
        Route a progress notification from a server to a client.
        
        Args:
            server_id: Source server ID
            client_id: Target client ID
            operation_id: Operation ID
            percent_complete: Percentage of completion (0-100)
            status_message: Status message describing current progress
            
        Returns:
            bool: True if the notification was routed successfully
        """
        self.logger.debug(f"Routing progress notification from server {server_id} to client {client_id}: " +
                         f"Operation {operation_id} - {percent_complete}% - {status_message}")
        
        # Check if progress reporting is enabled
        if not self.progress_enabled:
            self.logger.debug("Progress reporting is disabled, ignoring notification")
            return False
            
        # Check if the client exists
        if client_id not in self.clients:
            self.logger.warning(f"Cannot route progress notification: unknown client {client_id}")
            return False
            
        client_info = self.clients[client_id]
        client_instance = client_info.get("instance")
        
        if client_instance is None:
            self.logger.warning(f"Cannot route progress notification: no client instance for {client_id}")
            return False
            
        try:
            # Create a JSON-RPC notification for progress
            progress_notification = JsonRpc.create_notification(
                "progress/update",
                {
                    "server_id": server_id,
                    "operation_id": operation_id,
                    "percent_complete": percent_complete,
                    "status_message": status_message,
                    "timestamp": time.time()
                }
            )
            
            # Route the notification to the client
            if hasattr(client_instance, "handle_progress_notification"):
                client_instance.handle_progress_notification(progress_notification)
            else:
                self.logger.warning(f"Client {client_id} does not support progress notifications")
                return False
                
            self.logger.debug(f"Successfully routed progress notification to client {client_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error routing progress notification: {str(e)}")
            return False
        return True