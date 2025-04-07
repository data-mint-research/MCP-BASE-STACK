# MCP-BASE-STACK

A service-based architecture for managing and deploying AI models and services.

## Directory Structure

- `services/`: Contains service-specific code and configuration
  - `librechat/`: LibreChat service
  - `llm-server/`: LLM server (renamed from Ollama)
  - `mcp-server/`: MCP Server for orchestrating services
- `config/`: Contains configuration files
  - `environments/`: Environment-specific configuration
  - `models/`: Model-related configuration
- `data/`: Contains data files
  - `models/`: Model files organized by provider
- `deploy/`: Contains deployment configuration
  - `volumes/`: Volume configuration
- `scripts/`: Contains utility scripts
  - `setup/`: Setup scripts
  - `deployment/`: Deployment scripts
  - `maintenance/`: Maintenance scripts
- `core/`: Contains core components
  - `kg/`: Knowledge Graph
- `docs/`: Contains documentation
- `tests/`: Contains test files

## Getting Started

### Prerequisites

- Docker
- Docker Compose
- Python 3.10 or higher

### Setup

```bash
./mcp.sh setup
```

### Starting the Stack

```bash
./mcp.sh start
```

### Checking Status

```bash
./mcp.sh status
```

### Stopping the Stack

```bash
./mcp.sh stop
```

### Development Mode

```bash
./mcp.sh dev
```

## Services

- **LibreChat**: Web interface for interacting with AI models
- **LLM Server**: Serves AI models (renamed from Ollama)
- **MCP Server**: Orchestrates services and provides API endpoints

## Configuration

Configuration files are located in the `config/` directory:

- `environments/development.yaml`: Development environment configuration
- `environments/production.yaml`: Production environment configuration
- `models/registry.yaml`: Model registry configuration

## Deployment

Deployment files are located in the `deploy/` directory:

- `docker-compose.yml`: Main Docker Compose file
- `docker-compose.dev.yml`: Development Docker Compose file
- `volumes/model-volumes.yml`: Model volumes configuration

## Documentation

Documentation is located in the `docs/` directory.

## License

This project is licensed under the terms of the LICENSE file included in this repository.
## File Update Hooks

This repository includes Git hooks that automatically update README.md, .gitignore, and LICENSE files before every commit.

To install the hooks, run:

```bash
./install-file-update-hooks.sh
```

## Maintenance

Last updated: 2025-04-07 16:26:08
