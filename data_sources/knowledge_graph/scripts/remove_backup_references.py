#!/usr/bin/env python3

"""
Knowledge Graph Update Script for Backup System Changes

This script updates the Knowledge Graph to remove any references to the
local backup system, ensuring that only the git branch-based backup system
is referenced in the Knowledge Graph.
"""

import os
import sys
import logging
import networkx as nx
from rdflib import Graph, URIRef, Literal
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Define paths
PROJECT_ROOT = Path(__file__).resolve().parents[3]
KG_DATA_DIR = PROJECT_ROOT / "core" / "kg" / "data"
NX_GRAPH_PATH = KG_DATA_DIR / "knowledge_graph.graphml"
RDF_GRAPH_PATH = KG_DATA_DIR / "knowledge_graph.ttl"

def load_knowledge_graph():
    """Load the knowledge graph from files."""
    try:
        nx_graph = nx.read_graphml(NX_GRAPH_PATH)
        rdf_graph = Graph()
        rdf_graph.parse(RDF_GRAPH_PATH, format="turtle")
        logger.info("Knowledge graph loaded successfully.")
        return nx_graph, rdf_graph
    except Exception as e:
        logger.error(f"Error loading knowledge graph: {e}")
        sys.exit(1)

def save_knowledge_graph(nx_graph, rdf_graph):
    """Save the knowledge graph to files."""
    try:
        # Create backup of current KG
        timestamp = os.popen("date '+%Y%m%d-%H%M%S'").read().strip()
        backup_branch = f"backup-{timestamp}"
        os.system(f"cd {PROJECT_ROOT} && git checkout -b {backup_branch}")
        os.system(f"cd {PROJECT_ROOT} && git add {NX_GRAPH_PATH} {RDF_GRAPH_PATH}")
        os.system(f"cd {PROJECT_ROOT} && git commit -m 'Backup KG before removing backup system references'")
        os.system(f"cd {PROJECT_ROOT} && git checkout -")
        logger.info(f"Created backup of Knowledge Graph in branch: {backup_branch}")
        
        # Save updated graphs
        nx.write_graphml(nx_graph, NX_GRAPH_PATH)
        rdf_graph.serialize(destination=RDF_GRAPH_PATH, format="turtle")
        logger.info("Knowledge graph saved successfully.")
    except Exception as e:
        logger.error(f"Error saving knowledge graph: {e}")
        sys.exit(1)

def remove_backup_references(nx_graph, rdf_graph):
    """Remove references to the local backup system from the knowledge graph."""
    # Terms to search for in the NetworkX graph
    backup_terms = [
        "backup_dir", "directory-based backup", "local backup", 
        "backup directory", "backup_20250408", "essential_files_"
    ]
    
    # Track changes
    changes_made = False
    
    # Process NetworkX graph
    nodes_to_remove = []
    for node, attrs in nx_graph.nodes(data=True):
        # Check if any attribute contains backup terms
        for attr, value in attrs.items():
            if isinstance(value, str):
                for term in backup_terms:
                    if term in value.lower():
                        logger.info(f"Found backup reference in node {node}, attribute {attr}: {value}")
                        # If the node is specifically about local backup, mark for removal
                        if "local backup" in value.lower() or "directory-based backup" in value.lower():
                            nodes_to_remove.append(node)
                            changes_made = True
                            break
                        # Otherwise, update the attribute to remove the reference
                        elif "backup" in value.lower():
                            # Only modify if it's about local backup, not git backup
                            if "directory" in value.lower() or "local" in value.lower():
                                attrs[attr] = value.replace(term, "").strip()
                                changes_made = True
    
    # Remove marked nodes
    for node in nodes_to_remove:
        logger.info(f"Removing node: {node}")
        nx_graph.remove_node(node)
    
    # Process RDF graph
    # Search for triples containing backup terms
    backup_uris = []
    for s, p, o in rdf_graph:
        if isinstance(o, Literal):
            for term in backup_terms:
                if term in str(o).lower():
                    logger.info(f"Found backup reference in triple: {s} {p} {o}")
                    if "local backup" in str(o).lower() or "directory-based backup" in str(o).lower():
                        backup_uris.append(s)
                        changes_made = True
    
    # Remove triples with backup URIs
    for uri in backup_uris:
        logger.info(f"Removing triples with URI: {uri}")
        rdf_graph.remove((uri, None, None))
        rdf_graph.remove((None, None, uri))
    
    return changes_made

def main():
    """Main function to update the knowledge graph."""
    logger.info("Starting Knowledge Graph update to remove backup system references...")
    
    # Load the knowledge graph
    nx_graph, rdf_graph = load_knowledge_graph()
    
    # Remove backup references
    changes_made = remove_backup_references(nx_graph, rdf_graph)
    
    if changes_made:
        # Save the updated knowledge graph
        save_knowledge_graph(nx_graph, rdf_graph)
        logger.info("Knowledge Graph updated successfully to remove backup system references.")
    else:
        logger.info("No backup system references found in the Knowledge Graph. No changes made.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())