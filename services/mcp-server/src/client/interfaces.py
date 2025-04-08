"""
MCP Client Component Interfaces.

This module defines the interfaces for the MCP Client component.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable, Union

class IClient(ABC):
    """Interface for the MCP Client component."""
    
    @abstractmethod
    def connect_to_host(self, host: Any) -> bool:
        """
        Connect to an MCP Host.
        
        Args:
            host: The host instance to connect to
            
        Returns:
            bool: True if connection was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def disconnect_from_host(self) -> bool:
        """
        Disconnect from the current host.
        
        Returns:
            bool: True if disconnection was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def create_jsonrpc_request(self, method: str, params: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a JSON-RPC request.
        
        Args:
            method: The method to call
            params: The parameters for the method
            request_id: Optional request ID (will be generated if not provided)
            
        Returns:
            Dict[str, Any]: The JSON-RPC request
        """
        pass
    
    @abstractmethod
    def create_jsonrpc_notification(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a JSON-RPC notification.
        
        Args:
            method: The method to call
            params: The parameters for the method
            
        Returns:
            Dict[str, Any]: The JSON-RPC notification
        """
        pass
    
    @abstractmethod
    def send_request_to_server(self, server_id: str, method: str, params: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a request to a server.
        
        Args:
            server_id: The ID of the server to send the request to
            method: The method to call
            params: The parameters for the method
            request_id: Optional request ID (will be generated if not provided)
            
        Returns:
            Dict[str, Any]: The server's response
        """
        pass
    
    @abstractmethod
    def send_notification_to_server(self, server_id: str, method: str, params: Dict[str, Any]) -> None:
        """
        Send a notification to a server.
        
        Args:
            server_id: The ID of the server to send the notification to
            method: The method to call
            params: The parameters for the method
        """
        pass
    
    @abstractmethod
    def list_server_tools(self, server_id: str) -> List[str]:
        """
        List the tools available on a server.
        
        Args:
            server_id: The ID of the server
            
        Returns:
            List[str]: List of tool names
        """
        pass
    
    @abstractmethod
    def get_tool_details(self, server_id: str, tool_name: str) -> Dict[str, Any]:
        """
        Get details about a specific tool.
        
        Args:
            server_id: The ID of the server
            tool_name: The name of the tool
            
        Returns:
            Dict[str, Any]: Tool details
        """
        pass
    
    @abstractmethod
    def create_tool_proxy(self, server_id: str, tool_name: str) -> Callable:
        """
        Create a proxy function for a tool.
        
        Args:
            server_id: The ID of the server
            tool_name: The name of the tool
            
        Returns:
            Callable: A function that can be called to execute the tool
        """
        pass
    
    @abstractmethod
    def list_resources(self, server_id: str, provider: str, path: str) -> List[str]:
        """
        List resources available on a server.
        
        Args:
            server_id: The ID of the server
            provider: The resource provider
            path: The path to list resources from
            
        Returns:
            List[str]: List of resource URIs
        """
        pass
    
    @abstractmethod
    def access_resource(self, server_id: str, uri: str) -> Dict[str, Any]:
        """
        Access a resource on a server.
        
        Args:
            server_id: The ID of the server
            uri: The URI of the resource
            
        Returns:
            Dict[str, Any]: Resource data
        """
        pass
    
    @abstractmethod
    def subscribe_to_resource(self, server_id: str, uri: str, callback: Callable[[Dict[str, Any]], None]) -> str:
        """
        Subscribe to updates for a resource.
        
        Args:
            server_id: The ID of the server
            uri: The URI of the resource
            callback: A function to call when the resource is updated
            
        Returns:
            str: Subscription ID
        """
        pass
    
    @abstractmethod
    def unsubscribe_from_resource(self, subscription_id: str) -> bool:
        """
        Unsubscribe from a resource.
        
        Args:
            subscription_id: The ID of the subscription
            
        Returns:
            bool: True if unsubscription was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def handle_resource_update(self, subscription_id: str, update_data: Dict[str, Any]) -> None:
        """
        Handle an update for a subscribed resource.
        
        Args:
            subscription_id: The ID of the subscription
            update_data: The update data
        """
        pass
    
    @abstractmethod
    def negotiate_capabilities(self, server_id: str) -> Dict[str, Any]:
        """
        Negotiate capabilities with a server.
        
        Args:
            server_id: The ID of the server
            
        Returns:
            Dict[str, Any]: Negotiated capabilities
        """
        pass


class IToolProxy(ABC):
    """Interface for tool proxies."""
    
    @abstractmethod
    def create_proxy(self, server_id: str, tool_name: str, tool_details: Dict[str, Any]) -> Callable:
        """
        Create a proxy function for a tool.
        
        Args:
            server_id: The ID of the server
            tool_name: The name of the tool
            tool_details: Details about the tool
            
        Returns:
            Callable: A function that can be called to execute the tool
        """
        pass
    
    @abstractmethod
    def validate_arguments(self, tool_details: Dict[str, Any], arguments: Dict[str, Any]) -> bool:
        """
        Validate arguments against a tool's input schema.
        
        Args:
            tool_details: Details about the tool
            arguments: Arguments to validate
            
        Returns:
            bool: True if arguments are valid, False otherwise
        """
        pass


class IResourceSubscriber(ABC):
    """Interface for resource subscribers."""
    
    @abstractmethod
    def subscribe(self, server_id: str, uri: str, callback: Callable[[Dict[str, Any]], None]) -> str:
        """
        Subscribe to updates for a resource.
        
        Args:
            server_id: The ID of the server
            uri: The URI of the resource
            callback: A function to call when the resource is updated
            
        Returns:
            str: Subscription ID
        """
        pass
    
    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from a resource.
        
        Args:
            subscription_id: The ID of the subscription
            
        Returns:
            bool: True if unsubscription was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def handle_update(self, subscription_id: str, update_data: Dict[str, Any]) -> None:
        """
        Handle an update for a subscribed resource.
        
        Args:
            subscription_id: The ID of the subscription
            update_data: The update data
        """
        pass


class ICapabilityNegotiator(ABC):
    """Interface for capability negotiation."""
    
    @abstractmethod
    def negotiate(self, server_id: str, client_capabilities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Negotiate capabilities with a server.
        
        Args:
            server_id: The ID of the server
            client_capabilities: The client's capabilities
            
        Returns:
            Dict[str, Any]: Negotiated capabilities
        """
        pass
    
    @abstractmethod
    def get_client_capabilities(self) -> Dict[str, Any]:
        """
        Get the client's capabilities.
        
        Returns:
            Dict[str, Any]: The client's capabilities
        """
        pass
