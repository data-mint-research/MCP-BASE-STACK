# Knowledge Graph Schema

This document describes the schema of the MCP-BASE-STACK Knowledge Graph, including node types, edge types, and attributes.

## Overview

The Knowledge Graph serves as the Single Source of Truth for the MCP-BASE-STACK. It represents the relationships between components, features, and their implementation status. The graph is stored in two formats:

1. GraphML format (`.graphml`): For visualization and programmatic access
2. RDF/Turtle format (`.ttl`): For semantic querying and reasoning

## Node Types

The Knowledge Graph contains the following types of nodes:

### Component

Represents a software component in the system.

**Attributes:**
- `id`: Unique identifier for the component
- `name`: Human-readable name
- `type`: Type of component (e.g., "service", "library", "model")
- `status`: Current status (e.g., "installed", "configured", "deployed")
- `version`: Version information

**Examples:**
- `nvidia_gpu`: NVIDIA GPU hardware
- `docker`: Docker container runtime
- `nvidia_container`: NVIDIA Container Toolkit
- `librechat`: LibreChat web interface
- `ollama`: Ollama LLM server
- `mistral`: Mistral language model
- `deepseek`: DeepSeek Coder language model
- `mcp_server`: MCP Server middleware

### Feature

Represents a feature or capability of the system.

**Attributes:**
- `id`: Unique identifier for the feature
- `name`: Human-readable name
- `description`: Detailed description
- `owner`: Person responsible for the feature
- `status`: Implementation status (e.g., "planned", "in_progress", "completed")
- `priority`: Priority level (e.g., "high", "medium", "low")

**Examples:**
- `MCP Agent Test`: Test the MCP server's functionality
- `Documentation Structure`: Organized documentation structure
- `Test Structure`: Comprehensive test structure

### Directory

Represents a directory in the file system.

**Attributes:**
- `id`: Unique identifier for the directory
- `path`: Path to the directory
- `purpose`: Purpose of the directory (e.g., "documentation", "tests", "code")

**Examples:**
- `docs`: Documentation directory
- `tests`: Tests directory
- `kg`: Knowledge Graph directory

### File

Represents a file in the file system.

**Attributes:**
- `id`: Unique identifier for the file
- `path`: Path to the file
- `type`: File type (e.g., "code", "configuration", "documentation")
- `language`: Programming language (for code files)

**Examples:**
- `mcp_server.py`: MCP Server implementation
- `librechat.yaml`: LibreChat configuration
- `mcp_maintenance_guide.md`: Maintenance documentation

## Edge Types

The Knowledge Graph contains the following types of edges:

### DEPENDS_ON

Indicates that one node depends on another.

**Attributes:**
- `type`: Type of dependency (e.g., "runtime", "build", "optional")
- `criticality`: How critical the dependency is (e.g., "critical", "important", "nice-to-have")

**Examples:**
- `(librechat) --DEPENDS_ON--> (ollama)`
- `(mcp_server) --DEPENDS_ON--> (ollama)`

### IMPLEMENTS

Indicates that a component implements a feature.

**Attributes:**
- `completeness`: Degree of implementation (e.g., "full", "partial")
- `since_version`: Version when the implementation was added

**Examples:**
- `(mcp_server) --IMPLEMENTS--> (MCP Agent Test)`

### CONNECTS_TO

Indicates that one component connects to another.

**Attributes:**
- `protocol`: Communication protocol (e.g., "http", "tcp", "docker_network")
- `direction`: Direction of communication (e.g., "bidirectional", "outbound", "inbound")

**Examples:**
- `(librechat) --CONNECTS_TO--> (ollama)`
- `(librechat) --CONNECTS_TO--> (mcp_server)`

### CONTAINS

Indicates that one node contains another.

**Attributes:**
- `relationship`: Type of containment (e.g., "physical", "logical", "ownership")

**Examples:**
- `(docs) --CONTAINS--> (knowledge-graph)`
- `(tests) --CONTAINS--> (unit)`

### DOCUMENTS

Indicates that a documentation file documents a component or feature.

**Attributes:**
- `coverage`: Level of documentation coverage (e.g., "complete", "partial", "minimal")

**Examples:**
- `(docs/knowledge-graph/usage-guide.md) --DOCUMENTS--> (Knowledge Graph)`

### TESTS

Indicates that a test file tests a component or feature.

**Attributes:**
- `coverage`: Level of test coverage (e.g., "complete", "partial", "minimal")
- `test_type`: Type of test (e.g., "unit", "integration", "e2e")

**Examples:**
- `(tests/unit/api) --TESTS--> (mcp_server)`

## Schema Evolution

The Knowledge Graph schema can evolve over time as new components, features, and relationships are added. When extending the schema:

1. Add new node types or edge types as needed
2. Document the new types in this schema document
3. Update the Knowledge Graph scripts to handle the new types
4. Ensure backward compatibility with existing graph data

## Validation Rules

The Knowledge Graph enforces the following validation rules:

1. All nodes must have a unique `id`
2. All components must have a `status` attribute
3. All features must have a `description` and `owner`
4. All edges must connect valid node types according to the schema
5. Circular dependencies should be avoided or documented

## Querying the Schema

The schema can be queried programmatically using the NetworkX library (for GraphML) or RDFLib (for RDF/Turtle):

```python
# Using NetworkX
import networkx as nx
graph = nx.read_graphml("kg/data/knowledge_graph.graphml")
components = [n for n, d in graph.nodes(data=True) if d.get('type') == 'component']

# Using RDFLib
from rdflib import Graph, Namespace
rdf_graph = Graph()
rdf_graph.parse("kg/data/knowledge_graph.ttl", format="turtle")
ns = Namespace("http://mcp-base-stack.org/")
components = list(rdf_graph.subjects(ns.type, ns.Component))
```

For more information on working with the Knowledge Graph, see the [Usage Guide](usage-guide.md).