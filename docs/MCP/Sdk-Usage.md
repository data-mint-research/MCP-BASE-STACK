# MCP SDK Usage

Use the official `modelcontextprotocol` Python SDK.

## Quick Start
```python
from mcp import tool

@tool()
def greet(name: str) -> str:
    return f"Hello, {name}!"
```

This defines a compliant MCP tool. MCPgeek ensures all tools follow this schema.