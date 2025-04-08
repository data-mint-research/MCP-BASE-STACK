#!/usr/bin/env python3
"""
Knowledge Graph Update Script

This script updates the knowledge graph with the latest quality metrics and
compliance information for the MCP-BASE-STACK project.

Usage:
    python update_knowledge_graph.py
"""

import os
import sys
import json
import datetime
import networkx as nx
from pathlib import Path

# Configuration
KG_DATA_DIR = "core/kg/data"
QUALITY_REPORTS_DIR = "data/reports"
GRAPH_FILE = os.path.join(KG_DATA_DIR, "knowledge_graph.graphml")

def update_knowledge_graph():
    """Update the knowledge graph with the latest quality metrics."""
    print("Updating knowledge graph...")
    
    # Check if the knowledge graph exists
    if not os.path.exists(GRAPH_FILE):
        print(f"Error loading graphs: [Errno 2] No such file or directory: '{GRAPH_FILE}'")
        print("Please run setup_knowledge_graph.py first")
        return False
    
    try:
        # Load the graph
        nx_graph = nx.read_graphml(GRAPH_FILE)
        print(f"Loaded knowledge graph from {GRAPH_FILE}")
        
        # Update timestamp
        nx_graph.nodes["project"]["last_modified"] = datetime.datetime.now().timestamp()
        
        # Update file structure metrics
        update_file_structure_metrics(nx_graph)
        
        # Update dependency metrics
        update_dependency_metrics(nx_graph)
        
        # Update documentation metrics
        update_documentation_metrics(nx_graph)
        
        # Update code quality metrics
        update_code_quality_metrics(nx_graph)
        
        # Update MCP compliance
        update_mcp_compliance(nx_graph)
        
        # Save the updated graph
        nx.write_graphml(nx_graph, GRAPH_FILE)
        print(f"Knowledge graph updated and saved to {GRAPH_FILE}")
        
        return True
    except Exception as e:
        print(f"Error updating knowledge graph: {e}")
        return False

def update_file_structure_metrics(graph):
    """Update file structure metrics in the knowledge graph."""
    print("Updating file structure metrics...")
    
    # Load file structure report
    file_structure_report_path = os.path.join(QUALITY_REPORTS_DIR, "file-structure-report.json")
    if os.path.exists(file_structure_report_path):
        try:
            with open(file_structure_report_path, 'r') as f:
                report_data = json.load(f)
            
            # Update metrics
            graph.nodes["file_structure_metrics"]["total_files"] = report_data.get("total_files", 0)
            graph.nodes["file_structure_metrics"]["naming_compliance"] = report_data.get("naming_issues", {}).get("compliance_percentage", 0)
            graph.nodes["file_structure_metrics"]["directory_compliance"] = report_data.get("directory_issues", {}).get("compliance_percentage", 0)
            graph.nodes["file_structure_metrics"]["overall_compliance"] = report_data.get("overall_compliance_percentage", 0)
            graph.nodes["file_structure_metrics"]["naming_issues_count"] = report_data.get("naming_issues", {}).get("count", 0)
            graph.nodes["file_structure_metrics"]["directory_issues_count"] = report_data.get("directory_issues", {}).get("count", 0)
            graph.nodes["file_structure_metrics"]["last_modified"] = datetime.datetime.now().timestamp()
            
            print("File structure metrics updated.")
        except Exception as e:
            print(f"Error updating file structure metrics: {e}")
    else:
        print(f"File structure report not found at {file_structure_report_path}")

def update_dependency_metrics(graph):
    """Update dependency metrics in the knowledge graph."""
    print("Updating dependency metrics...")
    
    # Load dependency audit report
    dependency_report_path = os.path.join(QUALITY_REPORTS_DIR, "dependency-audit-report.json")
    if os.path.exists(dependency_report_path):
        try:
            with open(dependency_report_path, 'r') as f:
                report_data = json.load(f)
            
            # Update metrics
            graph.nodes["dependency_metrics"]["dependency_files_scanned"] = report_data.get("files_scanned", 0)
            graph.nodes["dependency_metrics"]["dependencies_checked"] = report_data.get("dependencies_checked", 0)
            graph.nodes["dependency_metrics"]["outdated_dependencies"] = report_data.get("outdated_dependencies", 0)
            graph.nodes["dependency_metrics"]["vulnerable_dependencies"] = report_data.get("vulnerable_dependencies", 0)
            graph.nodes["dependency_metrics"]["inconsistent_dependencies"] = report_data.get("inconsistent_dependencies", 0)
            graph.nodes["dependency_metrics"]["errors"] = report_data.get("errors", 0)
            graph.nodes["dependency_metrics"]["last_modified"] = datetime.datetime.now().timestamp()
            
            print("Dependency metrics updated.")
        except Exception as e:
            print(f"Error updating dependency metrics: {e}")
    else:
        print(f"Dependency report not found at {dependency_report_path}")

def update_documentation_metrics(graph):
    """Update documentation metrics in the knowledge graph."""
    print("Updating documentation metrics...")
    
    # Load documentation coverage metrics
    documentation_report_path = os.path.join(QUALITY_REPORTS_DIR, "documentation_coverage_metrics.json")
    if os.path.exists(documentation_report_path):
        try:
            with open(documentation_report_path, 'r') as f:
                report_data = json.load(f)
            
            # Update metrics
            graph.nodes["documentation_metrics"]["module_coverage"] = report_data.get("module_coverage", 0)
            graph.nodes["documentation_metrics"]["class_coverage"] = report_data.get("class_coverage", 0)
            graph.nodes["documentation_metrics"]["function_coverage"] = report_data.get("function_coverage", 0)
            graph.nodes["documentation_metrics"]["parameter_coverage"] = report_data.get("parameter_coverage", 0)
            graph.nodes["documentation_metrics"]["return_coverage"] = report_data.get("return_coverage", 0)
            graph.nodes["documentation_metrics"]["overall_coverage"] = report_data.get("overall_coverage", 0)
            graph.nodes["documentation_metrics"]["last_modified"] = datetime.datetime.now().timestamp()
            
            print("Documentation metrics updated.")
        except Exception as e:
            print(f"Error updating documentation metrics: {e}")
    else:
        print(f"Documentation report not found at {documentation_report_path}")

def update_code_quality_metrics(graph):
    """Update code quality metrics in the knowledge graph."""
    print("Updating code quality metrics...")
    
    # Load code quality report
    code_quality_report_path = os.path.join(QUALITY_REPORTS_DIR, "quality-standards-report.json")
    if os.path.exists(code_quality_report_path):
        try:
            with open(code_quality_report_path, 'r') as f:
                report_data = json.load(f)
            
            # Update metrics
            graph.nodes["code_quality_metrics"]["total_checks"] = report_data.get("total_checks", 0)
            graph.nodes["code_quality_metrics"]["passed"] = report_data.get("passed_checks", 0)
            graph.nodes["code_quality_metrics"]["failed"] = report_data.get("failed_checks", 0)
            graph.nodes["code_quality_metrics"]["last_modified"] = datetime.datetime.now().timestamp()
            
            print("Code quality metrics updated.")
        except Exception as e:
            print(f"Error updating code quality metrics: {e}")
    else:
        print(f"Code quality report not found at {code_quality_report_path}")

def update_mcp_compliance(graph):
    """Update MCP compliance in the knowledge graph."""
    print("Updating MCP compliance...")
    
    # Load MCP compliance entry
    mcp_compliance_path = os.path.join(KG_DATA_DIR, "mcp_compliance_entry.json")
    if os.path.exists(mcp_compliance_path):
        try:
            with open(mcp_compliance_path, 'r') as f:
                compliance_data = json.load(f)
            
            # Update compliance status
            graph.nodes["mcp_compliance"]["status"] = compliance_data.get("status", "unknown")
            graph.nodes["mcp_compliance"]["last_modified"] = datetime.datetime.now().timestamp()
            
            # Update individual requirements
            for requirement in compliance_data.get("requirements", []):
                req_id = requirement.get("id")
                if req_id:
                    graph.nodes["mcp_compliance"][req_id] = requirement.get("status", "unknown")
            
            print("MCP compliance updated.")
        except Exception as e:
            print(f"Error updating MCP compliance: {e}")
    else:
        print(f"MCP compliance entry not found at {mcp_compliance_path}")

if __name__ == "__main__":
    update_knowledge_graph()