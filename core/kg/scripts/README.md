# Knowledge Graph Scripts

## Overview

This directory contains scripts for managing and updating the knowledge graph, which serves as the single source of truth for the MCP-BASE-STACK project. These scripts handle the creation, modification, and querying of the knowledge graph to ensure it accurately reflects the current state of the system.

## Scripts

### record_logging_system.py

Records the logging system components in the knowledge graph. This script adds the logging system components (LogDirectoryManager, LoggingConfig) to the knowledge graph, along with their relationships and metadata about the standardized log directory structure and naming conventions.

Features:
- Adds or updates the logging system component in the knowledge graph
- Records logging modules and their relationships
- Adds documentation files related to the logging system
- Records test files that verify the logging system
- Adds metadata about directory structure and naming conventions
- Connects the logging system to existing components that use it
- Records migration decisions related to the logging system

Usage:
```bash
python record_logging_system.py
```

### setup_knowledge_graph.py

Sets up the initial knowledge graph structure. This script creates the basic nodes and relationships that form the foundation of the knowledge graph.

Features:
- Creates the knowledge graph files if they don't exist
- Establishes the basic node types and relationships
- Sets up the project structure in the knowledge graph
- Initializes quality metrics nodes
- Creates component nodes for core system components

Usage:
```bash
python setup_knowledge_graph.py
```

### update_knowledge_graph.py

Updates the knowledge graph based on the current implementation status. This script is used to keep the knowledge graph in sync with the actual state of the system.

Features:
- Updates component status based on file existence
- Updates quality metrics based on quality reports
- Updates directory structure information
- Records migration decisions
- Maintains relationships between components

Usage:
```bash
python update_knowledge_graph.py
```

## Knowledge Graph Structure

The knowledge graph is stored in two formats:
- GraphML format (`core/kg/data/knowledge_graph.graphml`): Used for visualization and programmatic access
- Turtle format (`core/kg/data/knowledge_graph.ttl`): Used for semantic queries and reasoning

The knowledge graph contains the following types of nodes:
- Components: Represent system components like services, models, and resources
- Directories: Represent filesystem directories in the project
- Files: Represent individual files in the project
- Metadata: Contain information about naming conventions, directory structures, etc.
- Decisions: Record architectural and implementation decisions
- Quality Metrics: Track code quality, documentation coverage, etc.

## Integration with Other Systems

The knowledge graph scripts are integrated with:

1. **Quality Enforcement System**: Quality metrics are recorded in the knowledge graph
2. **Deployment Scripts**: Component status is updated during deployment
3. **Maintenance Scripts**: System health information is recorded in the knowledge graph
4. **CI/CD Pipeline**: The knowledge graph is updated as part of the CI/CD process

## Best Practices

When working with the knowledge graph scripts:

1. Always run `update_knowledge_graph.py` after making significant changes to the system
2. Use the knowledge graph as the source of truth for system state
3. Create specialized scripts (like `record_logging_system.py`) for recording specific subsystems
4. Ensure that all components are properly represented in the knowledge graph
5. Use the knowledge graph for decision-making and system understanding

## Extending the Knowledge Graph

To extend the knowledge graph with new types of information:

1. Create a new script in this directory that follows the pattern of existing scripts
2. Use the `load_knowledge_graph()` and `save_knowledge_graph()` functions for consistency
3. Add new node types and relationships as needed
4. Update existing nodes with new information
5. Document the changes in the knowledge graph schema

Example of a new script:
```python
#!/usr/bin/env python3
"""
Record new component in the knowledge graph.

This script adds a new component to the knowledge graph, along with its
relationships and metadata.
"""

import os
import sys
from datetime import datetime

# Add the project directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

# Load the knowledge graph
nx_graph, rdf_graph = load_knowledge_graph()

# Add new component
# ...

# Save the knowledge graph
save_knowledge_graph(nx_graph, rdf_graph)