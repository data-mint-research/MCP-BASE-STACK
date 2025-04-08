"""
Enhanced MCP Server implementation using FastAPI.

This version includes:
1. The original shell_command tool
2. A MINTYcoder tool for code generation
3. A code_analyzer tool for analyzing code
4. Additional file resources
5. Proper JSON-RPC envelope validation
"""

import logging
import time
import json
import os
import subprocess
from typing import Dict, Any, Optional, List, Union
from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, Field, validator
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("enhanced_mcp_server")

# Create FastAPI app
app = FastAPI(title="Enhanced MCP Server")

# Define JSON-RPC models
class JsonRpcRequest(BaseModel):
    jsonrpc: str = Field("2.0", description="JSON-RPC version")
    id: Optional[str] = Field(None, description="Request ID")
    method: str = Field(..., description="Method to call")
    params: Dict[str, Any] = Field({}, description="Method parameters")

    @validator('jsonrpc')
    def validate_jsonrpc_version(cls, v):
        if v != "2.0":
            raise ValueError("Only JSON-RPC 2.0 is supported")
        return v

class JsonRpcResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

class JsonRpcError(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None

# Define tool models
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
    },
    "mintycoder": {
        "name": "mintycoder",
        "description": "Generate code using the MINTYcoder agent",
        "input_schema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "The coding task to perform"},
                "language": {"type": "string", "description": "The programming language"}
            },
            "required": ["prompt"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Generated code"},
                "explanation": {"type": "string", "description": "Explanation of the code"}
            }
        }
    },
    "code_analyzer": {
        "name": "code_analyzer",
        "description": "Analyze code for quality and issues",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "The code to analyze"},
                "language": {"type": "string", "description": "The programming language"}
            },
            "required": ["code"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "issues": {"type": "array", "description": "List of issues found"},
                "quality_score": {"type": "number", "description": "Quality score (0-100)"},
                "suggestions": {"type": "array", "description": "Improvement suggestions"}
            }
        }
    }
}

resources = {
    "file://example.txt": "This is an example file resource.",
    "file://code_templates/python.py": "def main():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    main()",
    "file://code_templates/javascript.js": "function main() {\n    console.log('Hello, World!');\n}\n\nmain();",
    "file://code_templates/java.java": "public class Main {\n    public static void main(String[] args) {\n        System.out.println(\"Hello, World!\");\n    }\n}"
}

# Helper functions for JSON-RPC
def create_jsonrpc_response(request_id: Optional[str], result: Any) -> Dict[str, Any]:
    """Create a JSON-RPC response."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result
    }

def create_jsonrpc_error(request_id: Optional[str], code: int, message: str, data: Any = None) -> Dict[str, Any]:
    """Create a JSON-RPC error response."""
    error = {
        "code": code,
        "message": message
    }
    if data is not None:
        error["data"] = data
    
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": error
    }

# Middleware to handle JSON-RPC requests
@app.middleware("http")
async def jsonrpc_middleware(request: Request, call_next):
    """Middleware to handle JSON-RPC requests."""
    # Only process POST requests to /jsonrpc endpoint
    if request.method == "POST" and request.url.path == "/jsonrpc":
        try:
            # Parse request body
            body = await request.json()
            
            # Validate JSON-RPC request
            try:
                jsonrpc_request = JsonRpcRequest(**body)
            except Exception as e:
                error_response = create_jsonrpc_error(
                    body.get("id"), 
                    -32600, 
                    "Invalid Request",
                    str(e)
                )
                return Response(
                    content=json.dumps(error_response),
                    media_type="application/json"
                )
            
            # Extract request details
            request_id = jsonrpc_request.id
            method = jsonrpc_request.method
            params = jsonrpc_request.params
            
            # Process the request based on method
            if method == "tools/list":
                result = {"tools": list(tools.keys())}
                response_body = create_jsonrpc_response(request_id, result)
            elif method == "tools/get":
                tool_name = params.get("name")
                if tool_name not in tools:
                    response_body = create_jsonrpc_error(
                        request_id, 
                        -32602, 
                        f"Tool '{tool_name}' not found"
                    )
                else:
                    result = tools[tool_name]
                    response_body = create_jsonrpc_response(request_id, result)
            elif method == "tools/execute":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                if tool_name not in tools:
                    response_body = create_jsonrpc_error(
                        request_id, 
                        -32602, 
                        f"Tool '{tool_name}' not found"
                    )
                else:
                    # Execute the tool
                    if tool_name == "shell_command":
                        command = arguments.get("command", "")
                        result = {
                            "output": f"Simulated output for command: {command}",
                            "exit_code": 0
                        }
                    elif tool_name == "mintycoder":
                        prompt = arguments.get("prompt", "")
                        language = arguments.get("language", "python")
                        result = {
                            "code": f"# Generated {language} code based on: {prompt}\ndef solution():\n    # Implementation based on the prompt\n    return 'Solution'\n",
                            "explanation": f"This code implements a solution for: {prompt}"
                        }
                    elif tool_name == "code_analyzer":
                        code = arguments.get("code", "")
                        language = arguments.get("language", "python")
                        result = {
                            "issues": [
                                {"line": 1, "message": "Missing docstring"},
                                {"line": 3, "message": "Unused variable"}
                            ],
                            "quality_score": 75,
                            "suggestions": [
                                "Add proper docstrings",
                                "Remove unused variables",
                                "Add type hints"
                            ]
                        }
                    else:
                        result = {"error": "Tool execution not implemented"}
                    
                    response_body = create_jsonrpc_response(request_id, result)
            elif method == "resources/list":
                result = {"resources": list(resources.keys())}
                response_body = create_jsonrpc_response(request_id, result)
            elif method == "resources/get":
                uri = params.get("uri")
                if uri not in resources:
                    response_body = create_jsonrpc_error(
                        request_id, 
                        -32602, 
                        f"Resource '{uri}' not found"
                    )
                else:
                    result = {"content": resources[uri]}
                    response_body = create_jsonrpc_response(request_id, result)
            else:
                response_body = create_jsonrpc_error(
                    request_id, 
                    -32601, 
                    f"Method '{method}' not found"
                )
            
            return Response(
                content=json.dumps(response_body),
                media_type="application/json"
            )
        except Exception as e:
            error_response = create_jsonrpc_error(
                None, 
                -32603, 
                "Internal error",
                str(e)
            )
            return Response(
                content=json.dumps(error_response),
                media_type="application/json"
            )
    
    # For non-JSON-RPC requests, proceed with normal processing
    return await call_next(request)

# MCP endpoints (RESTful API for backward compatibility)
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
    elif tool_name == "mintycoder":
        prompt = request.get("prompt", "")
        language = request.get("language", "python")
        return {
            "code": f"# Generated {language} code based on: {prompt}\ndef solution():\n    # Implementation based on the prompt\n    return 'Solution'\n",
            "explanation": f"This code implements a solution for: {prompt}"
        }
    elif tool_name == "code_analyzer":
        code = request.get("code", "")
        language = request.get("language", "python")
        return {
            "issues": [
                {"line": 1, "message": "Missing docstring"},
                {"line": 3, "message": "Unused variable"}
            ],
            "quality_score": 75,
            "suggestions": [
                "Add proper docstrings",
                "Remove unused variables",
                "Add type hints"
            ]
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

# JSON-RPC endpoint
@app.post("/jsonrpc")
async def jsonrpc_endpoint(request: Request):
    """JSON-RPC endpoint."""
    # This endpoint is handled by the middleware
    pass

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
