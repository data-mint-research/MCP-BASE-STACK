# Model Integration Guide

This document provides instructions for integrating new models with LibreChat.

## Supported Models

The MCP-BASE-STACK currently supports the following models:

- **Mistral**: Mistral AI's 7B parameter model (7.2B, GGUF format, Q4_0 quantization)
- **DeepSeek Coder**: Code generation and completion model (6.7B, GGUF format, Q4_0 quantization)

## Integration Architecture

The stack uses two different integration approaches:

1. **Direct Integration**: Mistral is directly integrated with LibreChat via Ollama
2. **MCP Server Integration**: DeepSeek Coder is accessed through the MCP Server, which connects to Ollama

## Integration Steps

### 1. Add Model to Ollama

First, pull the model to Ollama:

```bash
docker exec -it ollama ollama pull mistral
# or
docker exec -it ollama ollama pull deepseek-coder:6.7b
```

### 2. Configure LibreChat

Update the LibreChat configuration in `services/librechat/config/librechat.yaml`:

```yaml
endpoints:
  custom:
    - # Using Ollama as a custom endpoint
      baseURL: "http://ollama:11434/api"
      models:
        default: ["mistral", "deepseek-coder"]
        available:
          - id: "mistral"
            name: "Mistral"
            description: "Mistral AI's 7B parameter model"
          - id: "deepseek-coder"
            name: "DeepSeek Coder"
            description: "Code generation and completion model"
      titleConvo: true
      titleModel: "mistral"
```

### 3. Update Model Registry

Add the model information to `config/models/registry.yaml`:

```yaml
registry:
  providers:
    mistral:
      name: Mistral AI
      description: Open-source large language models from Mistral AI
      models:
        mistral:
          name: Mistral
          versions:
            - version: latest
              description: Latest version of Mistral
              parameters:
                context_length: 8192
                model_type: text-generation
```

### 4. Configure MCP Server (if needed)

If using the MCP Server for model access, update the server configuration to include the new model:

```python
# In mcp_server.py
payload = {"model": "your-model-name", "prompt": llm_query}
```

## Testing Integration

1. Start the stack with `./mcp.sh start`
2. Open LibreChat in your browser at http://localhost:3080/
3. Select the new model from the model dropdown
4. Test with a sample prompt

## Verification

You can verify the model integration with these commands:

```bash
# Check if Ollama is running and has the models
curl -s http://localhost:11434/api/tags

# Check if LibreChat can access the models
curl -I http://localhost:3080/

# Check if MCP Server is healthy (for models accessed via MCP)
curl -s http://localhost:8000/debug/health
```

## Troubleshooting

If the model integration fails:

1. Check that the model is properly loaded in Ollama
2. Verify the LibreChat configuration has the correct model IDs
3. Ensure the MCP Server is running if using it for model access
4. Check the container logs for any errors