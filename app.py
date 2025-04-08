"""
MCP-BASE-STACK Main Application.

This is the main entry point for the MCP-BASE-STACK application.
It initializes the MCP Host, Client, and Server components and sets up the FastAPI endpoints.
"""

import logging
import os
import uuid
from typing import Dict, Any, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import sys
import os

# Add the services directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "services", "mcp-server", "src"))

# Now import the modules
from di.containers import Container
from host.host import ConsentLevel

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp_app")

# Initialize dependency injection container
container = Container()
container.config.from_dict({
    'mcp': {
        'host_id': os.environ.get('MCP_HOST_ID', f'host-{uuid.uuid4()}'),
        'server_id': os.environ.get('MCP_SERVER_ID', 'default-server'),
        'client_id': os.environ.get('MCP_CLIENT_ID', f'client-{uuid.uuid4()}'),
        'default_consent_level': 'BASIC',
        'auto_consent': True
    },
    'auth': {
        'provider': 'basic',
        'session_timeout': 3600  # 1 hour
    },
    'context': {
        'storage': 'memory',
        'cleanup_interval': 3600  # 1 hour
    },
    'resources': {
        'file_base_path': os.path.dirname(os.path.abspath(__file__))
    }
})

# Initialize FastAPI app
app = FastAPI(
    title="MCP-BASE-STACK",
    description="Model Context Protocol Base Stack",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize MCP components
host = container.mcp_host()
server = container.mcp_server()
client = container.mcp_client()

# Define API models
class ServerInfo(BaseModel):
    server_id: str
    capabilities: Dict[str, Any]
    description: Optional[str] = None
    version: Optional[str] = None

class ClientInfo(BaseModel):
    client_id: str
    capabilities: Dict[str, Any]
    name: Optional[str] = None

class JsonRpcRequest(BaseModel):
    jsonrpc: str
    id: Optional[str] = None
    method: str
    params: Dict[str, Any]

class ConsentRequest(BaseModel):
    client_id: str
    server_id: str
    operation_pattern: str
    consent_level: str
    expiration: Optional[float] = None

# Define API endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "MCP-BASE-STACK API",
        "version": "1.0.0",
        "host_id": container.config.get("mcp")["host_id"]
    }

@app.get("/servers")
async def get_servers():
    """Get a list of available servers."""
    server_ids = host.get_available_servers()
    servers = []
    
    for server_id in server_ids:
        server_info = host.get_server_info(server_id)
        if server_info:
            servers.append(server_info)
            
    return {"servers": servers}

@app.get("/servers/{server_id}")
async def get_server(server_id: str):
    """Get information about a specific server."""
    server_info = host.get_server_info(server_id)
    if not server_info:
        raise HTTPException(status_code=404, detail=f"Server {server_id} not found")
        
    return server_info

@app.post("/servers")
async def register_server(server_info: ServerInfo):
    """Register a new server."""
    # In a real implementation, this would create a new server instance
    # For now, we'll just return an error
    raise HTTPException(status_code=501, detail="Server registration via API not implemented")

@app.get("/clients")
async def get_clients():
    """Get a list of registered clients."""
    client_ids = host.get_registered_clients()
    clients = []
    
    for client_id in client_ids:
        client_info = host.get_client_info(client_id)
        if client_info:
            clients.append(client_info)
            
    return {"clients": clients}

@app.get("/clients/{client_id}")
async def get_client(client_id: str):
    """Get information about a specific client."""
    client_info = host.get_client_info(client_id)
    if not client_info:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")
        
    return client_info

@app.post("/clients")
async def register_client(client_info: ClientInfo):
    """Register a new client."""
    # In a real implementation, this would create a new client instance
    # For now, we'll just return an error
    raise HTTPException(status_code=501, detail="Client registration via API not implemented")

@app.post("/rpc/{server_id}")
async def route_request(server_id: str, request: JsonRpcRequest, client_id: Optional[str] = None):
    """Route a JSON-RPC request to a server."""
    if server_id not in host.get_available_servers():
        raise HTTPException(status_code=404, detail=f"Server {server_id} not found")
        
    # Convert Pydantic model to dict
    request_dict = request.dict()
    
    # Route the request
    response = host.route_request(server_id, request_dict, client_id)
    if not response:
        raise HTTPException(status_code=500, detail="Failed to route request")
        
    return response

@app.post("/consent")
async def register_consent(request: ConsentRequest):
    """Register consent for a client to perform operations on a server."""
    try:
        consent_level = ConsentLevel[request.consent_level]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid consent level: {request.consent_level}")
        
    consent_id = host.register_consent(
        client_id=request.client_id,
        server_id=request.server_id,
        operation_pattern=request.operation_pattern,
        consent_level=consent_level,
        expiration=request.expiration
    )
    
    return {"consent_id": consent_id}

@app.delete("/consent/{consent_id}")
async def revoke_consent(consent_id: str):
    """Revoke a previously registered consent."""
    success = host.revoke_consent(consent_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Consent {consent_id} not found")
        
    return {"success": True}

@app.get("/status")
async def get_status():
    """Get the status of the MCP components."""
    return {
        "host": {
            "id": container.config.get("mcp")["host_id"],
            "servers": len(host.get_available_servers()),
            "clients": len(host.get_registered_clients())
        },
        "server": {
            "id": server.server_id,
            "tools": len(server.tools),
            "resource_providers": len(server.resource_providers)
        },
        "client": {
            "id": container.config.get("mcp")["client_id"],
            "connected": client.connected,
            "resources": len(client.resources),
            "subscriptions": len(client.subscriptions)
        }
    }

# Run the application
if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8000))
    
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=port)