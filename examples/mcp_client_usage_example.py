#!/usr/bin/env python3
"""
MCP Client Usage Example

This example demonstrates how to use the MCP Client component to interact with MCP servers.
It shows the basic workflow of:
1. Creating a client
2. Connecting to a host
3. Discovering servers
4. Using tools from servers
5. Accessing resources from servers
6. Subscribing to resource updates

Usage:
    python mcp_client_usage_example.py
"""

import logging
import json
import sys
import time
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp_client_example")

# Import the MCP Client component
sys.path.append("services/mcp-server/src")
from client import MCPClient
from host import MCPHost

def main():
    """Main function demonstrating MCP Client usage."""
    logger.info("Starting MCP Client usage example")
    
    # Create a configuration for the client
    client_config = {
        "mcp": {
            "client_id": "example-client-1"
        },
        "connection": {
            "retry_count": 3,
            "retry_delay": 1
        }
    }
    
    # Create the client
    client = MCPClient(
        logger=logger,
        config=client_config
    )
    logger.info(f"Created MCP Client with ID: {client.client_id}")
    
    # Create a host
    host = MCPHost(
        logger=logger,
        config={}
    )
    logger.info("Created MCP Host")
    
    # Connect the client to the host
    success = client.connect_to_host(host)
    if not success:
        logger.error("Failed to connect to host")
        return 1
    logger.info("Connected to host")
    
    # Discover available servers
    servers = host.list_servers()
    logger.info(f"Discovered {len(servers)} servers")
    
    if not servers:
        logger.warning("No servers available")
        return 0
    
    # For each server, demonstrate client capabilities
    for server_id in servers:
        demonstrate_server_interaction(client, server_id)
    
    # Disconnect from the host
    client.disconnect_from_host()
    logger.info("Disconnected from host")
    
    return 0

def demonstrate_server_interaction(client: MCPClient, server_id: str):
    """Demonstrate interaction with a server."""
    logger.info(f"Interacting with server: {server_id}")
    
    # Negotiate capabilities
    capabilities = client.negotiate_capabilities(server_id)
    logger.info(f"Negotiated capabilities: {json.dumps(capabilities, indent=2)}")
    
    # List available tools
    tools = client.list_server_tools(server_id)
    logger.info(f"Available tools: {tools}")
    
    # For each tool, get details and create a proxy
    for tool_name in tools:
        tool_details = client.get_tool_details(server_id, tool_name)
        logger.info(f"Tool details for {tool_name}: {json.dumps(tool_details, indent=2)}")
        
        # Create a proxy for the tool
        tool_proxy = client.create_tool_proxy(server_id, tool_name)
        logger.info(f"Created proxy for tool: {tool_name}")
    
    # List available resources
    try:
        resources = client.list_resources(server_id, "file", "/")
        logger.info(f"Available resources: {resources}")
        
        # Access a resource
        if resources:
            resource_data = client.access_resource(server_id, resources[0])
            logger.info(f"Resource data for {resources[0]}: {json.dumps(resource_data, indent=2)}")
            
            # Subscribe to resource updates
            def resource_update_callback(update_data: Dict[str, Any]):
                logger.info(f"Resource update received: {json.dumps(update_data, indent=2)}")
            
            subscription_id = client.subscribe_to_resource(server_id, resources[0], resource_update_callback)
            logger.info(f"Subscribed to resource updates with ID: {subscription_id}")
            
            # Wait for updates (in a real application, this would be event-driven)
            time.sleep(5)
            
            # Unsubscribe
            client.unsubscribe_from_resource(subscription_id)
            logger.info(f"Unsubscribed from resource updates")
    except Exception as e:
        logger.error(f"Error accessing resources: {str(e)}")

if __name__ == "__main__":
    sys.exit(main())