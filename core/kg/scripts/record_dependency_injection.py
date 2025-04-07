#!/usr/bin/env python3
"""
Record the dependency injection implementation in the knowledge graph.

This script records the dependency injection components and files in the knowledge graph,
documenting the rationale and purpose of this architectural improvement.
"""

import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Add the project directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

# Configuration
KG_DATA_DIR = "core/kg/data"
PROJECT_NAME = "MCP-BASE-STACK"

try:
    import networkx as nx
    from rdflib import Graph, Namespace, Literal, URIRef
    from rdflib.namespace import RDF, RDFS
except ImportError as e:
    logger.error(f"Could not import required libraries: {e}")
    logger.error("Make sure networkx and rdflib are installed.")
    sys.exit(1)


def load_knowledge_graph():
    """Load the knowledge graph from files."""
    try:
        nx_graph = nx.read_graphml(f"{KG_DATA_DIR}/knowledge_graph.graphml")
        rdf_graph = Graph()
        rdf_graph.parse(f"{KG_DATA_DIR}/knowledge_graph.ttl", format="turtle")
        return nx_graph, rdf_graph
    except Exception as e:
        logger.error(f"Error loading knowledge graph: {e}")
        logger.error("Make sure the knowledge graph files exist and are valid.")
        sys.exit(1)


def save_knowledge_graph(nx_graph, rdf_graph):
    """Save the knowledge graph to files."""
    try:
        nx.write_graphml(nx_graph, f"{KG_DATA_DIR}/knowledge_graph.graphml")
        rdf_graph.serialize(destination=f"{KG_DATA_DIR}/knowledge_graph.ttl", format="turtle")
        logger.info("Knowledge graph saved successfully.")
    except Exception as e:
        logger.error(f"Error saving knowledge graph: {e}")
        sys.exit(1)


def record_di_file(nx_graph, rdf_graph, file_id, file_name, file_path, file_description, file_language):
    """Record a dependency injection file in the knowledge graph."""
    ns = Namespace(f"http://{PROJECT_NAME.lower()}.org/")
    
    # Check if the file node already exists
    if file_id in nx_graph:
        logger.info(f"File {file_id} already exists in the knowledge graph. Updating...")
        # Update existing node
        nx_graph.nodes[file_id]["name"] = file_name
        nx_graph.nodes[file_id]["path"] = file_path
        nx_graph.nodes[file_id]["description"] = file_description
        nx_graph.nodes[file_id]["language"] = file_language
        nx_graph.nodes[file_id]["last_modified"] = datetime.now().timestamp()
    else:
        logger.info(f"Adding file {file_id} to the knowledge graph...")
        # Add new node
        nx_graph.add_node(
            file_id,
            type="file",
            name=file_name,
            path=file_path,
            description=file_description,
            language=file_language,
            last_modified=datetime.now().timestamp()
        )
    
    # Update RDF graph
    file_uri = ns[file_id]
    rdf_graph.add((file_uri, RDF.type, ns.File))
    rdf_graph.add((file_uri, ns.name, Literal(file_name)))
    rdf_graph.add((file_uri, ns.path, Literal(file_path)))
    rdf_graph.add((file_uri, ns.description, Literal(file_description)))
    rdf_graph.add((file_uri, ns.language, Literal(file_language)))
    rdf_graph.add((file_uri, ns.last_modified, Literal(datetime.now().timestamp())))
    
    return True


def add_dependency_injection_component(nx_graph, rdf_graph):
    """Add or update the dependency injection component in the knowledge graph."""
    ns = Namespace(f"http://{PROJECT_NAME.lower()}.org/")
    
    # Check if the component already exists
    if "dependency_injection" in nx_graph:
        logger.info("Dependency injection component already exists in the knowledge graph. Updating...")
        # Update existing node
        nx_graph.nodes["dependency_injection"]["status"] = "implemented"
    else:
        logger.info("Adding dependency injection component to the knowledge graph...")
        # Add new node
        nx_graph.add_node(
            "dependency_injection",
            type="component",
            name="Dependency Injection",
            description="Dependency injection framework for modular and testable code",
            status="implemented"
        )
    
    # Update RDF graph
    component_uri = ns["dependency_injection"]
    rdf_graph.add((component_uri, RDF.type, ns.Component))
    rdf_graph.add((component_uri, ns.name, Literal("Dependency Injection")))
    rdf_graph.add((component_uri, ns.description, Literal("Dependency injection framework for modular and testable code")))
    rdf_graph.add((component_uri, ns.status, Literal("implemented")))
    
    # Connect to mcp_server component if it exists
    if "mcp_server" in nx_graph:
        if not nx_graph.has_edge("mcp_server", "dependency_injection"):
            logger.info("Connecting dependency_injection component to mcp_server component...")
            nx_graph.add_edge("mcp_server", "dependency_injection", relation="contains")
            rdf_graph.add((ns["mcp_server"], ns.contains, component_uri))
    else:
        logger.warning("mcp_server component node not found in the knowledge graph.")
        # Connect to project_root as fallback
        if not nx_graph.has_edge("project_root", "dependency_injection"):
            logger.info("Connecting dependency_injection component to project_root...")
            nx_graph.add_edge("project_root", "dependency_injection", relation="contains")
            rdf_graph.add((ns["project_root"], ns.contains, component_uri))
    
    return True


def connect_file_to_component(nx_graph, rdf_graph, file_id, component_id):
    """Connect a file to a component in the knowledge graph."""
    ns = Namespace(f"http://{PROJECT_NAME.lower()}.org/")
    
    if file_id in nx_graph and component_id in nx_graph:
        if not nx_graph.has_edge(component_id, file_id):
            logger.info(f"Connecting {file_id} to {component_id} component...")
            nx_graph.add_edge(component_id, file_id, relation="contains")
            rdf_graph.add((ns[component_id], ns.contains, ns[file_id]))
            return True
    else:
        if file_id not in nx_graph:
            logger.warning(f"File {file_id} not found in the knowledge graph.")
        if component_id not in nx_graph:
            logger.warning(f"Component {component_id} not found in the knowledge graph.")
        return False


def record_migration_decision(nx_graph, rdf_graph):
    """Record the implementation of dependency injection as a migration decision."""
    ns = Namespace(f"http://{PROJECT_NAME.lower()}.org/")
    
    # Generate a unique ID for the decision
    decision_id = f"decision_dependency_injection_{int(datetime.now().timestamp())}"
    
    # Add the decision node
    nx_graph.add_node(
        decision_id,
        type="decision",
        name="Implementation of Dependency Injection",
        description="Implementation of a dependency injection framework for the MCP Server",
        rationale="To improve modularity, testability, and maintainability of the MCP Server",
        timestamp=datetime.now().isoformat()
    )
    
    # Update RDF graph
    decision_uri = ns[decision_id]
    rdf_graph.add((decision_uri, RDF.type, ns.Decision))
    rdf_graph.add((decision_uri, ns.name, Literal("Implementation of Dependency Injection")))
    rdf_graph.add((decision_uri, ns.description, Literal("Implementation of a dependency injection framework for the MCP Server")))
    rdf_graph.add((decision_uri, ns.rationale, Literal("To improve modularity, testability, and maintainability of the MCP Server")))
    rdf_graph.add((decision_uri, ns.timestamp, Literal(datetime.now().isoformat())))
    
    # Connect to dependency_injection component
    if "dependency_injection" in nx_graph:
        nx_graph.add_edge("dependency_injection", decision_id, relation="has_decision")
        rdf_graph.add((ns["dependency_injection"], ns.has_decision, decision_uri))
    
    return True


def main():
    """Record the dependency injection implementation in the knowledge graph."""
    try:
        # Load the knowledge graph
        nx_graph, rdf_graph = load_knowledge_graph()
        
        # Add or update the dependency injection component
        add_dependency_injection_component(nx_graph, rdf_graph)
        
        # Record each dependency injection file
        di_files = [
            {
                "id": "di_containers",
                "name": "containers.py",
                "path": "services/mcp-server/src/di/containers.py",
                "description": "Dependency injection container that wires up all application dependencies",
                "language": "python"
            },
            {
                "id": "di_providers",
                "name": "providers.py",
                "path": "services/mcp-server/src/di/providers.py",
                "description": "Service providers for the dependency injection container",
                "language": "python"
            },
            {
                "id": "di_init",
                "name": "__init__.py",
                "path": "services/mcp-server/src/di/__init__.py",
                "description": "Dependency injection module initialization",
                "language": "python"
            },
            {
                "id": "di_readme",
                "name": "README.md",
                "path": "services/mcp-server/src/di/README.md",
                "description": "Documentation for the dependency injection framework",
                "language": "markdown"
            },
            {
                "id": "example_service",
                "name": "example_service.py",
                "path": "services/mcp-server/src/services/example_service.py",
                "description": "Example service that demonstrates dependency injection",
                "language": "python"
            },
            {
                "id": "app_py",
                "name": "app.py",
                "path": "services/mcp-server/src/app.py",
                "description": "Main application entry point with dependency injection integration",
                "language": "python"
            }
        ]
        
        for file_info in di_files:
            record_di_file(
                nx_graph, 
                rdf_graph, 
                file_info["id"], 
                file_info["name"], 
                file_info["path"], 
                file_info["description"],
                file_info["language"]
            )
            
            # Connect each file to the dependency_injection component
            connect_file_to_component(nx_graph, rdf_graph, file_info["id"], "dependency_injection")
        
        # Connect the refactored app.py to the dependency_injection component
        if "app_py" in nx_graph and "dependency_injection" in nx_graph:
            connect_file_to_component(nx_graph, rdf_graph, "app_py", "dependency_injection")
        
        # Record the migration decision
        record_migration_decision(nx_graph, rdf_graph)
        
        # Save the knowledge graph
        save_knowledge_graph(nx_graph, rdf_graph)
        
        logger.info("Dependency injection implementation successfully recorded in the knowledge graph")
        return True
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    main()