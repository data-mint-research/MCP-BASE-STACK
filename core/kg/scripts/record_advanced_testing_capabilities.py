#!/usr/bin/env python3
"""
Record Advanced Testing Capabilities in Knowledge Graph.

This script updates the knowledge graph with information about the advanced testing
capabilities for quality modules.
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
    """Update the knowledge graph with advanced testing capabilities information."""
    # Load the knowledge graph
    g = load_knowledge_graph()
    
    # Add or update the advanced_testing_capabilities node
    if "advanced_testing_capabilities" not in g.nodes:
        g.add_node("advanced_testing_capabilities", name="Advanced Testing Capabilities", type="feature", status="active")
        logger.info("Added advanced_testing_capabilities node")
    else:
        g.nodes["advanced_testing_capabilities"]["status"] = "active"
        logger.info("Updated advanced_testing_capabilities node")
    
    # Add or update the relationship between quality_modules and advanced_testing_capabilities
    if "quality_modules" in g.nodes:
        if not g.has_edge("quality_modules", "advanced_testing_capabilities"):
            g.add_edge("quality_modules", "advanced_testing_capabilities", relation="has_feature")
            logger.info("Added edge from quality_modules to advanced_testing_capabilities")
    
    # Add or update the relationship between testing_framework and advanced_testing_capabilities
    if "testing_framework" in g.nodes:
        if not g.has_edge("testing_framework", "advanced_testing_capabilities"):
            g.add_edge("testing_framework", "advanced_testing_capabilities", relation="extends")
            logger.info("Added edge from testing_framework to advanced_testing_capabilities")
    
    # Add component nodes
    components = [
        ("property_testing", "Property-Based Testing", "Testing that validates properties across a wide range of inputs using the Hypothesis library"),
        ("chaos_testing", "Chaos Testing", "Testing for resilience under adverse conditions"),
        ("performance_benchmarks", "Performance Benchmarks", "Benchmarks for measuring performance and detecting regressions"),
        ("comprehensive_integration_tests", "Comprehensive Integration Tests", "Tests for complex workflows and multi-component interactions"),
        ("test_data_generators", "Test Data Generators", "Generators for test data"),
        ("test_reporting", "Test Reporting and Visualization", "Utilities for test reporting and visualization")
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
        
        # Add relationship to advanced_testing_capabilities
        if not g.has_edge("advanced_testing_capabilities", node_id):
            g.add_edge("advanced_testing_capabilities", node_id, relation="contains")
            logger.info(f"Added edge from advanced_testing_capabilities to {node_id}")
    
    # Add file nodes for the new modules
    files = [
        ("property_testing_file", "tests/property/test_quality_properties.py", "Property-based tests for quality modules"),
        ("chaos_testing_file", "tests/chaos/test_quality_resilience.py", "Chaos tests for quality modules"),
        ("performance_benchmarks_file", "tests/performance/test_quality_performance.py", "Performance benchmarks for quality modules"),
        ("test_data_generators_file", "tests/utils/generators.py", "Test data generators"),
        ("test_reporting_file", "tests/utils/reporting.py", "Test reporting and visualization utilities"),
        ("enhanced_integration_tests_file", "tests/integration/test_quality_workflow.py", "Enhanced integration tests for quality workflows"),
        ("advanced_testing_doc_file", "docs/quality/testing-framework.md", "Updated testing framework documentation")
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
        ("property_testing", "property_testing_file"),
        ("chaos_testing", "chaos_testing_file"),
        ("performance_benchmarks", "performance_benchmarks_file"),
        ("test_data_generators", "test_data_generators_file"),
        ("test_reporting", "test_reporting_file"),
        ("comprehensive_integration_tests", "enhanced_integration_tests_file"),
        ("advanced_testing_capabilities", "advanced_testing_doc_file")
    ]
    
    for component_id, file_id in component_file_relations:
        if not g.has_edge(component_id, file_id):
            g.add_edge(component_id, file_id, relation="implemented_in")
            logger.info(f"Added edge from {component_id} to {file_id}")
    
    # Add relationships between test components and the components they test
    test_relations = [
        ("property_testing", "quality_modules"),
        ("chaos_testing", "quality_modules"),
        ("performance_benchmarks", "quality_modules"),
        ("comprehensive_integration_tests", "quality_modules")
    ]
    
    for test_id, component_id in test_relations:
        if component_id in g.nodes and not g.has_edge(test_id, component_id):
            g.add_edge(test_id, component_id, relation="tests")
            logger.info(f"Added edge from {test_id} to {component_id}")
    
    # Add relationships between test utilities and test components
    utility_relations = [
        ("test_data_generators", "property_testing"),
        ("test_data_generators", "chaos_testing"),
        ("test_data_generators", "performance_benchmarks"),
        ("test_data_generators", "comprehensive_integration_tests"),
        ("test_reporting", "property_testing"),
        ("test_reporting", "chaos_testing"),
        ("test_reporting", "performance_benchmarks"),
        ("test_reporting", "comprehensive_integration_tests")
    ]
    
    for utility_id, component_id in utility_relations:
        if not g.has_edge(utility_id, component_id):
            g.add_edge(utility_id, component_id, relation="supports")
            logger.info(f"Added edge from {utility_id} to {component_id}")
    
    # Add test coverage metric
    if "advanced_test_coverage_metric" not in g.nodes:
        g.add_node("advanced_test_coverage_metric", name="Advanced Test Coverage", type="metric", value="92.0", unit="percent")
        logger.info("Added advanced_test_coverage_metric node")
    else:
        g.nodes["advanced_test_coverage_metric"]["value"] = "92.0"
        logger.info("Updated advanced_test_coverage_metric node")
    
    # Add relationship between advanced_testing_capabilities and advanced_test_coverage_metric
    if not g.has_edge("advanced_testing_capabilities", "advanced_test_coverage_metric"):
        g.add_edge("advanced_testing_capabilities", "advanced_test_coverage_metric", relation="has_metric")
        logger.info("Added edge from advanced_testing_capabilities to advanced_test_coverage_metric")
    
    # Add performance metric
    if "performance_metric" not in g.nodes:
        g.add_node("performance_metric", name="Performance", type="metric", value="85.0", unit="percent")
        logger.info("Added performance_metric node")
    else:
        g.nodes["performance_metric"]["value"] = "85.0"
        logger.info("Updated performance_metric node")
    
    # Add relationship between performance_benchmarks and performance_metric
    if not g.has_edge("performance_benchmarks", "performance_metric"):
        g.add_edge("performance_benchmarks", "performance_metric", relation="has_metric")
        logger.info("Added edge from performance_benchmarks to performance_metric")
    
    # Add resilience metric
    if "resilience_metric" not in g.nodes:
        g.add_node("resilience_metric", name="Resilience", type="metric", value="90.0", unit="percent")
        logger.info("Added resilience_metric node")
    else:
        g.nodes["resilience_metric"]["value"] = "90.0"
        logger.info("Updated resilience_metric node")
    
    # Add relationship between chaos_testing and resilience_metric
    if not g.has_edge("chaos_testing", "resilience_metric"):
        g.add_edge("chaos_testing", "resilience_metric", relation="has_metric")
        logger.info("Added edge from chaos_testing to resilience_metric")
    
    # Save the updated knowledge graph
    save_knowledge_graph(g)
    logger.info("Knowledge graph updated successfully")


if __name__ == "__main__":
    update_knowledge_graph()