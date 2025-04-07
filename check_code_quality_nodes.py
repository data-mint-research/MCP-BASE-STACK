#!/usr/bin/env python3
import networkx as nx

# Load the knowledge graph
g = nx.read_graphml('core/kg/data/knowledge_graph.graphml')

# Check code quality component
print('Code Quality Component:')
for node, attrs in g.nodes(data=True):
    if node == 'code_quality':
        print(f'- {node}: {attrs.get("name", "N/A")} ({attrs.get("status", "N/A")})')

# Check convention document nodes
print('\nConvention Document Nodes:')
convention_docs = ['style_guide', 'coding_conventions', 'review_checklist', 'graph_guidelines']
for node, attrs in g.nodes(data=True):
    if attrs.get('type') == 'file' and node in convention_docs:
        print(f'- {node}: {attrs.get("path", "N/A")}')

# Check code quality relationships
print('\nCode Quality Relationships:')
for source, target, attrs in g.edges(data=True):
    if source == 'code_quality' or target == 'code_quality':
        print(f'- {source} --{attrs.get("relation", "")}-> {target}')

# Check docs_conventions relationships
print('\nDocs Conventions Relationships:')
for source, target, attrs in g.edges(data=True):
    if source == 'docs_conventions' and target in convention_docs:
        print(f'- {source} --{attrs.get("relation", "")}-> {target}')