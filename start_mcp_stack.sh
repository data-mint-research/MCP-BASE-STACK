#!/bin/bash

# Start MCP Stack
# This script starts all components of the MCP stack

# Set environment variables
export MCP_SERVER_ID=serj-agent
export LOG_LEVEL=INFO
export SERVER_HOST=0.0.0.0
export SERVER_PORT=8000
export MCP_ADAPTER_PORT=8001
export OLLAMA_API_HOST=${OLLAMA_API_HOST:-http://localhost:11434}

# Function to check if a port is in use
port_in_use() {
  lsof -i:"$1" >/dev/null 2>&1
  return $?
}

# Function to start a component
start_component() {
  local name=$1
  local command=$2
  local port=$3
  
  echo "Starting $name..."
  
  if port_in_use "$port"; then
    echo "Port $port is already in use. $name may already be running."
  else
    # Start the component in the background
    eval "$command" &
    
    # Wait for the port to be available
    for i in {1..10}; do
      if port_in_use "$port"; then
        echo "$name started successfully on port $port."
        break
      fi
      
      if [ $i -eq 10 ]; then
        echo "Failed to start $name on port $port."
        exit 1
      fi
      
      echo "Waiting for $name to start..."
      sleep 1
    done
  fi
}

# Create log directory if it doesn't exist
mkdir -p logs

# Start MCP Server
start_component "MCP Server" "python3 -m uvicorn mcp_server:app --host $SERVER_HOST --port $SERVER_PORT > logs/mcp_server.log 2>&1" "$SERVER_PORT"

# Start MCP Adapter
start_component "MCP Adapter" "python3 librechat_mcp_adapter.py > logs/mcp_adapter.log 2>&1" "$MCP_ADAPTER_PORT"

echo "MCP Stack started successfully!"
echo "MCP Server running on http://$SERVER_HOST:$SERVER_PORT"
echo "MCP Adapter running on http://$SERVER_HOST:$MCP_ADAPTER_PORT"
echo "LibreChat can be configured to use the MCP Adapter at http://localhost:$MCP_ADAPTER_PORT"
echo ""
echo "To stop the MCP Stack, run: ./stop_mcp_stack.sh"
