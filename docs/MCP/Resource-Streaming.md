# MCP Resource Streaming and Compression

This document describes the enhanced resource handling capabilities in the MCP-BASE-STACK, including streaming, caching, and compression.

## Overview

The MCP-BASE-STACK now supports advanced resource handling capabilities:

1. **Resource Streaming**: Efficiently transfer large resources in chunks
2. **Resource Caching**: Improve performance with client and server-side caching
3. **Resource Compression**: Reduce bandwidth usage with automatic compression
4. **Range Requests**: Access specific portions of resources

## Resource Streaming

Resource streaming allows large resources to be transferred in manageable chunks, reducing memory usage and improving responsiveness.

### Server-Side Implementation

The server creates a stream and sends chunks to the client:

```python
# Create a stream
stream_id = f"file_{path.replace('/', '_')}_{int(time.time())}_{id(self)}"
self.active_streams[stream_id] = {
    "uri": uri,
    "path": target_path,
    "position": start,
    "end": end,
    "chunk_size": self.streaming_config["chunk_size"],
    "timestamp": time.time(),
    "compression": compression_info
}

# Send chunks
with open(path, 'r', errors='replace') as f:
    f.seek(position)
    bytes_to_read = min(chunk_size, end - position)
    content = f.read(bytes_to_read)
```

### Client-Side Implementation

The client buffers chunks and processes them:

```python
# Handle incoming chunks
if "content" in chunk_data:
    content = chunk_data["content"]
    
    # Check if content is compressed
    compression_info = chunk_data.get("metadata", {}).get("compression")
    if compression_info and isinstance(content, str):
        # Decompress the content
        content = self._decompress_content(content, compression_info)
    
    # Add to buffer
    buffer_info["buffer"] += content.encode("utf-8")
```

## Resource Compression

Compression reduces bandwidth usage by compressing resource content before transmission.

### Compression Configuration

```python
self.streaming_config = self.config.get("streaming", {
    "enabled": True,
    "chunk_size": 1024 * 1024,  # 1 MB chunks
    "buffer_size": 4 * 1024 * 1024,  # 4 MB buffer
    "compression": {
        "enabled": True,
        "min_size": 10 * 1024,  # Only compress resources larger than 10 KB
        "algorithm": "gzip",  # Options: "gzip", "zlib"
        "level": 6,  # Compression level (1-9, where 9 is highest compression)
        "exclude_types": [  # MIME types to exclude from compression
            "image/jpeg", "image/png", "image/gif", "image/webp",
            "audio/mpeg", "audio/mp4", "video/mp4", "video/mpeg",
            "application/zip", "application/gzip", "application/x-7z-compressed"
        ]
    }
})
```

### Compression Process

1. The server determines if compression should be used based on:
   - Resource size (only compress resources larger than min_size)
   - MIME type (don't compress already compressed formats)
   - Explicit compression request

2. If compression is enabled, the server:
   - Compresses the content using the specified algorithm
   - Encodes the compressed content as base64
   - Includes compression metadata in the response

3. The client:
   - Detects compressed content from metadata
   - Decodes base64 if needed
   - Decompresses the content using the appropriate algorithm
   - Provides the decompressed content to the application

## Resource Caching

Caching improves performance by storing frequently accessed resources.

### Cache Configuration

```python
self.cache_config = self.config.get("cache", {
    "enabled": True,
    "max_size": 100,  # Maximum number of resources to cache
    "ttl": 300,  # Time to live in seconds (5 minutes)
    "max_size_per_resource": 10 * 1024 * 1024  # 10 MB max size per resource
})
```

### Cache Features

1. **Size Limits**: Individual resources larger than max_size_per_resource are not cached
2. **LRU Eviction**: Least recently used resources are evicted when the cache is full
3. **TTL Expiration**: Resources expire after a configurable time-to-live period
4. **Cache Bypass**: Clients can bypass the cache with the bypass_cache parameter

## Range Requests

Range requests allow clients to request specific portions of a resource.

### Range Specification

Range specifications can be in one of three formats:
- `start-end`: Request bytes from start to end (inclusive)
- `start-`: Request bytes from start to the end of the resource
- `-end`: Request the last 'end' bytes of the resource

### Example

```python
# Request bytes 1000-1999 of a resource
response = client.access_resource(server_id, "resource://file/large_file.txt", range_spec="1000-1999")
```

## Usage Examples

### Streaming a Large Resource

```python
# Server-side
stream_response = file_provider.read_resource_stream("resource://file/large_file.txt")
stream_id = stream_response["stream_id"]

# Send chunks
while True:
    chunk = file_provider.get_next_stream_chunk(stream_id)
    if chunk["complete"]:
        break
    # Send chunk to client

# Client-side
stream_response = client.access_resource(server_id, "resource://file/large_file.txt", stream=True)
stream_id = stream_response["stream_id"]

# Process chunks
while True:
    chunk = client.get_stream_chunk(stream_id)
    if chunk["complete"]:
        break
    # Process chunk
```

### Using Compression

```python
# Server-side (compression is automatic based on configuration)
response = file_provider.read_resource_stream("resource://file/large_file.txt")

# Client-side (decompression is automatic)
response = client.access_resource(server_id, "resource://file/large_file.txt", stream=True)
```

### Using Range Requests

```python
# Get the first 1000 bytes
response = client.access_resource(server_id, "resource://file/large_file.txt", range_spec="0-999")

# Get the last 1000 bytes
response = client.access_resource(server_id, "resource://file/large_file.txt", range_spec="-1000")

# Get bytes from position 1000 to the end
response = client.access_resource(server_id, "resource://file/large_file.txt", range_spec="1000-")
```

## Performance Considerations

1. **Compression Trade-offs**: Compression reduces bandwidth but increases CPU usage
2. **Streaming Chunk Size**: Larger chunks reduce overhead but increase memory usage
3. **Cache Size**: Larger caches improve performance but increase memory usage
4. **Range Requests**: Can significantly reduce bandwidth for large resources

## Security Considerations

1. **Sensitive Resources**: The system automatically detects sensitive resources and requires elevated consent
2. **Resource Validation**: All resource operations include validation to prevent security issues
3. **Authorization**: Resource access requires appropriate authorization levels