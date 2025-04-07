#!/usr/bin/env python3
"""
Record the GitHub Actions workflow file in the knowledge graph.

This script records the GitHub Actions workflow file for code quality checks
as a continuous integration implementation in the knowledge graph,
documenting the rationale and purpose.
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


def record_workflow_file(nx_graph, rdf_graph):
    """Record the GitHub Actions workflow file in the knowledge graph."""
    ns = Namespace(f"http://{PROJECT_NAME.lower()}.org/")
    
    file_id = "github_actions_workflow"
    file_name = "code-quality.yml"
    file_path = ".github/workflows/code-quality.yml"
    file_description = "GitHub Actions workflow for automated code quality checks"
    file_language = "yaml"
    
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
    
    # Connect to code_quality component if it exists
    if "code_quality" in nx_graph:
        if not nx_graph.has_edge("code_quality", file_id):
            logger.info(f"Connecting {file_id} to code_quality component...")
            nx_graph.add_edge("code_quality", file_id, relation="contains")
            rdf_graph.add((ns["code_quality"], ns.contains, file_uri))
    else:
        logger.warning("code_quality component node not found in the knowledge graph.")
    
    return True


def record_ci_implementation_decision(nx_graph, rdf_graph):
    """Record the implementation of CI for code quality as a decision."""
    ns = Namespace(f"http://{PROJECT_NAME.lower()}.org/")
    
    # Generate a unique ID for the decision
    decision_id = f"decision_ci_code_quality_{int(datetime.now().timestamp())}"
    
    # Add the decision node
    nx_graph.add_node(
        decision_id,
        type="decision",
        name="Implementation of CI for Code Quality",
        description="Implementation of GitHub Actions workflow for continuous integration of code quality checks",
        rationale="To automate code quality checks on push and pull requests, ensuring consistent code quality standards across the project",
        timestamp=datetime.now().isoformat()
    )
    
    # Update RDF graph
    decision_uri = ns[decision_id]
    rdf_graph.add((decision_uri, RDF.type, ns.Decision))
    rdf_graph.add((decision_uri, ns.name, Literal("Implementation of CI for Code Quality")))
    rdf_graph.add((decision_uri, ns.description, Literal("Implementation of GitHub Actions workflow for continuous integration of code quality checks")))
    rdf_graph.add((decision_uri, ns.rationale, Literal("To automate code quality checks on push and pull requests, ensuring consistent code quality standards across the project")))
    rdf_graph.add((decision_uri, ns.timestamp, Literal(datetime.now().isoformat())))
    
    # Connect to code_quality component
    if "code_quality" in nx_graph:
        nx_graph.add_edge("code_quality", decision_id, relation="has_decision")
        rdf_graph.add((ns["code_quality"], ns.has_decision, decision_uri))
    
    # Connect to the workflow file
    if "github_actions_workflow" in nx_graph:
        nx_graph.add_edge("github_actions_workflow", decision_id, relation="implements")
        rdf_graph.add((ns["github_actions_workflow"], ns.implements, decision_uri))
    
    return True


def main():
    """Record the GitHub Actions workflow in the knowledge graph."""
    try:
        # Load the knowledge graph
        nx_graph, rdf_graph = load_knowledge_graph()
        
        # Record the GitHub Actions workflow file
        record_workflow_file(nx_graph, rdf_graph)
        
        # Record the CI implementation decision
        record_ci_implementation_decision(nx_graph, rdf_graph)
        
        # Save the knowledge graph
        save_knowledge_graph(nx_graph, rdf_graph)
        
        logger.info("GitHub Actions workflow successfully recorded in the knowledge graph")
        return True
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    main()