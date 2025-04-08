#!/usr/bin/env python3
"""
Record Code Quality Enforcement in Knowledge Graph

This script updates the knowledge graph with information about the code quality
enforcement implementation, including the enhanced check and fix scripts and the
new Python wrapper script.
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
    """Update the knowledge graph with code quality enforcement information."""
    print("Updating knowledge graph with code quality enforcement information...")
    
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
    
    # Get or create the code_quality_enforcement node
    if "code_quality_enforcement" not in g.nodes:
        g.add_node(
            "code_quality_enforcement",
            name="Code Quality Enforcement",
            type="feature",
            status="active",
            description="Comprehensive code quality enforcement system",
            created_at=datetime.utcnow().isoformat()
        )
        g.add_edge("code_quality", "code_quality_enforcement", relation="has_feature")
        print("Created code_quality_enforcement node")
    
    # Update the code_quality_enforcement node
    g.nodes["code_quality_enforcement"]["updated_at"] = datetime.utcnow().isoformat()
    g.nodes["code_quality_enforcement"]["version"] = "1.0.0"
    
    # Add or update script nodes
    script_nodes = {
        "check_code_quality_script": {
            "name": "Check Code Quality Script",
            "path": "scripts/utils/quality/check_code_quality.sh",
            "type": "script",
            "description": "Enhanced script to check code quality based on standards from the specification manifest",
            "supports_standards": True,
            "generates_report": True,
            "updates_kg": True
        },
        "fix_code_quality_script": {
            "name": "Fix Code Quality Script",
            "path": "scripts/utils/quality/fix_code_quality.sh",
            "type": "script",
            "description": "Enhanced script to fix code quality issues based on standards from the specification manifest",
            "supports_standards": True,
            "generates_report": True,
            "updates_kg": True
        },
        "enforce_code_standards_script": {
            "name": "Enforce Code Standards Script",
            "path": "scripts/utils/quality/enforce_code_standards.py",
            "type": "script",
            "description": "Python wrapper script providing a unified interface to check and fix code quality issues",
            "supports_standards": True,
            "generates_report": True,
            "updates_kg": True,
            "integrates_with_quality_enforcer": True
        },
        "check_code_quality_nodes_script": {
            "name": "Check Code Quality Nodes Script",
            "path": "scripts/utils/quality/check_code_quality_nodes.py",
            "type": "script",
            "description": "Script to update the knowledge graph with code quality check and fix results",
            "updates_kg": True
        }
    }
    
    for node_id, attrs in script_nodes.items():
        if node_id not in g.nodes:
            g.add_node(node_id, **attrs)
            g.add_edge("code_quality_enforcement", node_id, relation="implements")
            print(f"Created {node_id} node")
        else:
            # Update existing node
            for key, value in attrs.items():
                g.nodes[node_id][key] = value
            print(f"Updated {node_id} node")
    
    # Add or update tool nodes
    tool_nodes = {
        "black": {
            "name": "Black",
            "type": "tool",
            "category": "python",
            "description": "Python code formatter"
        },
        "isort": {
            "name": "isort",
            "type": "tool",
            "category": "python",
            "description": "Python import sorter"
        },
        "flake8": {
            "name": "flake8",
            "type": "tool",
            "category": "python",
            "description": "Python linter"
        },
        "mypy": {
            "name": "mypy",
            "type": "tool",
            "category": "python",
            "description": "Python type checker"
        },
        "pylint": {
            "name": "pylint",
            "type": "tool",
            "category": "python",
            "description": "Python linter"
        },
        "autopep8": {
            "name": "autopep8",
            "type": "tool",
            "category": "python",
            "description": "Python code fixer for flake8 issues"
        },
        "autoflake": {
            "name": "autoflake",
            "type": "tool",
            "category": "python",
            "description": "Python unused imports and variables remover"
        },
        "shellcheck": {
            "name": "shellcheck",
            "type": "tool",
            "category": "shell",
            "description": "Shell script linter"
        },
        "shfmt": {
            "name": "shfmt",
            "type": "tool",
            "category": "shell",
            "description": "Shell script formatter"
        },
        "markdownlint": {
            "name": "markdownlint",
            "type": "tool",
            "category": "markdown",
            "description": "Markdown linter"
        },
        "yamllint": {
            "name": "yamllint",
            "type": "tool",
            "category": "yaml",
            "description": "YAML linter"
        },
        "prettier": {
            "name": "prettier",
            "type": "tool",
            "category": "general",
            "description": "Code formatter for JavaScript, TypeScript, JSON, CSS, YAML, and Markdown"
        }
    }
    
    for node_id, attrs in tool_nodes.items():
        tool_node_id = f"tool_{node_id}"
        if tool_node_id not in g.nodes:
            g.add_node(tool_node_id, **attrs)
            g.add_edge("code_quality_enforcement", tool_node_id, relation="uses")
            print(f"Created {tool_node_id} node")
        else:
            # Update existing node
            for key, value in attrs.items():
                g.nodes[tool_node_id][key] = value
            
            # Ensure the edge exists
            if not g.has_edge("code_quality_enforcement", tool_node_id):
                g.add_edge("code_quality_enforcement", tool_node_id, relation="uses")
            
            print(f"Updated {tool_node_id} node")
    
    # Add or update category nodes
    category_nodes = {
        "python": {
            "name": "Python",
            "type": "category",
            "description": "Python code quality standards"
        },
        "shell": {
            "name": "Shell",
            "type": "category",
            "description": "Shell script code quality standards"
        },
        "markdown": {
            "name": "Markdown",
            "type": "category",
            "description": "Markdown code quality standards"
        },
        "yaml": {
            "name": "YAML",
            "type": "category",
            "description": "YAML code quality standards"
        },
        "json": {
            "name": "JSON",
            "type": "category",
            "description": "JSON code quality standards"
        },
        "javascript": {
            "name": "JavaScript",
            "type": "category",
            "description": "JavaScript code quality standards"
        },
        "typescript": {
            "name": "TypeScript",
            "type": "category",
            "description": "TypeScript code quality standards"
        },
        "css": {
            "name": "CSS",
            "type": "category",
            "description": "CSS code quality standards"
        }
    }
    
    for node_id, attrs in category_nodes.items():
        category_node_id = f"category_{node_id}"
        if category_node_id not in g.nodes:
            g.add_node(category_node_id, **attrs)
            g.add_edge("code_quality_enforcement", category_node_id, relation="supports")
            print(f"Created {category_node_id} node")
        else:
            # Update existing node
            for key, value in attrs.items():
                g.nodes[category_node_id][key] = value
            
            # Ensure the edge exists
            if not g.has_edge("code_quality_enforcement", category_node_id):
                g.add_edge("code_quality_enforcement", category_node_id, relation="supports")
            
            print(f"Updated {category_node_id} node")
    
    # Add relationships between tools and categories
    tool_category_relationships = {
        "tool_black": "category_python",
        "tool_isort": "category_python",
        "tool_flake8": "category_python",
        "tool_mypy": "category_python",
        "tool_pylint": "category_python",
        "tool_autopep8": "category_python",
        "tool_autoflake": "category_python",
        "tool_shellcheck": "category_shell",
        "tool_shfmt": "category_shell",
        "tool_markdownlint": "category_markdown",
        "tool_yamllint": "category_yaml",
        "tool_prettier": "category_javascript",
        "tool_prettier": "category_typescript",
        "tool_prettier": "category_json",
        "tool_prettier": "category_css",
        "tool_prettier": "category_yaml",
        "tool_prettier": "category_markdown"
    }
    
    for source, target in tool_category_relationships.items():
        if source in g.nodes and target in g.nodes and not g.has_edge(source, target):
            g.add_edge(source, target, relation="applies_to")
            print(f"Created edge from {source} to {target}")
    
    # Add relationship to specification manifest
    if "specification_manifest" in g.nodes:
        if not g.has_edge("code_quality_enforcement", "specification_manifest"):
            g.add_edge("code_quality_enforcement", "specification_manifest", relation="uses_standards_from")
            print("Created edge from code_quality_enforcement to specification_manifest")
    
    # Add relationship to QualityEnforcer
    if "quality_enforcer" not in g.nodes:
        g.add_node(
            "quality_enforcer",
            name="Quality Enforcer",
            type="class",
            path="core/quality/enforcer.py",
            description="Facade for the quality enforcement system"
        )
        print("Created quality_enforcer node")
    
    if not g.has_edge("enforce_code_standards_script", "quality_enforcer"):
        g.add_edge("enforce_code_standards_script", "quality_enforcer", relation="integrates_with")
        print("Created edge from enforce_code_standards_script to quality_enforcer")
    
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