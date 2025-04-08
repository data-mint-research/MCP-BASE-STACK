#!/usr/bin/env python3
"""
MCP Batch Processing Example

This example demonstrates how to use batch processing with the MCP components.
Batch processing allows sending multiple requests in a single operation,
which can significantly improve performance for multiple related operations.
"""

import logging
import sys
import uuid
import json
from typing import Dict, Any, List

# Add the project root to the Python path
sys.path.append(".")

from services.mcp_server.src.client.client import MCPClient
from services.mcp_server.src.host.host import MCPHost
from services.mcp_server.src.server.server import MCPServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp_batch_example")

def setup_mcp_components():
    """
    Set up the MCP components (server, host, client) for the example.
    
    Returns:
        tuple: (server, host, client) instances
    """
    # Create a server with a unique ID
    server_id = "example-server"
    server_config = {
        "consent": {
            "max_violations_history": 100
        }
    }
    server = MCPServer(server_id, logger, server_config)
    
    # Register some example tools
    @server.mcp_server.tool()
    def add(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b
    
    @server.mcp_server.tool()
    def multiply(a: int, b: int) -> int:
        """Multiply two numbers."""
        return a * b
    
    @server.mcp_server.tool()
    def divide(a: int, b: int) -> float:
        """Divide two numbers."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    
    # Register the tools with the server
    server.register_tool(add)
    server.register_tool(multiply)
    server.register_tool(divide)
    
    # Create a host
    host_config = {
        "mcp": {
            "host_id": "example-host"
        },
        "auth": {
            "token_expiration": 3600
        }
    }
    host = MCPHost(logger, host_config)
    
    # Register the server with the host
    host.register_server(server_id, {"capabilities": server.capabilities}, server)
    
    # Create a client
    client_config = {
        "mcp": {
            "client_id": "example-client"
        }
    }
    client = MCPClient(logger, client_config)
    
    # Connect the client to the host
    client.connect_to_host(host)
    
    return server, host, client

def demonstrate_individual_requests(client, server_id):
    """
    Demonstrate sending individual requests one by one.
    
    Args:
        client: MCPClient instance
        server_id: Server ID to send requests to
    """
    logger.info("Demonstrating individual requests...")
    
    # Execute tools individually
    start_time = __import__('time').time()
    
    # Request 1: Add two numbers
    add_result = client.execute_tool(server_id, "add", {"a": 5, "b": 3})
    logger.info(f"Add result: {add_result}")
    
    # Request 2: Multiply two numbers
    multiply_result = client.execute_tool(server_id, "multiply", {"a": 5, "b": 3})
    logger.info(f"Multiply result: {multiply_result}")
    
    # Request 3: Divide two numbers
    divide_result = client.execute_tool(server_id, "divide", {"a": 10, "b": 2})
    logger.info(f"Divide result: {divide_result}")
    
    end_time = __import__('time').time()
    logger.info(f"Individual requests completed in {end_time - start_time:.4f} seconds")

def demonstrate_batch_requests(client, server_id):
    """
    Demonstrate sending multiple requests in a single batch.
    
    Args:
        client: MCPClient instance
        server_id: Server ID to send requests to
    """
    logger.info("Demonstrating batch requests...")
    
    # Create individual requests
    request1 = client.create_jsonrpc_request("tools/execute", {
        "name": "add",
        "arguments": {"a": 5, "b": 3}
    })
    
    request2 = client.create_jsonrpc_request("tools/execute", {
        "name": "multiply",
        "arguments": {"a": 5, "b": 3}
    })
    
    request3 = client.create_jsonrpc_request("tools/execute", {
        "name": "divide",
        "arguments": {"a": 10, "b": 2}
    })
    
    # Create a batch request
    batch_request = client.create_batch_request([request1, request2, request3])
    
    # Send the batch request
    start_time = __import__('time').time()
    batch_results = client.send_batch_request_to_server(server_id, batch_request)
    end_time = __import__('time').time()
    
    # Process the results
    for i, result in enumerate(batch_results):
        logger.info(f"Batch result {i+1}: {result}")
    
    logger.info(f"Batch request completed in {end_time - start_time:.4f} seconds")

def demonstrate_error_handling(client, server_id):
    """
    Demonstrate error handling in batch requests.
    
    Args:
        client: MCPClient instance
        server_id: Server ID to send requests to
    """
    logger.info("Demonstrating batch request error handling...")
    
    # Create requests with an error
    request1 = client.create_jsonrpc_request("tools/execute", {
        "name": "add",
        "arguments": {"a": 5, "b": 3}
    })
    
    # This request will cause an error (divide by zero)
    request2 = client.create_jsonrpc_request("tools/execute", {
        "name": "divide",
        "arguments": {"a": 10, "b": 0}
    })
    
    request3 = client.create_jsonrpc_request("tools/execute", {
        "name": "multiply",
        "arguments": {"a": 5, "b": 3}
    })
    
    # Create a batch request
    batch_request = client.create_batch_request([request1, request2, request3])
    
    # Send the batch request and handle errors
    try:
        batch_results = client.send_batch_request_to_server(server_id, batch_request)
        
        # Process the results
        for i, result in enumerate(batch_results):
            if result.get("status") == "error":
                logger.error(f"Batch request {i+1} failed: {result.get('error')}")
            else:
                logger.info(f"Batch request {i+1} succeeded: {result.get('data')}")
    except Exception as e:
        logger.error(f"Batch request failed: {str(e)}")

def main():
    """Main function to run the example."""
    logger.info("Starting MCP Batch Processing Example")
    
    # Set up MCP components
    server, host, client = setup_mcp_components()
    server_id = "example-server"
    
    # Discover server capabilities
    capabilities = client.discover_server_capabilities(server_id)
    logger.info(f"Server capabilities: {capabilities}")
    
    # Check if batch processing is supported
    if capabilities.get("capabilities", {}).get("batch", False):
        logger.info("Batch processing is supported by the server")
    else:
        logger.warning("Batch processing is not supported by the server")
        return
    
    # Demonstrate individual requests
    demonstrate_individual_requests(client, server_id)
    
    # Demonstrate batch requests
    demonstrate_batch_requests(client, server_id)
    
    # Demonstrate error handling
    demonstrate_error_handling(client, server_id)
    
    logger.info("MCP Batch Processing Example completed")

if __name__ == "__main__":
    main()