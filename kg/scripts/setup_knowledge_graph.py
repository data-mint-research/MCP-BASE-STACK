import os
import networkx as nx
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS

# Configuration
PROJECT_NAME = "MCP-BASE-STACK"
KG_DATA_DIR = "kg/data"
KG_DOCS_DIR = "kg/docs"

class KnowledgeGraphSetup:
    def __init__(self):
        self.nx_graph = nx.DiGraph(name=PROJECT_NAME)
        self.rdf_graph = Graph()
        self.ns = Namespace(f"http://{PROJECT_NAME.lower()}.org/")
        
    def initialize_graph(self):
        """Initialize the base Knowledge Graph structure"""
        # Add project root
        self.nx_graph.add_node("project_root", type="project", name=PROJECT_NAME)
        
        # Add planned stack components
        components = [
            ("nvidia_gpu", "hardware", "NVIDIA RTX 4090 GPU"),
            ("wsl2", "platform", "Windows Subsystem for Linux 2"),
            ("docker", "software", "Docker Engine"),
            ("nvidia_container", "software", "NVIDIA Container Toolkit"),
            ("librechat", "software", "LibreChat UI and API"),
            ("mongodb", "software", "MongoDB Database"),
            ("meilisearch", "software", "Meilisearch Engine"),
            ("ollama", "software", "Ollama LLM Server"),
            ("mistral", "model", "Mistral 7B LLM"),
            ("deepseek", "model", "DeepSeek Coder LLM"),
            ("mcp_server", "software", "MCP FastAPI Server")
        ]
        
        # Add component nodes
        for component_id, component_type, component_name in components:
            self.nx_graph.add_node(component_id, type=component_type, name=component_name)
            self.nx_graph.add_edge("project_root", component_id, relation="contains")
            
            # Add to RDF graph
            self.rdf_graph.add((self.ns[component_id], RDF.type, self.ns[component_type]))
            self.rdf_graph.add((self.ns[component_id], RDFS.label, Literal(component_name)))
            self.rdf_graph.add((self.ns.project, self.ns.contains, self.ns[component_id]))
        
        # Add relationships between components
        relationships = [
            ("nvidia_gpu", "wsl2", "accessible_from"),
            ("docker", "wsl2", "runs_on"),
            ("nvidia_container", "docker", "extends"),
            ("nvidia_container", "nvidia_gpu", "enables_access"),
            ("ollama", "docker", "containerized_in"),
            ("ollama", "nvidia_gpu", "uses"),
            ("mistral", "ollama", "served_by"),
            ("deepseek", "ollama", "served_by"),
            ("librechat", "docker", "containerized_in"),
            ("mongodb", "docker", "containerized_in"),
            ("meilisearch", "docker", "containerized_in"),
            ("librechat", "mongodb", "uses"),
            ("librechat", "meilisearch", "uses"),
            ("librechat", "mistral", "integrates"),
            ("librechat", "deepseek", "integrates"),
            ("mcp_server", "deepseek", "uses")
        ]
        
        # Add relationship edges
        for source, target, relation in relationships:
            self.nx_graph.add_edge(source, target, relation=relation)
            self.rdf_graph.add((self.ns[source], self.ns[relation], self.ns[target]))
    
    def save_graphs(self):
        """Save both graph formats to files"""
        os.makedirs(KG_DATA_DIR, exist_ok=True)
        os.makedirs(KG_DOCS_DIR, exist_ok=True)
        
        # Save NetworkX graph
        nx.write_graphml(self.nx_graph, f"{KG_DATA_DIR}/knowledge_graph.graphml")
        
        # Save RDF graph
        self.rdf_graph.serialize(destination=f"{KG_DATA_DIR}/knowledge_graph.ttl", format="turtle")
        
        # Create visualization
        try:
            import matplotlib.pyplot as plt
            plt.figure(figsize=(12, 10))
            pos = nx.spring_layout(self.nx_graph, seed=42)
            node_colors = {
                'project': 'lightblue',
                'hardware': 'red',
                'platform': 'green',
                'software': 'yellow',
                'model': 'purple'
            }
            colors = [node_colors.get(self.nx_graph.nodes[n]['type'], 'gray') for n in self.nx_graph.nodes()]
            
            nx.draw(self.nx_graph, pos, with_labels=True, node_color=colors, 
                    node_size=1500, edge_color="gray", font_size=8)
            plt.savefig(f"{KG_DOCS_DIR}/graph_visualization.png")
        except ImportError:
            print("Matplotlib not available. No visualization created.")
        
        # Generate statistics report
        node_types = {}
        for _, data in self.nx_graph.nodes(data=True):
            node_type = data.get('type', 'unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        with open(f"{KG_DOCS_DIR}/graph_stats.txt", 'w') as f:
            f.write(f"Knowledge Graph Statistics for {PROJECT_NAME}\n")
            f.write(f"Total nodes: {len(self.nx_graph.nodes())}\n")
            f.write(f"Total edges: {len(self.nx_graph.edges())}\n")
            f.write("Node types:\n")
            for node_type, count in node_types.items():
                f.write(f"  - {node_type}: {count}\n")
        
        print(f"Knowledge Graph initialized with {len(self.nx_graph.nodes())} nodes and {len(self.nx_graph.edges())} edges.")

if __name__ == "__main__":
    graph_setup = KnowledgeGraphSetup()
    graph_setup.initialize_graph()
    graph_setup.save_graphs()