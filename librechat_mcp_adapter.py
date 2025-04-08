"""
LibreChat MCP Adapter

This adapter translates between LibreChat's plugin API and our MCP server's JSON-RPC API.
It acts as a bridge between LibreChat and the MCP server.
"""

import json
import uuid
import requests
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request, Response, HTTPException
import uvicorn

app = FastAPI(title="LibreChat MCP Adapter")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"Received request: {request.method} {request.url}")
    response = await call_next(request)
    print(f"Response status: {response.status_code}")
    return response

# MCP server URL
MCP_SERVER_URL = "http://localhost:8000"

# Request counter for generating unique request IDs
request_counter = 0

def get_request_id() -> str:
    """
    Get a unique request ID.
    
    Returns:
        str: Unique request ID
    """
    global request_counter
    request_counter += 1
    return f"librechat-adapter-{request_counter}"

def create_jsonrpc_request(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a JSON-RPC request.
    
    Args:
        method: Method to call
        params: Method parameters
        
    Returns:
        Dict[str, Any]: JSON-RPC request
    """
    return {
        "jsonrpc": "2.0",
        "id": get_request_id(),
        "method": method,
        "params": params
    }

def send_jsonrpc_request(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a JSON-RPC request to the MCP server.
    
    Args:
        method: Method to call
        params: Method parameters
        
    Returns:
        Dict[str, Any]: JSON-RPC response
    """
    request = create_jsonrpc_request(method, params)
    response = requests.post(
        f"{MCP_SERVER_URL}/jsonrpc",
        json=request,
        headers={"Content-Type": "application/json"}
    )
    return response.json()

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "LibreChat MCP Adapter"}

@app.get("/api/manifest")
async def get_manifest():
    """Get the plugin manifest."""
    # Get the list of tools from the MCP server
    response = send_jsonrpc_request("tools/list", {})
    tools = response.get("result", {}).get("tools", [])
    
    # Get details for each tool
    tool_details = []
    for tool_name in tools:
        tool_response = send_jsonrpc_request("tools/get", {"name": tool_name})
        tool_info = tool_response.get("result", {})
        
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
        "description": "Access to MCP tools and resources",
        "logo": "/plugins/mcp-logo.png",
        "contact": "admin@example.com",
        "tools": tool_details
    }
    
    return manifest

@app.post("/api/tools/{tool_name}")
async def execute_tool(tool_name: str, request: Request):
    """Execute a tool."""
    # Parse the request body
    body = await request.json()
    
    # Send the request to the MCP server
    response = send_jsonrpc_request(
        "tools/execute",
        {
            "name": tool_name,
            "arguments": body
        }
    )
    
    # Check for errors
    if "error" in response:
        raise HTTPException(
            status_code=400,
            detail=response["error"].get("message", "Unknown error")
        )
    
    # Return the result
    return response.get("result", {})

@app.get("/api/resources")
async def list_resources():
    """List available resources."""
    response = send_jsonrpc_request("resources/list", {})
    return response.get("result", {})

@app.get("/api/resources/{resource_uri:path}")
async def get_resource(resource_uri: str):
    """Get a resource."""
    response = send_jsonrpc_request(
        "resources/get",
        {"uri": f"file://{resource_uri}"}
    )
    
    # Check for errors
    if "error" in response:
        raise HTTPException(
            status_code=404,
            detail=response["error"].get("message", "Resource not found")
        )
    
    # Return the content
    return {"content": response.get("result", {}).get("content", "")}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
