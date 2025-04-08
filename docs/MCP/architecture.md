# MCP Architecture

The Model Context Protocol follows a strict Host–Client–Server structure:
- **Host**: Coordinates multiple clients, manages consent, and context.
- **Client**: One per server. Routes JSON-RPC, handles subscriptions.
- **Server**: Stateless capability providers.

Each part plays a defined role. MCPgeek ensures your architecture aligns with this model.