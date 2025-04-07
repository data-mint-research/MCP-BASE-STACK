#!/usr/bin/env python3
import networkx as nx
import argparse
import os
from datetime import datetime
from rdflib import Graph, Namespace, Literal

# Configuration
KG_DATA_DIR = "kg/data"
PROJECT_NAME = "MCP-BASE-STACK"

def register_feature(name, description, owner):
    """Register a new feature in the Knowledge Graph before implementation"""
    # Load existing graphs
    nx_graph = nx.read_graphml(f"{KG_DATA_DIR}/knowledge_graph.graphml")
    rdf_graph = Graph()
    rdf_graph.parse(f"{KG_DATA_DIR}/knowledge_graph.ttl", format="turtle")
    
    # Namespace for RDF
    ns = Namespace(f"http://{PROJECT_NAME.lower()}.org/")
    
    # Create feature ID (sanitized name)
    feature_id = f"feature_{name.lower().replace(' ', '_')}"
    
    # Add feature to NetworkX graph
    nx_graph.add_node(feature_id, 
                      type="feature", 
                      name=name, 
                      description=description,
                      owner=owner,
                      status="planned",
                      created_at=datetime.now().isoformat())
    
    # Connect feature to project root
    nx_graph.add_edge("project_root", feature_id, relation="contains")
    
    # Add to RDF graph
    rdf_graph.add((ns[feature_id], ns.type, ns.Feature))
    rdf_graph.add((ns[feature_id], ns.name, Literal(name)))
    rdf_graph.add((ns[feature_id], ns.description, Literal(description)))
    rdf_graph.add((ns[feature_id], ns.owner, Literal(owner)))
    rdf_graph.add((ns[feature_id], ns.status, Literal("planned")))
    rdf_graph.add((ns[feature_id], ns.created_at, Literal(datetime.now().isoformat())))
    rdf_graph.add((ns.project, ns.contains, ns[feature_id]))
    
    # Save updated graphs
    nx.write_graphml(nx_graph, f"{KG_DATA_DIR}/knowledge_graph.graphml")
    rdf_graph.serialize(destination=f"{KG_DATA_DIR}/knowledge_graph.ttl", format="turtle")
    
    print(f"Feature '{name}' registered successfully with ID: {feature_id}")
    return feature_id

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Register a new feature in the Knowledge Graph")
    parser.add_argument("--name", required=True, help="Name of the feature")
    parser.add_argument("--description", required=True, help="Description of the feature")
    parser.add_argument("--owner", required=True, help="Owner/implementer of the feature")
    
    args = parser.parse_args()
    register_feature(args.name, args.description, args.owner)