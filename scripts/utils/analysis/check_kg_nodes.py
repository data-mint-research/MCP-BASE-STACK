#!/usr/bin/env python3
import networkx as nx

# Load the knowledge graph
g = nx.read_graphml('core/kg/data/knowledge_graph.graphml')

# Check file nodes
print('File Nodes:')
for node, attrs in g.nodes(data=True):
    if attrs.get('type') == 'file' and node in ['pre_commit_hook', 'install_hooks_script', 'hooks_documentation', 'git_hooks_kg_integration_plan']:
        print(f'- {node}: {attrs.get("path", "N/A")}')

# Check relationships
print('\nRelationships:')
for source, target, attrs in g.edges(data=True):
    if source == 'git_hooks' or target == 'git_hooks':
        print(f'- {source} --{attrs.get("relation", "")}-> {target}')