# Knowledge Graph Usage Guide

The Knowledge Graph serves as the Single Source of Truth for the entire MCP-BASE-STACK. This guide explains how to maintain, query, and extend the graph.

## Updating the Knowledge Graph

Regular maintenance ensures the Knowledge Graph accurately reflects the system state:

```bash
# Update the Knowledge Graph manually
python3 kg/scripts/update_knowledge_graph.py

# View current graph statistics
cat kg/docs/graph_stats.txt

# Visualize the current graph (requires matplotlib)
python3 kg/scripts/visualize_graph.py  # (create this script if needed)
```

## Registering New Features

When implementing new features or modifications:

```bash
# Before implementation
python3 kg/scripts/register_feature.py --name "Feature Name" \
  --description "Feature description" \
  --owner "Engineer Name"

# After completion
python3 kg/scripts/update_feature.py --name "Feature Name" --status "completed"
```

## Querying the Knowledge Graph

The Knowledge Graph can be queried to understand relationships between components and track the status of features. This section will be expanded with specific query examples.

## Extending the Knowledge Graph

To extend the Knowledge Graph with new component types or relationships, modify the following files:
- `kg/scripts/update_knowledge_graph.py`: Add new component checks
- `kg/scripts/register_feature.py`: For new feature types
- `kg/scripts/update_feature.py`: For new status types

The Knowledge Graph is designed to be extensible to accommodate the evolving needs of the project.