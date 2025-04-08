#!/usr/bin/env python3
"""
MCP Resource Streaming and Compression Example

This example demonstrates how to use the enhanced resource handling capabilities
in the MCP-BASE-STACK, including streaming, caching, compression, and range requests.
"""

import logging
import time
import sys
import os
import base64

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.mcp_server.src.client.client import MCPClient
from services.mcp_server.src.host.host import MCPHost
from services.mcp_server.src.server.server import MCPServer
from services.mcp_server.src.server.resources.file_resource import FileResourceProvider

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("resource_example")

def setup_example_environment():
    """Set up a simple MCP environment for the example."""
    # Create a host
    host = MCPHost(logger=logging.getLogger("mcp_host"))
    
    # Create a server with file resource provider
    server = MCPServer(
        server_id="example_server",
        logger=logging.getLogger("mcp_server"),
        config={
            "resources": {
                "providers": ["file"]
            }
        }
    )
    
    # Configure the file resource provider
    file_provider = FileResourceProvider(
        base_path="./examples/data",
        config={
            "cache": {
                "enabled": True,
                "max_size": 10,
                "ttl": 60,
                "max_size_per_resource": 1024 * 1024
            },
            "streaming": {
                "enabled": True,
                "chunk_size": 1024,
                "buffer_size": 4096,
                "compression": {
                    "enabled": True,
                    "min_size": 1024,
                    "algorithm": "gzip",
                    "level": 6
                }
            }
        }
    )
    
    # Register the file provider with the server
    server.register_resource_provider("file", file_provider)
    
    # Register the server with the host
    host.register_server(server)
    
    # Create a client
    client = MCPClient(
        logger=logging.getLogger("mcp_client"),
        config={
            "resource_cache": {
                "max_size": 10,
                "ttl": 60,
                "max_size_per_resource": 1024 * 1024
            }
        }
    )
    
    # Connect the client to the host
    client.connect_to_host(host)
    
    # Create example data directory and file if they don't exist
    os.makedirs("./examples/data", exist_ok=True)
    
    # Create a sample text file
    with open("./examples/data/sample.txt", "w") as f:
        f.write("This is a sample text file for demonstrating resource streaming and compression.\n")
        f.write("It contains multiple lines of text to make it more realistic.\n")
        for i in range(100):
            f.write(f"Line {i}: The quick brown fox jumps over the lazy dog.\n")
    
    # Create a sample binary file
    with open("./examples/data/sample.bin", "wb") as f:
        f.write(os.urandom(1024 * 10))  # 10 KB of random data
    
    return host, server, client, file_provider

def demonstrate_basic_resource_access(client, server_id):
    """Demonstrate basic resource access."""
    logger.info("=== Basic Resource Access ===")
    
    # Access a text resource
    response = client.access_resource(
        server_id=server_id,
        resource_uri="resource://file/sample.txt"
    )
    
    if response.get("success", False):
        logger.info(f"Successfully accessed resource: {response['metadata']['name']}")
        logger.info(f"Resource size: {response['metadata']['size']} bytes")
        logger.info(f"First 100 characters: {response['content'][:100]}...")
    else:
        logger.error(f"Failed to access resource: {response.get('error', 'Unknown error')}")
    
    # Access the same resource again (should use cache)
    start_time = time.time()
    response = client.access_resource(
        server_id=server_id,
        resource_uri="resource://file/sample.txt"
    )
    end_time = time.time()
    
    if response.get("success", False):
        logger.info(f"Cache access time: {(end_time - start_time) * 1000:.2f} ms")
    
    # Access with cache bypass
    response = client.access_resource(
        server_id=server_id,
        resource_uri="resource://file/sample.txt",
        bypass_cache=True
    )
    
    if response.get("success", False):
        logger.info("Successfully bypassed cache")

def demonstrate_range_requests(client, server_id):
    """Demonstrate range requests."""
    logger.info("\n=== Range Requests ===")
    
    # Get the first 50 bytes
    response = client.access_resource(
        server_id=server_id,
        resource_uri="resource://file/sample.txt",
        range_spec="0-49"
    )
    
    if response.get("success", False):
        logger.info(f"First 50 bytes: {response['content']}")
        logger.info(f"Range: {response['metadata']['range']}")
    
    # Get the last 50 bytes
    response = client.access_resource(
        server_id=server_id,
        resource_uri="resource://file/sample.txt",
        range_spec="-50"
    )
    
    if response.get("success", False):
        logger.info(f"Last 50 bytes: {response['content']}")
        logger.info(f"Range: {response['metadata']['range']}")
    
    # Get bytes from position 100 to the end
    response = client.access_resource(
        server_id=server_id,
        resource_uri="resource://file/sample.txt",
        range_spec="100-"
    )
    
    if response.get("success", False):
        logger.info(f"From position 100: {response['content'][:50]}...")
        logger.info(f"Range: {response['metadata']['range']}")

def demonstrate_streaming(client, server_id):
    """Demonstrate resource streaming."""
    logger.info("\n=== Resource Streaming ===")
    
    # Start streaming a resource
    response = client.access_resource(
        server_id=server_id,
        resource_uri="resource://file/sample.bin",
        stream=True
    )
    
    if not response.get("success", False):
        logger.error(f"Failed to start streaming: {response.get('error', 'Unknown error')}")
        return
    
    stream_id = response.get("stream_id")
    if not stream_id:
        logger.error("No stream ID returned")
        return
    
    logger.info(f"Started streaming with ID: {stream_id}")
    logger.info(f"Stream metadata: {response.get('metadata', {})}")
    
    # Get stream chunks
    total_bytes = 0
    chunk_count = 0
    
    while True:
        # In a real application, you would get chunks from the server
        # Here we simulate by directly accessing the client's buffer
        buffer_info = client.get_stream_buffer(stream_id)
        
        # Check if stream is complete
        if buffer_info.get("complete", False):
            logger.info("Stream complete")
            break
        
        # Get next chunk
        chunk_data = client.handle_resource_stream_chunk(
            stream_id,
            {
                "content": f"Chunk {chunk_count}",
                "complete": chunk_count >= 5,  # Complete after 5 chunks
                "metadata": {
                    "position": chunk_count * 1024,
                    "bytes_read": 1024
                }
            }
        )
        
        total_bytes += 1024
        chunk_count += 1
        
        logger.info(f"Received chunk {chunk_count}, total bytes: {total_bytes}")
        
        # Simulate processing time
        time.sleep(0.1)
    
    # Close the stream
    client.clear_stream_buffer(stream_id)
    logger.info("Stream closed")

def demonstrate_compression(client, server_id, file_provider):
    """Demonstrate resource compression."""
    logger.info("\n=== Resource Compression ===")
    
    # Create a highly compressible file
    with open("./examples/data/compressible.txt", "w") as f:
        f.write("a" * 10000)  # Highly compressible content
    
    # Access the resource with compression
    response = client.access_resource(
        server_id=server_id,
        resource_uri="resource://file/compressible.txt",
        stream=True
    )
    
    if not response.get("success", False):
        logger.error(f"Failed to access resource: {response.get('error', 'Unknown error')}")
        return
    
    # Check if compression was applied
    metadata = response.get("metadata", {})
    compression_info = metadata.get("compression")
    
    if compression_info:
        logger.info(f"Compression applied: {compression_info}")
        logger.info(f"Original size: {metadata.get('size', 0)} bytes")
        if "ratio" in compression_info:
            logger.info(f"Compression ratio: {compression_info['ratio']:.2f}")
            logger.info(f"Space saved: {(1 - compression_info['ratio']) * 100:.2f}%")
    else:
        logger.info("No compression applied")
    
    # Simulate decompression
    logger.info("\nSimulating decompression:")
    
    # Create compressed content
    import gzip
    content = "a" * 10000
    compressed = gzip.compress(content.encode('utf-8'), compresslevel=6)
    compressed_b64 = base64.b64encode(compressed).decode('ascii')
    
    # Decompress
    decompressed = client._decompress_content(
        compressed_b64,
        {
            "algorithm": "gzip",
            "encoding": "base64",
            "original_size": len(content),
            "compressed_size": len(compressed)
        }
    )
    
    logger.info(f"Original size: {len(content)} bytes")
    logger.info(f"Compressed size: {len(compressed)} bytes")
    logger.info(f"Compression ratio: {len(compressed) / len(content):.2f}")
    logger.info(f"Decompressed size: {len(decompressed)} bytes")
    logger.info(f"Decompression successful: {len(decompressed) == len(content)}")

def main():
    """Run the example."""
    logger.info("Starting MCP Resource Streaming and Compression Example")
    
    # Set up the example environment
    host, server, client, file_provider = setup_example_environment()
    
    # Demonstrate basic resource access
    demonstrate_basic_resource_access(client, server.server_id)
    
    # Demonstrate range requests
    demonstrate_range_requests(client, server.server_id)
    
    # Demonstrate streaming
    demonstrate_streaming(client, server.server_id)
    
    # Demonstrate compression
    demonstrate_compression(client, server.server_id, file_provider)
    
    logger.info("\nExample complete")

if __name__ == "__main__":
    main()