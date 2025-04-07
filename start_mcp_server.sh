#!/bin/bash
echo "Starting MCP Server..."
nohup python3 -m uvicorn mcp_server:app --host 0.0.0.0 --port 8000 > mcp_server.log 2>&1 &
echo $! > mcp_server.pid
echo "MCP Server started with PID $(cat mcp_server.pid)"