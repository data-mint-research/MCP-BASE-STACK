# MCP Client Implementation

This document describes the implementation of the Model Context Protocol (MCP) client component in the MCP-BASE-STACK project.

## Overview

The MCP client component is responsible for:

1. Communicating with the LLM (Large Language Model)
2. Managing client-side resources
3. Handling client-side operations
4. Routing JSON-RPC requests to the server via the host
5. Managing subscriptions to resources

The client follows the MCP architecture, which consists of three main components:

- **Host**: Coordinates multiple clients, manages consent, and context
- **Client**: One per server, routes JSON-RPC, handles subscriptions
- **Server**: Stateless capability providers

## Architecture

The client component is implemented in the `MCPClient` class, which is located in the `services/mcp-server/src/client/client.py` file. The client communicates with the server through the host component, which routes requests to the appropriate server.

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│   LLM   │◄────┤ Client  │◄────┤  Host   │
└─────────┘     └─────────┘     └─────────┘
                                     ▲
                                     │
                                     ▼
                                ┌─────────┐
                                │ Server  │
                                └─────────┘
```

## JSON-RPC Communication

The client uses JSON-RPC 2.0 for communication with the server. The client provides methods for creating JSON-RPC requests and notifications, sending requests to the server, and parsing responses.

### Creating JSON-RPC Requests

```python
request = client.create_jsonrpc_request(
    method="tools/execute",
    params={"name": "execute_shell_command", "arguments": {"command": "echo 'Hello'"}}
)
```

### Creating JSON-RPC Notifications

```python
notification = client.create_jsonrpc_notification(
    method="resources/subscribe",
    params={"uri": "resource://file/path/to/resource"}
)
```

### Sending Requests to the Server

```python
response = client.send_request_to_server(
    server_id="example-server",
    method="tools/execute",
    params={"name": "execute_shell_command", "arguments": {"command": "echo 'Hello'"}}
)
```

## Capability Negotiation

The client can negotiate capabilities with the server to determine which features are supported by both the client and server.

```python
capabilities = client.negotiate_capabilities("example-server")
```

The negotiated capabilities include:

- `tools`: Whether the server supports tools
- `resources`: Whether the server supports resources
- `subscriptions`: Whether the server supports subscriptions

## Tool Proxies

The client can create proxy functions for server tools, which simplify the process of executing tools.

```python
shell_command = client.create_tool_proxy("example-server", "execute_shell_command")
result = shell_command(command="echo 'Hello'")
```

The tool proxy validates the parameters against the tool's input schema before sending the request to the server.

## Resource Access

The client can access resources provided by the server.

```python
resources = client.list_resources("example-server", "file", "examples")
resource_data = client.access_resource("example-server", "resource://file/examples/example.txt")
```

## Subscription Management

The client can subscribe to resources to receive updates when the resource changes.

```python
def callback(update_data):
    print(f"Resource update: {update_data}")

subscription_id = client.subscribe_to_resource(
    "example-server",
    "resource://file/examples/example.txt",
    callback
)

# Later, unsubscribe
client.unsubscribe_from_resource(subscription_id)
```

## Error Handling and Retry Logic

The client includes error handling and retry logic for sending requests to the server. If a request fails, the client will retry the request a configurable number of times before giving up.

```python
client.connection_retry_count = 3  # Number of retries
client.connection_retry_delay = 2  # Delay between retries in seconds
```

## Connection Management

The client can connect to and disconnect from a host.

```python
client.connect_to_host(host)
client.disconnect_from_host()
```

## Dependency Injection

The client component is wired up using dependency injection in the `services/mcp-server/src/di/containers.py` file. The client is created with a logger, configuration, and a host instance.

```python
mcp_client = providers.Singleton(
    MCPComponentProvider.get_client,
    logger=logger,
    config=config,
    host=mcp_host
)
```

## Example Usage

See the `services/mcp-server/src/examples/client_example.py` file for a complete example of how to use the client component.

## Testing

The client component includes unit tests in the `services/mcp-server/src/tests/test_client.py` file. These tests verify the functionality of the client, including JSON-RPC message formatting, routing, and subscription handling.

To run the tests:

```bash
cd services/mcp-server/src
python -m unittest tests/test_client.py