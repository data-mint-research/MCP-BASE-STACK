"""
Example script demonstrating the use of the MCP Client component.

This script shows how to:
1. Initialize the MCP Client
2. Connect to a host
3. Discover server capabilities
4. List and execute tools
5. Access resources
6. Subscribe to resource updates
"""

import logging
import sys
import os
import time
from typing import Dict, Any

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.client import MCPClient
from host.host import MCPHost
from server.server import MCPServer
from server.tools import execute_shell_command
from server.resources import FileResourceProvider


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger("mcp_client_example")


def create_test_server(logger):
    """Create a test server with tools and resources."""
    # Create a config dictionary
    config = {
        'mcp': {
            'server_id': 'example-server',
            'host_enabled': True,
            'client_enabled': True,
            'server_enabled': True,
        },
        'resources': {
            'file_base_path': os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        }
    }
    
    # Create a server
    server = MCPServer(server_id='example-server', logger=logger, config=config)
    
    # Register tools
    server.register_tool(execute_shell_command)
    
    # Register resource providers
    file_provider = FileResourceProvider(base_path=config['resources']['file_base_path'])
    server.register_resource_provider("file", file_provider)
    
    return server, config


def resource_update_callback(update_data):
    """Callback function for resource updates."""
    print(f"Resource update received: {update_data}")


def main():
    """Main function demonstrating the MCP Client usage."""
    # Set up logging
    logger = setup_logging()
    logger.info("Starting MCP Client example")
    
    # Create a test server and config
    server, config = create_test_server(logger)
    
    # Create a host
    host = MCPHost(logger=logger, config=config)
    
    # Register the server with the host
    server_info = {
        "capabilities": server.capabilities,
        "server_id": "example-server"
    }
    host.register_server("example-server", server_info, server)
    
    # Create the client
    client = MCPClient(logger=logger, config=config)
    
    # Connect the client to the host
    client.connect_to_host(host)
    
    try:
        # Step 1: Negotiate capabilities with the server
        logger.info("Negotiating capabilities with the server")
        capabilities = client.negotiate_capabilities("example-server")
        logger.info(f"Negotiated capabilities: {capabilities}")
        
        # Step 2: List available tools
        logger.info("Listing available tools")
        tools = client.list_server_tools("example-server")
        logger.info(f"Available tools: {tools}")
        
        # Step 3: Get details for a specific tool
        logger.info("Getting details for the shell_command tool")
        tool_details = client.get_tool_details("example-server", "execute_shell_command")
        logger.info(f"Tool details: {tool_details}")
        
        # Step 4: Create a tool proxy
        logger.info("Creating a tool proxy for the shell_command tool")
        shell_command = client.create_tool_proxy("example-server", "execute_shell_command")
        
        # Step 5: Execute the tool
        logger.info("Executing the shell_command tool")
        result = shell_command(command="echo 'Hello from MCP Client!'")
        logger.info(f"Tool execution result: {result}")
        
        # Step 6: List available resources
        logger.info("Listing available resources")
        resources = client.list_resources("example-server", "file", "examples")
        logger.info(f"Available resources: {resources}")
        
        # Step 7: Access a resource
        logger.info("Accessing a resource")
        resource_data = client.access_resource("example-server", "resource://file/examples/client_example.py")
        logger.info(f"Resource data: {resource_data}")
        
        # Step 8: Subscribe to a resource
        logger.info("Subscribing to a resource")
        subscription_id = client.subscribe_to_resource(
            "example-server",
            "resource://file/examples/client_example.py",
            resource_update_callback
        )
        logger.info(f"Subscription ID: {subscription_id}")
        
        # Wait for a moment to simulate resource updates
        logger.info("Waiting for resource updates (simulated)")
        time.sleep(2)
        
        # Simulate a resource update
        client.handle_resource_update(
            subscription_id,
            {"content": "Updated content", "timestamp": time.time()}
        )
        
        # Step 9: Unsubscribe from the resource
        logger.info("Unsubscribing from the resource")
        client.unsubscribe_from_resource(subscription_id)
        
    except Exception as e:
        logger.error(f"Error in MCP Client example: {str(e)}")
    finally:
        # Disconnect the client from the host
        client.disconnect_from_host()
        logger.info("MCP Client example completed")


if __name__ == "__main__":
    main()