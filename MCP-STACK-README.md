# MCP Stack with SERJ Agent Architecture

This repository contains a complete Model Context Protocol (MCP) stack implementation with SERJ agent architecture, including:

1. An MCP server with tools and resources
2. An MCP client for programmatic access
3. A LibreChat integration with SERJ agent
4. Docker Compose configuration for deployment

## Components

### MCP Server

The MCP server (`mcp_server.py`) is a FastAPI application that implements the Model Context Protocol. It provides:

- **Tools**: 
  - Shell command execution
  - Code generation (MINTYcoder powered by DeepSeek Coder)
  - Code analysis
- **Resources**: File resources, including code templates
- **JSON-RPC API**: Compliant with the MCP specification (2025-03-26)

### MCP Client

The MCP client (`mcp_client.py`) is a Python library that provides a simple interface for interacting with the MCP server. It handles:

- JSON-RPC request/response formatting
- Tool execution
- Resource access

### LibreChat Integration

The LibreChat integration consists of:

- **LibreChat Configuration**: Updated to include SERJ agent and MCP tools
- **MCP Adapter**: A bridge between LibreChat's plugin API and the MCP server's JSON-RPC API
- **Custom LLM Manager**: Manages LLMs through a custom function in LibreChat

## SERJ Agent Architecture

The SERJ (Specialized Expert Reasoning JSON) agent architecture is implemented as follows:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  LibreChat  │◄────┤ MCP Adapter │◄────┤  MCP Server │
└─────────────┘     └─────────────┘     └─────────────┘
       ▲                                       ▲
       │                                       │
       ▼                                       ▼
┌─────────────┐                        ┌─────────────┐
│  LLM Server │                        │ MINTYcoder  │
└─────────────┘                        └─────────────┘
```

- **LibreChat**: User interface with SERJ agent
- **SERJ Agent**: Orchestrates tasks between models
  - Uses Mistral (7B) as its primary model
  - Delegates coding tasks to MINTYcoder
  - All communication follows MCP protocol with proper JSON-RPC envelopes
- **MINTYcoder**: Specialized agent for code generation (powered by DeepSeek Coder)
- **LLM Server**: Provides language model capabilities through Ollama

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.10 or later (for local development)

### Setting Up Ollama for LLMs

The MCP stack uses Ollama to run the LLMs (Large Language Models) locally. To set up Ollama and pull the required models:

1. Run the setup script:

```bash
./setup_ollama.sh
```

This script will:
- Install Ollama if it's not already installed
- Start the Ollama service if it's not running
- Pull the required models:
  - mistral:7b
  - deepseek-coder:6.7b
  - command-rp:latest

2. Verify that Ollama is running and the models are available:

```bash
ollama list
```

### Running the Stack

1. Start the MCP stack:

```bash
./start_mcp_stack.sh
```

2. Access LibreChat at http://localhost:3080

3. When you're done, stop the MCP stack:

```bash
./stop_mcp_stack.sh
```

### Using the MCP Client

```python
from mcp_client import MCPClient

# Create a client
client = MCPClient()

# List available tools
tools = client.list_tools()
print(f"Available tools: {tools}")

# Execute the mintycoder tool
result = client.execute_tool(
    "mintycoder",
    {
        "prompt": "Create a function to calculate the factorial of a number",
        "language": "python"
    }
)
print(f"MINTYcoder result: {result}")
```

## Docker Deployment

For production deployment, use Docker Compose:

```bash
docker-compose -f docker-compose.mcp.yml up -d
```

This will start:
- MCP Server
- MCP Adapter
- LibreChat
- MongoDB
- Ollama (with GPU support if available)

## Custom LLM Manager

The custom LLM manager (`llm_manager.js`) provides:

- Direct integration with Ollama
- SERJ agent implementation
- Automatic routing of coding tasks to MINTYcoder
- Model selection in LibreChat

## Future Enhancements

The MCP Server is designed to be extended with:

- Request router for more complex workflows
- LangGraph integration for advanced agent workflows
- ContextHandler for better context management
- Enhanced error handling and logging
- Additional APIs for external integrations

## Protocol Compliance

This implementation follows the Model Context Protocol (MCP) specification version 2025-03-26, including:

- Proper JSON-RPC envelope structure
- Correct error handling
- Tool and resource capabilities
- Proper schema validation

## Extending the Stack

### Adding New Tools

To add a new tool to the MCP server, add it to the `tools` dictionary in `mcp_server.py`:

```python
tools["new_tool"] = {
    "name": "new_tool",
    "description": "Description of the new tool",
    "input_schema": {
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "Parameter 1"}
        },
        "required": ["param1"]
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "result": {"type": "string", "description": "Result"}
        }
    }
}
```

Then implement the tool execution in the `execute_tool` function.

### Adding New Resources

To add a new resource to the MCP server, add it to the `resources` dictionary in `mcp_server.py`:

```python
resources["file://path/to/resource"] = "Resource content"
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
