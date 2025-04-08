# MCP-BASE-STACK

Model Context Protocol (MCP) Base Stack implementation with Host, Client, and Server components.

## Overview

This project implements the Model Context Protocol (MCP) architecture, which consists of three main components:

- **Host**: Coordinates multiple clients, manages consent, and context
- **Client**: One per server, routes JSON-RPC, handles subscriptions
- **Server**: Stateless capability providers

The implementation uses the Python MCP SDK (`modelcontextprotocol`) to ensure compliance with the MCP specification.

## Architecture

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│  Client │◄────┤   Host  │◄────┤ Server  │
└─────────┘     └─────────┘     └─────────┘
                     ▲
                     │
                     ▼
                ┌─────────┐
                │ Server  │
                └─────────┘
```

The Host component is the central coordinator that manages communication between Clients and Servers. It handles:

- Server registration and discovery
- Client registration and management
- Request routing
- Context tracking
- Consent management
- Authentication and authorization
- Event propagation

## Components

### Host

The Host component is implemented in `services/mcp-server/src/host/host.py`. It provides:

- Server management (registration, unregistration, listing)
- Client management (registration, unregistration, listing)
- Request routing
- Context management
- Consent management
- Authentication and authorization
- Event system
- Client coordination

### Client

The Client component is implemented in `services/mcp-server/src/client/client.py`. It provides:

- Communication with the LLM
- Managing client-side resources
- Handling client-side operations
- Routing JSON-RPC requests to the server via the host
- Managing subscriptions to resources

### Server

The Server component is implemented in `services/mcp-server/src/server/server.py`. It provides:

- Registering and providing tools to clients
- Managing server-side resources
- Handling server-side operations using JSON-RPC 2.0

## API

The MCP Host component is exposed through a FastAPI application that provides the following endpoints:

- `/servers` - Get a list of available servers
- `/servers/{server_id}` - Get information about a specific server
- `/clients` - Get a list of registered clients
- `/clients/{client_id}` - Get information about a specific client
- `/rpc/{server_id}` - Route a JSON-RPC request to a server
- `/consent` - Register consent for a client to perform operations on a server
- `/consent/{consent_id}` - Revoke a previously registered consent
- `/status` - Get the status of the MCP components

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/MCP-BASE-STACK.git
   cd MCP-BASE-STACK
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

You can run the application using the provided script:

```bash
chmod +x scripts/run-mcp-host.sh
./scripts/run-mcp-host.sh
```

Or manually:

```bash
export MCP_HOST_ID="main-host"
export MCP_SERVER_ID="main-server"
export MCP_CLIENT_ID="main-client"
export PORT=8000
python app.py
```

The application will start on http://localhost:8000.

## Examples

### Client Example

The `examples/mcp_client_example.py` script demonstrates how to use the MCP Host component from a client perspective:

```bash
python examples/mcp_client_example.py
```

This example shows how to:
1. Connect to the MCP Host
2. Discover available servers
3. Execute tools on servers
4. Access resources from servers
5. Register consent for operations

## Testing

You can run the tests using pytest:

```bash
cd services/mcp-server/src
python -m pytest tests/
```

## Documentation

- [Host Implementation](docs/MCP/host-implementation.md)
- [Client Implementation](docs/MCP/client-implementation.md)
- [MCP Protocol](docs/MCP/protocol.md)
- [MCP Architecture](docs/MCP/architecture.md)

## License

This project is licensed under the MIT License - see the LICENSE file for details.