# Updating Stack Components

This guide provides step-by-step instructions for updating the various components of the MCP-BASE-STACK.

## Updating LibreChat

To update the LibreChat application:

```bash
cd LibreChat
docker compose down
git pull origin main
docker compose pull
docker compose up -d
```

After updating, verify your custom configuration:
- Check that librechat.yaml is still present
- If the update overwrote it, restore from your backup or recreate it
- Verify that custom endpoints still appear in the UI

## Updating Ollama

To update the Ollama server:

```bash
# Stop the current container
docker stop ollama
docker rm ollama

# Pull the latest image
docker pull ollama/ollama:latest

# Run the container again with the same settings
docker run -d --gpus=all --name ollama \
  --network LibreChat_default \
  -v ollama:/root/.ollama \
  -p 11434:11434 \
  ollama/ollama:latest
```

## Updating Models

Periodically check for new versions of models:

```bash
# Update Mistral to latest version
docker exec ollama ollama pull mistral

# Update DeepSeek Coder to specific version
docker exec ollama ollama pull deepseek-coder:6.7b
```

## Updating MCP Server

To update the MCP server code:

```bash
# Stop the current server
kill $(cat mcp_server.pid)

# Update the code (e.g., edit mcp_server.py)

# Restart the server
./start-mcp-server.sh
```

## Best Practices for Updates

- Always back up your configuration files before updating
- Test updates in a staging environment if possible
- Monitor logs after updates to catch any issues early
- Keep a record of the versions you're updating from and to
- Schedule updates during low-usage periods