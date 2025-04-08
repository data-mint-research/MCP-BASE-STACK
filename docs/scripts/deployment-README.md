# Deployment Scripts

## Overview

This directory contains scripts for deploying and managing the MCP-BASE-STACK components. These scripts handle the deployment, configuration, and management of various services and ensure that the knowledge graph is updated accordingly.

## Scripts

### register-new-features.sh

Registers new features in the knowledge graph when they are deployed. This script ensures that the knowledge graph accurately reflects the current state of the system.

Features:
- Adds new feature nodes to the knowledge graph
- Updates existing feature nodes with new information
- Establishes relationships between features and components
- Records deployment timestamps and metadata

Usage:
```bash
./register-new-features.sh [feature_name] [feature_description]
```

### restart-stack.sh

Safely restarts the entire MCP-BASE-STACK or specific components. This script ensures that services are restarted in the correct order to maintain system integrity.

Features:
- Graceful shutdown of services
- Dependency-aware restart sequence
- Health checks after restart
- Rollback capability if restart fails

Usage:
```bash
# Restart the entire stack
./restart-stack.sh

# Restart specific components
./restart-stack.sh --components "librechat,mcp_server"

# Restart with verbose logging
./restart-stack.sh --verbose
```

### start-mcp-server.sh

Starts the MCP server with the appropriate configuration. This script handles environment setup, dependency checks, and service initialization.

Features:
- Configures environment variables
- Verifies dependencies are available
- Initializes the MCP server
- Monitors startup process
- Registers the server in the knowledge graph

Usage:
```bash
./start-mcp-server.sh [--config path/to/config.yaml]
```

### update_kg_deployment.py

Updates the knowledge graph with deployment information. This script records deployment events, service configurations, and system state changes.

Features:
- Records deployment timestamps
- Updates component status in the knowledge graph
- Tracks configuration changes
- Maintains deployment history

Usage:
```bash
python update_kg_deployment.py --component [component_name] --status [status]
```

### update_kg_root.py

Updates the root nodes of the knowledge graph. This script is used to make fundamental changes to the knowledge graph structure.

Features:
- Updates root node properties
- Manages top-level relationships
- Ensures knowledge graph integrity
- Handles schema migrations

Usage:
```bash
python update_kg_root.py
```

### update-ollama-references.sh

Updates references to Ollama models throughout the system. This script ensures that model references are consistent and up-to-date.

Features:
- Updates configuration files
- Modifies service definitions
- Updates documentation references
- Ensures consistency across the system

Usage:
```bash
./update-ollama-references.sh [old_reference] [new_reference]
```

## Deployment Workflow

The typical deployment workflow using these scripts is:

1. Update the knowledge graph root structure if needed:
   ```bash
   python update_kg_root.py
   ```

2. Start or restart the MCP server:
   ```bash
   ./start-mcp-server.sh
   ```

3. Register new features in the knowledge graph:
   ```bash
   ./register-new-features.sh "Feature Name" "Feature Description"
   ```

4. Update the knowledge graph with deployment information:
   ```bash
   python update_kg_deployment.py --component "component_name" --status "deployed"
   ```

5. Restart the stack if needed:
   ```bash
   ./restart-stack.sh
   ```

## Integration with CI/CD

These deployment scripts can be integrated into CI/CD pipelines to automate the deployment process. Example integration in a GitHub Actions workflow:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Update knowledge graph
        run: python scripts/deployment/update_kg_deployment.py --component "mcp_server" --status "deploying"
      - name: Start MCP server
        run: ./scripts/deployment/start-mcp-server.sh
      - name: Register new features
        run: ./scripts/deployment/register-new-features.sh "New Feature" "Description of new feature"
      - name: Update deployment status
        run: python scripts/deployment/update_kg_deployment.py --component "mcp_server" --status "deployed"
```

## Best Practices

When using these deployment scripts:

1. Always update the knowledge graph before and after deployment
2. Use the restart script rather than manually stopping and starting services
3. Test deployments in a staging environment before applying to production
4. Monitor the system after deployment to ensure everything is functioning correctly
5. Keep deployment scripts up-to-date with system changes