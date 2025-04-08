# MCP Base Protocol

- Based on JSON-RPC 2.0
- Messages must include valid `id`, `method`, `params`
- Server must respond to requests with corresponding `id`
- Notifications are one-way, without `id`
- Supports batch messages and progress reporting

MCPgeek validates all message structures and flow.