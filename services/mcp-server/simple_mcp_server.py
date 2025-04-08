"""
Simple MCP Server implementation using FastAPI.
"""

import logging
import time
import json
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_server")

# Create FastAPI app
app = FastAPI(title="Simple MCP Server")

# Define data models
class ToolRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]

class ToolResponse(BaseModel):
    result: Any

class ResourceRequest(BaseModel):
    uri: str

class ResourceResponse(BaseModel):
    content: Any

# In-memory storage for tools and resources
tools = {
    "shell_command": {
        "name": "shell_command",
        "description": "Execute a shell command",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The command to execute"}
            },
            "required": ["command"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "output": {"type": "string", "description": "Command output"},
                "exit_code": {"type": "integer", "description": "Exit code"}
            }
        }
    }
}

resources = {
    "file://example.txt": "This is an example file resource."
}

# MCP endpoints
@app.get("/mcp/capabilities")
async def get_capabilities():
    """Get server capabilities."""
    return {
        "tools": True,
        "resources": True,
        "subscriptions": False,
        "prompts": False,
        "batch": False,
        "progress": False
    }

@app.get("/mcp/tools")
async def list_tools():
    """List available tools."""
    return {"tools": list(tools.keys())}

@app.get("/mcp/tools/{tool_name}")
async def get_tool(tool_name: str):
    """Get tool details."""
    if tool_name not in tools:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    return tools[tool_name]

@app.post("/mcp/tools/{tool_name}/execute")
async def execute_tool(tool_name: str, request: Dict[str, Any]):
    """Execute a tool."""
    if tool_name not in tools:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
    logger.info(f"Executing tool: {tool_name} with arguments: {request}")
    
    if tool_name == "shell_command":
        # Mock shell command execution
        return {
            "output": f"Simulated output for command: {request.get('command', 'unknown')}",
            "exit_code": 0
        }
    
    return {"result": "Tool execution not implemented"}

@app.get("/mcp/resources")
async def list_resources():
    """List available resources."""
    return {"resources": list(resources.keys())}

@app.get("/mcp/resources/{resource_uri:path}")
async def get_resource(resource_uri: str):
    """Get resource content."""
    uri = f"file://{resource_uri}"
    if uri not in resources:
        raise HTTPException(status_code=404, detail=f"Resource '{uri}' not found")
    return {"content": resources[uri]}

# Debug endpoints
@app.get("/debug/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
