#!/usr/bin/env python3
"""
Unit test for the record_logging_system.py script.

This test verifies that the script can be run without errors and
properly updates the knowledge graph with logging system information.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import shutil

# Add the project root to the Python path to allow importing from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the script to test
from core.kg.scripts.record_logging_system import (
    add_logging_system_component,
    add_logging_module,
    add_documentation_file,
    add_test_file,
    add_directory_structure_metadata,
    add_naming_convention_metadata,
    connect_to_existing_components,
    record_migration_decision,
    main
)


class TestRecordLoggingSystem(unittest.TestCase):
    """Tests for the record_logging_system.py script."""

    def setUp(self):
        """Set up the test environment."""
        # Create a mock NetworkX graph and RDFLib graph
        self.mock_nx_graph = MagicMock()
        self.mock_rdf_graph = MagicMock()
        
        # Mock node access in NetworkX graph
        self.mock_nx_graph.__contains__.return_value = False
        self.mock_nx_graph.has_edge.return_value = False
        self.mock_nx_graph.nodes = MagicMock()
        self.mock_nx_graph.nodes.__getitem__ = MagicMock(return_value={})

    def test_add_logging_system_component(self):
        """Test adding the logging system component to the knowledge graph."""
        # Run the function
        result = add_logging_system_component(self.mock_nx_graph, self.mock_rdf_graph)
        
        # Check that the function returned True
        self.assertTrue(result)
        
        # Check that the add_node method was called
        self.mock_nx_graph.add_node.assert_called_once()
        
        # Check that the add_edge method was called
        self.mock_nx_graph.add_edge.assert_called_once()
        
        # Check that the RDF graph add method was called multiple times
        self.assertTrue(self.mock_rdf_graph.add.call_count > 0)

    def test_add_logging_module(self):
        """Test adding a logging module to the knowledge graph."""
        # Set up the mock to make "logging_system" exist in the graph
        self.mock_nx_graph.__contains__.side_effect = lambda x: x == "logging_system"
        
        # Run the function
        result = add_logging_module(
            self.mock_nx_graph,
            self.mock_rdf_graph,
            "test_module",
            "Test Module",
            "test/path.py",
            "Test description"
        )
        
        # Check that the function returned True
        self.assertTrue(result)
        
        # Check that the add_node method was called
        self.mock_nx_graph.add_node.assert_called_once()
        
        # Check that the add_edge method was called
        self.mock_nx_graph.add_edge.assert_called_once()
        
        # Check that the RDF graph add method was called multiple times
        self.assertTrue(self.mock_rdf_graph.add.call_count > 0)

    def test_main_function(self):
        """Test the main function with mocked dependencies."""
        # Mock the load_knowledge_graph function
        mock_load = MagicMock(return_value=(self.mock_nx_graph, self.mock_rdf_graph))
        
        # Mock the save_knowledge_graph function
        mock_save = MagicMock()
        
        # Patch the necessary functions
        with patch('core.kg.scripts.record_logging_system.load_knowledge_graph', mock_load), \
             patch('core.kg.scripts.record_logging_system.save_knowledge_graph', mock_save), \
             patch('core.kg.scripts.record_logging_system.add_logging_system_component'), \
             patch('core.kg.scripts.record_logging_system.add_logging_module'), \
             patch('core.kg.scripts.record_logging_system.add_documentation_file'), \
             patch('core.kg.scripts.record_logging_system.add_test_file'), \
             patch('core.kg.scripts.record_logging_system.add_directory_structure_metadata'), \
             patch('core.kg.scripts.record_logging_system.add_naming_convention_metadata'), \
             patch('core.kg.scripts.record_logging_system.connect_to_existing_components'), \
             patch('core.kg.scripts.record_logging_system.record_migration_decision'):
            
            # Run the main function
            result = main()
            
            # Check that the function returned True
            self.assertTrue(result)
            
            # Check that load_knowledge_graph was called
            mock_load.assert_called_once()
            
            # Check that save_knowledge_graph was called
            mock_save.assert_called_once()

    def test_idempotence(self):
        """Test that the script is idempotent (can be run multiple times)."""
        # Mock the graph to simulate that nodes already exist
        self.mock_nx_graph.__contains__.return_value = True
        
        # Mock the nodes dictionary to return a mutable dict for the node
        node_dict = {}
        self.mock_nx_graph.nodes.__getitem__.return_value = node_dict
        
        # Run the functions that should handle existing nodes
        result1 = add_logging_system_component(self.mock_nx_graph, self.mock_rdf_graph)
        result2 = add_logging_module(
            self.mock_nx_graph,
            self.mock_rdf_graph,
            "test_module",
            "Test Module",
            "test/path.py",
            "Test description"
        )
        
        # Check that the functions returned True
        self.assertTrue(result1)
        self.assertTrue(result2)
        
        # Check that add_node was not called (since nodes already exist)
        self.mock_nx_graph.add_node.assert_not_called()


if __name__ == "__main__":
    unittest.main()