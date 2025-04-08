import networkx as nx
import os
import sys
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS

# Configuration
KG_DATA_DIR = "core/kg/data"
PROJECT_NAME = "MCP-BASE-STACK"

def setup_knowledge_graph():
    """Initialize an empty Knowledge Graph with the basic structure"""
    print("Setting up Knowledge Graph...")
    
    # Create data directory if it doesn't exist
    os.makedirs(KG_DATA_DIR, exist_ok=True)
    
    # Initialize NetworkX graph for GraphML format
    nx_graph = nx.DiGraph()
    
    # Initialize RDFLib graph for RDF/Turtle format
    rdf_graph = Graph()
    
    # Namespace for RDF
    ns = Namespace(f"http://{PROJECT_NAME.lower()}.org/")
    
    # Add basic component nodes
    components = [
        # id, name, type, status
        ("nvidia_gpu", "NVIDIA GPU", "hardware", "planned"),
        ("docker", "Docker", "runtime", "planned"),
        ("nvidia_container", "NVIDIA Container Toolkit", "runtime", "planned"),
        ("librechat", "LibreChat", "service", "planned"),
        ("llm_server", "LLM Server", "service", "planned"),
        ("mistral", "Mistral", "model", "planned"),
        ("deepseek", "DeepSeek Coder", "model", "planned"),
        ("mcp_server", "MCP Server", "service", "planned"),
        ("documentation", "Documentation", "resource", "planned"),
        ("tests", "Tests", "resource", "planned")
    ]
    
    for component_id, name, comp_type, status in components:
        # Add to NetworkX graph
        nx_graph.add_node(
            component_id, 
            name=name,
            type="component",
            component_type=comp_type,
            status=status
        )
        
        # Add to RDF graph
        rdf_graph.add((ns[component_id], RDF.type, ns.Component))
        rdf_graph.add((ns[component_id], ns.name, Literal(name)))
        rdf_graph.add((ns[component_id], ns.component_type, Literal(comp_type)))
        rdf_graph.add((ns[component_id], ns.status, Literal(status)))
        
        print(f"Added component: {component_id}")
    
    # Add basic feature nodes
    features = [
        # id, name, description, owner, status
        ("kg_visualization", "Knowledge Graph Visualization", "Visualize the knowledge graph", "System Admin", "planned"),
        ("mcp_agent_test", "MCP Agent Test", "Test the MCP server's functionality", "Developer", "planned"),
        ("documentation_structure", "Documentation Structure", "Organized documentation structure", "Technical Writer", "planned"),
        ("test_structure", "Test Structure", "Comprehensive test structure", "QA Engineer", "planned")
    ]
    
    for feature_id, name, description, owner, status in features:
        # Add to NetworkX graph
        nx_graph.add_node(
            feature_id,
            name=name,
            type="feature",
            description=description,
            owner=owner,
            status=status
        )
        
        # Add to RDF graph
        rdf_graph.add((ns[feature_id], RDF.type, ns.Feature))
        rdf_graph.add((ns[feature_id], ns.name, Literal(name)))
        rdf_graph.add((ns[feature_id], ns.description, Literal(description)))
        rdf_graph.add((ns[feature_id], ns.owner, Literal(owner)))
        rdf_graph.add((ns[feature_id], ns.status, Literal(status)))
        
        print(f"Added feature: {feature_id}")
    
    # Add basic directory nodes
    directories = [
        # id, path, purpose
        ("docs", "docs", "documentation"),
        ("tests", "tests", "testing"),
        ("core", "core", "core_functionality"),
        ("kg", "core/kg", "knowledge_graph")
    ]
    
    for dir_id, path, purpose in directories:
        # Add to NetworkX graph
        nx_graph.add_node(
            dir_id,
            type="directory",
            path=path,
            purpose=purpose
        )
        
        # Add to RDF graph
        rdf_graph.add((ns[dir_id], RDF.type, ns.Directory))
        rdf_graph.add((ns[dir_id], ns.path, Literal(path)))
        rdf_graph.add((ns[dir_id], ns.purpose, Literal(purpose)))
        
        print(f"Added directory: {dir_id}")
    
    # Add basic relationships (edges)
    relationships = [
        # source, target, relationship
        ("librechat", "llm_server", "DEPENDS_ON"),
        ("mcp_server", "llm_server", "DEPENDS_ON"),
        ("llm_server", "mistral", "DEPENDS_ON"),
        ("llm_server", "deepseek", "DEPENDS_ON"),
        ("mcp_server", "mcp_agent_test", "IMPLEMENTS"),
        ("documentation", "documentation_structure", "IMPLEMENTS"),
        ("tests", "test_structure", "IMPLEMENTS"),
        ("librechat", "llm_server", "CONNECTS_TO"),
        ("librechat", "mcp_server", "CONNECTS_TO"),
        ("core", "kg", "CONTAINS"),
        ("docs", "documentation_structure", "DOCUMENTS"),
        ("tests", "test_structure", "TESTS")
    ]
    
    for source, target, relationship in relationships:
        # Add to NetworkX graph
        nx_graph.add_edge(source, target, relationship=relationship)
        
        # Add to RDF graph
        rel_predicate = ns[relationship.lower()]
        rdf_graph.add((ns[source], rel_predicate, ns[target]))
        
        print(f"Added relationship: {source} --{relationship}--> {target}")
    
    # Save the graphs
    nx.write_graphml(nx_graph, f"{KG_DATA_DIR}/knowledge_graph.graphml")
    rdf_graph.serialize(destination=f"{KG_DATA_DIR}/knowledge_graph.ttl", format="turtle")
    
    print(f"Knowledge Graph initialized successfully.")
    print(f"- GraphML file: {KG_DATA_DIR}/knowledge_graph.graphml")
    print(f"- RDF/Turtle file: {KG_DATA_DIR}/knowledge_graph.ttl")

if __name__ == "__main__":
    setup_knowledge_graph()