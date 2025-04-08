# Tools in MCP

Each tool must:
- Have a `name`, `description`, `inputSchema`
- Use `@tool()` decorator if using Python SDK
- Optionally be annotated with `dangerous`, `readOnly`, etc.

MCPgeek checks for proper registration and annotations.