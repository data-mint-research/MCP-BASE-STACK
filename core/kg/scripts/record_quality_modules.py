#!/usr/bin/env python3
"""
Record Quality Modules in Knowledge Graph

This script updates the knowledge graph with information about the new modular
quality architecture. It records the components, their relationships, and the
plugin system.
"""

import logging
import networkx as nx
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Path to the knowledge graph
KG_PATH = Path("core/kg/data/knowledge_graph.graphml")


def load_knowledge_graph():
    """Load the knowledge graph from the GraphML file."""
    logger.info(f"Loading knowledge graph from {KG_PATH}")
    return nx.read_graphml(KG_PATH)


def save_knowledge_graph(graph):
    """Save the knowledge graph to the GraphML file."""
    logger.info(f"Saving knowledge graph to {KG_PATH}")
    nx.write_graphml(graph, KG_PATH)


def update_knowledge_graph():
    """Update the knowledge graph with quality modules information."""
    # Load the knowledge graph
    g = load_knowledge_graph()
    
    # Add or update the quality_modules node
    if "quality_modules" not in g.nodes:
        g.add_node("quality_modules", name="Quality Modules", type="component", status="active")
        logger.info("Added quality_modules node")
    else:
        g.nodes["quality_modules"]["status"] = "active"
        logger.info("Updated quality_modules node")
    
    # Add or update the relationship between code_quality and quality_modules
    if "code_quality" in g.nodes:
        if not g.has_edge("code_quality", "quality_modules"):
            g.add_edge("code_quality", "quality_modules", relation="implements")
            logger.info("Added edge from code_quality to quality_modules")
    
    # Add component nodes
    components = [
        ("quality_base", "Quality Base", "Base classes and interfaces for quality components"),
        ("quality_code_style", "Code Style", "Code style and formatting checks"),
        ("quality_static_analysis", "Static Analysis", "Static code analysis checks"),
        ("quality_documentation", "Documentation", "Documentation quality checks"),
        ("quality_structure", "Project Structure", "Project structure and organization checks")
    ]
    
    for node_id, name, description in components:
        if node_id not in g.nodes:
            g.add_node(node_id, name=name, description=description, type="component", status="active")
            logger.info(f"Added {node_id} node")
        else:
            g.nodes[node_id]["name"] = name
            g.nodes[node_id]["description"] = description
            g.nodes[node_id]["status"] = "active"
            logger.info(f"Updated {node_id} node")
        
        # Add relationship to quality_modules
        if not g.has_edge("quality_modules", node_id):
            g.add_edge("quality_modules", node_id, relation="contains")
            logger.info(f"Added edge from quality_modules to {node_id}")
    
    # Add plugin system node
    if "quality_plugin_system" not in g.nodes:
        g.add_node("quality_plugin_system", name="Quality Plugin System", 
                  description="System for dynamically loading quality check plugins",
                  type="component", status="active")
        logger.info("Added quality_plugin_system node")
    else:
        g.nodes["quality_plugin_system"]["status"] = "active"
        logger.info("Updated quality_plugin_system node")
    
    # Add relationship between quality_base and quality_plugin_system
    if not g.has_edge("quality_base", "quality_plugin_system"):
        g.add_edge("quality_base", "quality_plugin_system", relation="implements")
        logger.info("Added edge from quality_base to quality_plugin_system")
    
    # Add enforcer node
    if "quality_enforcer" not in g.nodes:
        g.add_node("quality_enforcer", name="Quality Enforcer", 
                  description="Facade over the quality component system",
                  type="component", status="active")
        logger.info("Added quality_enforcer node")
    else:
        g.nodes["quality_enforcer"]["status"] = "active"
        logger.info("Updated quality_enforcer node")
    
    # Add relationships between enforcer and components
    for node_id, _, _ in components:
        if not g.has_edge("quality_enforcer", node_id):
            g.add_edge("quality_enforcer", node_id, relation="uses")
            logger.info(f"Added edge from quality_enforcer to {node_id}")
    
    # Add relationship between enforcer and plugin system
    if not g.has_edge("quality_enforcer", "quality_plugin_system"):
        g.add_edge("quality_enforcer", "quality_plugin_system", relation="uses")
        logger.info("Added edge from quality_enforcer to quality_plugin_system")
    
    # Add hooks compatibility node
    if "quality_hooks_compatibility" not in g.nodes:
        g.add_node("quality_hooks_compatibility", name="Quality Hooks Compatibility", 
                  description="Backward compatibility with existing hooks",
                  type="component", status="active")
        logger.info("Added quality_hooks_compatibility node")
    else:
        g.nodes["quality_hooks_compatibility"]["status"] = "active"
        logger.info("Updated quality_hooks_compatibility node")
    
    # Add relationship between enforcer and hooks compatibility
    if not g.has_edge("quality_enforcer", "quality_hooks_compatibility"):
        g.add_edge("quality_enforcer", "quality_hooks_compatibility", relation="provides")
        logger.info("Added edge from quality_enforcer to quality_hooks_compatibility")
    
    # Add file nodes for the new modules
    files = [
        ("quality_init_file", "core/quality/__init__.py", "Quality module initialization"),
        ("quality_enforcer_file", "core/quality/enforcer.py", "Quality enforcer implementation"),
        ("quality_base_file", "core/quality/components/base.py", "Base classes for quality components"),
        ("quality_code_style_file", "core/quality/components/code_style.py", "Code style component"),
        ("quality_static_analysis_file", "core/quality/components/static_analysis.py", "Static analysis component"),
        ("quality_documentation_file", "core/quality/components/documentation.py", "Documentation component"),
        ("quality_structure_file", "core/quality/components/structure.py", "Project structure component"),
        ("quality_hooks_init_file", "core/quality/hooks/__init__.py", "Hooks compatibility layer")
    ]
    
    for node_id, path, description in files:
        if node_id not in g.nodes:
            g.add_node(node_id, name=path, path=path, description=description, type="file", status="active")
            logger.info(f"Added {node_id} node")
        else:
            g.nodes[node_id]["path"] = path
            g.nodes[node_id]["description"] = description
            g.nodes[node_id]["status"] = "active"
            logger.info(f"Updated {node_id} node")
    
    # Add relationships between component nodes and file nodes
    component_file_relations = [
        ("quality_modules", "quality_init_file"),
        ("quality_enforcer", "quality_enforcer_file"),
        ("quality_base", "quality_base_file"),
        ("quality_code_style", "quality_code_style_file"),
        ("quality_static_analysis", "quality_static_analysis_file"),
        ("quality_documentation", "quality_documentation_file"),
        ("quality_structure", "quality_structure_file"),
        ("quality_hooks_compatibility", "quality_hooks_init_file")
    ]
    
    for component_id, file_id in component_file_relations:
        if not g.has_edge(component_id, file_id):
            g.add_edge(component_id, file_id, relation="implemented_in")
            logger.info(f"Added edge from {component_id} to {file_id}")
    
    # Save the updated knowledge graph
    save_knowledge_graph(g)
    logger.info("Knowledge graph updated successfully")


if __name__ == "__main__":
    update_knowledge_graph()