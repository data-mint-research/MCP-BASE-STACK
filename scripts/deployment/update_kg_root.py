#!/usr/bin/env python3
import networkx as nx

try:
    g = nx.read_graphml('core/kg/data/knowledge_graph.graphml')
    
    # Get all nodes that are directly connected to project_root
    root_files = []
    for node in g.nodes():
        if g.has_edge('project_root', node):
            root_files.append(node)
    
    # Remove all edges from project_root to nodes that are not in the allowed list
    allowed_files = ['mcp.sh', 'README.md', 'LICENSE', '.gitignore']
    for node in root_files:
        if node not in allowed_files and node not in ['config', 'core', 'data', 'deploy', 'docs', 'scripts', 'services', 'tests']:
            g.remove_edge('project_root', node)
    
    # Add mcp.sh node if it doesn't exist
    if 'mcp.sh' not in g:
        g.add_node('mcp.sh', type='script', path='mcp.sh')
        g.add_edge('project_root', 'mcp.sh', relation='contains')
    
    # Save updated graph
    nx.write_graphml(g, 'core/kg/data/knowledge_graph.graphml')
    print('Knowledge Graph updated with clean root directory')
except Exception as e:
    print(f"Error updating Knowledge Graph: {e}")