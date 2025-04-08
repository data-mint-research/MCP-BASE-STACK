#!/usr/bin/env python3
"""
Update documentation coverage metrics in the knowledge graph.

This script checks for the existence of README.md files in specified directories,
calculates documentation coverage percentage, and updates the knowledge graph with this information.
"""

import os
import sys
import json
import networkx as nx
from datetime import datetime
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS

# Configuration
KG_DATA_DIR = "core/kg/data"
PROJECT_NAME = "MCP-BASE-STACK"
REPORTS_DIR = "data/reports"

# Directories to check for documentation
DIRECTORIES_TO_CHECK = [
    "./scripts/maintenance",
    "./scripts/utils/cleanup",
    "./scripts/utils/validation",
    "./scripts/deployment",
    "./core/kg/scripts",
    "./scripts/utils/quality"
]

def update_documentation_coverage():
    """Update documentation coverage metrics in the knowledge graph."""
    print("Updating documentation coverage metrics...")
    
    # Load existing graphs
    try:
        nx_graph = nx.read_graphml(f"{KG_DATA_DIR}/knowledge_graph.graphml")
        rdf_graph = Graph()
        rdf_graph.parse(f"{KG_DATA_DIR}/knowledge_graph.ttl", format="turtle")
    except Exception as e:
        print(f"Error loading graphs: {e}")
        print("Please run setup_knowledge_graph.py first")
        sys.exit(1)
    
    # Namespace for RDF
    ns = Namespace(f"http://{PROJECT_NAME.lower()}.org/")
    
    # Check documentation coverage
    total_dirs = len(DIRECTORIES_TO_CHECK)
    documented_dirs = 0
    
    for directory in DIRECTORIES_TO_CHECK:
        if os.path.exists(f"{directory}/README.md"):
            documented_dirs += 1
            print(f"✓ {directory} is documented")
        else:
            print(f"✗ {directory} is not documented")
    
    # Calculate coverage percentage
    coverage_percentage = (documented_dirs / total_dirs) * 100 if total_dirs > 0 else 0
    print(f"Documentation coverage: {coverage_percentage:.2f}% ({documented_dirs}/{total_dirs} directories)")
    
    # Update or create documentation coverage metrics node
    node_id = "documentation_coverage_metrics"
    timestamp = datetime.now().timestamp()
    
    if node_id in nx_graph:
        # Update existing node
        nx_graph.nodes[node_id]["last_modified"] = timestamp
        nx_graph.nodes[node_id]["total_directories"] = total_dirs
        nx_graph.nodes[node_id]["documented_directories"] = documented_dirs
        nx_graph.nodes[node_id]["coverage_percentage"] = coverage_percentage
        nx_graph.nodes[node_id]["status"] = "updated"
        
        # Update RDF
        rdf_graph.add((ns[node_id], ns.last_modified, Literal(timestamp)))
        rdf_graph.add((ns[node_id], ns.total_directories, Literal(total_dirs)))
        rdf_graph.add((ns[node_id], ns.documented_directories, Literal(documented_dirs)))
        rdf_graph.add((ns[node_id], ns.coverage_percentage, Literal(coverage_percentage)))
        rdf_graph.add((ns[node_id], ns.status, Literal("updated")))
        
        print(f"Updated documentation coverage metrics in knowledge graph")
    else:
        # Add new node
        nx_graph.add_node(
            node_id,
            name="Documentation Coverage Metrics",
            type="metrics",
            component_type="documentation",
            description="Documentation coverage metrics for key directories",
            last_modified=timestamp,
            total_directories=total_dirs,
            documented_directories=documented_dirs,
            coverage_percentage=coverage_percentage,
            status="created"
        )
        
        # Update RDF
        rdf_graph.add((ns[node_id], RDF.type, ns.Metrics))
        rdf_graph.add((ns[node_id], ns.name, Literal("Documentation Coverage Metrics")))
        rdf_graph.add((ns[node_id], ns.component_type, Literal("documentation")))
        rdf_graph.add((ns[node_id], ns.description, Literal("Documentation coverage metrics for key directories")))
        rdf_graph.add((ns[node_id], ns.last_modified, Literal(timestamp)))
        rdf_graph.add((ns[node_id], ns.total_directories, Literal(total_dirs)))
        rdf_graph.add((ns[node_id], ns.documented_directories, Literal(documented_dirs)))
        rdf_graph.add((ns[node_id], ns.coverage_percentage, Literal(coverage_percentage)))
        rdf_graph.add((ns[node_id], ns.status, Literal("created")))
        
        # Create relationship with quality_metrics
        if "quality_metrics" in nx_graph:
            nx_graph.add_edge("quality_metrics", node_id, relationship="TRACKS")
            rdf_graph.add((ns["quality_metrics"], ns.TRACKS, ns[node_id]))
        
        print(f"Added new documentation coverage metrics to knowledge graph")
    
    # Save updated graphs
    nx.write_graphml(nx_graph, f"{KG_DATA_DIR}/knowledge_graph.graphml")
    rdf_graph.serialize(destination=f"{KG_DATA_DIR}/knowledge_graph.ttl", format="turtle")
    
    # Save metrics to JSON file
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "documentation_coverage_metrics": {
            "total_directories": total_dirs,
            "documented_directories": documented_dirs,
            "coverage_percentage": coverage_percentage
        }
    }
    
    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(f"{REPORTS_DIR}/documentation_coverage_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    
    print(f"Documentation coverage metrics saved to {REPORTS_DIR}/documentation_coverage_metrics.json")
    print("Knowledge Graph updated successfully.")

if __name__ == "__main__":
    update_documentation_coverage()