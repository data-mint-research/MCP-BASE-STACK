#!/usr/bin/env python3
import networkx as nx

# Load the Knowledge Graph from the new location
try:
    g_new = nx.read_graphml('core/kg/data/knowledge_graph.graphml')
    print(f'New KG nodes: {len(g_new.nodes())}, edges: {len(g_new.edges())}')
    print("Knowledge Graph migration successful!")
except Exception as e:
    print(f"Error loading Knowledge Graph: {e}")
    print("Migration verification failed.")