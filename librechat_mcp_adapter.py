"""
LibreChat MCP Adapter

This adapter translates between LibreChat's plugin API and our MCP server's JSON-RPC API.
It acts as a bridge between LibreChat and the MCP server using the official MCP SDK.
"""

import json
import os
import uuid
import requests
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request, Response, HTTPException
import uvicorn
from mcp_sdk import MCPClient, Tool, Resource

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("librechat_mcp_adapter")

# Create FastAPI app
app = FastAPI(title="LibreChat MCP Adapter")

# Configure MCP client
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://mcp-server:8000")
mcp_client = MCPClient(server_url=MCP_SERVER_URL)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Received request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

# Initialize MCP client
@app.on_event("startup")
async def startup_event():
    """Initialize the MCP client on startup."""
    logger.info(f"Connecting to MCP server at {MCP_SERVER_URL}")
    
    # Check server capabilities
    capabilities = await mcp_client.get_capabilities()
    logger.info(f"MCP server capabilities: {capabilities}")
    
    # Verify required capabilities
    if not capabilities.get("tools", False):
        logger.error("MCP server does not support tools capability")
        raise RuntimeError("MCP server does not support tools capability")
    
    if not capabilities.get("resources", False):
        logger.warning("MCP server does not support resources capability")

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "LibreChat MCP Adapter", "version": "2.0.0", "protocol": "MCP 2025-03-26"}

@app.get("/api/manifest")
async def get_manifest():
    """Get the plugin manifest."""
    try:
        # Get the list of tools from the MCP server using the SDK
        tools = await mcp_client.list_tools()
        
        # Get details for each tool
        tool_details = []
        for tool_name in tools:
            tool_info = await mcp_client.get_tool_details(tool_name)
            
            # Convert MCP tool schema to LibreChat tool schema
            tool_details.append({
                "name": tool_info.get("name", ""),
                "description": tool_info.get("description", ""),
                "input_schema": tool_info.get("input_schema", {}),
                "output_schema": tool_info.get("output_schema", {})
            })
        
        # Create the manifest
        manifest = {
            "name": "MCP Tools",
            "description": "Access to MCP tools and resources via Model Context Protocol",
            "logo": "/plugins/mcp-logo.png",
            "contact": "admin@example.com",
            "protocol": "MCP 2025-03-26",
            "tools": tool_details
        }
        
        return manifest
    except Exception as e:
        logger.error(f"Error getting manifest: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting manifest: {str(e)}")

@app.post("/api/tools/{tool_name}")
async def execute_tool(tool_name: str, request: Request):
    """Execute a tool."""
    try:
        # Parse the request body
        body = await request.json()
        
        # Execute the tool using the MCP SDK
        result = await mcp_client.execute_tool(tool_name, body)
        
        # Return the result
        return result
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}")
        raise HTTPException(status_code=400, detail=f"Error executing tool: {str(e)}")

@app.get("/api/resources")
async def list_resources():
    """List available resources."""
    try:
        resources = await mcp_client.list_resources()
        return {"resources": resources}
    except Exception as e:
        logger.error(f"Error listing resources: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing resources: {str(e)}")

@app.get("/api/resources/{resource_uri:path}")
async def get_resource(resource_uri: str):
    """Get a resource."""
    try:
        uri = f"file://{resource_uri}"
        content = await mcp_client.get_resource(uri)
        
        # Return the content
        return {"content": content}
    except Exception as e:
        logger.error(f"Error getting resource {resource_uri}: {e}")
        raise HTTPException(status_code=404, detail=f"Resource not found: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
