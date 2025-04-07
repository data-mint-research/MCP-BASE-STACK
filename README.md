# MCP-BASE-STACK

MCP-BASE-STACK is a comprehensive environment for running large language models (LLMs) with the following components:

- **LibreChat**: Web interface for interacting with LLMs
- **Ollama**: Local LLM server for running models
- **MCP Server**: Model Context Protocol server for enhanced model capabilities
- **Knowledge Graph**: Source of truth for system components and relationships

## Documentation

Comprehensive documentation is available in the `docs/` directory:

- [Knowledge Graph Documentation](docs/knowledge-graph/): Schema, code generation, examples, and usage guide
- [Tutorials](docs/tutorials/): Step-by-step guides for common tasks
- [Troubleshooting](docs/troubleshooting/): Known issues and how to fix them
- [Conventions](docs/conventions/): Project-wide standards and guidelines

## Test Structure

The test suite is organized in the `tests/` directory:

- Unit tests for individual components
- Integration tests for component interactions
- Agent tests for specific scenarios
- End-to-end tests for realistic user flows
- Performance tests for load and latency measurements
- Regression tests for detecting changes

## Getting Started

To get started with the MCP-BASE-STACK:

1. Ensure you have Docker and NVIDIA drivers installed
2. Clone the repository
3. Run the setup script
4. Access LibreChat at http://localhost:3080

## System Architecture

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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2025 MINT-RESEARCH