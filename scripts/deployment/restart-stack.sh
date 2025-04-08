#!/bin/bash
echo "Restarting MCP-BASE-STACK..."

# Update Knowledge Graph before restart
python3 core/kg/scripts/update_knowledge_graph.py

# Restart all services using the root docker-compose.yml
echo "Restarting all services..."
docker compose up -d

# Verify stack health
echo "Verifying stack health..."
./scripts/utils/validation/verify-stack-health.sh

echo "Stack restart completed."