# Knowledge Graph Examples

This document provides examples of how the Knowledge Graph is used in the MCP-BASE-STACK, including example queries, graph structures, and code generation examples.

## MCP Agent Test Examples

The following examples demonstrate the MCP Agent (MINTYcoder) capabilities, which are tracked in the Knowledge Graph:

### Simple LLM Query

```
Query: What is 2+2?
Response: The result of 2 + 2 in basic arithmetic operations using Python would be 4.
```

### Code Generation

```
Query: Write a Python function to check if a string is a palindrome
Response:

def check_palindrome(input_string):
    # We convert the string to lower case and remove any white space or special characters using translate() method
    input_string = "".join(char.lower() for char in input_string if char.isalnum()) 
    
    # Compare the original (or reversed) string with its reverse
    return input_string == input_string[::-1]
```

Example usage:

```python
print(check_palindrome("A man, a plan, a canal: Panama"))  # returns True
print(check_palindrome("Python"))  # returns False
```

### Tool Invocation

```
Query: !shell echo Hello from MINTYcoder
Response: Hello from MINTYcoder
```

### System Info Tool

```
Query: !shell uname -a
Response: Linux ESCA-FAT 5.15.167.4-microsoft-standard-WSL2 #1 SMP Tue Nov 5 00:21:55 UTC 2024 x86_64 x86_64 x86_64 GNU/Linux
```

## LibreChat Model Integration Examples

The following examples demonstrate the LibreChat model integration, which is tracked in the Knowledge Graph:

### LibreChat Configuration

```yaml
version: 1.0.3

# Social login configuration is managed through environment variables
# ALLOW_SOCIAL_LOGIN=true in .env file

endpoints:
  custom:
    - # Using Ollama as a custom endpoint
      baseURL: "http://ollama:11434/api"
      models:
        default: ["mistral", "deepseek-coder"]
        available:
          - id: "mistral"
            name: "Mistral"
            description: "Mistral AI's 7B parameter model"
          - id: "deepseek-coder"
            name: "DeepSeek Coder"
            description: "Code generation and completion model"
      titleConvo: true
      titleModel: "mistral"
```

### Integration Architecture

The MCP-BASE-STACK uses the following integration architecture:

1. Mistral: Direct integration via Ollama
2. DeepSeek Coder: Accessed through MCP Server, which connects to Ollama

## Knowledge Graph Structure Examples

### Component Relationships

The Knowledge Graph represents relationships between components:

```
(LibreChat) --CONNECTS_TO--> (MCP Server)
(MCP Server) --CONNECTS_TO--> (Ollama)
(Ollama) --HOSTS--> (Mistral)
(Ollama) --HOSTS--> (DeepSeek Coder)
```

### Feature Tracking

Features are tracked in the Knowledge Graph with their implementation status:

```
(Feature: MCP Agent Test) --HAS_STATUS--> (completed)
(Feature: MCP Agent Test) --IMPLEMENTED_BY--> (MCP Server)
(Feature: MCP Agent Test) --DEPENDS_ON--> (DeepSeek Coder)
```

## Code Generation Examples

The Knowledge Graph can be used to generate code. Here's an example of how a component definition in the graph maps to actual code:

### Graph Definition

```
(Component: MCP Server)
  |-- IMPLEMENTS --> (Feature: API Endpoint)
  |-- USES --> (Component: Ollama Client)
  |-- EXPOSES --> (Port: 8000)
```

### Generated Code

```python
# Generated from Knowledge Graph definition
from fastapi import FastAPI
from ollama import Client

app = FastAPI()
ollama_client = Client(host="ollama", port=11434)

@app.get("/debug/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

# Additional endpoints would be generated based on the graph
```

## Using These Examples

These examples demonstrate how the Knowledge Graph serves as the source of truth for the MCP-BASE-STACK. When extending the system:

1. Define new components and relationships in the Knowledge Graph
2. Use the graph to generate code scaffolding
3. Implement the details of the generated code
4. Update the graph to reflect the implementation status

For more details on working with the Knowledge Graph, see the [Usage Guide](usage-guide.md).