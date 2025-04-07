# Code Generation from Knowledge Graph

This document explains how the Knowledge Graph maps to real code in the MCP-BASE-STACK, including the code generation process, mapping rules, and examples.

## Overview

The Knowledge Graph serves as a blueprint for code generation in the MCP-BASE-STACK. It defines the components, their relationships, and the features they implement. Code can be generated from this graph to ensure consistency between the design and implementation.

## Code Generation Process

The code generation process follows these steps:

1. **Extract**: Extract relevant subgraphs from the Knowledge Graph
2. **Transform**: Transform the graph representation into code templates
3. **Generate**: Fill in the templates with specific implementation details
4. **Validate**: Validate the generated code against the graph to ensure consistency

## Mapping Rules

### Component to Module/Class

Components in the Knowledge Graph map to modules or classes in the code:

**Graph:**
```
(Component: mcp_server)
  |-- type: "service"
  |-- status: "implemented"
```

**Code:**
```python
# mcp_server.py
class MCPServer:
    """
    MCP Server implementation.
    Generated from Knowledge Graph component 'mcp_server'.
    """
    def __init__(self):
        self.status = "implemented"
```

### Dependency to Import/Instantiation

Dependencies between components map to imports and instantiations:

**Graph:**
```
(Component: mcp_server) --DEPENDS_ON--> (Component: ollama)
```

**Code:**
```python
# mcp_server.py
from ollama import Client

class MCPServer:
    def __init__(self):
        self.ollama_client = Client(host="ollama", port=11434)
```

### Feature to Method/Function

Features implemented by components map to methods or functions:

**Graph:**
```
(Component: mcp_server) --IMPLEMENTS--> (Feature: health_check)
```

**Code:**
```python
# mcp_server.py
import time

class MCPServer:
    # ...
    
    def health_check(self):
        """
        Health check endpoint.
        Generated from Knowledge Graph feature 'health_check'.
        """
        return {"status": "healthy", "timestamp": time.time()}
```

### Connection to API/Client

Connections between components map to API endpoints or client code:

**Graph:**
```
(Component: librechat) --CONNECTS_TO--> (Component: mcp_server)
  |-- protocol: "http"
  |-- direction: "outbound"
```

**Code:**
```python
# In LibreChat's code
import requests

def connect_to_mcp_server():
    response = requests.get("http://mcp_server:8000/debug/health")
    return response.json()
```

### Directory Structure to File Organization

The directory structure in the Knowledge Graph maps to the file organization:

**Graph:**
```
(Directory: docs) --CONTAINS--> (Directory: knowledge-graph)
(Directory: knowledge-graph) --CONTAINS--> (File: schema.md)
```

**File System:**
```
docs/
  └── knowledge-graph/
      └── schema.md
```

## Code Generation Templates

Code generation uses templates that are filled with data from the Knowledge Graph. Here's an example template for a FastAPI endpoint:

```python
# Template for FastAPI endpoint
@app.{{ method }}("{{ path }}")
async def {{ function_name }}({{ parameters }}):
    """
    {{ description }}
    Generated from Knowledge Graph feature '{{ feature_id }}'.
    """
    {{ implementation }}
    return {{ response }}
```

This template would be filled with data from the Knowledge Graph:

```python
# Generated code
@app.get("/debug/health")
async def health_check():
    """
    Health check endpoint.
    Generated from Knowledge Graph feature 'health_check'.
    """
    return {"status": "healthy", "timestamp": time.time()}
```

## Example: MCP Server Generation

Here's a complete example of generating the MCP Server from the Knowledge Graph:

### Knowledge Graph Definition

```
(Component: mcp_server)
  |-- type: "service"
  |-- status: "implemented"
  |-- DEPENDS_ON --> (Component: ollama)
  |-- IMPLEMENTS --> (Feature: health_check)
  |-- IMPLEMENTS --> (Feature: infer)
  |-- EXPOSES --> (Port: 8000)
```

### Generated Code

```python
# mcp_server.py
import time
from fastapi import FastAPI, HTTPException
from ollama import Client

app = FastAPI()
ollama_client = Client(host="ollama", port=11434)

@app.get("/debug/health")
async def health_check():
    """
    Health check endpoint.
    Generated from Knowledge Graph feature 'health_check'.
    """
    return {"status": "healthy", "timestamp": time.time()}

@app.post("/mcp/infer")
async def infer(request: dict):
    """
    Inference endpoint.
    Generated from Knowledge Graph feature 'infer'.
    """
    try:
        prompt = request.get("prompt")
        if prompt.startswith("!shell "):
            # Handle shell command
            command = prompt[7:]
            # Implementation details...
            return {"answer": "Command executed.", "tool_output": "..."}
        else:
            # Handle LLM query
            response = ollama_client.generate(model="deepseek-coder", prompt=prompt)
            return {"answer": response, "tool_output": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Customizing Generated Code

The generated code provides a starting point that can be customized:

1. **Protected Regions**: Sections of code marked as protected will not be overwritten during regeneration
2. **Manual Overrides**: Specific implementations can be manually overridden
3. **Extension Points**: The generated code includes extension points for custom logic

Example of a protected region:

```python
# Generated code
@app.post("/mcp/infer")
async def infer(request: dict):
    """
    Inference endpoint.
    Generated from Knowledge Graph feature 'infer'.
    """
    # [START PROTECTED REGION: Custom inference logic]
    try:
        prompt = request.get("prompt")
        if prompt.startswith("!shell "):
            # Custom shell command handling
            # ...
        else:
            # Custom LLM query handling
            # ...
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    # [END PROTECTED REGION]
```

## Updating the Knowledge Graph from Code

Changes to the code can be reflected back to the Knowledge Graph through a process called "reverse engineering":

1. Analyze the code to extract components, features, and relationships
2. Compare the extracted information with the existing Knowledge Graph
3. Update the Knowledge Graph to reflect the changes
4. Validate the updated graph for consistency

This bidirectional mapping ensures that the Knowledge Graph remains the Single Source of Truth while allowing for code evolution.

## Best Practices

When working with code generation from the Knowledge Graph:

1. **Keep the Graph Updated**: Always update the Knowledge Graph when making significant code changes
2. **Use Protected Regions**: Use protected regions for custom logic that should not be overwritten
3. **Validate Generated Code**: Always validate generated code before committing it
4. **Document Mapping Rules**: Document any custom mapping rules for future reference
5. **Version Control**: Keep both the Knowledge Graph and generated code under version control

## Tools and Scripts

The MCP-BASE-STACK includes tools and scripts for code generation:

- `kg/scripts/generate_code.py`: Generate code from the Knowledge Graph
- `kg/scripts/reverse_engineer.py`: Update the Knowledge Graph from code
- `kg/scripts/validate_consistency.py`: Validate consistency between code and graph

For more information on using these tools, see the [Usage Guide](usage-guide.md).