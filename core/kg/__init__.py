"""
Knowledge Graph Module

This module provides knowledge graph functionality for the MCP-BASE-STACK project.
"""

import os
import networkx as nx
from typing import Optional, Dict, Any

from core.kg.scripts import (
    setup_knowledge_graph,
    update_component_status,
    update_file_structure_metrics,
    update_quality_metrics,
)

# Configuration
KG_DATA_DIR = "core/kg/data"

def get_knowledge_graph() -> Optional[Dict[str, Any]]:
    """
    Get the current knowledge graph.
    
    Returns:
        Optional[Dict[str, Any]]: Knowledge graph data or None if not available
    """
    try:
        # Load the knowledge graph from the data directory
        graph_path = os.path.join(KG_DATA_DIR, "knowledge_graph.graphml")
        if not os.path.exists(graph_path):
            return None
            
        # Load the graph using NetworkX
        nx_graph = nx.read_graphml(graph_path)
        
        # Convert to a dictionary representation
        graph_data = {
            "nodes": [],
            "edges": []
        }
        
        # Add nodes
        for node_id, node_data in nx_graph.nodes(data=True):
            node_info = {"id": node_id}
            node_info.update(node_data)
            graph_data["nodes"].append(node_info)
            
        # Add edges
        for source, target, edge_data in nx_graph.edges(data=True):
            edge_info = {"source": source, "target": target}
            edge_info.update(edge_data)
            graph_data["edges"].append(edge_info)
            
        return graph_data
    except Exception as e:
        print(f"Error loading knowledge graph: {e}")
        return None

__all__ = [
    'setup_knowledge_graph',
    'update_component_status',
    'update_file_structure_metrics',
    'update_quality_metrics',
    'get_knowledge_graph',
]