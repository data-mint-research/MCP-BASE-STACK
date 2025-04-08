# Integrating Ollama with LibreChat: Troubleshooting Guide

This document details the process of integrating Ollama with LibreChat, including the issues encountered and their solutions.

## Table of Contents
1. [Overview](#overview)
2. [Environment Setup](#environment-setup)
3. [Issue: Ollama Models Not Appearing](#issue-ollama-models-not-appearing)
4. [Solution: Adding a Dummy API Key](#solution-adding-a-dummy-api-key)
5. [Networking Considerations](#networking-considerations)
6. [Alternative Approaches](#alternative-approaches)
7. [Long-term Fixes](#long-term-fixes)

## Overview

LibreChat is a chat interface that supports multiple LLM backends, including custom endpoints. Ollama is a local LLM server that allows running various open-source models. This guide documents the integration of Ollama with LibreChat and the troubleshooting process.

## Environment Setup

Our environment consists of:
- LibreChat running in a Docker container
- Ollama running on the host machine (WSL2)
- MCP (Model Context Protocol) components for additional functionality

### Components:
- **LibreChat**: Chat interface with support for multiple LLM backends
- **Ollama**: Local LLM server running models like mistral:7b and deepseek-coder:6.7b
- **MCP Server**: Provides additional functionality through the Model Context Protocol
- **MCP Adapter**: Connects LibreChat to the MCP Server

## Issue: Ollama Models Not Appearing

Despite successful configuration and connection between LibreChat and Ollama, the Ollama models were not appearing in the LibreChat interface dropdown.

### Initial Configuration

```yaml
# Configuration version
version: 1.2.1

# Cache settings
cache: true

# Endpoints configuration
endpoints:
  # Custom endpoints configuration
  custom:
    - name: "Ollama"
      apiKey: ""  # No API key needed for Ollama
      baseURL: "http://host.docker.internal:11434"
      models:
        default: ["deepseek-coder:6.7b", "mistral:7b"]
        fetch: true  # Fetch available models from Ollama
      titleConvo: true
      titleModel: "mistral:7b"
```

### Diagnosis Steps

1. **Verified Ollama Server**: Confirmed Ollama was running correctly with the command:
   ```bash
   sudo -u ollama OLLAMA_HOST=0.0.0.0:11434 ollama serve
   ```

2. **Checked Network Connectivity**: Verified that the LibreChat container could connect to Ollama:
   ```bash
   docker exec LibreChat curl -s http://host.docker.internal:11434/api/tags
   ```
   Initially, this failed due to networking issues.

3. **Updated Network Configuration**: Changed the Ollama endpoint from `host.docker.internal` to the direct WSL2 IP address:
   ```bash
   docker exec LibreChat curl -s http://172.20.106.58:11434/api/tags
   ```
   This successfully returned the list of available models.

4. **Examined LibreChat Code**: Investigated how LibreChat processes custom endpoints by examining the code:
   ```javascript
   // From /app/api/server/services/Config/loadConfigEndpoints.js
   const customEndpoints = endpoints[EModelEndpoint.custom].filter(
     (endpoint) =>
       endpoint.baseURL &&
       endpoint.apiKey &&  // This requires a non-empty apiKey
       endpoint.name &&
       endpoint.models &&
       (endpoint.models.fetch || endpoint.models.default),
   );
   ```

5. **Identified Root Cause**: Discovered that LibreChat's code requires a non-empty `apiKey` for all custom endpoints, but our configuration had an empty string for Ollama (which doesn't require an API key).

## Solution: Adding a Dummy API Key

The solution was to add a dummy non-empty API key to the configuration:

```yaml
# Configuration version (updated)
version: 1.2.4

# Cache settings
cache: true

# Endpoints configuration
endpoints:
  # Custom endpoints configuration
  custom:
    - name: "Ollama"
      apiKey: "dummy-key"  # Adding a dummy key to pass the filter
      baseURL: "http://172.20.106.58:11434"
      models:
        default: ["deepseek-coder:6.7b", "mistral:7b"]
        fetch: true  # Fetch available models from Ollama
      titleConvo: true
      titleModel: "mistral:7b"
```

This allowed the Ollama endpoint to pass the filter in the LibreChat code, making the models appear in the dropdown. Since Ollama doesn't actually use the API key, this doesn't affect functionality.

## Networking Considerations

### WSL2, Docker, and VSCode Integration

When integrating services across WSL2, Docker, and VSCode, several networking considerations come into play:

1. **Docker to Host Communication**:
   - `host.docker.internal` is a special DNS name that Docker provides to refer to the host machine
   - However, this doesn't always work correctly with WSL2, especially for services bound to specific interfaces

2. **WSL2 IP Addressing**:
   - WSL2 runs in a virtual machine with its own IP address
   - This IP address can be found using `ip addr show eth0` in the WSL2 environment
   - In our case, the WSL2 IP was `172.20.106.58`

3. **Binding Services in WSL2**:
   - For services in WSL2 to be accessible from Docker or other systems, they need to bind to `0.0.0.0` (all interfaces) rather than just localhost
   - We achieved this with: `OLLAMA_HOST=0.0.0.0:11434 ollama serve`

4. **MCP Components**:
   - The MCP Server runs on port 8000
   - The MCP Adapter runs on port 8001
   - These need to be accessible to the LibreChat container

### Network Flow

The complete network flow for our setup is:

```
LibreChat Container (172.18.0.6) 
    → WSL2 Host (172.20.106.58:11434) 
        → Ollama Server
```

## Alternative Approaches

### Using the Ollama Python Package

The [ollama-python](https://github.com/ollama/ollama-python) package is the official Python client for Ollama. While we considered using this approach, we ultimately didn't need it because:

1. LibreChat already has built-in support for custom endpoints
2. LibreChat uses the JavaScript Ollama client (`ollama` npm package, version 0.5.14)
3. The issue was with LibreChat's endpoint filtering, not with the client library

If you want to use the Python client in a different context, you can install it with:

```bash
pip install ollama
```

And use it like this:

```python
import ollama

# Generate a response
response = ollama.chat(model='mistral:7b', messages=[
    {
        'role': 'user',
        'content': 'Why is the sky blue?'
    }
])
print(response['message']['content'])
```

## Long-term Fixes

For a more permanent solution, consider:

1. **Submit a Pull Request**: Modify the LibreChat codebase to allow empty API keys when appropriate:
   ```javascript
   const customEndpoints = endpoints[EModelEndpoint.custom].filter(
     (endpoint) =>
       endpoint.baseURL &&
       (endpoint.apiKey !== undefined) &&  // Allow empty strings but not undefined
       endpoint.name &&
       endpoint.models &&
       (endpoint.models.fetch || endpoint.models.default),
   );
   ```

2. **Custom Build**: Create a custom build of LibreChat with this modification

3. **Environment Variable**: Use an environment variable for the API key that can be set to a dummy value

Until then, the current workaround with the dummy key is effective and doesn't impact functionality.