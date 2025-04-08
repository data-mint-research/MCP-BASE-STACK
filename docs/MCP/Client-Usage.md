# MCP Client Component Usage Guide

This document provides guidance on how to use the MCP Client component in your applications.

## Overview

The MCP Client component is responsible for:

1. Communicating with the LLM
2. Managing client-side resources
3. Handling client-side operations
4. Routing JSON-RPC requests to the server via the host
5. Managing subscriptions to resources

## Installation

The MCP Client component is part of the MCP-BASE-STACK. To use it, you need to:

1. Clone the repository
2. Run the implementation scripts:
   ```bash
   python scripts/migration/mcp/implement_host_component.py
   python scripts/migration/mcp/implement_client_component.py
   ```

## Basic Usage

Here's a simple example of how to use the MCP Client component:

```python
import logging
from client import MCPClient
from host import MCPHost

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_example")

# Create a client configuration
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

# Create a host
host = MCPHost(
    logger=logger,
    config={}
)

# Connect the client to the host
success = client.connect_to_host(host)
if not success:
    logger.error("Failed to connect to host")
    exit(1)

# Now you can interact with servers through the client
# ...

# Disconnect when done
client.disconnect_from_host()
```

## Working with Servers

### Discovering Servers

To discover available servers:

```python
servers = host.list_servers()
for server_id in servers:
    print(f"Found server: {server_id}")
```

### Negotiating Capabilities

Before interacting with a server, you should negotiate capabilities:

```python
capabilities = client.negotiate_capabilities(server_id)
print(f"Negotiated capabilities: {capabilities}")
```

### Using Tools

To use tools provided by a server:

```python
# List available tools
tools = client.list_server_tools(server_id)

# Get details about a specific tool
tool_details = client.get_tool_details(server_id, tool_name)

# Create a proxy for the tool
tool_proxy = client.create_tool_proxy(server_id, tool_name)

# Use the tool
result = tool_proxy(param1="value1", param2="value2")
```

### Accessing Resources

To access resources provided by a server:

```python
# List available resources
resources = client.list_resources(server_id, provider, path)

# Access a specific resource
resource_data = client.access_resource(server_id, uri)
```

### Subscribing to Resources

To subscribe to resource updates:

```python
# Define a callback function
def resource_update_callback(update_data):
    print(f"Resource update received: {update_data}")

# Subscribe to the resource
subscription_id = client.subscribe_to_resource(
    server_id=server_id,
    uri=resource_uri,
    callback=resource_update_callback
)

# Later, unsubscribe when done
client.unsubscribe_from_resource(subscription_id)
```

## JSON-RPC Message Format

The MCP Client component uses JSON-RPC 2.0 for communication. Here's an example of a request:

```json
{
  "jsonrpc": "2.0",
  "id": "client-1-1",
  "method": "tools/list",
  "params": {}
}
```

And a response:

```json
{
  "jsonrpc": "2.0",
  "id": "client-1-1",
  "result": {
    "tools": ["tool1", "tool2"]
  }
}
```

## Error Handling

The MCP Client component provides robust error handling:

```python
try:
    result = client.send_request_to_server(
        server_id=server_id,
        method="tools/execute",
        params={
            "name": tool_name,
            "arguments": arguments
        }
    )
except ConnectionError as e:
    logger.error(f"Connection error: {str(e)}")
except Exception as e:
    logger.error(f"Error: {str(e)}")
```

## Testing

You can test the MCP Client component using the provided test script:

```bash
python scripts/test_mcp_client.py
```

This script creates a mock server and tests various client operations.

## Examples

For more examples, see:

- `examples/mcp_client_usage_example.py` - Basic usage example
- `scripts/test_mcp_client.py` - Comprehensive test script with a mock server

## Protocol Compliance

The MCP Client component is fully compliant with the Model Context Protocol (2025-03-26) specification. It:

- Uses the official MCP SDK
- Properly formats JSON-RPC messages
- Handles subscriptions correctly
- Routes requests through the host component
- Validates capabilities according to protocol

## Troubleshooting

If you encounter issues:

1. Check the logs for error messages
2. Verify that the host component is running
3. Ensure that servers are registered with the host
4. Check network connectivity if using remote servers

## Advanced Configuration

The client can be configured with various options:

```python
client_config = {
    "mcp": {
        "client_id": "custom-client-id",
        "protocol_version": "2025-03-26"
    },
    "connection": {
        "retry_count": 5,
        "retry_delay": 2
    },
    "logging": {
        "level": "DEBUG"
    }
}
```

## Contributing

To contribute to the MCP Client component:

1. Follow the MCP protocol specification
2. Use the official MCP SDK
3. Write tests for your changes
4. Document your changes