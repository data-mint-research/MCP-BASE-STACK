#!/bin/bash
echo "=== VERIFYING LIBRECHAT MODEL INTEGRATION ===" | tee librechat-model-integration.txt
echo "$(date)" | tee -a librechat-model-integration.txt
echo "" | tee -a librechat-model-integration.txt

# Check if librechat.yaml is mounted in the container
echo "=== Checking librechat.yaml in container ===" | tee -a librechat-model-integration.txt
docker exec librechat-api-1 ls -la /app/librechat.yaml 2>/dev/null | tee -a librechat-model-integration.txt
echo "" | tee -a librechat-model-integration.txt

# View the actual config to verify model settings
echo "=== Examining model configuration ===" | tee -a librechat-model-integration.txt
docker exec librechat-api-1 cat /app/librechat.yaml 2>/dev/null | tee -a librechat-model-integration.txt
echo "" | tee -a librechat-model-integration.txt

# Check container logs for any configuration loading messages
echo "=== Checking container logs for config loading ===" | tee -a librechat-model-integration.txt
docker logs librechat-api-1 2>&1 | grep -i "custom" | head -n 10 | tee -a librechat-model-integration.txt
echo "" | tee -a librechat-model-integration.txt

# Verify Mistral direct access configuration
echo "=== Verifying Mistral configuration ===" | tee -a librechat-model-integration.txt
docker exec librechat-api-1 env | grep -E "MISTRAL" | tee -a librechat-model-integration.txt
echo "" | tee -a librechat-model-integration.txt

# Verify MCP Server connectivity (for DeepSeek Coder access)
echo "=== Verifying MCP Server connectivity for DeepSeek Coder ===" | tee -a librechat-model-integration.txt
curl -s http://localhost:8000/debug/health | tee -a librechat-model-integration.txt
echo "" | tee -a librechat-model-integration.txt
curl -s http://localhost:8000/debug/ollama-status | tee -a librechat-model-integration.txt
echo "" | tee -a librechat-model-integration.txt

# Test connection from LibreChat to Ollama (for Mistral)
echo "=== Testing LibreChat to Ollama connection (for Mistral) ===" | tee -a librechat-model-integration.txt
if docker exec librechat-api-1 curl -s http://ollama:11434/api/tags 2>/dev/null | grep -q "models"; then
  echo "LibreChat can successfully connect to Ollama" | tee -a librechat-model-integration.txt
else
  echo "LibreChat cannot connect to Ollama" | tee -a librechat-model-integration.txt
fi
echo "" | tee -a librechat-model-integration.txt

# Test connection from LibreChat to MCP Server (if applicable)
echo "=== Testing LibreChat to MCP Server connection (for DeepSeek via MCP) ===" | tee -a librechat-model-integration.txt
# This assumes host.docker.internal resolves to the host in your Docker setup
if docker exec librechat-api-1 curl -s http://host.docker.internal:8000/debug/health 2>/dev/null | grep -q "healthy"; then
  echo "LibreChat can successfully connect to MCP Server" | tee -a librechat-model-integration.txt
else
  echo "LibreChat cannot connect to MCP Server" | tee -a librechat-model-integration.txt
fi
echo "" | tee -a librechat-model-integration.txt

echo "=== Integration Architecture Summary ===" | tee -a librechat-model-integration.txt
echo "1. Mistral: Direct integration via Ollama" | tee -a librechat-model-integration.txt
echo "2. DeepSeek Coder: Accessed through MCP Server, which connects to Ollama" | tee -a librechat-model-integration.txt
echo "" | tee -a librechat-model-integration.txt

echo "Verification completed - see librechat-model-integration.txt for results"
echo "IMPORTANT: For complete verification, open http://localhost:3080 in a browser"
echo "and check that Mistral appears in the model dropdown menu"
echo "Then test sending coding-related queries to the MCP Server endpoint"