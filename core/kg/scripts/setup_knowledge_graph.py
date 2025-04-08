#!/usr/bin/env python3
"""
Knowledge Graph Setup Script

This script initializes the knowledge graph for the MCP-BASE-STACK project.
It creates the necessary files and directories, and populates the graph with
initial data based on the current state of the project.

Usage:
    python setup_knowledge_graph.py
"""

import os
import sys
import json
import datetime
import networkx as nx
from pathlib import Path
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS

# Configuration
KG_DATA_DIR = "core/kg/data"
PROJECT_NAME = "MCP-BASE-STACK"
QUALITY_REPORTS_DIR = "data/reports"

def setup_knowledge_graph():
    """Set up the knowledge graph for the MCP-BASE-STACK project."""
    print("Setting up knowledge graph...")
    
    # Create the data directory if it doesn't exist
    os.makedirs(KG_DATA_DIR, exist_ok=True)
    
    # Create a new NetworkX graph
    nx_graph = nx.DiGraph()
    
    # Create a new RDF graph
    rdf_graph = Graph()
    
    # Namespace for RDF
    ns = Namespace(f"http://{PROJECT_NAME.lower()}.org/")
    
    # Add project node
    nx_graph.add_node(
        "project",
        name=PROJECT_NAME,
        type="project",
        description="Model Context Protocol Base Stack",
        created=datetime.datetime.now().timestamp(),
        last_modified=datetime.datetime.now().timestamp(),
        status="active"
    )
    
    # Add project to RDF graph
    rdf_graph.add((ns["project"], RDF.type, ns.Project))
    rdf_graph.add((ns["project"], ns.name, Literal(PROJECT_NAME)))
    rdf_graph.add((ns["project"], ns.description, Literal("Model Context Protocol Base Stack")))
    rdf_graph.add((ns["project"], ns.created, Literal(datetime.datetime.now().timestamp())))
    rdf_graph.add((ns["project"], ns.last_modified, Literal(datetime.datetime.now().timestamp())))
    rdf_graph.add((ns["project"], ns.status, Literal("active")))
    
    # Add quality metrics node
    nx_graph.add_node(
        "quality_metrics",
        name="Quality Metrics",
        type="metrics",
        description="Quality metrics for the project",
        created=datetime.datetime.now().timestamp(),
        last_modified=datetime.datetime.now().timestamp(),
        status="active"
    )
    
    # Add quality metrics to RDF graph
    rdf_graph.add((ns["quality_metrics"], RDF.type, ns.Metrics))
    rdf_graph.add((ns["quality_metrics"], ns.name, Literal("Quality Metrics")))
    rdf_graph.add((ns["quality_metrics"], ns.description, Literal("Quality metrics for the project")))
    rdf_graph.add((ns["quality_metrics"], ns.created, Literal(datetime.datetime.now().timestamp())))
    rdf_graph.add((ns["quality_metrics"], ns.last_modified, Literal(datetime.datetime.now().timestamp())))
    rdf_graph.add((ns["quality_metrics"], ns.status, Literal("active")))
    
    # Add relationship between project and quality metrics
    nx_graph.add_edge("project", "quality_metrics", relationship="HAS_METRICS")
    rdf_graph.add((ns["project"], ns.HAS_METRICS, ns["quality_metrics"]))
    
    # Add file structure metrics node
    nx_graph.add_node(
        "file_structure_metrics",
        name="File Structure Metrics",
        type="metrics",
        component_type="file_structure",
        description="File structure standardization metrics",
        created=datetime.datetime.now().timestamp(),
        last_modified=datetime.datetime.now().timestamp(),
        status="active"
    )
    
    # Add file structure metrics to RDF graph
    rdf_graph.add((ns["file_structure_metrics"], RDF.type, ns.Metrics))
    rdf_graph.add((ns["file_structure_metrics"], ns.name, Literal("File Structure Metrics")))
    rdf_graph.add((ns["file_structure_metrics"], ns.component_type, Literal("file_structure")))
    rdf_graph.add((ns["file_structure_metrics"], ns.description, Literal("File structure standardization metrics")))
    rdf_graph.add((ns["file_structure_metrics"], ns.created, Literal(datetime.datetime.now().timestamp())))
    rdf_graph.add((ns["file_structure_metrics"], ns.last_modified, Literal(datetime.datetime.now().timestamp())))
    rdf_graph.add((ns["file_structure_metrics"], ns.status, Literal("active")))
    
    # Add relationship between quality metrics and file structure metrics
    nx_graph.add_edge("quality_metrics", "file_structure_metrics", relationship="TRACKS")
    rdf_graph.add((ns["quality_metrics"], ns.TRACKS, ns["file_structure_metrics"]))
    
    # Add dependency metrics node
    nx_graph.add_node(
        "dependency_metrics",
        name="Dependency Metrics",
        type="metrics",
        component_type="dependency",
        description="Dependency management metrics",
        created=datetime.datetime.now().timestamp(),
        last_modified=datetime.datetime.now().timestamp(),
        status="active"
    )
    
    # Add dependency metrics to RDF graph
    rdf_graph.add((ns["dependency_metrics"], RDF.type, ns.Metrics))
    rdf_graph.add((ns["dependency_metrics"], ns.name, Literal("Dependency Metrics")))
    rdf_graph.add((ns["dependency_metrics"], ns.component_type, Literal("dependency")))
    rdf_graph.add((ns["dependency_metrics"], ns.description, Literal("Dependency management metrics")))
    rdf_graph.add((ns["dependency_metrics"], ns.created, Literal(datetime.datetime.now().timestamp())))
    rdf_graph.add((ns["dependency_metrics"], ns.last_modified, Literal(datetime.datetime.now().timestamp())))
    rdf_graph.add((ns["dependency_metrics"], ns.status, Literal("active")))
    
    # Add relationship between quality metrics and dependency metrics
    nx_graph.add_edge("quality_metrics", "dependency_metrics", relationship="TRACKS")
    rdf_graph.add((ns["quality_metrics"], ns.TRACKS, ns["dependency_metrics"]))
    
    # Add documentation metrics node
    nx_graph.add_node(
        "documentation_metrics",
        name="Documentation Metrics",
        type="metrics",
        component_type="documentation",
        description="Documentation coverage metrics",
        created=datetime.datetime.now().timestamp(),
        last_modified=datetime.datetime.now().timestamp(),
        status="active"
    )
    
    # Add documentation metrics to RDF graph
    rdf_graph.add((ns["documentation_metrics"], RDF.type, ns.Metrics))
    rdf_graph.add((ns["documentation_metrics"], ns.name, Literal("Documentation Metrics")))
    rdf_graph.add((ns["documentation_metrics"], ns.component_type, Literal("documentation")))
    rdf_graph.add((ns["documentation_metrics"], ns.description, Literal("Documentation coverage metrics")))
    rdf_graph.add((ns["documentation_metrics"], ns.created, Literal(datetime.datetime.now().timestamp())))
    rdf_graph.add((ns["documentation_metrics"], ns.last_modified, Literal(datetime.datetime.now().timestamp())))
    rdf_graph.add((ns["documentation_metrics"], ns.status, Literal("active")))
    
    # Add relationship between quality metrics and documentation metrics
    nx_graph.add_edge("quality_metrics", "documentation_metrics", relationship="TRACKS")
    rdf_graph.add((ns["quality_metrics"], ns.TRACKS, ns["documentation_metrics"]))
    
    # Add code quality metrics node
    nx_graph.add_node(
        "code_quality_metrics",
        name="Code Quality Metrics",
        type="metrics",
        component_type="code_quality",
        description="Code quality metrics",
        created=datetime.datetime.now().timestamp(),
        last_modified=datetime.datetime.now().timestamp(),
        status="active"
    )
    
    # Add code quality metrics to RDF graph
    rdf_graph.add((ns["code_quality_metrics"], RDF.type, ns.Metrics))
    rdf_graph.add((ns["code_quality_metrics"], ns.name, Literal("Code Quality Metrics")))
    rdf_graph.add((ns["code_quality_metrics"], ns.component_type, Literal("code_quality")))
    rdf_graph.add((ns["code_quality_metrics"], ns.description, Literal("Code quality metrics")))
    rdf_graph.add((ns["code_quality_metrics"], ns.created, Literal(datetime.datetime.now().timestamp())))
    rdf_graph.add((ns["code_quality_metrics"], ns.last_modified, Literal(datetime.datetime.now().timestamp())))
    rdf_graph.add((ns["code_quality_metrics"], ns.status, Literal("active")))
    
    # Add relationship between quality metrics and code quality metrics
    nx_graph.add_edge("quality_metrics", "code_quality_metrics", relationship="TRACKS")
    rdf_graph.add((ns["quality_metrics"], ns.TRACKS, ns["code_quality_metrics"]))
    
    # Add MCP compliance node
    nx_graph.add_node(
        "mcp_compliance",
        name="MCP Compliance",
        type="compliance",
        description="MCP compliance status",
        created=datetime.datetime.now().timestamp(),
        last_modified=datetime.datetime.now().timestamp(),
        status="active"
    )
    
    # Add MCP compliance to RDF graph
    rdf_graph.add((ns["mcp_compliance"], RDF.type, ns.Compliance))
    rdf_graph.add((ns["mcp_compliance"], ns.name, Literal("MCP Compliance")))
    rdf_graph.add((ns["mcp_compliance"], ns.description, Literal("MCP compliance status")))
    rdf_graph.add((ns["mcp_compliance"], ns.created, Literal(datetime.datetime.now().timestamp())))
    rdf_graph.add((ns["mcp_compliance"], ns.last_modified, Literal(datetime.datetime.now().timestamp())))
    rdf_graph.add((ns["mcp_compliance"], ns.status, Literal("active")))
    
    # Add relationship between project and MCP compliance
    nx_graph.add_edge("project", "mcp_compliance", relationship="HAS_COMPLIANCE")
    rdf_graph.add((ns["project"], ns.HAS_COMPLIANCE, ns["mcp_compliance"]))
    
    # Update metrics from final quality report if available
    final_report_path = os.path.join(QUALITY_REPORTS_DIR, "final_quality_report.json")
    if os.path.exists(final_report_path):
        print(f"Updating metrics from {final_report_path}...")
        try:
            with open(final_report_path, 'r') as f:
                report_data = json.load(f)
            
            # Update file structure metrics
            if "metrics" in report_data and "file_structure" in report_data["metrics"]:
                fs_metrics = report_data["metrics"]["file_structure"]
                for key, value in fs_metrics.items():
                    nx_graph.nodes["file_structure_metrics"][key] = value
                    rdf_graph.add((ns["file_structure_metrics"], ns[key], Literal(value)))
            
            # Update dependency metrics
            if "metrics" in report_data and "dependency_management" in report_data["metrics"]:
                dep_metrics = report_data["metrics"]["dependency_management"]
                for key, value in dep_metrics.items():
                    nx_graph.nodes["dependency_metrics"][key] = value
                    rdf_graph.add((ns["dependency_metrics"], ns[key], Literal(value)))
            
            # Update documentation metrics
            if "metrics" in report_data and "documentation" in report_data["metrics"]:
                doc_metrics = report_data["metrics"]["documentation"]
                for key, value in doc_metrics.items():
                    nx_graph.nodes["documentation_metrics"][key] = value
                    rdf_graph.add((ns["documentation_metrics"], ns[key], Literal(value)))
            
            # Update code quality metrics
            if "metrics" in report_data and "code_quality" in report_data["metrics"]:
                cq_metrics = report_data["metrics"]["code_quality"]
                for key, value in cq_metrics.items():
                    nx_graph.nodes["code_quality_metrics"][key] = value
                    rdf_graph.add((ns["code_quality_metrics"], ns[key], Literal(value)))
            
            # Update MCP compliance
            if "mcp_compliance" in report_data:
                mcp_comp = report_data["mcp_compliance"]
                for key, value in mcp_comp.items():
                    if isinstance(value, dict) and "status" in value:
                        nx_graph.nodes["mcp_compliance"][key] = value["status"]
                        rdf_graph.add((ns["mcp_compliance"], ns[key], Literal(value["status"])))
            
            print("Metrics updated from final quality report.")
        except Exception as e:
            print(f"Error updating metrics from final quality report: {e}")
    
    # Save the graphs
    nx.write_graphml(nx_graph, os.path.join(KG_DATA_DIR, "knowledge_graph.graphml"))
    rdf_graph.serialize(destination=os.path.join(KG_DATA_DIR, "knowledge_graph.ttl"), format="turtle")
    
    print(f"Knowledge graph saved to {KG_DATA_DIR}/knowledge_graph.graphml and {KG_DATA_DIR}/knowledge_graph.ttl")
    print("Knowledge graph setup complete.")

if __name__ == "__main__":
    setup_knowledge_graph()