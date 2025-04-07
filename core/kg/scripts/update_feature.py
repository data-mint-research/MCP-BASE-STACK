#!/usr/bin/env python3
import networkx as nx
import argparse
import os
from datetime import datetime
from rdflib import Graph, Namespace, Literal

# Configuration
KG_DATA_DIR = "core/kg/data"
PROJECT_NAME = "MCP-BASE-STACK"

def update_feature(name, status):
    """Update the status of a feature after implementation"""
    # Load existing graphs
    nx_graph = nx.read_graphml(f"{KG_DATA_DIR}/knowledge_graph.graphml")
    rdf_graph = Graph()
    rdf_graph.parse(f"{KG_DATA_DIR}/knowledge_graph.ttl", format="turtle")
    
    # Namespace for RDF
    ns = Namespace(f"http://{PROJECT_NAME.lower()}.org/")
    
    # Find feature ID
    feature_id = f"feature_{name.lower().replace(' ', '_')}"
    
    # Update feature in NetworkX graph
    if feature_id in nx_graph:
        nx_graph.nodes[feature_id]['status'] = status
        nx_graph.nodes[feature_id]['updated_at'] = datetime.now().isoformat()
        
        # Update RDF graph
        rdf_graph.remove((ns[feature_id], ns.status, None))
        rdf_graph.add((ns[feature_id], ns.status, Literal(status)))
        rdf_graph.add((ns[feature_id], ns.updated_at, Literal(datetime.now().isoformat())))
        
        # Save updated graphs
        nx.write_graphml(nx_graph, f"{KG_DATA_DIR}/knowledge_graph.graphml")
        rdf_graph.serialize(destination=f"{KG_DATA_DIR}/knowledge_graph.ttl", format="turtle")
        
        print(f"Feature '{name}' updated to status: {status}")
    else:
        print(f"Feature '{name}' not found in Knowledge Graph")
        print("Please register the feature first using register_feature.py")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update a feature status in the Knowledge Graph")
    parser.add_argument("--name", required=True, help="Name of the feature")
    parser.add_argument("--status", required=True, choices=["planned", "in_progress", "completed", "testing", "deployed"], 
                       help="New status of the feature")
    
    args = parser.parse_args()
    update_feature(args.name, args.status)