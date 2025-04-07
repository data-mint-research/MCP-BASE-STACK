# MCP-BASE-STACK Maintenance Guide

This document outlines procedures for maintaining the MCP-BASE-STACK over time, including updates, monitoring, and troubleshooting.

## 1. Knowledge Graph Maintenance

### Updating the Knowledge Graph

The Knowledge Graph serves as the Single Source of Truth for the entire stack. Regular maintenance ensures it accurately reflects the system state:

```bash
# Update the Knowledge Graph manually
python3 core/kg/scripts/update_knowledge_graph.py

# View current graph statistics
cat core/kg/docs/graph_stats.txt

# Visualize the current graph (requires matplotlib)
python3 core/kg/scripts/visualize_graph.py  # (create this script if needed)
```

### Registering New Features
When implementing new features or modifications:

```bash
# Before implementation
python3 core/kg/scripts/register_feature.py --name "Feature Name" \
  --description "Feature description" \
  --owner "Engineer Name"

# After completion
python3 core/kg/scripts/update_feature.py --name "Feature Name" --status "completed"
```

## 2. Updating Stack Components

### Updating LibreChat
To update the LibreChat application:

```bash
cd services/librechat
docker compose down
git pull origin main
docker compose pull
docker compose up -d
```

After updating, verify your custom configuration:
- Check that librechat.yaml is still present
- If the update overwrote it, restore from your backup or recreate it
- Verify that custom endpoints still appear in the UI

### Updating LLM Server (formerly Ollama)
To update the LLM server:

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

### Updating Models
Periodically check for new versions of models:

```bash
# Update Mistral to latest version
docker exec ollama ollama pull mistral

# Update DeepSeek Coder to specific version
docker exec ollama ollama pull deepseek-coder:6.7b
```

### Updating MCP Server
To update the MCP server code:

```bash
# Stop the current server
kill $(cat mcp_server.pid)

# Update the code

# Restart the server
bash scripts/deployment/start_mcp_server.sh
```

## 3. Monitoring and Logging

### Viewing Logs
```bash
# LibreChat logs
cd services/librechat
docker compose logs -f
# or for a specific service
docker compose logs -f api

# LLM Server logs
docker logs -f ollama

# MCP Server logs
tail -f mcp_server.log
tail -f mcp_debug.log
```

### Health Checks
Run periodic health checks to ensure all components are functioning:

```bash
bash scripts/maintenance/verify_stack_health.sh
```

## 4. Resource Management

### GPU Monitoring
Monitor GPU usage with:

```bash
nvidia-smi
# or for continuous monitoring
watch -n 1 nvidia-smi
```

### Managing Resources
When not actively using the stack, you can stop components to free resources:

```bash
# Stop LLM Server (frees GPU memory)
docker stop ollama

# Stop LibreChat stack
cd services/librechat
docker compose down

# Stop MCP Server
kill $(cat mcp_server.pid)
```

To restart the complete stack, use the mcp.sh script:

```bash
./mcp.sh restart
```

## 5. Data Backup

### Backing up LibreChat Data
Back up the MongoDB data for conversation history:

```bash
# Create a backup directory
mkdir -p backups/$(date +%Y%m%d)

# Backup MongoDB data
docker exec chat-mongodb mongodump --out /tmp/mongo-backup
docker cp chat-mongodb:/tmp/mongo-backup backups/$(date +%Y%m%d)/mongo-backup
```

### Backing up Knowledge Graph
Regularly back up the Knowledge Graph data:

```bash
cp -r core/kg/data backups/$(date +%Y%m%d)/kg-data
```

## 6. Troubleshooting

### Common Issues and Resolutions

#### LibreChat can't connect to LLM Server
Check network connectivity:

```bash
docker exec LibreChat ping -c 3 ollama
```

#### Models not loading in LLM Server
Verify model files:

```bash
docker exec ollama ls -la /root/.ollama/models
```

#### MCP Server fails to start
Check for port conflicts:

```bash
ss -tln | grep 8000
```

#### GPU not accessible in container
Verify Docker GPU runtime:

```bash
docker run --rm --gpus=all nvidia/cuda:11.8.0-base nvidia-smi