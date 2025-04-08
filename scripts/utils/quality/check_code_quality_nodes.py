#!/usr/bin/env python3
"""
Knowledge Graph Integration for Code Quality

This script integrates code quality check and fix results with the knowledge graph.
It can load reports from the check_code_quality.sh and fix_code_quality.sh scripts
and update the knowledge graph accordingly.
"""

import argparse
import datetime
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import networkx as nx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("check_code_quality_nodes")

# Define paths
PROJECT_ROOT = Path(__file__).resolve().parents[4]
KG_PATH = PROJECT_ROOT / "core" / "kg" / "data" / "knowledge_graph.graphml"


def load_knowledge_graph(kg_path: Path = KG_PATH) -> nx.Graph:
    """
    Load the knowledge graph.
    
    Args:
        kg_path: Path to the knowledge graph file.
        
    Returns:
        The loaded knowledge graph.
    """
    logger.info(f"Loading knowledge graph from {kg_path}")
    
    if not kg_path.exists():
        logger.warning(f"Knowledge graph file not found: {kg_path}")
        logger.info("Creating a new knowledge graph")
        g = nx.Graph()
        g.add_node("code_quality", name="Code Quality", type="component", status="active")
        return g
    
    try:
        g = nx.read_graphml(kg_path)
        logger.info(f"Knowledge graph loaded with {len(g.nodes)} nodes and {len(g.edges)} edges")
        return g
    except Exception as e:
        logger.error(f"Error loading knowledge graph: {e}")
        logger.info("Creating a new knowledge graph")
        g = nx.Graph()
        g.add_node("code_quality", name="Code Quality", type="component", status="active")
        return g


def save_knowledge_graph(g: nx.Graph, kg_path: Path = KG_PATH) -> None:
    """
    Save the knowledge graph.
    
    Args:
        g: The knowledge graph to save.
        kg_path: Path to save the knowledge graph to.
    """
    logger.info(f"Saving knowledge graph to {kg_path}")
    
    # Ensure the directory exists
    kg_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        nx.write_graphml(g, kg_path)
        logger.info(f"Knowledge graph saved with {len(g.nodes)} nodes and {len(g.edges)} edges")
    except Exception as e:
        logger.error(f"Error saving knowledge graph: {e}")
        logger.warning("Continuing without saving knowledge graph")


def load_report(report_path: Path) -> Dict[str, Any]:
    """
    Load a report from a JSON file.
    
    Args:
        report_path: Path to the report file.
        
    Returns:
        The loaded report.
    """
    logger.info(f"Loading report from {report_path}")
    
    if not report_path.exists():
        logger.error(f"Report file not found: {report_path}")
        sys.exit(1)
    
    try:
        with open(report_path, "r") as f:
            report = json.load(f)
        
        logger.info(f"Report loaded successfully")
        return report
    except Exception as e:
        logger.error(f"Error loading report: {e}")
        sys.exit(1)


def update_knowledge_graph_with_check_results(g: nx.Graph, report: Dict[str, Any]) -> nx.Graph:
    """
    Update the knowledge graph with code quality check results.
    
    Args:
        g: The knowledge graph to update.
        report: The report with check results.
        
    Returns:
        The updated knowledge graph.
    """
    logger.info("Updating knowledge graph with code quality check results")
    
    # Get or create the code_quality node
    if "code_quality" not in g.nodes:
        g.add_node("code_quality", name="Code Quality", type="component", status="active")
        logger.info("Created code_quality node")
    
    # Get or create the code_quality_checks node
    if "code_quality_checks" not in g.nodes:
        g.add_node("code_quality_checks", name="Code Quality Checks", type="feature", status="active")
        g.add_edge("code_quality", "code_quality_checks", relation="has_feature")
        logger.info("Created code_quality_checks node")
    
    # Update the code_quality_checks node with the latest check results
    g.nodes["code_quality_checks"]["last_check"] = report.get("timestamp", datetime.datetime.utcnow().isoformat())
    g.nodes["code_quality_checks"]["total_checks"] = report.get("summary", {}).get("total_checks", 0)
    g.nodes["code_quality_checks"]["passed_checks"] = report.get("summary", {}).get("passed", 0)
    g.nodes["code_quality_checks"]["failed_checks"] = report.get("summary", {}).get("failed", 0)
    
    # Add category nodes
    categories = report.get("summary", {}).get("categories", {})
    for category, count in categories.items():
        category_node = f"code_quality_{category}"
        if category_node not in g.nodes:
            g.add_node(category_node, name=f"{category.capitalize()} Code Quality", type="category", count=count)
            g.add_edge("code_quality_checks", category_node, relation="has_category")
            logger.info(f"Created {category_node} node")
        else:
            g.nodes[category_node]["count"] = count
    
    # Add tool nodes
    tools = set()
    for result in report.get("results", []):
        tool = result.get("tool", "").replace(" ", "_").lower()
        if tool:
            tools.add(tool)
    
    for tool in tools:
        tool_node = f"tool_{tool}"
        if tool_node not in g.nodes:
            g.add_node(tool_node, name=tool, type="tool")
            g.add_edge("code_quality_checks", tool_node, relation="uses_tool")
            logger.info(f"Created {tool_node} node")
    
    logger.info("Knowledge graph updated with check results")
    return g


def update_knowledge_graph_with_fix_results(g: nx.Graph, report: Dict[str, Any]) -> nx.Graph:
    """
    Update the knowledge graph with code quality fix results.
    
    Args:
        g: The knowledge graph to update.
        report: The report with fix results.
        
    Returns:
        The updated knowledge graph.
    """
    logger.info("Updating knowledge graph with code quality fix results")
    
    # Get or create the code_quality node
    if "code_quality" not in g.nodes:
        g.add_node("code_quality", name="Code Quality", type="component", status="active")
        logger.info("Created code_quality node")
    
    # Get or create the code_quality_fixes node
    if "code_quality_fixes" not in g.nodes:
        g.add_node("code_quality_fixes", name="Code Quality Fixes", type="feature", status="active")
        g.add_edge("code_quality", "code_quality_fixes", relation="has_feature")
        logger.info("Created code_quality_fixes node")
    
    # Update the code_quality_fixes node with the latest fix results
    g.nodes["code_quality_fixes"]["last_fix"] = report.get("timestamp", datetime.datetime.utcnow().isoformat())
    g.nodes["code_quality_fixes"]["total_issues"] = report.get("total_issues", 0)
    g.nodes["code_quality_fixes"]["fixable_issues"] = report.get("fixable_issues", 0)
    g.nodes["code_quality_fixes"]["fixed_issues"] = report.get("fixed_count", 0)
    g.nodes["code_quality_fixes"]["unfixed_issues"] = report.get("unfixed_count", 0)
    
    # Add category nodes
    categories = report.get("summary", {}).get("categories", {})
    for category, count in categories.items():
        category_node = f"code_quality_{category}"
        if category_node not in g.nodes:
            g.add_node(category_node, name=f"{category.capitalize()} Code Quality", type="category", count=count)
            g.add_edge("code_quality_fixes", category_node, relation="has_category")
            logger.info(f"Created {category_node} node")
        else:
            g.nodes[category_node]["count"] = count
    
    # Add tool nodes
    tools = set()
    for result in report.get("results", []):
        tool = result.get("tool", "").replace(" ", "_").lower()
        if tool:
            tools.add(tool)
    
    for tool in tools:
        tool_node = f"tool_{tool}"
        if tool_node not in g.nodes:
            g.add_node(tool_node, name=tool, type="tool")
            g.add_edge("code_quality_fixes", tool_node, relation="uses_tool")
            logger.info(f"Created {tool_node} node")
    
    logger.info("Knowledge graph updated with fix results")
    return g


def print_code_quality_nodes(g: nx.Graph) -> None:
    """
    Print code quality nodes in the knowledge graph.
    
    Args:
        g: The knowledge graph.
    """
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
    
    # Check code quality checks
    if 'code_quality_checks' in g.nodes:
        print('\nCode Quality Checks:')
        attrs = g.nodes['code_quality_checks']
        print(f'- Last check: {attrs.get("last_check", "N/A")}')
        print(f'- Total checks: {attrs.get("total_checks", 0)}')
        print(f'- Passed checks: {attrs.get("passed_checks", 0)}')
        print(f'- Failed checks: {attrs.get("failed_checks", 0)}')
    
    # Check code quality fixes
    if 'code_quality_fixes' in g.nodes:
        print('\nCode Quality Fixes:')
        attrs = g.nodes['code_quality_fixes']
        print(f'- Last fix: {attrs.get("last_fix", "N/A")}')
        print(f'- Total issues: {attrs.get("total_issues", 0)}')
        print(f'- Fixable issues: {attrs.get("fixable_issues", 0)}')
        print(f'- Fixed issues: {attrs.get("fixed_issues", 0)}')
        print(f'- Unfixed issues: {attrs.get("unfixed_issues", 0)}')


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Knowledge Graph Integration for Code Quality")
    
    parser.add_argument("--report", type=str, help="Path to the report file")
    parser.add_argument("--fixes", action="store_true", help="Update with fix results instead of check results")
    parser.add_argument("--kg-path", type=str, help="Path to the knowledge graph file")
    
    return parser.parse_args()


def main() -> int:
    """
    Main function.
    
    Returns:
        Exit code.
    """
    args = parse_args()
    
    # Load the knowledge graph
    kg_path = Path(args.kg_path) if args.kg_path else KG_PATH
    g = load_knowledge_graph(kg_path)
    
    # Update the knowledge graph with report results if provided
    if args.report:
        report_path = Path(args.report)
        report = load_report(report_path)
        
        if args.fixes:
            g = update_knowledge_graph_with_fix_results(g, report)
        else:
            g = update_knowledge_graph_with_check_results(g, report)
        
        # Save the updated knowledge graph
        save_knowledge_graph(g, kg_path)
    
    # Print code quality nodes
    print_code_quality_nodes(g)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())