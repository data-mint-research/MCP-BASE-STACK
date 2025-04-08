# MCP-BASE-STACK Deployment

This directory contains deployment configuration files for the MCP-BASE-STACK services.

## Directory Structure

- `docker-compose.yml`: Main Docker Compose file for production deployment
- `docker-compose.dev.yml`: Docker Compose override file for development
- `volumes/`: Contains volume configuration files
  - `model-volumes.yml`: Configuration for model storage volumes

## Usage

### Production Deployment

```bash
cd deploy
docker-compose up -d
```

### Development Deployment

```bash
cd deploy
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

## Services

- `librechat`: LibreChat API service
- `mongodb`: MongoDB database for LibreChat
- `llm-server`: LLM server (renamed from Ollama)
- `mcp-server`: MCP Server for orchestrating services