#!/usr/bin/env python3
"""
Record Quality Standards Enforcer in Knowledge Graph

This script updates the knowledge graph with information about the quality standards enforcer
implementation, which orchestrates the execution of all quality enforcement scripts in an
iterative cycle until no further changes are needed.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import networkx as nx
from datetime import datetime

# Define paths
PROJECT_ROOT = Path(__file__).resolve().parents[3]
KG_PATH = PROJECT_ROOT / "core" / "kg" / "data" / "knowledge_graph.graphml"


def update_knowledge_graph():
    """Update the knowledge graph with quality standards enforcer information."""
    print("Updating knowledge graph with quality standards enforcer information...")
    
    # Load the knowledge graph
    if not os.path.exists(KG_PATH):
        print(f"Error: Knowledge graph not found at {KG_PATH}")
        return False
    
    try:
        g = nx.read_graphml(KG_PATH)
        print(f"Loaded knowledge graph with {len(g.nodes)} nodes and {len(g.edges)} edges")
    except Exception as e:
        print(f"Error loading knowledge graph: {e}")
        return False
    
    # Get or create the code_quality node
    if "code_quality" not in g.nodes:
        g.add_node("code_quality", name="Code Quality", type="component", status="active")
        print("Created code_quality node")
    
    # Get or create the quality_standards_enforcer node
    if "quality_standards_enforcer" not in g.nodes:
        g.add_node(
            "quality_standards_enforcer",
            name="Quality Standards Enforcer",
            type="feature",
            status="active",
            description="Master script that orchestrates the execution of all quality enforcement scripts in an iterative cycle",
            created_at=datetime.utcnow().isoformat()
        )
        g.add_edge("code_quality", "quality_standards_enforcer", relation="has_feature")
        print("Created quality_standards_enforcer node")
    
    # Update the quality_standards_enforcer node
    g.nodes["quality_standards_enforcer"]["updated_at"] = datetime.utcnow().isoformat()
    g.nodes["quality_standards_enforcer"]["version"] = "1.0.0"
    
    # Add or update script node
    script_node_id = "enforce_quality_standards_script"
    if script_node_id not in g.nodes:
        g.add_node(
            script_node_id,
            name="Enforce Quality Standards Script",
            path="enforce_quality_standards.py",
            type="script",
            description="Master script that orchestrates the execution of all quality enforcement scripts in an iterative cycle",
            supports_iterative_execution=True,
            generates_report=True,
            updates_kg=True
        )
        g.add_edge("quality_standards_enforcer", script_node_id, relation="implements")
        print(f"Created {script_node_id} node")
    else:
        # Update existing node
        g.nodes[script_node_id]["updated_at"] = datetime.utcnow().isoformat()
        g.nodes[script_node_id]["version"] = "1.0.0"
        print(f"Updated {script_node_id} node")
    
    # Add relationships to other quality scripts
    script_relationships = {
        "check_code_quality_script": "executes",
        "fix_code_quality_script": "executes",
        "cleanup_script": "executes",
        "update_essential_files_script": "executes",
        "dependency_audit_script": "executes"
    }
    
    for target_node_id, relation in script_relationships.items():
        if target_node_id in g.nodes and not g.has_edge(script_node_id, target_node_id):
            g.add_edge(script_node_id, target_node_id, relation=relation)
            print(f"Created edge from {script_node_id} to {target_node_id} with relation {relation}")
    
    # Add relationship to QualityEnforcer
    if "quality_enforcer" in g.nodes and not g.has_edge(script_node_id, "quality_enforcer"):
        g.add_edge(script_node_id, "quality_enforcer", relation="integrates_with")
        print("Created edge from enforce_quality_standards_script to quality_enforcer")
    
    # Add capabilities
    capability_nodes = {
        "iterative_execution": {
            "name": "Iterative Execution",
            "type": "capability",
            "description": "Executes quality enforcement scripts in an iterative cycle until no further changes are needed"
        },
        "comprehensive_reporting": {
            "name": "Comprehensive Reporting",
            "type": "capability",
            "description": "Generates a comprehensive final report of the quality enforcement process"
        },
        "kg_integration": {
            "name": "Knowledge Graph Integration",
            "type": "capability",
            "description": "Updates the knowledge graph with the final state of the quality enforcement process"
        },
        "error_handling": {
            "name": "Error Handling",
            "type": "capability",
            "description": "Handles errors gracefully and provides detailed logging of the process"
        }
    }
    
    for node_id, attrs in capability_nodes.items():
        capability_node_id = f"capability_{node_id}"
        if capability_node_id not in g.nodes:
            g.add_node(capability_node_id, **attrs)
            g.add_edge("quality_standards_enforcer", capability_node_id, relation="has_capability")
            print(f"Created {capability_node_id} node")
        else:
            # Update existing node
            for key, value in attrs.items():
                g.nodes[capability_node_id][key] = value
            
            # Ensure the edge exists
            if not g.has_edge("quality_standards_enforcer", capability_node_id):
                g.add_edge("quality_standards_enforcer", capability_node_id, relation="has_capability")
            
            print(f"Updated {capability_node_id} node")
    
    # Save the updated knowledge graph
    try:
        nx.write_graphml(g, KG_PATH)
        print(f"Saved knowledge graph with {len(g.nodes)} nodes and {len(g.edges)} edges")
        return True
    except Exception as e:
        print(f"Error saving knowledge graph: {e}")
        return False


if __name__ == "__main__":
    if update_knowledge_graph():
        print("Knowledge graph updated successfully")
        sys.exit(0)
    else:
        print("Failed to update knowledge graph")
        sys.exit(1)