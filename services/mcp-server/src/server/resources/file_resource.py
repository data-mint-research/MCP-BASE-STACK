"""
File Resource Provider for MCP Server.

This module implements a resource provider for accessing files on the server.
Files are exposed via the resource://file/ URI scheme.
"""

import os
import logging
import json
import time
import gzip
import zlib
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
from mimetypes import guess_type

logger = logging.getLogger("mcp_server.resources.file")

class FileResourceProvider:
    """
    Resource provider for accessing files on the server.
    
    This provider exposes files via the resource://file/ URI scheme.
    It supports listing, reading, and subscribing to file resources.
    """
    
    def __init__(self, base_path: str = None, config: Dict[str, Any] = None):
        """
        Initialize the file resource provider.
        
        Args:
            base_path: Base path for file resources. If None, the current working directory is used.
            config: Configuration dictionary for the resource provider
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.subscribers = {}
        
        # Initialize cache
        self.cache = {}
        self.config = config or {}
        self.cache_config = self.config.get("cache", {
            "enabled": True,
            "max_size": 100,  # Maximum number of resources to cache
            "ttl": 300,  # Time to live in seconds (5 minutes)
            "max_size_per_resource": 10 * 1024 * 1024  # 10 MB max size per resource
        })
        
        # Initialize streaming settings
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
        
        # Track active streams
        self.active_streams = {}
        
        logger.info(f"File resource provider initialized with base path: {self.base_path}")
        logger.info(f"Cache enabled: {self.cache_config['enabled']}, Streaming enabled: {self.streaming_config['enabled']}")
        
    def list_resources(self, path: str = "") -> Dict[str, Any]:
        """
        List file resources at the specified path.
        
        Args:
            path: Path relative to the base path
            
        Returns:
            Dict[str, Any]: Dictionary containing the list of resources
        """
        try:
            target_path = self.base_path / path
            if not target_path.exists():
                return {
                    "success": False,
                    "error": f"Path not found: {path}"
                }
                
            if target_path.is_file():
                return {
                    "success": True,
                    "resources": [{
                        "uri": f"resource://file/{path}",
                        "type": "file",
                        "name": target_path.name,
                        "size": target_path.stat().st_size,
                        "modified": datetime.fromtimestamp(target_path.stat().st_mtime).isoformat()
                    }]
                }
                
            resources = []
            for item in target_path.iterdir():
                resource_path = str(item.relative_to(self.base_path)).replace("\\", "/")
                resources.append({
                    "uri": f"resource://file/{resource_path}",
                    "type": "file" if item.is_file() else "directory",
                    "name": item.name,
                    "size": item.stat().st_size if item.is_file() else None,
                    "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                })
                
            return {
                "success": True,
                "resources": resources
            }
        except Exception as e:
            logger.error(f"Error listing resources: {str(e)}")
            return {
                "success": False,
                "error": f"Error listing resources: {str(e)}"
            }
            
    def read_resource(self, uri: str, bypass_cache: bool = False) -> Dict[str, Any]:
        """
        Read a file resource.
        
        Args:
            uri: Resource URI (resource://file/path/to/file)
            bypass_cache: Whether to bypass the cache
            
        Returns:
            Dict[str, Any]: Dictionary containing the resource content
        """
        try:
            if not uri.startswith("resource://file/"):
                return {
                    "success": False,
                    "error": f"Invalid URI scheme: {uri}"
                }
                
            # Check cache first if enabled and not bypassing
            if self.cache_config["enabled"] and not bypass_cache and uri in self.cache:
                cache_entry = self.cache[uri]
                current_time = time.time()
                
                # Check if cache entry is still valid
                if current_time - cache_entry["timestamp"] < self.cache_config["ttl"]:
                    logger.debug(f"Cache hit for resource: {uri}")
                    
                    # Update access timestamp
                    cache_entry["timestamp"] = current_time
                    return cache_entry["data"]
                else:
                    # Remove expired entry
                    del self.cache[uri]
                    logger.debug(f"Removed expired cache entry for: {uri}")
                
            path = uri[len("resource://file/"):]
            target_path = self.base_path / path
            
            if not target_path.exists():
                return {
                    "success": False,
                    "error": f"Resource not found: {uri}"
                }
                
            if target_path.is_dir():
                return {
                    "success": False,
                    "error": f"Cannot read directory as file: {uri}"
                }
                
            content = target_path.read_text(errors="replace")
            result = {
                "success": True,
                "content": content,
                "metadata": {
                    "uri": uri,
                    "type": "file",
                    "name": target_path.name,
                    "size": target_path.stat().st_size,
                    "modified": datetime.fromtimestamp(target_path.stat().st_mtime).isoformat()
                }
            }
            
            # Cache the result if caching is enabled
            if self.cache_config["enabled"] and not bypass_cache:
                self._cache_resource(uri, result)
                
            return result
        except Exception as e:
            logger.error(f"Error reading resource: {str(e)}")
            return {
                "success": False,
                "error": f"Error reading resource: {str(e)}"
            }
            
    def subscribe(self, uri: str, callback_id: str) -> Dict[str, Any]:
        """
        Subscribe to changes in a file resource.
        
        Args:
            uri: Resource URI (resource://file/path/to/file)
            callback_id: ID for the callback
            
        Returns:
            Dict[str, Any]: Dictionary containing subscription status
        """
        try:
            if not uri.startswith("resource://file/"):
                return {
                    "success": False,
                    "error": f"Invalid URI scheme: {uri}"
                }
                
            path = uri[len("resource://file/"):]
            target_path = self.base_path / path
            
            if not target_path.exists():
                return {
                    "success": False,
                    "error": f"Resource not found: {uri}"
                }
                
            if uri not in self.subscribers:
                self.subscribers[uri] = []
                
            if callback_id not in self.subscribers[uri]:
                self.subscribers[uri].append(callback_id)
                
            return {
                "success": True,
                "message": f"Subscribed to {uri}",
                "subscription_id": f"{uri}:{callback_id}"
            }
        except Exception as e:
            logger.error(f"Error subscribing to resource: {str(e)}")
            return {
                "success": False,
                "error": f"Error subscribing to resource: {str(e)}"
            }
            
    def unsubscribe(self, uri: str, callback_id: str) -> Dict[str, Any]:
        """
        Unsubscribe from changes in a file resource.
        
        Args:
            uri: Resource URI (resource://file/path/to/file)
            callback_id: ID for the callback
            
        Returns:
            Dict[str, Any]: Dictionary containing unsubscription status
        """
        try:
            if uri not in self.subscribers:
                return {
                    "success": False,
                    "error": f"No subscribers for {uri}"
                }
                
            if callback_id not in self.subscribers[uri]:
                return {
                    "success": False,
                    "error": f"Callback {callback_id} not subscribed to {uri}"
                }
                
            self.subscribers[uri].remove(callback_id)
            if not self.subscribers[uri]:
                del self.subscribers[uri]
                
            return {
                "success": True,
                "message": f"Unsubscribed from {uri}"
            }
        except Exception as e:
            logger.error(f"Error unsubscribing from resource: {str(e)}")
            return {
                "success": False,
                "error": f"Error unsubscribing from resource: {str(e)}"
            }
            
    def read_resource_stream(self, uri: str, range_spec: Optional[str] = None,
                            compress: Optional[bool] = None) -> Dict[str, Any]:
        """
        Read a file resource as a stream.
        
        Args:
            uri: Resource URI (resource://file/path/to/file)
            range_spec: Range specification for partial access (e.g., "0-499", "-500", "500-")
            
        Returns:
            Dict[str, Any]: Dictionary containing stream information
        """
        try:
            if not uri.startswith("resource://file/"):
                return {
                    "success": False,
                    "error": f"Invalid URI scheme: {uri}"
                }
                
            if not self.streaming_config["enabled"]:
                logger.warning(f"Streaming is disabled, falling back to standard read for: {uri}")
                return self.read_resource(uri)
                
            path = uri[len("resource://file/"):]
            target_path = self.base_path / path
            
            if not target_path.exists():
                return {
                    "success": False,
                    "error": f"Resource not found: {uri}"
                }
                
            if target_path.is_dir():
                return {
                    "success": False,
                    "error": f"Cannot read directory as file: {uri}"
                }
                
            # Get file size
            file_size = target_path.stat().st_size
            
            # Parse range if specified
            start, end = 0, file_size
            if range_spec:
                try:
                    start, end = self._parse_range(range_spec, file_size)
                except ValueError as e:
                    return {
                        "success": False,
                        "error": f"Invalid range specification: {str(e)}"
                    }
            
            # Generate a unique stream ID
            stream_id = f"file_{path.replace('/', '_')}_{int(time.time())}_{id(self)}"
            
            # Determine if compression should be used
            compression_enabled = self._should_use_compression(target_path, compress)
            compression_info = None
            
            if compression_enabled:
                compression_config = self.streaming_config.get("compression", {})
                algorithm = compression_config.get("algorithm", "gzip")
                level = compression_config.get("level", 6)
                compression_info = {
                    "algorithm": algorithm,
                    "level": level
                }
                logger.debug(f"Compression enabled for stream {stream_id} using {algorithm} level {level}")
            
            # Set up the stream
            self.active_streams[stream_id] = {
                "uri": uri,
                "path": target_path,
                "position": start,
                "end": end,
                "chunk_size": self.streaming_config["chunk_size"],
                "timestamp": time.time(),
                "compression": compression_info
            }
            
            logger.info(f"Created stream {stream_id} for resource: {uri}, range: {start}-{end}")
            
            return {
                "success": True,
                "stream_id": stream_id,
                "metadata": {
                    "uri": uri,
                    "type": "file",
                    "name": target_path.name,
                    "size": file_size,
                    "modified": datetime.fromtimestamp(target_path.stat().st_mtime).isoformat(),
                    "range": {
                        "start": start,
                        "end": end,
                        "total_size": file_size
                    },
                    "compression": compression_info
                }
            }
        except Exception as e:
            logger.error(f"Error setting up stream for resource: {str(e)}")
            return {
                "success": False,
                "error": f"Error setting up stream: {str(e)}"
            }
            
    def read_resource_range(self, uri: str, range_spec: str) -> Dict[str, Any]:
        """
        Read a specific range of a file resource.
        
        Args:
            uri: Resource URI (resource://file/path/to/file)
            range_spec: Range specification (e.g., "0-499", "-500", "500-")
            
        Returns:
            Dict[str, Any]: Dictionary containing the resource content for the specified range
        """
        try:
            if not uri.startswith("resource://file/"):
                return {
                    "success": False,
                    "error": f"Invalid URI scheme: {uri}"
                }
                
            path = uri[len("resource://file/"):]
            target_path = self.base_path / path
            
            if not target_path.exists():
                return {
                    "success": False,
                    "error": f"Resource not found: {uri}"
                }
                
            if target_path.is_dir():
                return {
                    "success": False,
                    "error": f"Cannot read directory as file: {uri}"
                }
                
            # Get file size
            file_size = target_path.stat().st_size
            
            # Parse range
            try:
                start, end = self._parse_range(range_spec, file_size)
            except ValueError as e:
                return {
                    "success": False,
                    "error": f"Invalid range specification: {str(e)}"
                }
                
            # Read the specified range
            with open(target_path, 'r', errors='replace') as f:
                f.seek(start)
                content = f.read(end - start)
                
            return {
                "success": True,
                "content": content,
                "metadata": {
                    "uri": uri,
                    "type": "file",
                    "name": target_path.name,
                    "size": file_size,
                    "modified": datetime.fromtimestamp(target_path.stat().st_mtime).isoformat(),
                    "range": {
                        "start": start,
                        "end": end,
                        "total_size": file_size
                    }
                }
            }
        except Exception as e:
            logger.error(f"Error reading resource range: {str(e)}")
            return {
                "success": False,
                "error": f"Error reading resource range: {str(e)}"
            }
            
    def get_next_stream_chunk(self, stream_id: str) -> Dict[str, Any]:
        """
        Get the next chunk of data from a stream.
        
        Args:
            stream_id: Stream ID
            
        Returns:
            Dict[str, Any]: Dictionary containing the next chunk of data
        """
        try:
            if stream_id not in self.active_streams:
                return {
                    "success": False,
                    "error": f"Unknown stream ID: {stream_id}"
                }
                
            stream_info = self.active_streams[stream_id]
            path = stream_info["path"]
            position = stream_info["position"]
            end = stream_info["end"]
            chunk_size = stream_info["chunk_size"]
            
            # Check if we've reached the end
            if position >= end:
                # Clean up the stream
                del self.active_streams[stream_id]
                logger.debug(f"Stream {stream_id} completed and removed")
                
                return {
                    "success": True,
                    "complete": True,
                    "content": "",
                    "metadata": {
                        "uri": stream_info["uri"],
                        "position": position,
                        "end": end
                    }
                }
                
            # Read the next chunk
            with open(path, 'r', errors='replace') as f:
                f.seek(position)
                bytes_to_read = min(chunk_size, end - position)
                content = f.read(bytes_to_read)
                
            # Apply compression if enabled
            compression_info = stream_info.get("compression")
            if compression_info:
                content, compression_stats = self._compress_content(content, compression_info)
                
            # Update position
            new_position = position + len(content)
            stream_info["position"] = new_position
            stream_info["timestamp"] = time.time()
            
            # Check if this is the last chunk
            is_complete = new_position >= end
            
            # Clean up if complete
            if is_complete:
                del self.active_streams[stream_id]
                logger.debug(f"Stream {stream_id} completed and removed")
                
            # Prepare response
            response = {
                "success": True,
                "complete": is_complete,
                "content": content,
                "metadata": {
                    "uri": stream_info["uri"],
                    "position": position,
                    "new_position": new_position,
                    "end": end,
                    "bytes_read": len(content)
                }
            }
            
            # Add compression metadata if compression was applied
            if compression_info:
                response["metadata"]["compression"] = compression_stats
                
            return response
        except Exception as e:
            logger.error(f"Error getting stream chunk: {str(e)}")
            
            # Clean up the stream on error
            if stream_id in self.active_streams:
                del self.active_streams[stream_id]
                
            return {
                "success": False,
                "error": f"Error getting stream chunk: {str(e)}"
            }
            
    def close_stream(self, stream_id: str) -> Dict[str, Any]:
        """
        Close a stream.
        
        Args:
            stream_id: Stream ID
            
        Returns:
            Dict[str, Any]: Dictionary containing the result of the operation
        """
        try:
            if stream_id not in self.active_streams:
                return {
                    "success": False,
                    "error": f"Unknown stream ID: {stream_id}"
                }
                
            # Get stream info for the response
            stream_info = self.active_streams[stream_id]
            uri = stream_info["uri"]
            
            # Clean up the stream
            del self.active_streams[stream_id]
            logger.debug(f"Stream {stream_id} closed")
            
            return {
                "success": True,
                "message": f"Stream closed: {stream_id}",
                "metadata": {
                    "uri": uri
                }
            }
        except Exception as e:
            logger.error(f"Error closing stream: {str(e)}")
            return {
                "success": False,
                "error": f"Error closing stream: {str(e)}"
            }
            
    def _cache_resource(self, uri: str, data: Dict[str, Any]) -> None:
        """
        Cache a resource for future access.
        
        Args:
            uri: Resource URI
            data: Resource data to cache
        """
        if not self.cache_config["enabled"]:
            return
            
        # Skip caching if the resource is too large
        content_size = len(data.get("content", "")) if isinstance(data.get("content"), str) else 0
        if content_size > self.cache_config["max_size_per_resource"]:
            logger.debug(f"Resource too large to cache: {uri} ({content_size} bytes)")
            return
            
        # Evict oldest entries if cache is full
        if len(self.cache) >= self.cache_config["max_size"]:
            # Sort by timestamp (oldest first)
            sorted_cache = sorted(self.cache.items(), key=lambda x: x[1]["timestamp"])
            # Remove oldest entry
            oldest_uri = sorted_cache[0][0]
            del self.cache[oldest_uri]
            logger.debug(f"Evicted oldest cache entry: {oldest_uri}")
            
        # Add to cache with current timestamp
        self.cache[uri] = {
            "data": data,
            "timestamp": time.time(),
            "size": content_size
        }
        logger.debug(f"Cached resource: {uri} ({content_size} bytes)")
        
    def _parse_range(self, range_spec: str, content_length: int) -> tuple:
        """
        Parse a range specification string.
        
        Args:
            range_spec: Range specification (e.g., "0-499", "-500", "500-")
            content_length: Total length of the content
            
        Returns:
            tuple: (start, end) byte positions
            
        Raises:
            ValueError: If the range specification is invalid
        """
        if not range_spec or not isinstance(range_spec, str):
            raise ValueError("Invalid range specification")
            
        # Parse range specification
        if "-" not in range_spec:
            raise ValueError("Range must include '-' character")
            
        parts = range_spec.split("-")
        if len(parts) != 2:
            raise ValueError("Range must have format 'start-end'")
            
        start_str, end_str = parts
        
        # Handle different range formats
        if start_str and end_str:  # "start-end"
            try:
                start = int(start_str)
                end = int(end_str) + 1  # Make end inclusive
            except ValueError:
                raise ValueError("Range values must be integers")
                
            if start < 0 or end <= 0 or start >= content_length:
                raise ValueError("Range values out of bounds")
                
            if start >= end:
                raise ValueError("Range start must be less than end")
                
        elif start_str:  # "start-" (from start to end)
            try:
                start = int(start_str)
            except ValueError:
                raise ValueError("Range start must be an integer")
                
            if start < 0 or start >= content_length:
                raise ValueError("Range start out of bounds")
                
            end = content_length
            
        elif end_str:  # "-end" (last N bytes)
            try:
                last_n = int(end_str)
            except ValueError:
                raise ValueError("Range end must be an integer")
                
            if last_n <= 0:
                raise ValueError("Range end must be positive")
                
            start = max(0, content_length - last_n)
            end = content_length
            
        else:
            raise ValueError("Range must specify at least start or end")
            
        return start, min(end, content_length)
        
    def is_sensitive_resource(self, uri: str) -> bool:
        """
        Determine if a resource is sensitive and requires elevated consent.
        
        Args:
            uri: Resource URI
            
        Returns:
            bool: True if the resource is sensitive
        """
        # Check if the resource is in a sensitive category
        sensitive_patterns = [
            "/config/",
            "/private/",
            "/security/",
            "/credentials/",
            "/.env",
            "/secrets/"
        ]
        
        path = uri[len("resource://file/"):]
        
        for pattern in sensitive_patterns:
            if pattern in path:
                logger.debug(f"Resource {uri} identified as sensitive due to pattern: {pattern}")
                return True
                
        # Check file extensions for sensitive files
        sensitive_extensions = [
            ".key", ".pem", ".env", ".secret", ".password", ".credential"
        ]
        
        for ext in sensitive_extensions:
            if path.endswith(ext):
                logger.debug(f"Resource {uri} identified as sensitive due to extension: {ext}")
                return True
                
        return False
        
    def _should_use_compression(self, file_path: Path, explicit_compress: Optional[bool] = None) -> bool:
        """
        Determine if compression should be used for a file.
        
        Args:
            file_path: Path to the file
            explicit_compress: Explicitly request compression (overrides automatic detection)
            
        Returns:
            bool: True if compression should be used
        """
        # If compression is explicitly requested or disabled, honor that
        if explicit_compress is not None:
            return explicit_compress
            
        # Check if compression is enabled in config
        compression_config = self.streaming_config.get("compression", {})
        if not compression_config.get("enabled", False):
            return False
            
        # Check file size - only compress files larger than min_size
        min_size = compression_config.get("min_size", 10 * 1024)  # Default 10 KB
        if file_path.stat().st_size < min_size:
            logger.debug(f"File {file_path} too small for compression ({file_path.stat().st_size} bytes)")
            return False
            
        # Check file type - don't compress already compressed formats
        mime_type, _ = guess_type(str(file_path))
        excluded_types = compression_config.get("exclude_types", [])
        
        if mime_type and mime_type in excluded_types:
            logger.debug(f"File {file_path} has excluded MIME type {mime_type}, skipping compression")
            return False
            
        return True
        
    def _compress_content(self, content: str, compression_info: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Compress content using the specified algorithm.
        
        Args:
            content: Content to compress
            compression_info: Compression configuration
            
        Returns:
            Tuple[str, Dict[str, Any]]: Compressed content and compression statistics
        """
        if not content:
            return content, {"algorithm": None, "original_size": 0, "compressed_size": 0, "ratio": 1.0}
            
        algorithm = compression_info.get("algorithm", "gzip")
        level = compression_info.get("level", 6)
        original_size = len(content.encode('utf-8'))
        
        try:
            if algorithm == "gzip":
                compressed = gzip.compress(content.encode('utf-8'), compresslevel=level)
            elif algorithm == "zlib":
                compressed = zlib.compress(content.encode('utf-8'), level=level)
            else:
                logger.warning(f"Unknown compression algorithm: {algorithm}, using gzip")
                compressed = gzip.compress(content.encode('utf-8'), compresslevel=level)
                
            compressed_size = len(compressed)
            ratio = compressed_size / original_size if original_size > 0 else 1.0
            
            # Convert back to base64 string for transmission
            import base64
            compressed_b64 = base64.b64encode(compressed).decode('ascii')
            
            stats = {
                "algorithm": algorithm,
                "original_size": original_size,
                "compressed_size": compressed_size,
                "ratio": ratio,
                "encoding": "base64"
            }
            
            logger.debug(f"Compressed content: {original_size} -> {compressed_size} bytes (ratio: {ratio:.2f})")
            return compressed_b64, stats
            
        except Exception as e:
            logger.error(f"Compression error: {str(e)}, returning uncompressed content")
            return content, {"algorithm": None, "error": str(e)}