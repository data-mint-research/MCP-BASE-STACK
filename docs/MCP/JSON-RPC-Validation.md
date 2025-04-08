# JSON-RPC Message Structure Validation

This document describes the JSON-RPC message structure validation implementation for the MCP-BASE-STACK project.

## Overview

The Model Context Protocol (MCP) uses JSON-RPC 2.0 as its underlying communication protocol. To ensure compliance with the JSON-RPC 2.0 specification, we have implemented comprehensive validation for all JSON-RPC messages.

## Implementation

The validation is implemented in two main components:

1. **JsonRpc Class**: Located in `services/mcp-server/src/mcp.py`, this class provides methods for creating and validating JSON-RPC messages.
2. **JsonRpcValidator Class**: Located in `services/mcp-server/src/modelcontextprotocol/json_rpc_validator.py`, this class provides a centralized validation interface that delegates to the JsonRpc class.

## Validation Rules

The validation ensures that all JSON-RPC messages comply with the JSON-RPC 2.0 specification:

### Request Validation

All JSON-RPC requests must:
- Include a `jsonrpc` field with value `"2.0"`
- Include a `method` field with a non-empty string value
- Include an `id` field (for requests) with a string, number, or null value
- Include a `params` field (optional) with an object or array value

### Response Validation

All JSON-RPC responses must:
- Include a `jsonrpc` field with value `"2.0"`
- Include an `id` field with a string, number, or null value
- Include either a `result` field or an `error` field, but not both
- If an `error` field is present, it must be an object with:
  - A `code` field with an integer value
  - A `message` field with a string value
  - An optional `data` field with any valid JSON value

### Batch Request/Response Validation

Batch requests and responses must:
- Be arrays
- Not be empty
- Contain valid individual requests or responses

### Tool Parameter Validation

Tool parameters are validated against the tool's input schema:
- Required parameters must be present
- Parameter types must match the schema

### Resource URI Validation

Resource URIs must:
- Be strings
- Start with `resource://`
- Include a provider

## Error Handling

When validation fails, detailed error information is provided:
- For requests, a JSON-RPC error response is returned with code -32600 (Invalid Request)
- For responses, the error is logged and a fallback error response is generated
- For batch requests, each invalid request is reported with its index and specific errors

## Usage

The validation is automatically applied in the following places:

1. **Client**: When creating and sending requests, and when receiving responses
2. **Server**: When receiving requests and sending responses
3. **Host**: When routing requests and responses between clients and servers

## Example

```python
# Validate a request
request = {
    "jsonrpc": "2.0",
    "method": "tools/execute",
    "params": {
        "name": "execute_shell_command",
        "arguments": {
            "command": "echo 'Hello, World!'"
        }
    },
    "id": "request-1"
}

validation_result = JsonRpcValidator.validate_request(request)
if validation_result["valid"]:
    # Process the request
else:
    # Handle validation errors
    errors = validation_result["errors"]
    print(f"Validation errors: {errors}")
```

## Compliance with MCP

This validation implementation ensures that all JSON-RPC messages in the MCP-BASE-STACK project comply with both the JSON-RPC 2.0 specification and the MCP requirements. It is a critical component of the MCP compliance checklist.