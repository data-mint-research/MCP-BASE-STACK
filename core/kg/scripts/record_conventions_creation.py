#!/usr/bin/env python3
"""
Record the creation of convention documents in the knowledge graph.

This script records the creation of the style guide, coding conventions,
review checklist, and graph guidelines as a migration decision in the
knowledge graph, documenting the rationale and purpose.
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


def record_convention_document(nx_graph, rdf_graph, doc_id, doc_name, doc_path, doc_description):
    """Record a convention document in the knowledge graph."""
    ns = Namespace(f"http://{PROJECT_NAME.lower()}.org/")
    
    # Check if the document node already exists
    if doc_id in nx_graph:
        logger.info(f"Document {doc_id} already exists in the knowledge graph. Updating...")
        # Update existing node
        nx_graph.nodes[doc_id]["name"] = doc_name
        nx_graph.nodes[doc_id]["path"] = doc_path
        nx_graph.nodes[doc_id]["description"] = doc_description
        nx_graph.nodes[doc_id]["last_modified"] = datetime.now().timestamp()
    else:
        logger.info(f"Adding document {doc_id} to the knowledge graph...")
        # Add new node
        nx_graph.add_node(
            doc_id,
            type="file",
            name=doc_name,
            path=doc_path,
            description=doc_description,
            language="markdown",
            last_modified=datetime.now().timestamp()
        )
    
    # Update RDF graph
    doc_uri = ns[doc_id]
    rdf_graph.add((doc_uri, RDF.type, ns.File))
    rdf_graph.add((doc_uri, ns.name, Literal(doc_name)))
    rdf_graph.add((doc_uri, ns.path, Literal(doc_path)))
    rdf_graph.add((doc_uri, ns.description, Literal(doc_description)))
    rdf_graph.add((doc_uri, ns.language, Literal("markdown")))
    rdf_graph.add((doc_uri, ns.last_modified, Literal(datetime.now().timestamp())))
    
    # Connect to docs_conventions directory if it exists
    if "docs_conventions" in nx_graph:
        if not nx_graph.has_edge("docs_conventions", doc_id):
            logger.info(f"Connecting {doc_id} to docs_conventions directory...")
            nx_graph.add_edge("docs_conventions", doc_id, relation="contains")
            rdf_graph.add((ns["docs_conventions"], ns.contains, doc_uri))
    else:
        logger.warning("docs_conventions directory node not found in the knowledge graph.")
    
    # Connect to code_quality component if it exists
    if "code_quality" in nx_graph:
        if not nx_graph.has_edge("code_quality", doc_id):
            logger.info(f"Connecting {doc_id} to code_quality component...")
            nx_graph.add_edge("code_quality", doc_id, relation="contains")
            rdf_graph.add((ns["code_quality"], ns.contains, doc_uri))
    
    return True


def add_code_quality_component(nx_graph, rdf_graph):
    """Add or update the code quality component in the knowledge graph."""
    ns = Namespace(f"http://{PROJECT_NAME.lower()}.org/")
    
    # Check if the component already exists
    if "code_quality" in nx_graph:
        logger.info("Code quality component already exists in the knowledge graph. Updating...")
        # Update existing node
        nx_graph.nodes["code_quality"]["status"] = "implemented"
    else:
        logger.info("Adding code quality component to the knowledge graph...")
        # Add new node
        nx_graph.add_node(
            "code_quality",
            type="component",
            name="Code Quality",
            description="Code quality standards and tools",
            status="implemented"
        )
    
    # Update RDF graph
    component_uri = ns["code_quality"]
    rdf_graph.add((component_uri, RDF.type, ns.Component))
    rdf_graph.add((component_uri, ns.name, Literal("Code Quality")))
    rdf_graph.add((component_uri, ns.description, Literal("Code quality standards and tools")))
    rdf_graph.add((component_uri, ns.status, Literal("implemented")))
    
    # Connect to project_root if not already connected
    if not nx_graph.has_edge("project_root", "code_quality"):
        logger.info("Connecting code_quality component to project_root...")
        nx_graph.add_edge("project_root", "code_quality", relation="contains")
        rdf_graph.add((ns["project_root"], ns.contains, component_uri))
    
    return True


def record_migration_decision(nx_graph, rdf_graph):
    """Record the creation of convention documents as a migration decision."""
    ns = Namespace(f"http://{PROJECT_NAME.lower()}.org/")
    
    # Generate a unique ID for the decision
    decision_id = f"decision_conventions_creation_{int(datetime.now().timestamp())}"
    
    # Add the decision node
    nx_graph.add_node(
        decision_id,
        type="decision",
        name="Creation of Convention Documents",
        description="Creation of style guide, coding conventions, review checklist, and graph guidelines",
        rationale="To establish gold standard code quality practices for the MCP-BASE-STACK project",
        timestamp=datetime.now().isoformat()
    )
    
    # Update RDF graph
    decision_uri = ns[decision_id]
    rdf_graph.add((decision_uri, RDF.type, ns.Decision))
    rdf_graph.add((decision_uri, ns.name, Literal("Creation of Convention Documents")))
    rdf_graph.add((decision_uri, ns.description, Literal("Creation of style guide, coding conventions, review checklist, and graph guidelines")))
    rdf_graph.add((decision_uri, ns.rationale, Literal("To establish gold standard code quality practices for the MCP-BASE-STACK project")))
    rdf_graph.add((decision_uri, ns.timestamp, Literal(datetime.now().isoformat())))
    
    # Connect to code_quality component
    if "code_quality" in nx_graph:
        nx_graph.add_edge("code_quality", decision_id, relation="has_decision")
        rdf_graph.add((ns["code_quality"], ns.has_decision, decision_uri))
    
    return True


def main():
    """Record the convention documents creation in the knowledge graph."""
    try:
        # Load the knowledge graph
        nx_graph, rdf_graph = load_knowledge_graph()
        
        # Add or update the code quality component
        add_code_quality_component(nx_graph, rdf_graph)
        
        # Record each convention document
        documents = [
            {
                "id": "style_guide",
                "name": "Style Guide",
                "path": "docs/conventions/style-guide.md",
                "description": "Coding standards and conventions for the MCP-BASE-STACK project"
            },
            {
                "id": "coding_conventions",
                "name": "Coding Conventions",
                "path": "docs/conventions/coding-conventions.md",
                "description": "Specific coding practices and patterns for the MCP-BASE-STACK project"
            },
            {
                "id": "review_checklist",
                "name": "Review Checklist",
                "path": "docs/conventions/review-checklist.md",
                "description": "Comprehensive checklist for code reviews in the MCP-BASE-STACK project"
            },
            {
                "id": "graph_guidelines",
                "name": "Graph Guidelines",
                "path": "docs/conventions/graph-guidelines.md",
                "description": "Standards and best practices for working with the knowledge graph"
            }
        ]
        
        for doc in documents:
            record_convention_document(
                nx_graph, 
                rdf_graph, 
                doc["id"], 
                doc["name"], 
                doc["path"], 
                doc["description"]
            )
        
        # Record the migration decision
        record_migration_decision(nx_graph, rdf_graph)
        
        # Save the knowledge graph
        save_knowledge_graph(nx_graph, rdf_graph)
        
        logger.info("Convention documents successfully recorded in the knowledge graph")
        return True
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    main()