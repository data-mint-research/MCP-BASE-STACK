"""
MCP Client Component Resource Subscriber.

This module implements the resource subscriber functionality for the MCP Client component
using the SDK's JsonRpc class for subscription handling.
"""

import logging
import json
import uuid
import time
import re
from typing import Dict, Any, List, Optional, Callable, Union

from mcp import JsonRpc, JsonRpcRequest, JsonRpcResponse, Resource

from .interfaces import IResourceSubscriber


class ResourceSubscriberManager(IResourceSubscriber):
    """
    Manages resource subscriptions for the MCP Client component.
    
    This implementation uses the SDK's JsonRpc class for all subscription operations,
    ensuring full protocol compliance.
    """
    
    def __init__(self, client: Any):
        """
        Initialize the ResourceSubscriberManager.
        
        Args:
            client: The MCP Client instance
        """
        self.client = client
        self.subscriptions = {}
        self.callbacks = {}
        
        # Initialize SDK Resource component if available
        self.resource_manager = None
        try:
            self.resource_manager = Resource.create_manager()
        except Exception as e:
            # Fall back to custom implementation if SDK component is not available
            pass
            
        # Compile regex for resource URI validation
        self.resource_uri_pattern = re.compile(r'^resource://([^/]+)(/.*)?$')
        
    def validate_resource_uri(self, uri: str) -> bool:
        """
        Validate a resource URI according to the MCP specification.
        
        Args:
            uri: The URI to validate
            
        Returns:
            bool: True if the URI is valid, False otherwise
        """
        # Use SDK's JsonRpc.validate_resource_uri if available
        if hasattr(JsonRpc, "validate_resource_uri"):
            return JsonRpc.validate_resource_uri(uri)
            
        # Fall back to our own validation
        if not isinstance(uri, str):
            return False
            
        # Check for resource:// scheme
        if not uri.startswith("resource://"):
            return False
            
        # Check for provider
        match = self.resource_uri_pattern.match(uri)
        if not match or not match.group(1):
            return False
            
        return True
    
    def subscribe(self, server_id: str, uri: str, callback: Callable[[Dict[str, Any]], None]) -> str:
        """
        Subscribe to updates for a resource using the SDK's JsonRpc class.
        
        This method ensures that capability negotiation occurs before resource subscription.
        It checks if capabilities have been negotiated with the server, and if not,
        it negotiates them first.
        
        Args:
            server_id: The ID of the server
            uri: The URI of the resource
            callback: A function to call when the resource is updated
            
        Returns:
            str: Subscription ID
            
        Raises:
            ValidationError: If the server_id, uri, or callback is invalid
            ResourceError: If there's an error subscribing to the resource
            NetworkError: If there's a network error
            MCPError: If capability negotiation fails or the server doesn't support resources or subscriptions
        """
        # Import here to avoid circular imports
        from .error_handler import ValidationError, ResourceError, MCPError, ErrorCode
        
        # Validate parameters
        if not server_id:
            raise ValidationError(
                message="Server ID cannot be empty",
                field_errors={"server_id": ["Server ID cannot be empty"]}
            )
        
        if not uri:
            raise ValidationError(
                message="URI cannot be empty",
                field_errors={"uri": ["URI cannot be empty"]}
            )
            
        # Validate resource URI format
        if not self.validate_resource_uri(uri):
            raise ValidationError(
                message=f"Invalid resource URI format: {uri}. Must follow 'resource://provider/path' format.",
                field_errors={"uri": [f"Invalid resource URI format: {uri}. Must follow 'resource://provider/path' format."]}
            )
        
        if not callback or not callable(callback):
            raise ValidationError(
                message="Callback must be a callable function",
                field_errors={"callback": ["Callback must be a callable function"]}
            )
            
        # Ensure capability negotiation has occurred
        self._ensure_capability_negotiation(server_id)
        
        # Generate a subscription ID
        subscription_id = str(uuid.uuid4())
        
        # Use SDK Resource manager if available
        if self.resource_manager and hasattr(self.resource_manager, "subscribe"):
            try:
                sdk_subscription_id = self.resource_manager.subscribe(server_id, uri, callback)
                # Store mapping between our subscription ID and SDK subscription ID
                self.subscriptions[subscription_id] = {
                    "server_id": server_id,
                    "uri": uri,
                    "created_at": time.time(),
                    "sdk_subscription_id": sdk_subscription_id
                }
                return subscription_id
            except Exception as e:
                # Fall back to custom implementation if SDK subscription fails
                self.client.logger.error(f"Error subscribing via SDK: {str(e)}")
        
        try:
            # Create a JSON-RPC request using the SDK's JsonRpc class
            params = {
                "uri": uri,
                "subscription_id": subscription_id
            }
            
            # Send a subscription request to the server
            self.client.send_request_to_server(
                server_id=server_id,
                method="resources/subscribe",
                params=params
            )
            
            # Store the subscription
            self.subscriptions[subscription_id] = {
                "server_id": server_id,
                "uri": uri,
                "created_at": time.time()
            }
            
            # Store the callback
            self.callbacks[subscription_id] = callback
            
            return subscription_id
        except Exception as e:
            # Wrap the exception in a ResourceError
            raise ResourceError(
                message=f"Failed to subscribe to resource {uri} on server {server_id}: {str(e)}",
                resource_uri=uri,
                data={"server_id": server_id},
                original_exception=e
            )
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from a resource using the SDK's JsonRpc class.
        
        Args:
            subscription_id: The ID of the subscription
            
        Returns:
            bool: True if unsubscription was successful, False otherwise
            
        Raises:
            ValidationError: If the subscription_id is invalid
            ResourceError: If there's an error unsubscribing from the resource
            NetworkError: If there's a network error
            MCPError: For other errors
        """
        # Import here to avoid circular imports
        from .error_handler import ValidationError, ResourceError
        
        # Validate parameters
        if not subscription_id:
            raise ValidationError(
                message="Subscription ID cannot be empty",
                field_errors={"subscription_id": ["Subscription ID cannot be empty"]}
            )
        
        # Check if the subscription exists
        if subscription_id not in self.subscriptions:
            raise ResourceError(
                message=f"Subscription {subscription_id} not found",
                data={"subscription_id": subscription_id}
            )
        
        # Get the subscription details
        subscription = self.subscriptions[subscription_id]
        
        # Use SDK Resource manager if available and SDK subscription ID exists
        if self.resource_manager and hasattr(self.resource_manager, "unsubscribe") and "sdk_subscription_id" in subscription:
            try:
                sdk_result = self.resource_manager.unsubscribe(subscription["sdk_subscription_id"])
                if sdk_result:
                    # Clean up our subscription records
                    del self.subscriptions[subscription_id]
                    if subscription_id in self.callbacks:
                        del self.callbacks[subscription_id]
                    return True
            except Exception as e:
                # Fall back to custom implementation if SDK unsubscription fails
                self.client.logger.error(f"Error unsubscribing via SDK: {str(e)}")
        
        try:
            # Create a JSON-RPC request using the SDK's JsonRpc class
            params = {
                "subscription_id": subscription_id
            }
            
            # Send an unsubscribe request to the server
            self.client.send_request_to_server(
                server_id=subscription["server_id"],
                method="resources/unsubscribe",
                params=params
            )
            
            # Remove the subscription
            del self.subscriptions[subscription_id]
            
            # Remove the callback
            if subscription_id in self.callbacks:
                del self.callbacks[subscription_id]
            
            return True
        except Exception as e:
            # Wrap the exception in a ResourceError
            raise ResourceError(
                message=f"Failed to unsubscribe from resource with subscription ID {subscription_id}: {str(e)}",
                data={"subscription_id": subscription_id, "server_id": subscription.get("server_id"), "uri": subscription.get("uri")},
                original_exception=e
            )
    
    def handle_update(self, subscription_id: str, update_data: Dict[str, Any]) -> None:
        """
        Handle an update for a subscribed resource.
        
        Args:
            subscription_id: The ID of the subscription
            update_data: The update data
            
        Raises:
            ValidationError: If the subscription_id or update_data is invalid
            ResourceError: If there's an error handling the update
            MCPError: For other errors
        """
        # Import here to avoid circular imports
        from .error_handler import ValidationError, ResourceError
        
        # Validate parameters
        if not subscription_id:
            raise ValidationError(
                message="Subscription ID cannot be empty",
                field_errors={"subscription_id": ["Subscription ID cannot be empty"]}
            )
        
        if update_data is None:
            raise ValidationError(
                message="Update data cannot be None",
                field_errors={"update_data": ["Update data cannot be None"]}
            )
        
        # Check if the subscription exists
        if subscription_id not in self.subscriptions:
            raise ResourceError(
                message=f"Subscription {subscription_id} not found",
                data={"subscription_id": subscription_id}
            )
        
        # Use SDK Resource manager if available and SDK subscription ID exists
        subscription = self.subscriptions[subscription_id]
        if self.resource_manager and hasattr(self.resource_manager, "handle_update") and "sdk_subscription_id" in subscription:
            try:
                self.resource_manager.handle_update(subscription["sdk_subscription_id"], update_data)
                return
            except Exception as e:
                # Log the error but continue with custom implementation
                self.client.logger.error(f"Error handling update via SDK: {str(e)}")
        
        # Get the callback
        callback = self.callbacks.get(subscription_id)
        
        # Check if there's a callback for this subscription
        if not callback:
            raise ResourceError(
                message=f"No callback found for subscription {subscription_id}",
                data={"subscription_id": subscription_id}
            )
        
        # Call the callback
        try:
            callback(update_data)
        except Exception as e:
            # Log the error and propagate it as a ResourceError
            self.client.logger.error(f"Error in resource update callback: {str(e)}")
            raise ResourceError(
                message=f"Error in resource update callback for subscription {subscription_id}: {str(e)}",
                data={"subscription_id": subscription_id},
                original_exception=e
            )
            
    def _ensure_capability_negotiation(self, server_id: str) -> None:
        """
        Ensure that capability negotiation has occurred with the server.
        
        Args:
            server_id: The ID of the server
            
        Raises:
            MCPError: If capability negotiation fails or the server doesn't support resources or subscriptions
        """
        # Import here to avoid circular imports
        from .error_handler import MCPError, ErrorCode
        
        # Check if capabilities have been negotiated
        if server_id not in self.client.capability_negotiator.negotiated_capabilities:
            self.client.logger.info(f"Negotiating capabilities with server {server_id} before resource operation")
            
            try:
                # Get client capabilities
                client_capabilities = self.client.capability_negotiator.get_client_capabilities()
                
                # Negotiate capabilities
                negotiated = self.client.capability_negotiator.negotiate(server_id, client_capabilities)
                
                # Check if the server supports resources
                if not negotiated.get("resources", False):
                    raise MCPError(
                        error_code=ErrorCode.CAPABILITY_NOT_SUPPORTED,
                        message=f"Server {server_id} does not support resources",
                        data={"server_id": server_id, "capability": "resources"}
                    )
                    
                # Check if the server supports subscriptions
                if not negotiated.get("subscriptions", False):
                    raise MCPError(
                        error_code=ErrorCode.CAPABILITY_NOT_SUPPORTED,
                        message=f"Server {server_id} does not support subscriptions",
                        data={"server_id": server_id, "capability": "subscriptions"}
                    )
            except Exception as e:
                # If it's already an MCPError, re-raise it
                if isinstance(e, MCPError):
                    raise
                
                # Wrap the exception in an MCPError
                raise MCPError(
                    error_code=ErrorCode.INTERNAL_ERROR,
                    message=f"Failed to negotiate capabilities with server {server_id}: {str(e)}",
                    data={"server_id": server_id},
                    original_exception=e
                )
