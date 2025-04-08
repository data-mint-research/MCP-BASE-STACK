#!/usr/bin/env python3
"""
Update Knowledge Graph with Quality Metrics Dashboard

This script updates the knowledge graph with information about the Quality Metrics Dashboard
component. It adds a new node for the dashboard and establishes relationships with other
quality-related components.
"""

import logging
import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).resolve().parents[3]))

import networkx as nx
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Get logger
logger = logging.getLogger("update_kg_dashboard")

# Constants
KG_DATA_DIR = "core/kg/data"
PROJECT_NAME = "MCP-BASE-STACK"

def update_knowledge_graph():
    """Update the Knowledge Graph with Quality Metrics Dashboard information."""
    logger.info("Updating Knowledge Graph with Quality Metrics Dashboard information...")
    
    # Load existing graphs
    try:
        nx_graph = nx.read_graphml(f"{KG_DATA_DIR}/knowledge_graph.graphml")
        rdf_graph = Graph()
        rdf_graph.parse(f"{KG_DATA_DIR}/knowledge_graph.ttl", format="turtle")
    except Exception as e:
        logger.error(f"Error loading graphs: {e}")
        logger.error("Please run setup_knowledge_graph.py first")
        sys.exit(1)
    
    # Namespace for RDF
    ns = Namespace(f"http://{PROJECT_NAME.lower()}.org/")
    
    # Add Quality Metrics Dashboard node
    dashboard_id = "quality_metrics_dashboard"
    
    if dashboard_id in nx_graph:
        # Update existing node
        nx_graph.nodes[dashboard_id]["name"] = "Quality Metrics Dashboard"
        nx_graph.nodes[dashboard_id]["description"] = "Centralized dashboard for quality metrics, trend analysis, and improvement tracking"
        nx_graph.nodes[dashboard_id]["type"] = "component"
        nx_graph.nodes[dashboard_id]["component_type"] = "dashboard"
        nx_graph.nodes[dashboard_id]["status"] = "implemented"
        
        # Update RDF
        rdf_graph.add((ns[dashboard_id], ns.name, Literal("Quality Metrics Dashboard")))
        rdf_graph.add((ns[dashboard_id], ns.description, Literal("Centralized dashboard for quality metrics, trend analysis, and improvement tracking")))
        rdf_graph.add((ns[dashboard_id], ns.status, Literal("implemented")))
        
        logger.info(f"Updated {dashboard_id} node")
    else:
        # Add new node
        nx_graph.add_node(
            dashboard_id,
            name="Quality Metrics Dashboard",
            description="Centralized dashboard for quality metrics, trend analysis, and improvement tracking",
            type="component",
            component_type="dashboard",
            status="implemented"
        )
        
        # Update RDF
        rdf_graph.add((ns[dashboard_id], RDF.type, ns.Component))
        rdf_graph.add((ns[dashboard_id], ns.name, Literal("Quality Metrics Dashboard")))
        rdf_graph.add((ns[dashboard_id], ns.description, Literal("Centralized dashboard for quality metrics, trend analysis, and improvement tracking")))
        rdf_graph.add((ns[dashboard_id], ns.component_type, Literal("dashboard")))
        rdf_graph.add((ns[dashboard_id], ns.status, Literal("implemented")))
        
        logger.info(f"Added new node {dashboard_id}")
    
    # Add relationships
    relationships = [
        # Dashboard uses Quality Enforcer
        (dashboard_id, "quality_enforcer", "uses"),
        # Dashboard uses Knowledge Graph
        (dashboard_id, "knowledge_graph", "uses"),
        # Dashboard visualizes Quality Metrics
        (dashboard_id, "quality_metrics", "visualizes"),
        # Dashboard is part of Quality System
        (dashboard_id, "quality_system", "part_of")
    ]
    
    for source, target, relationship in relationships:
        if target in nx_graph:
            # Add edge if it doesn't exist
            if not nx_graph.has_edge(source, target):
                nx_graph.add_edge(source, target, relationship=relationship)
                rdf_graph.add((ns[source], ns[relationship], ns[target]))
                logger.info(f"Added relationship: {source} {relationship} {target}")
    
    # Save updated graphs
    nx.write_graphml(nx_graph, f"{KG_DATA_DIR}/knowledge_graph.graphml")
    rdf_graph.serialize(destination=f"{KG_DATA_DIR}/knowledge_graph.ttl", format="turtle")
    
    logger.info("Knowledge Graph updated successfully with Quality Metrics Dashboard information.")

if __name__ == "__main__":
    update_knowledge_graph()