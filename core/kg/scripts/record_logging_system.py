#!/usr/bin/env python3
"""
Record the logging system in the knowledge graph.

This script adds the logging system components (LogDirectoryManager, LoggingConfig)
to the knowledge graph, along with their relationships and metadata about the
standardized log directory structure and naming conventions.
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


def add_logging_system_component(nx_graph, rdf_graph):
    """Add or update the logging system component in the knowledge graph."""
    ns = Namespace(f"http://{PROJECT_NAME.lower()}.org/")
    
    # Check if the component already exists
    if "logging_system" in nx_graph:
        logger.info("Logging system component already exists in the knowledge graph. Updating...")
        # Update existing node
        nx_graph.nodes["logging_system"]["status"] = "implemented"
    else:
        logger.info("Adding logging system component to the knowledge graph...")
        # Add new node
        nx_graph.add_node(
            "logging_system",
            type="component",
            name="Logging System",
            description="Standardized logging system for the MCP-BASE-STACK project",
            status="implemented"
        )
    
    # Update RDF graph
    component_uri = ns["logging_system"]
    rdf_graph.add((component_uri, RDF.type, ns.Component))
    rdf_graph.add((component_uri, ns.name, Literal("Logging System")))
    rdf_graph.add((component_uri, ns.description, Literal("Standardized logging system for the MCP-BASE-STACK project")))
    rdf_graph.add((component_uri, ns.status, Literal("implemented")))
    
    # Connect to project_root if not already connected
    if not nx_graph.has_edge("project_root", "logging_system"):
        logger.info("Connecting logging_system component to project_root...")
        nx_graph.add_edge("project_root", "logging_system", relation="contains")
        rdf_graph.add((ns["project_root"], ns.contains, component_uri))
    
    return True


def add_logging_module(nx_graph, rdf_graph, module_id, module_name, file_path, description, language="python"):
    """Add or update a logging module in the knowledge graph."""
    ns = Namespace(f"http://{PROJECT_NAME.lower()}.org/")
    
    # Check if the module already exists
    if module_id in nx_graph:
        logger.info(f"Module {module_id} already exists in the knowledge graph. Updating...")
        # Update existing node
        nx_graph.nodes[module_id]["name"] = module_name
        nx_graph.nodes[module_id]["path"] = file_path
        nx_graph.nodes[module_id]["description"] = description
        nx_graph.nodes[module_id]["language"] = language
        nx_graph.nodes[module_id]["last_modified"] = datetime.now().timestamp()
    else:
        logger.info(f"Adding module {module_id} to the knowledge graph...")
        # Add new node
        nx_graph.add_node(
            module_id,
            type="module",
            name=module_name,
            path=file_path,
            description=description,
            language=language,
            last_modified=datetime.now().timestamp()
        )
    
    # Update RDF graph
    module_uri = ns[module_id]
    rdf_graph.add((module_uri, RDF.type, ns.Module))
    rdf_graph.add((module_uri, ns.name, Literal(module_name)))
    rdf_graph.add((module_uri, ns.path, Literal(file_path)))
    rdf_graph.add((module_uri, ns.description, Literal(description)))
    rdf_graph.add((module_uri, ns.language, Literal(language)))
    rdf_graph.add((module_uri, ns.last_modified, Literal(datetime.now().timestamp())))
    
    # Connect to logging_system component if it exists
    if "logging_system" in nx_graph:
        if not nx_graph.has_edge("logging_system", module_id):
            logger.info(f"Connecting {module_id} to logging_system component...")
            nx_graph.add_edge("logging_system", module_id, relation="contains")
            rdf_graph.add((ns["logging_system"], ns.contains, module_uri))
    else:
        logger.warning("logging_system component node not found in the knowledge graph.")
    
    return True


def add_documentation_file(nx_graph, rdf_graph, doc_id, doc_name, doc_path, description):
    """Add or update a documentation file in the knowledge graph."""
    ns = Namespace(f"http://{PROJECT_NAME.lower()}.org/")
    
    # Check if the documentation already exists
    if doc_id in nx_graph:
        logger.info(f"Documentation {doc_id} already exists in the knowledge graph. Updating...")
        # Update existing node
        nx_graph.nodes[doc_id]["name"] = doc_name
        nx_graph.nodes[doc_id]["path"] = doc_path
        nx_graph.nodes[doc_id]["description"] = description
        nx_graph.nodes[doc_id]["language"] = "markdown"
        nx_graph.nodes[doc_id]["last_modified"] = datetime.now().timestamp()
    else:
        logger.info(f"Adding documentation {doc_id} to the knowledge graph...")
        # Add new node
        nx_graph.add_node(
            doc_id,
            type="file",
            name=doc_name,
            path=doc_path,
            description=description,
            language="markdown",
            last_modified=datetime.now().timestamp()
        )
    
    # Update RDF graph
    doc_uri = ns[doc_id]
    rdf_graph.add((doc_uri, RDF.type, ns.File))
    rdf_graph.add((doc_uri, ns.name, Literal(doc_name)))
    rdf_graph.add((doc_uri, ns.path, Literal(doc_path)))
    rdf_graph.add((doc_uri, ns.description, Literal(description)))
    rdf_graph.add((doc_uri, ns.language, Literal("markdown")))
    rdf_graph.add((doc_uri, ns.last_modified, Literal(datetime.now().timestamp())))
    
    # Connect to logging_system component
    if "logging_system" in nx_graph:
        if not nx_graph.has_edge("logging_system", doc_id):
            logger.info(f"Connecting {doc_id} to logging_system component...")
            nx_graph.add_edge("logging_system", doc_id, relation="documented_by")
            rdf_graph.add((ns["logging_system"], ns.documented_by, doc_uri))
    
    # Connect to docs directory if it exists
    if "docs" in nx_graph:
        if not nx_graph.has_edge("docs", doc_id):
            logger.info(f"Connecting {doc_id} to docs directory...")
            nx_graph.add_edge("docs", doc_id, relation="contains")
            rdf_graph.add((ns["docs"], ns.contains, doc_uri))
    
    return True


def add_test_file(nx_graph, rdf_graph, test_id, test_name, test_path, description):
    """Add or update a test file in the knowledge graph."""
    ns = Namespace(f"http://{PROJECT_NAME.lower()}.org/")
    
    # Check if the test already exists
    if test_id in nx_graph:
        logger.info(f"Test {test_id} already exists in the knowledge graph. Updating...")
        # Update existing node
        nx_graph.nodes[test_id]["name"] = test_name
        nx_graph.nodes[test_id]["path"] = test_path
        nx_graph.nodes[test_id]["description"] = description
        nx_graph.nodes[test_id]["language"] = "python"
        nx_graph.nodes[test_id]["last_modified"] = datetime.now().timestamp()
    else:
        logger.info(f"Adding test {test_id} to the knowledge graph...")
        # Add new node
        nx_graph.add_node(
            test_id,
            type="file",
            name=test_name,
            path=test_path,
            description=description,
            language="python",
            last_modified=datetime.now().timestamp()
        )
    
    # Update RDF graph
    test_uri = ns[test_id]
    rdf_graph.add((test_uri, RDF.type, ns.File))
    rdf_graph.add((test_uri, ns.name, Literal(test_name)))
    rdf_graph.add((test_uri, ns.path, Literal(test_path)))
    rdf_graph.add((test_uri, ns.description, Literal(description)))
    rdf_graph.add((test_uri, ns.language, Literal("python")))
    rdf_graph.add((test_uri, ns.last_modified, Literal(datetime.now().timestamp())))
    
    # Connect to logging_system component
    if "logging_system" in nx_graph:
        if not nx_graph.has_edge(test_id, "logging_system"):
            logger.info(f"Connecting {test_id} to logging_system component...")
            nx_graph.add_edge(test_id, "logging_system", relation="tests")
            rdf_graph.add((test_uri, ns.tests, ns["logging_system"]))
    
    # Connect to tests directory if it exists
    if "tests" in nx_graph:
        if not nx_graph.has_edge("tests", test_id):
            logger.info(f"Connecting {test_id} to tests directory...")
            nx_graph.add_edge("tests", test_id, relation="contains")
            rdf_graph.add((ns["tests"], ns.contains, test_uri))
    
    return True


def add_directory_structure_metadata(nx_graph, rdf_graph):
    """Add metadata about the logging system directory structure."""
    ns = Namespace(f"http://{PROJECT_NAME.lower()}.org/")
    
    # Add metadata node for directory structure
    metadata_id = "logging_directory_structure"
    if metadata_id in nx_graph:
        logger.info(f"Metadata {metadata_id} already exists in the knowledge graph. Updating...")
        # Update existing node
        nx_graph.nodes[metadata_id]["description"] = "Standardized directory structure for logs"
        nx_graph.nodes[metadata_id]["base_directory"] = "docs/logs"
        nx_graph.nodes[metadata_id]["module_subdirectories"] = "docs/logs/<module_name>"
        nx_graph.nodes[metadata_id]["last_modified"] = datetime.now().timestamp()
    else:
        logger.info(f"Adding metadata {metadata_id} to the knowledge graph...")
        # Add new node
        nx_graph.add_node(
            metadata_id,
            type="metadata",
            name="Logging Directory Structure",
            description="Standardized directory structure for logs",
            base_directory="docs/logs",
            module_subdirectories="docs/logs/<module_name>",
            last_modified=datetime.now().timestamp()
        )
    
    # Update RDF graph
    metadata_uri = ns[metadata_id]
    rdf_graph.add((metadata_uri, RDF.type, ns.Metadata))
    rdf_graph.add((metadata_uri, ns.name, Literal("Logging Directory Structure")))
    rdf_graph.add((metadata_uri, ns.description, Literal("Standardized directory structure for logs")))
    rdf_graph.add((metadata_uri, ns.base_directory, Literal("docs/logs")))
    rdf_graph.add((metadata_uri, ns.module_subdirectories, Literal("docs/logs/<module_name>")))
    rdf_graph.add((metadata_uri, ns.last_modified, Literal(datetime.now().timestamp())))
    
    # Connect to logging_system component
    if "logging_system" in nx_graph:
        if not nx_graph.has_edge("logging_system", metadata_id):
            logger.info(f"Connecting {metadata_id} to logging_system component...")
            nx_graph.add_edge("logging_system", metadata_id, relation="has_metadata")
            rdf_graph.add((ns["logging_system"], ns.has_metadata, metadata_uri))
    
    return True


def add_naming_convention_metadata(nx_graph, rdf_graph):
    """Add metadata about the logging system naming conventions."""
    ns = Namespace(f"http://{PROJECT_NAME.lower()}.org/")
    
    # Add metadata node for naming conventions
    metadata_id = "logging_naming_conventions"
    if metadata_id in nx_graph:
        logger.info(f"Metadata {metadata_id} already exists in the knowledge graph. Updating...")
        # Update existing node
        nx_graph.nodes[metadata_id]["description"] = "Standardized naming conventions for log files"
        nx_graph.nodes[metadata_id]["file_naming_pattern"] = "YYYY-MM-DD_module-name-log"
        nx_graph.nodes[metadata_id]["last_modified"] = datetime.now().timestamp()
    else:
        logger.info(f"Adding metadata {metadata_id} to the knowledge graph...")
        # Add new node
        nx_graph.add_node(
            metadata_id,
            type="metadata",
            name="Logging Naming Conventions",
            description="Standardized naming conventions for log files",
            file_naming_pattern="YYYY-MM-DD_module-name-log",
            last_modified=datetime.now().timestamp()
        )
    
    # Update RDF graph
    metadata_uri = ns[metadata_id]
    rdf_graph.add((metadata_uri, RDF.type, ns.Metadata))
    rdf_graph.add((metadata_uri, ns.name, Literal("Logging Naming Conventions")))
    rdf_graph.add((metadata_uri, ns.description, Literal("Standardized naming conventions for log files")))
    rdf_graph.add((metadata_uri, ns.file_naming_pattern, Literal("YYYY-MM-DD_module-name-log")))
    rdf_graph.add((metadata_uri, ns.last_modified, Literal(datetime.now().timestamp())))
    
    # Connect to logging_system component
    if "logging_system" in nx_graph:
        if not nx_graph.has_edge("logging_system", metadata_id):
            logger.info(f"Connecting {metadata_id} to logging_system component...")
            nx_graph.add_edge("logging_system", metadata_id, relation="has_metadata")
            rdf_graph.add((ns["logging_system"], ns.has_metadata, metadata_uri))
    
    return True


def connect_to_existing_components(nx_graph, rdf_graph):
    """Connect the logging system to existing components that use it."""
    ns = Namespace(f"http://{PROJECT_NAME.lower()}.org/")
    
    # List of components that use the logging system
    components_using_logging = [
        "core_kg",
        "mcp_server",
        "code_quality"
    ]
    
    for component_id in components_using_logging:
        if component_id in nx_graph and "logging_system" in nx_graph:
            if not nx_graph.has_edge(component_id, "logging_system"):
                logger.info(f"Connecting {component_id} to logging_system component...")
                nx_graph.add_edge(component_id, "logging_system", relation="uses")
                rdf_graph.add((ns[component_id], ns.uses, ns["logging_system"]))
        else:
            logger.warning(f"Component {component_id} or logging_system not found in the knowledge graph.")
    
    return True


def record_migration_decision(nx_graph, rdf_graph):
    """Record the creation of the logging system as a migration decision."""
    ns = Namespace(f"http://{PROJECT_NAME.lower()}.org/")
    
    # Generate a unique ID for the decision
    decision_id = f"decision_logging_system_{int(datetime.now().timestamp())}"
    
    # Add the decision node
    nx_graph.add_node(
        decision_id,
        type="decision",
        name="Implementation of Standardized Logging System",
        description="Implementation of a standardized logging system with consistent directory structure and naming conventions",
        rationale="To ensure consistent logging practices across the MCP-BASE-STACK project and improve debugging and monitoring capabilities",
        timestamp=datetime.now().isoformat()
    )
    
    # Update RDF graph
    decision_uri = ns[decision_id]
    rdf_graph.add((decision_uri, RDF.type, ns.Decision))
    rdf_graph.add((decision_uri, ns.name, Literal("Implementation of Standardized Logging System")))
    rdf_graph.add((decision_uri, ns.description, Literal("Implementation of a standardized logging system with consistent directory structure and naming conventions")))
    rdf_graph.add((decision_uri, ns.rationale, Literal("To ensure consistent logging practices across the MCP-BASE-STACK project and improve debugging and monitoring capabilities")))
    rdf_graph.add((decision_uri, ns.timestamp, Literal(datetime.now().isoformat())))
    
    # Connect to logging_system component
    if "logging_system" in nx_graph:
        nx_graph.add_edge("logging_system", decision_id, relation="has_decision")
        rdf_graph.add((ns["logging_system"], ns.has_decision, decision_uri))
    
    return True


def main():
    """Record the logging system in the knowledge graph."""
    try:
        # Load the knowledge graph
        nx_graph, rdf_graph = load_knowledge_graph()
        
        # Add or update the logging system component
        add_logging_system_component(nx_graph, rdf_graph)
        
        # Add logging modules
        add_logging_module(
            nx_graph,
            rdf_graph,
            "log_directory_manager",
            "LogDirectoryManager",
            "core/logging/directory_manager.py",
            "Manages the creation and organization of log directories and files"
        )
        
        add_logging_module(
            nx_graph,
            rdf_graph,
            "logging_config",
            "LoggingConfig",
            "core/logging/config.py",
            "Configures loggers with standardized settings and handlers"
        )
        
        # Add documentation file
        add_documentation_file(
            nx_graph,
            rdf_graph,
            "logging_system_documentation",
            "Logging System Documentation",
            "docs/logging-system.md",
            "Documentation for the standardized logging system"
        )
        
        # Add test files
        add_test_file(
            nx_graph,
            rdf_graph,
            "logging_integration_test",
            "Logging Integration Test",
            "tests/integration/test_logging_integration.py",
            "Integration tests for the standardized logging system"
        )
        
        add_test_file(
            nx_graph,
            rdf_graph,
            "log_directory_manager_test",
            "LogDirectoryManager Unit Test",
            "tests/unit/test_log_directory_manager.py",
            "Unit tests for the LogDirectoryManager module"
        )
        
        add_test_file(
            nx_graph,
            rdf_graph,
            "logging_config_test",
            "LoggingConfig Unit Test",
            "tests/unit/test_logging_config.py",
            "Unit tests for the LoggingConfig module"
        )
        
        # Add metadata about directory structure and naming conventions
        add_directory_structure_metadata(nx_graph, rdf_graph)
        add_naming_convention_metadata(nx_graph, rdf_graph)
        
        # Connect to existing components that use the logging system
        connect_to_existing_components(nx_graph, rdf_graph)
        
        # Record the migration decision
        record_migration_decision(nx_graph, rdf_graph)
        
        # Save the knowledge graph
        save_knowledge_graph(nx_graph, rdf_graph)
        
        logger.info("Logging system successfully recorded in the knowledge graph")
        return True
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    main()