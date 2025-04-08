#!/bin/bash

# Stop MCP Stack
# This script stops all components of the MCP stack

echo "Stopping MCP Stack..."

# Stop MCP Server
echo "Stopping MCP Server..."
pkill -f "uvicorn enhanced_mcp_server:app" || echo "MCP Server not running"

# Stop MCP Adapter
echo "Stopping MCP Adapter..."
pkill -f "python3 librechat_mcp_adapter.py" || echo "MCP Adapter not running"

echo "MCP Stack stopped successfully!"
