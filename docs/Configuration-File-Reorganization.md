# Configuration File Reorganization

This document describes the reorganization of configuration files in the MCP-BASE-STACK project.

## Overview

The configuration file reorganization was performed to:

1. Centralize all configuration files in the `config` directory
2. Organize configuration files by type and purpose
3. Ensure consistency in configuration file locations
4. Improve maintainability and discoverability of configuration files

## Directory Structure

The reorganized configuration files follow this directory structure:

```
config/
  environments/           # Environment-specific configuration files
    dev.yaml              # Development environment configuration
    test.yaml             # Test environment configuration
    prod.yaml             # Production environment configuration
  deploy/                 # Deployment configuration files
    docker-compose.yml    # Main Docker Compose file
    docker-compose.dev.yml # Development Docker Compose file
    model-volumes.yml     # Model volumes configuration
  services/               # Service-specific configuration files
    librechat/            # LibreChat service configuration
      docker-compose.yml  # LibreChat Docker Compose file
      librechat.yaml      # LibreChat service configuration
    llm-server/           # LLM Server configuration
      docker-compose.yml  # LLM Server Docker Compose file
      server.yaml         # LLM Server configuration
    mcp-server/           # MCP Server configuration
      docker-compose.yml  # MCP Server Docker Compose file
      README.md           # MCP Server configuration documentation
  lint/                   # Linting and code quality configuration
    markdownlint.yaml     # Markdown linting configuration
    pre-commit-config.yaml # Pre-commit hooks configuration
    yamllint.yaml         # YAML linting configuration
  pytest.ini              # PyTest configuration
```

## Changes Made

1. Created `config/environments/` directory with environment-specific YAML files:
   - `dev.yaml`: Development environment configuration
   - `test.yaml`: Test environment configuration
   - `prod.yaml`: Production environment configuration

2. Moved linting and code quality configuration files to `config/lint/`:
   - `.markdownlint.yaml` → `config/lint/markdownlint.yaml`
   - `.pre-commit-config.yaml` → `config/lint/pre-commit-config.yaml`
   - `.yamllint.yaml` → `config/lint/yamllint.yaml`

3. Moved testing configuration files to `config/`:
   - `pytest.ini` → `config/pytest.ini`

4. Ensured service-specific configuration files are in `config/services/`:
   - Copied `services/mcp-server/config/README.md` to `config/services/mcp-server/README.md`

## References to Configuration Files

The following files may contain references to the relocated configuration files:

1. Pre-commit configuration references to linting configuration files
2. CI/CD pipeline configurations
3. Documentation references
4. Code that loads configuration files

## Future Work

1. Update all references to the relocated configuration files
2. Remove duplicate configuration files once all references are updated
3. Implement automated checks to ensure configuration files are in the correct locations