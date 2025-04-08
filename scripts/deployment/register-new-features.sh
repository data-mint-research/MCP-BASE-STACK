#!/bin/bash

# Register Documentation Structure feature
echo "Registering Documentation Structure feature..."
python3 core/kg/scripts/register_feature.py --name "Documentation Structure" \
  --description "Organized documentation structure with knowledge graph, tutorials, troubleshooting, and conventions" \
  --owner "MCP-Deployment-Engineer"

# Register Test Structure feature
echo "Registering Test Structure feature..."
python3 core/kg/scripts/register_feature.py --name "Test Structure" \
  --description "Comprehensive test structure for unit, integration, agent, e2e, performance, and regression tests" \
  --owner "MCP-Deployment-Engineer"

# Update the Knowledge Graph
echo "Updating Knowledge Graph..."
python3 core/kg/scripts/update_knowledge_graph.py

# Mark features as completed
echo "Marking features as completed..."
python3 core/kg/scripts/update_feature.py --name "Documentation Structure" --status "completed"
python3 core/kg/scripts/update_feature.py --name "Test Structure" --status "completed"

echo "Features registered and Knowledge Graph updated successfully."