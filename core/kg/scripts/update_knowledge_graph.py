import networkx as nx
import os
import sys
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS

# Configuration
KG_DATA_DIR = "core/kg/data"
PROJECT_NAME = "MCP-BASE-STACK"

def update_knowledge_graph():
    """Update the Knowledge Graph based on current implementation status"""
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
    
    # Update implementation status based on file existence
    component_checks = [
        # Component ID, File to check, Status attribute
        ("nvidia_gpu", "nvidia-smi-output.txt", "verified"),
        ("docker", "docker-version.txt", "installed"),
        ("nvidia_container", "nvidia-container-output.txt", "configured"),
        ("librechat", "services/librechat/docker-compose.yml", "cloned"),
        ("librechat", "services/librechat/config/librechat.yaml", "configured"),
        ("librechat", "librechat-status.txt", "deployed"),
        ("llm_server", "data/logs/llm-server-status.txt", "deployed"),
        ("mistral", "mistral-model.txt", "loaded"),
        ("deepseek", "deepseek-model.txt", "loaded"),
        ("mcp_server", "services/mcp-server/src/app.py", "implemented"),
        ("documentation", "docs/README.md", "created"),
        ("tests", "tests/README.md", "created")
    ]
    
    # Update status based on file checks
    for component_id, check_file, status in component_checks:
        if os.path.exists(check_file):
            if component_id in nx_graph:
                nx_graph.nodes[component_id]['status'] = status
                
                # Update RDF
                rdf_graph.add((ns[component_id], ns.status, Literal(status)))
                
                print(f"Updated {component_id} status to '{status}'")
            else:
                # Add new component if it doesn't exist
                nx_graph.add_node(component_id, status=status, type="component")
                
                # Update RDF
                rdf_graph.add((ns[component_id], RDF.type, ns.Component))
                rdf_graph.add((ns[component_id], ns.status, Literal(status)))
                
                print(f"Added new component {component_id} with status '{status}'")
    
    # Automatically detect and track docs and tests directories
    update_directory_structure(nx_graph, rdf_graph, ns)
    
    # Save updated graphs
    nx.write_graphml(nx_graph, f"{KG_DATA_DIR}/knowledge_graph.graphml")
    rdf_graph.serialize(destination=f"{KG_DATA_DIR}/knowledge_graph.ttl", format="turtle")
    
    print("Knowledge Graph updated successfully.")

def update_directory_structure(nx_graph, rdf_graph, ns):
    """Update the Knowledge Graph with directory structure information"""
    # Check for docs directory
    if os.path.exists("docs"):
        update_directory_info(nx_graph, rdf_graph, ns, "docs", "docs")
        
        # Process docs subdirectories
        for subdir in ["knowledge-graph", "tutorials", "troubleshooting", "conventions"]:
            if os.path.exists(f"docs/{subdir}"):
                update_directory_info(nx_graph, rdf_graph, ns, f"docs/{subdir}", f"docs_{subdir}")
                
                # Create relationship between docs and subdirectory
                if "docs" in nx_graph and f"docs_{subdir}" in nx_graph:
                    nx_graph.add_edge("docs", f"docs_{subdir}", relationship="contains")
                    rdf_graph.add((ns["docs"], ns.contains, ns[f"docs_{subdir}"]))
                
                # Count files in subdirectory
                file_count = len([f for f in os.listdir(f"docs/{subdir}") if f.endswith('.md')])
                if f"docs_{subdir}" in nx_graph:
                    nx_graph.nodes[f"docs_{subdir}"]["file_count"] = file_count
                    rdf_graph.add((ns[f"docs_{subdir}"], ns.file_count, Literal(file_count)))
    
    # Check for tests directory
    if os.path.exists("tests"):
        update_directory_info(nx_graph, rdf_graph, ns, "tests", "tests")
        
        # Process tests subdirectories
        test_subdirs = ["unit", "integration", "agent_tests", "e2e", "performance", "regression", "data"]
        for subdir in test_subdirs:
            if os.path.exists(f"tests/{subdir}"):
                update_directory_info(nx_graph, rdf_graph, ns, f"tests/{subdir}", f"tests_{subdir}")
                
                # Create relationship between tests and subdirectory
                if "tests" in nx_graph and f"tests_{subdir}" in nx_graph:
                    nx_graph.add_edge("tests", f"tests_{subdir}", relationship="contains")
                    rdf_graph.add((ns["tests"], ns.contains, ns[f"tests_{subdir}"]))
                
                # Count files in subdirectory recursively
                file_count = count_files_recursive(f"tests/{subdir}")
                if f"tests_{subdir}" in nx_graph:
                    nx_graph.nodes[f"tests_{subdir}"]["file_count"] = file_count
                    rdf_graph.add((ns[f"tests_{subdir}"], ns.file_count, Literal(file_count)))

def update_directory_info(nx_graph, rdf_graph, ns, path, node_id):
    """Add or update directory information in the graph"""
    if node_id in nx_graph:
        # Update existing node
        nx_graph.nodes[node_id]["path"] = path
        nx_graph.nodes[node_id]["last_modified"] = os.path.getmtime(path)
        
        # Update RDF
        rdf_graph.add((ns[node_id], ns.path, Literal(path)))
        rdf_graph.add((ns[node_id], ns.last_modified, Literal(os.path.getmtime(path))))
        
        print(f"Updated directory info for {node_id}")
    else:
        # Add new node
        nx_graph.add_node(
            node_id, 
            type="directory", 
            path=path, 
            last_modified=os.path.getmtime(path)
        )
        
        # Update RDF
        rdf_graph.add((ns[node_id], RDF.type, ns.Directory))
        rdf_graph.add((ns[node_id], ns.path, Literal(path)))
        rdf_graph.add((ns[node_id], ns.last_modified, Literal(os.path.getmtime(path))))
        
        print(f"Added new directory {node_id}")

def count_files_recursive(directory):
    """Count files recursively in a directory"""
    count = 0
    for root, dirs, files in os.walk(directory):
        count += len(files)
    return count

def register_feature(nx_graph, rdf_graph, ns, feature_id, name, description, owner, status="planned"):
    """Register a new feature in the Knowledge Graph"""
    if feature_id in nx_graph:
        # Update existing feature
        nx_graph.nodes[feature_id]["name"] = name
        nx_graph.nodes[feature_id]["description"] = description
        nx_graph.nodes[feature_id]["owner"] = owner
        nx_graph.nodes[feature_id]["status"] = status
        
        # Update RDF
        rdf_graph.add((ns[feature_id], ns.name, Literal(name)))
        rdf_graph.add((ns[feature_id], ns.description, Literal(description)))
        rdf_graph.add((ns[feature_id], ns.owner, Literal(owner)))
        rdf_graph.add((ns[feature_id], ns.status, Literal(status)))
        
        print(f"Updated feature {feature_id}")
    else:
        # Add new feature
        nx_graph.add_node(
            feature_id, 
            type="feature", 
            name=name, 
            description=description, 
            owner=owner, 
            status=status
        )
        
        # Update RDF
        rdf_graph.add((ns[feature_id], RDF.type, ns.Feature))
        rdf_graph.add((ns[feature_id], ns.name, Literal(name)))
        rdf_graph.add((ns[feature_id], ns.description, Literal(description)))
        rdf_graph.add((ns[feature_id], ns.owner, Literal(owner)))
        rdf_graph.add((ns[feature_id], ns.status, Literal(status)))
        
        print(f"Added new feature {feature_id}")

if __name__ == "__main__":
    update_knowledge_graph()