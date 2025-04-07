#!/usr/bin/env python3
"""
Register the file cleanup feature in the knowledge graph.
"""

import os
import sys
import networkx as nx
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS

# Add parent directory to path to import common modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.register_feature import KG_DATA_DIR, PROJECT_NAME

def register_file_cleanup_feature():
    """Register the file cleanup feature in the knowledge graph"""
    print("Registering File Cleanup feature in Knowledge Graph...")
    
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
    
    # Register feature if it doesn't exist
    feature_id = "feature_file_cleanup"
    feature_name = "File Cleanup Tool"
    feature_description = "Identifies and safely removes orphaned or outdated files in the project"
    feature_owner = "Maintenance Team"
    
    if feature_id in nx_graph:
        print(f"Feature {feature_id} already exists, updating...")
        nx_graph.nodes[feature_id]['name'] = feature_name
        nx_graph.nodes[feature_id]['description'] = feature_description
        nx_graph.nodes[feature_id]['owner'] = feature_owner
        nx_graph.nodes[feature_id]['status'] = "implemented"
    else:
        print(f"Adding new feature {feature_id}...")
        nx_graph.add_node(
            feature_id,
            type="feature",
            name=feature_name,
            description=feature_description,
            owner=feature_owner,
            status="implemented"
        )
    
    # Update RDF
    rdf_graph.add((ns[feature_id], RDF.type, ns.Feature))
    rdf_graph.add((ns[feature_id], ns.name, Literal(feature_name)))
    rdf_graph.add((ns[feature_id], ns.description, Literal(feature_description)))
    rdf_graph.add((ns[feature_id], ns.owner, Literal(feature_owner)))
    rdf_graph.add((ns[feature_id], ns.status, Literal("implemented")))
    
    # Connect to project_root if not already connected
    if not nx_graph.has_edge("project_root", feature_id):
        nx_graph.add_edge("project_root", feature_id, relation="contains")
        rdf_graph.add((ns["project_root"], ns.contains, ns[feature_id]))
        print(f"Connected {feature_id} to project_root")
    
    # Add file_cleanup component
    component_id = "file_cleanup_component"
    if component_id in nx_graph:
        print(f"Component {component_id} already exists, updating...")
        nx_graph.nodes[component_id]['status'] = "implemented"
        nx_graph.nodes[component_id]['type'] = "component"
        nx_graph.nodes[component_id]['name'] = "File Cleanup Tool"
    else:
        print(f"Adding new component {component_id}...")
        nx_graph.add_node(
            component_id, 
            type="component", 
            name="File Cleanup Tool",
            status="implemented"
        )
    
    # Update RDF
    rdf_graph.add((ns[component_id], RDF.type, ns.Component))
    rdf_graph.add((ns[component_id], ns.name, Literal("File Cleanup Tool")))
    rdf_graph.add((ns[component_id], ns.status, Literal("implemented")))
    
    # Connect to project_root if not already connected
    if not nx_graph.has_edge("project_root", component_id):
        nx_graph.add_edge("project_root", component_id, relation="contains")
        rdf_graph.add((ns["project_root"], ns.contains, ns[component_id]))
        print(f"Connected {component_id} to project_root")
    
    # Add file nodes
    files = [
        ("cleanup_files.py", "cleanup_script", "python"),
        ("cleanup-report.json", "cleanup_report", "json")
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
        
        # Connect to component if not already connected
        if not nx_graph.has_edge(component_id, file_id):
            nx_graph.add_edge(component_id, file_id, relation="contains")
            rdf_graph.add((ns[component_id], ns.contains, ns[file_id]))
            print(f"Connected {file_id} to {component_id}")
    
    # Connect component to feature
    if not nx_graph.has_edge(component_id, feature_id):
        nx_graph.add_edge(component_id, feature_id, relation="implements")
        rdf_graph.add((ns[component_id], ns.implements, ns[feature_id]))
        print(f"Connected {component_id} to {feature_id}")
    
    # Add documentation relationship
    doc_file_id = "file_cleanup_guide"
    doc_file_path = "docs/file-cleanup-guide.md"
    
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
    if "docs" in nx_graph and not nx_graph.has_edge("docs", doc_file_id):
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
    
    print("File cleanup feature successfully registered in Knowledge Graph")

if __name__ == "__main__":
    register_file_cleanup_feature()