#!/bin/bash
echo "Starting MCP Server..."

# Check if the MCP server is already running in Docker
if docker ps | grep -q mcp-server; then
  echo "MCP Server is already running in Docker. Use docker compose commands to manage it."
  exit 0
fi

# If we're here, we're starting the MCP server directly (not through Docker)
cd services/mcp-server
nohup python3 -m uvicorn src.app:app --host 0.0.0.0 --port 8000 > ../../mcp_server.log 2>&1 &
echo $! > ../../mcp_server.pid
cd ../..
echo "MCP Server started with PID $(cat mcp_server.pid)"