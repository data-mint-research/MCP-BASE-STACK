#!/usr/bin/env python3
import networkx as nx
import os
import sys
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS

# Configuration
KG_DATA_DIR = "core/kg/data"
PROJECT_NAME = "MCP-BASE-STACK"

def add_git_hooks_to_kg():
    """Add Git Hooks component and related files to the Knowledge Graph"""
    print("Adding Git Hooks to Knowledge Graph...")
    
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
    
    # Add git_hooks component
    component_id = "git_hooks"
    if component_id in nx_graph:
        print(f"Component {component_id} already exists, updating...")
        nx_graph.nodes[component_id]['status'] = "implemented"
        nx_graph.nodes[component_id]['type'] = "component"
        nx_graph.nodes[component_id]['name'] = "Git Hooks"
    else:
        print(f"Adding new component {component_id}...")
        nx_graph.add_node(
            component_id, 
            type="component", 
            name="Git Hooks",
            status="implemented"
        )
    
    # Update RDF
    rdf_graph.add((ns[component_id], RDF.type, ns.Component))
    rdf_graph.add((ns[component_id], ns.name, Literal("Git Hooks")))
    rdf_graph.add((ns[component_id], ns.status, Literal("implemented")))
    
    # Connect to project_root if not already connected
    if not nx_graph.has_edge("project_root", component_id):
        nx_graph.add_edge("project_root", component_id, relation="contains")
        rdf_graph.add((ns["project_root"], ns.contains, ns[component_id]))
        print(f"Connected {component_id} to project_root")
    
    # Add file nodes
    files = [
        (".git-hooks/pre-commit", "pre_commit_hook", "bash"),
        ("install-file-update-hooks.sh", "install_hooks_script", "bash"),
        (".git-hooks/README.md", "hooks_documentation", "markdown")
    ]
    
    for file_path, file_id, language in files:
        if file_id in nx_graph:
            print(f"File {file_id} already exists, updating...")
            nx_graph.nodes[file_id]['path'] = file_path
            nx_graph.nodes[file_id]['type'] = "file"
            nx_graph.nodes[file_id]['language'] = language
        else:
            print(f"Adding new file {file_id}...")
            nx_graph.add_node(
                file_id,
                type="file",
                path=file_path,
                language=language
            )
        
        # Update RDF
        rdf_graph.add((ns[file_id], RDF.type, ns.File))
        rdf_graph.add((ns[file_id], ns.path, Literal(file_path)))
        rdf_graph.add((ns[file_id], ns.language, Literal(language)))
        
        # Connect to git_hooks component if not already connected
        if not nx_graph.has_edge(component_id, file_id):
            nx_graph.add_edge(component_id, file_id, relation="contains")
            rdf_graph.add((ns[component_id], ns.contains, ns[file_id]))
            print(f"Connected {file_id} to {component_id}")
    
    # Connect to feature
    feature_id = "feature_git_file_update_hooks"
    if feature_id in nx_graph:
        if not nx_graph.has_edge(component_id, feature_id):
            nx_graph.add_edge(component_id, feature_id, relation="implements")
            rdf_graph.add((ns[component_id], ns.implements, ns[feature_id]))
            print(f"Connected {component_id} to {feature_id}")
    else:
        print(f"Warning: Feature {feature_id} not found in the Knowledge Graph")
    
    # Add documentation relationship
    if "docs" in nx_graph:
        doc_file_id = "git_hooks_kg_integration_plan"
        doc_file_path = "docs/git-hooks-kg-integration-plan.md"
        
        if doc_file_id in nx_graph:
            print(f"Documentation {doc_file_id} already exists, updating...")
            nx_graph.nodes[doc_file_id]['path'] = doc_file_path
            nx_graph.nodes[doc_file_id]['type'] = "file"
            nx_graph.nodes[doc_file_id]['language'] = "markdown"
        else:
            print(f"Adding new documentation {doc_file_id}...")
            nx_graph.add_node(
                doc_file_id,
                type="file",
                path=doc_file_path,
                language="markdown"
            )
        
        # Update RDF
        rdf_graph.add((ns[doc_file_id], RDF.type, ns.File))
        rdf_graph.add((ns[doc_file_id], ns.path, Literal(doc_file_path)))
        rdf_graph.add((ns[doc_file_id], ns.language, Literal("markdown")))
        
        # Connect to docs directory
        if not nx_graph.has_edge("docs", doc_file_id):
            nx_graph.add_edge("docs", doc_file_id, relation="contains")
            rdf_graph.add((ns["docs"], ns.contains, ns[doc_file_id]))
            print(f"Connected {doc_file_id} to docs")
        
        # Add DOCUMENTS relationship to feature
        if not nx_graph.has_edge(doc_file_id, feature_id):
            nx_graph.add_edge(doc_file_id, feature_id, relation="documents")
            rdf_graph.add((ns[doc_file_id], ns.documents, ns[feature_id]))
            print(f"Added DOCUMENTS relationship from {doc_file_id} to {feature_id}")
    
    # Save updated graphs
    nx.write_graphml(nx_graph, f"{KG_DATA_DIR}/knowledge_graph.graphml")
    rdf_graph.serialize(destination=f"{KG_DATA_DIR}/knowledge_graph.ttl", format="turtle")
    
    print("Git Hooks successfully added to Knowledge Graph")

if __name__ == "__main__":
    add_git_hooks_to_kg()