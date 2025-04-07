#!/bin/bash
echo "Restarting MCP-BASE-STACK..."

# Update Knowledge Graph before restart
python3 kg/scripts/update_knowledge_graph.py

# Restart LibreChat
echo "Restarting LibreChat..."
cd LibreChat
docker compose restart
cd ..

# Restart Ollama
echo "Restarting Ollama..."
docker restart ollama

# Restart MCP Server
echo "Restarting MCP Server..."
if [ -f mcp_server.pid ]; then
  echo "Stopping existing MCP Server..."
  kill $(cat mcp_server.pid)
  rm mcp_server.pid
fi
./start_mcp_server.sh

# Verify stack health
echo "Verifying stack health..."
./verify_stack_health.sh

echo "Stack restart completed."