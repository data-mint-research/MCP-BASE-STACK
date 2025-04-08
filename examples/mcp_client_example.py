"""
Example script demonstrating how to use the MCP Client component with SDK methods.

This script shows how to:
1. Connect to the MCP Host
2. Discover available servers
3. Execute tools on servers
4. Access resources from servers
5. Subscribe to resource updates

This implementation uses the SDK's JsonRpc class and transport mechanisms
for all JSON-RPC operations, ensuring full protocol compliance.
"""

import sys
import os
import json
import time
import logging
from typing import Dict, Any, Callable

# Add the services directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "services", "mcp-server", "src"))

# Import MCP components
from client.client import MCPClient
from host.host import MCPHost, ConsentLevel
from modelcontextprotocol.json_rpc import JsonRpc

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mcp_client_example")

def resource_update_callback(update_data: Dict[str, Any]) -> None:
    """Callback function for resource updates."""
    logger.info(f"Resource update received: {json.dumps(update_data, indent=2)}")

def main():
    """Main function demonstrating the MCP client usage with SDK methods."""
    try:
        # Step 1: Create a client configuration
        client_config = {
            "mcp": {
                "client_id": "example-client",
                "client_name": "Example Client"
            },
            "connection": {
                "retry_count": 3,
                "retry_delay": 1
            }
        }
        
        # Step 2: Create the client using SDK factory methods
        logger.info("Creating MCP Client...")
        client = MCPClient(
            logger=logger,
            config=client_config
        )
        logger.info(f"Created MCP Client with ID: {client.client_id}")
        
        # Step 3: Create a host
        logger.info("Creating MCP Host...")
        host_config = {
            "mcp": {
                "host_id": "example-host",
                "default_consent_level": "BASIC",
                "auto_consent": True
            }
        }
        host = MCPHost(
            logger=logger,
            config=host_config
        )
        logger.info(f"Created MCP Host with ID: {host_config['mcp']['host_id']}")
        
        # Step 4: Connect the client to the host
        logger.info("Connecting client to host...")
        success = client.connect_to_host(host)
        if not success:
            logger.error("Failed to connect to host")
            return
        logger.info("Successfully connected to host")
        
        # Step 5: Get a list of available servers
        logger.info("Getting available servers...")
        servers = host.get_available_servers()
        logger.info(f"Available servers: {servers}")
        
        if not servers:
            logger.warning("No servers available. Creating a test server...")
            
            # Create a test server
            from server.server import MCPServer
            from server.tools import execute_shell_command
            from server.resources import FileResourceProvider
            
            server_config = {
                "mcp": {
                    "server_id": "example-server",
                    "server_description": "Example Server",
                    "server_version": "1.0.0"
                },
                "resources": {
                    "file_base_path": os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                }
            }
            
            server = MCPServer(
                server_id="example-server",
                logger=logger,
                config=server_config
            )
            
            # Register tools
            server.register_tool(execute_shell_command)
            
            # Register resource providers
            file_provider = FileResourceProvider(base_path=server_config["resources"]["file_base_path"])
            server.register_resource_provider("file", file_provider)
            
            # Register server with host
            server_info = {
                "capabilities": server.capabilities,
                "server_id": "example-server",
                "description": "Example Server",
                "version": "1.0.0"
            }
            host.register_server("example-server", server_info, server)
            
            # Update servers list
            servers = host.get_available_servers()
            logger.info(f"Created test server. Available servers: {servers}")
        
        # Step 6: Register consent for the client
        for server_id in servers:
            logger.info(f"Registering consent for client {client.client_id} on server {server_id}")
            consent_id = host.register_consent(
                client_id=client.client_id,
                server_id=server_id,
                operation_pattern="*",
                consent_level=ConsentLevel.FULL
            )
            logger.info(f"Consent registered with ID: {consent_id}")
            
            # Step 7: Negotiate capabilities with the server
            logger.info(f"Negotiating capabilities with server: {server_id}")
            capabilities = client.negotiate_capabilities(server_id)
            logger.info(f"Negotiated capabilities: {json.dumps(capabilities, indent=2)}")
            
            # Step 8: List available tools
            logger.info(f"Listing tools for server: {server_id}")
            tools = client.list_server_tools(server_id)
            logger.info(f"Available tools: {tools}")
            
            # Step 9: Execute a tool if available
            if "execute_shell_command" in tools:
                logger.info("Getting details for shell command tool...")
                tool_details = client.get_tool_details(server_id, "execute_shell_command")
                logger.info(f"Tool details: {json.dumps(tool_details, indent=2)}")
                
                logger.info("Creating proxy for shell command tool...")
                shell_command = client.create_tool_proxy(server_id, "execute_shell_command")
                
                logger.info("Executing shell command tool...")
                result = shell_command(command="echo 'Hello from MCP Client Example using SDK methods!'")
                logger.info(f"Tool execution result: {json.dumps(result, indent=2)}")
            
            # Step 10: List and access resources
            logger.info(f"Listing resources for server: {server_id}")
            resources = client.list_resources(server_id, "file", "/")
            logger.info(f"Available resources: {resources}")
            
            if resources:
                # Access the first resource
                resource_uri = resources[0]
                logger.info(f"Accessing resource: {resource_uri}")
                resource_data = client.access_resource(server_id, resource_uri)
                logger.info(f"Resource data: {json.dumps(resource_data, indent=2)}")
                
                # Subscribe to resource updates
                logger.info(f"Subscribing to resource: {resource_uri}")
                subscription_id = client.subscribe_to_resource(
                    server_id,
                    resource_uri,
                    resource_update_callback
                )
                logger.info(f"Subscribed with ID: {subscription_id}")
                
                # Wait for a moment to simulate resource updates
                logger.info("Waiting for resource updates (simulated)...")
                time.sleep(2)
                
                # Simulate a resource update
                client.handle_resource_update(
                    subscription_id,
                    {"content": "Updated content", "timestamp": time.time()}
                )
                
                # Unsubscribe from the resource
                logger.info(f"Unsubscribing from resource...")
                client.unsubscribe_from_resource(subscription_id)
                logger.info("Unsubscribed successfully")
        
        # Step 11: Disconnect from the host
        logger.info("Disconnecting from host...")
        client.disconnect_from_host()
        logger.info("Disconnected successfully")
        
    except Exception as e:
        logger.error(f"Error in MCP client example: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()