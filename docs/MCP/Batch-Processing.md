# MCP Batch Processing

This document describes the batch processing feature in the Model Context Protocol (MCP) implementation. Batch processing allows clients to send multiple requests in a single operation, which can significantly improve performance and reduce overhead.

## Overview

Batch processing is a standard feature of JSON-RPC 2.0, which the MCP protocol is built upon. It allows multiple JSON-RPC requests to be sent in a single HTTP request, reducing network overhead and improving performance.

In the MCP implementation, batch processing is supported across all three main components:
- **Server**: Processes multiple requests in a batch and returns a batch of responses
- **Client**: Creates and sends batch requests to servers
- **Host**: Routes batch requests to the appropriate server

## Benefits

Batch processing offers several advantages:

1. **Reduced Network Overhead**: Sending multiple requests in a single operation reduces the number of network round-trips, which can significantly improve performance, especially for high-latency connections.

2. **Improved Throughput**: The server can process multiple requests more efficiently by reducing the overhead of handling each request separately.

3. **Atomic Operations**: Related operations can be grouped together, making it easier to reason about their execution.

4. **Partial Success Handling**: Even if some requests in a batch fail, others can still succeed, allowing for more robust error handling.

## Implementation Details

### Server Component

The server component has been enhanced to handle batch requests with the following features:

- **Validation**: Batch requests are validated to ensure they conform to the JSON-RPC 2.0 specification.
- **Authentication and Authorization**: The server verifies that the client has the necessary permissions to execute all requests in the batch.
- **Consent Verification**: Each request in the batch is checked against the client's consent level.
- **Parallel Processing**: Requests in a batch can be processed in parallel for improved performance.
- **Error Handling**: If a request in the batch fails, the server continues processing the remaining requests and returns appropriate error responses.

### Client Component

The client component has been enhanced to support creating and sending batch requests:

- **Batch Creation**: The client can create a batch request from multiple individual requests.
- **Validation**: Batch requests are validated before being sent to ensure they conform to the JSON-RPC 2.0 specification.
- **Fallback Mechanism**: If a server doesn't support batch processing, the client can fall back to sending individual requests.
- **Result Processing**: The client processes the batch response and extracts individual results.

### Host Component

The host component has been enhanced to route batch requests:

- **Routing**: The host routes batch requests to the appropriate server.
- **Authentication**: The host verifies the client's authentication token for the entire batch.
- **Capability Checking**: The host checks if the target server supports batch processing.
- **Fallback Mechanism**: If a server doesn't support batch processing, the host can fall back to routing individual requests.

## Usage

### Creating and Sending Batch Requests

```python
# Create individual requests
request1 = client.create_jsonrpc_request("tools/execute", {
    "name": "add",
    "arguments": {"a": 5, "b": 3}
})

request2 = client.create_jsonrpc_request("tools/execute", {
    "name": "multiply",
    "arguments": {"a": 5, "b": 3}
})

# Create a batch request
batch_request = client.create_batch_request([request1, request2])

# Send the batch request
batch_results = client.send_batch_request_to_server(server_id, batch_request)

# Process the results
for i, result in enumerate(batch_results):
    print(f"Result {i+1}: {result}")
```

### Error Handling in Batch Requests

```python
try:
    batch_results = client.send_batch_request_to_server(server_id, batch_request)
    
    # Process the results
    for i, result in enumerate(batch_results):
        if result.get("status") == "error":
            print(f"Request {i+1} failed: {result.get('error')}")
        else:
            print(f"Request {i+1} succeeded: {result.get('data')}")
except Exception as e:
    print(f"Batch request failed: {str(e)}")
```

## Performance Considerations

While batch processing can significantly improve performance, there are some considerations to keep in mind:

1. **Batch Size**: Very large batches may consume excessive server resources. It's recommended to limit batch sizes to a reasonable number (e.g., 10-50 requests).

2. **Request Independence**: Batch requests are processed independently. If requests depend on each other, they should be sent in separate batches or as individual requests.

3. **Error Handling**: All requests in a batch should have proper error handling, as errors in one request don't affect the processing of other requests in the batch.

4. **Timeout Handling**: Batch requests may take longer to process than individual requests. Clients should set appropriate timeouts.

## Example

See the `examples/batch_processing_example.py` file for a complete example of using batch processing with the MCP components.

## Compatibility

Batch processing is an optional capability in the MCP protocol. Servers can indicate support for batch processing through the `batch` capability:

```json
{
  "capabilities": {
    "tools": true,
    "resources": true,
    "batch": true
  }
}
```

Clients should check if a server supports batch processing before sending batch requests. If a server doesn't support batch processing, clients should fall back to sending individual requests.