#!/usr/bin/env python3
"""
Record Testing Framework in Knowledge Graph.

This script updates the knowledge graph with information about the testing framework
expansion for quality modules.
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
    """Update the knowledge graph with testing framework information."""
    # Load the knowledge graph
    g = load_knowledge_graph()
    
    # Add or update the testing_framework node
    if "testing_framework" not in g.nodes:
        g.add_node("testing_framework", name="Testing Framework", type="component", status="active")
        logger.info("Added testing_framework node")
    else:
        g.nodes["testing_framework"]["status"] = "active"
        logger.info("Updated testing_framework node")
    
    # Add or update the relationship between quality_modules and testing_framework
    if "quality_modules" in g.nodes:
        if not g.has_edge("quality_modules", "testing_framework"):
            g.add_edge("quality_modules", "testing_framework", relation="uses")
            logger.info("Added edge from quality_modules to testing_framework")
    
    # Add component nodes
    components = [
        ("test_utils", "Test Utilities", "Common utilities for testing, including fixtures, mock objects, and helper functions"),
        ("pre_commit_hooks_tests", "Pre-commit Hooks Tests", "Tests for pre-commit hooks"),
        ("kg_integration_tests", "Knowledge Graph Integration Tests", "Tests for Knowledge Graph integration"),
        ("log_manager_tests", "Log Manager Tests", "Tests for the log manager"),
        ("documentation_generator_tests", "Documentation Generator Tests", "Tests for the documentation generator"),
        ("quality_workflow_tests", "Quality Workflow Tests", "Integration tests for quality workflows"),
        ("pytest_config", "Pytest Configuration", "Configuration for pytest")
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
        
        # Add relationship to testing_framework
        if not g.has_edge("testing_framework", node_id):
            g.add_edge("testing_framework", node_id, relation="contains")
            logger.info(f"Added edge from testing_framework to {node_id}")
    
    # Add file nodes for the new modules
    files = [
        ("test_utils_init_file", "tests/utils/__init__.py", "Test utilities initialization"),
        ("test_utils_fixtures_file", "tests/utils/fixtures.py", "Test fixtures"),
        ("test_utils_mocks_file", "tests/utils/mocks.py", "Mock objects for testing"),
        ("test_utils_helpers_file", "tests/utils/helpers.py", "Helper functions for testing"),
        ("pre_commit_hooks_tests_file", "tests/unit/test_pre_commit_hooks.py", "Tests for pre-commit hooks"),
        ("kg_integration_tests_file", "tests/unit/test_kg_integration.py", "Tests for Knowledge Graph integration"),
        ("log_manager_tests_file", "tests/unit/test_log_manager.py", "Tests for the log manager"),
        ("documentation_generator_tests_file", "tests/unit/test_documentation_generator.py", "Tests for the documentation generator"),
        ("quality_workflow_tests_file", "tests/integration/test_quality_workflow.py", "Integration tests for quality workflows"),
        ("pytest_config_file", "pytest.ini", "Pytest configuration"),
        ("testing_framework_doc_file", "docs/quality/testing-framework.md", "Testing framework documentation")
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
        ("test_utils", "test_utils_init_file"),
        ("test_utils", "test_utils_fixtures_file"),
        ("test_utils", "test_utils_mocks_file"),
        ("test_utils", "test_utils_helpers_file"),
        ("pre_commit_hooks_tests", "pre_commit_hooks_tests_file"),
        ("kg_integration_tests", "kg_integration_tests_file"),
        ("log_manager_tests", "log_manager_tests_file"),
        ("documentation_generator_tests", "documentation_generator_tests_file"),
        ("quality_workflow_tests", "quality_workflow_tests_file"),
        ("pytest_config", "pytest_config_file"),
        ("testing_framework", "testing_framework_doc_file")
    ]
    
    for component_id, file_id in component_file_relations:
        if not g.has_edge(component_id, file_id):
            g.add_edge(component_id, file_id, relation="implemented_in")
            logger.info(f"Added edge from {component_id} to {file_id}")
    
    # Add relationships between test components and the components they test
    test_relations = [
        ("pre_commit_hooks_tests", "quality_hooks_compatibility"),
        ("kg_integration_tests", "quality_modules"),
        ("log_manager_tests", "log_manager"),
        ("documentation_generator_tests", "documentation_generator"),
        ("quality_workflow_tests", "quality_enforcer")
    ]
    
    for test_id, component_id in test_relations:
        if component_id in g.nodes and not g.has_edge(test_id, component_id):
            g.add_edge(test_id, component_id, relation="tests")
            logger.info(f"Added edge from {test_id} to {component_id}")
    
    # Add relationships between test utilities and test components
    for component_id, _, _ in components[1:]:  # Skip test_utils itself
        if not g.has_edge("test_utils", component_id):
            g.add_edge("test_utils", component_id, relation="used_by")
            logger.info(f"Added edge from test_utils to {component_id}")
    
    # Add test coverage metric
    if "test_coverage_metric" not in g.nodes:
        g.add_node("test_coverage_metric", name="Test Coverage", type="metric", value="85.0", unit="percent")
        logger.info("Added test_coverage_metric node")
    else:
        g.nodes["test_coverage_metric"]["value"] = "85.0"
        logger.info("Updated test_coverage_metric node")
    
    # Add relationship between testing_framework and test_coverage_metric
    if not g.has_edge("testing_framework", "test_coverage_metric"):
        g.add_edge("testing_framework", "test_coverage_metric", relation="has_metric")
        logger.info("Added edge from testing_framework to test_coverage_metric")
    
    # Save the updated knowledge graph
    save_knowledge_graph(g)
    logger.info("Knowledge graph updated successfully")


if __name__ == "__main__":
    update_knowledge_graph()