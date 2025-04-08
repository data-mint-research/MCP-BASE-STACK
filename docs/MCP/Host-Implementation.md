# MCP Host Implementation

This document describes the implementation of the Model Context Protocol (MCP) host component in the MCP-BASE-STACK project.

## Overview

The MCP host component is responsible for:

1. Managing connections to MCP Servers
2. Routing requests from Clients to appropriate Servers
3. Handling lifecycle events for the MCP ecosystem
4. Managing client registration and authentication
5. Tracking context and consent for operations
6. Coordinating multiple clients

The host follows the MCP architecture, which consists of three main components:

- **Host**: Coordinates multiple clients, manages consent, and context
- **Client**: One per server, routes JSON-RPC, handles subscriptions
- **Server**: Stateless capability providers

## Architecture

The host component is implemented in the `MCPHost` class, which is located in the `services/mcp-server/src/host/host.py` file. The host communicates with both clients and servers, acting as the central coordinator for the MCP ecosystem.

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

## MCP SDK Integration

The host component uses the Python MCP SDK (`modelcontextprotocol`) to implement its functionality. The SDK provides classes and methods for:

- Host management
- Client registration and management
- Server registration and management
- Context tracking
- Consent management
- Authentication and authorization
- JSON-RPC message handling

## Key Features

### Server Management

The host maintains a registry of available servers and their capabilities. It provides methods for:

- Registering servers
- Unregistering servers
- Getting information about available servers
- Routing requests to servers

### Client Management

The host manages client connections and provides methods for:

- Registering clients
- Unregistering clients
- Getting information about connected clients
- Broadcasting messages to clients

### Request Routing

The host routes JSON-RPC requests from clients to the appropriate servers. It handles:

- Request validation
- Consent checking
- Error handling
- Response routing

### Context Management

The host tracks context information for each client, including:

- Active sessions
- Server connections
- Subscriptions
- Last activity time

### Consent Management

The host implements a consent system that controls what operations clients can perform on servers. It provides:

- Consent registration
- Consent revocation
- Consent checking
- Consent levels (NONE, READ_ONLY, BASIC, ELEVATED, FULL)

### Authentication and Authorization

The host includes an authentication and authorization system that:

- Authenticates users
- Creates and manages sessions
- Checks permissions
- Grants and revokes permissions

### Event System

The host implements an event system that allows components to subscribe to and publish events. This is used for:

- Notifying clients about server changes
- Coordinating actions between components
- Implementing the observer pattern

## API Endpoints

The host component is exposed through a FastAPI application that provides the following endpoints:

- `/servers` - Get a list of available servers
- `/servers/{server_id}` - Get information about a specific server
- `/clients` - Get a list of registered clients
- `/clients/{client_id}` - Get information about a specific client
- `/rpc/{server_id}` - Route a JSON-RPC request to a server
- `/consent` - Register consent for a client to perform operations on a server
- `/consent/{consent_id}` - Revoke a previously registered consent
- `/status` - Get the status of the MCP components

## Dependency Injection

The host component is wired up using dependency injection in the `services/mcp-server/src/di/containers.py` file. The host is created with a logger and configuration, and other components (clients and servers) are registered with it.

```python
mcp_host = providers.Singleton(
    MCPHost,
    logger=logger,
    config=config
)
```

## Example Usage

See the `app.py` file for a complete example of how to use the host component in a FastAPI application.

## Testing

The host component includes unit tests that verify its functionality, including:

- Server registration and management
- Client registration and management
- Request routing
- Consent management
- Authentication and authorization

## Future Improvements

- Implement persistent storage for context and consent information
- Add support for distributed host deployments
- Enhance security with more advanced authentication mechanisms
- Implement rate limiting and quota management
- Add support for more MCP primitives (e.g., prompts)