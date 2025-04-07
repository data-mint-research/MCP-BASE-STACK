# MCP-BASE-STACK Documentation

Welcome to the MCP-BASE-STACK documentation. This repository contains comprehensive documentation for setting up, maintaining, and troubleshooting the MCP-BASE-STACK.

## Quick Start

The MCP-BASE-STACK is a comprehensive environment for running large language models (LLMs) with the following components:

- **LibreChat**: Web interface for interacting with LLMs
- **Ollama**: Local LLM server for running models
- **MCP Server**: Model Context Protocol server for enhanced model capabilities
- **Knowledge Graph**: Source of truth for system components and relationships

## Documentation Structure

This documentation is organized into the following sections:

### Knowledge Graph

Documentation related to the Knowledge Graph, which serves as the single source of truth for the system:

- [Schema](knowledge-graph/schema.md): Node types, edges, and attributes
- [Code Generation](knowledge-graph/code-generation.md): How the graph maps to real code
- [Examples](knowledge-graph/examples.md): Small graph examples and what they generate
- [Usage Guide](knowledge-graph/usage-guide.md): How to query, edit, and extend the graph

### Tutorials

Step-by-step guides for common tasks:

- [Create Agent](tutorials/create-agent.md): How to create a new agent
- [Add Function](tutorials/add-function.md): How to add new functionality
- [Generate Code](tutorials/generate-code.md): How to generate code from the Knowledge Graph
- [Run End-to-End](tutorials/run-end-to-end.md): Complete end-to-end workflow
- [Update Components](tutorials/update-components.md): How to update stack components
- [Data Backup](tutorials/data-backup.md): How to back up and restore data

### Troubleshooting

Known issues and how to fix them:

- [Code Not Updating](troubleshooting/code-not-updating.md): Issues with code generation
- [Broken Links](troubleshooting/broken-links.md): Fixing broken links in the Knowledge Graph
- [Ollama Errors](troubleshooting/ollama-errors.md): Common Ollama issues and solutions
- [Agent Misbehavior](troubleshooting/agent-misbehavior.md): Debugging agent behavior
- [Monitoring and Logging](troubleshooting/monitoring-and-logging.md): How to monitor the system and access logs
- [Resource Management](troubleshooting/resource-management.md): Managing system resources
- [Common Issues](troubleshooting/common-issues.md): Frequently encountered issues and their solutions

### Conventions

Project-wide standards and guidelines:

- [Style Guide](conventions/style-guide.md): Naming, casing, structure (graph + code)
- [Coding Conventions](conventions/coding-conventions.md): For generated and custom code
- [Graph Guidelines](conventions/graph-guidelines.md): How to model logic correctly in the graph
- [Review Checklist](conventions/review-checklist.md): What to check before committing changes

## System Architecture

The MCP-BASE-STACK consists of the following components:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  LibreChat  │────▶│  MCP Server │────▶│    Ollama   │
│  (Frontend) │     │ (Middleware)│     │  (LLM Host) │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────────────────────────────────────────┐
│               Knowledge Graph                    │
│  (Source of Truth for System Configuration)      │
└─────────────────────────────────────────────────┘
```

## Getting Started

To get started with the MCP-BASE-STACK:

1. Ensure you have Docker and NVIDIA drivers installed
2. Clone the repository
3. Run the setup script
4. Access LibreChat at http://localhost:3080

For detailed setup instructions, see the [Run End-to-End](tutorials/run-end-to-end.md) tutorial.

## Contributing

When contributing to the documentation:

1. Follow the [Style Guide](conventions/style-guide.md)
2. Update the Knowledge Graph when adding new components
3. Include examples for new functionality
4. Add tests for new features

## Support

If you encounter issues:

1. Check the [Troubleshooting](troubleshooting/common-issues.md) section
2. Run the health check script: `./verify_stack_health.sh`
3. Review the logs as described in [Monitoring and Logging](troubleshooting/monitoring-and-logging.md)