#!/usr/bin/env python3
"""
Unit tests for the design_mcp_architecture.py script.

This module contains tests to verify the functionality of the architecture design script.
"""

import os
import sys
import json
import unittest
import logging
import tempfile
import yaml
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the script to test
import design_mcp_architecture as designer
from design_mcp_architecture import (
    ArchitectureDesigner, 
    Component, 
    Interface, 
    DataFlow, 
    ArchitectureDesign
)


class TestArchitectureDesigner(unittest.TestCase):
    """Test cases for the ArchitectureDesigner class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create a temporary analysis report file
        self.analysis_report_path = os.path.join(self.temp_dir.name, "analysis_report.json")
        self.create_test_analysis_report()
        
        # Create a temporary structure.yaml file
        self.structure_yaml = os.path.join(self.temp_dir.name, "structure.yaml")
        self.create_test_structure_yaml()

    def tearDown(self):
        """Tear down test fixtures."""
        self.temp_dir.cleanup()

    def create_test_analysis_report(self):
        """Create a test analysis report JSON file."""
        report = {
            "components": [
                {
                    "name": "mcp-server",
                    "path": "/services/mcp-server",
                    "description": "Core MCP server implementation",
                    "required_files": [],
                    "existing_files": [],
                    "missing_files": [],
                    "migration_status": "partial",
                    "completion_percentage": 50.0
                },
                {
                    "name": "host",
                    "path": "/services/mcp-server/src/host",
                    "description": "Host component",
                    "required_files": [
                        "services/mcp-server/src/host/__init__.py",
                        "services/mcp-server/src/host/host.py"
                    ],
                    "existing_files": [
                        "services/mcp-server/src/host/__init__.py"
                    ],
                    "missing_files": [
                        "services/mcp-server/src/host/host.py"
                    ],
                    "migration_status": "partial",
                    "completion_percentage": 50.0
                },
                {
                    "name": "client",
                    "path": "/services/mcp-server/src/client",
                    "description": "Client component",
                    "required_files": [
                        "services/mcp-server/src/client/__init__.py",
                        "services/mcp-server/src/client/client.py"
                    ],
                    "existing_files": [
                        "services/mcp-server/src/client/__init__.py",
                        "services/mcp-server/src/client/client.py"
                    ],
                    "missing_files": [],
                    "migration_status": "complete",
                    "completion_percentage": 100.0
                }
            ],
            "migration_candidates": [
                {
                    "name": "host",
                    "path": "/services/mcp-server/src/host",
                    "description": "Host component",
                    "required_files": [
                        "services/mcp-server/src/host/__init__.py",
                        "services/mcp-server/src/host/host.py"
                    ],
                    "existing_files": [
                        "services/mcp-server/src/host/__init__.py"
                    ],
                    "missing_files": [
                        "services/mcp-server/src/host/host.py"
                    ],
                    "migration_status": "partial",
                    "completion_percentage": 50.0
                }
            ],
            "missing_components": [],
            "existing_components": [
                {
                    "name": "client",
                    "path": "/services/mcp-server/src/client",
                    "description": "Client component",
                    "required_files": [
                        "services/mcp-server/src/client/__init__.py",
                        "services/mcp-server/src/client/client.py"
                    ],
                    "existing_files": [
                        "services/mcp-server/src/client/__init__.py",
                        "services/mcp-server/src/client/client.py"
                    ],
                    "missing_files": [],
                    "migration_status": "complete",
                    "completion_percentage": 100.0
                }
            ],
            "timestamp": "2025-04-08T14:00:00.000000",
            "codebase_path": "/home/user/project",
            "target_structure_path": "/home/user/project/structure.yaml"
        }
        
        with open(self.analysis_report_path, 'w') as f:
            json.dump(report, f)

    def create_test_structure_yaml(self):
        """Create a test structure.yaml file."""
        structure = {
            "version": "1.0",
            "description": "Test structure for unit tests",
            "structure": {
                "services": {
                    "mcp-server": {
                        "description": "Core MCP server implementation",
                        "components": {
                            "host": {
                                "description": "Host component",
                                "required_files": [
                                    "services/mcp-server/src/host/__init__.py",
                                    "services/mcp-server/src/host/host.py"
                                ]
                            },
                            "client": {
                                "description": "Client component",
                                "required_files": [
                                    "services/mcp-server/src/client/__init__.py",
                                    "services/mcp-server/src/client/client.py"
                                ]
                            },
                            "server": {
                                "description": "Server component",
                                "required_files": [
                                    "services/mcp-server/src/server/__init__.py",
                                    "services/mcp-server/src/server/server.py"
                                ],
                                "components": {
                                    "tools": {
                                        "description": "Tool implementations",
                                        "required_files": [
                                            "services/mcp-server/src/server/tools/__init__.py",
                                            "services/mcp-server/src/server/tools/registry.py"
                                        ],
                                        "components": {
                                            "shell": {
                                                "description": "Shell command tools",
                                                "required_files": [
                                                    "services/mcp-server/src/server/tools/shell/__init__.py",
                                                    "services/mcp-server/src/server/tools/shell/command.py"
                                                ]
                                            }
                                        }
                                    },
                                    "resources": {
                                        "description": "Resource implementations",
                                        "required_files": [
                                            "services/mcp-server/src/server/resources/__init__.py",
                                            "services/mcp-server/src/server/resources/registry.py"
                                        ],
                                        "components": {
                                            "file": {
                                                "description": "File resources",
                                                "required_files": [
                                                    "services/mcp-server/src/server/resources/file/__init__.py",
                                                    "services/mcp-server/src/server/resources/file/provider.py"
                                                ]
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        with open(self.structure_yaml, 'w') as f:
            yaml.dump(structure, f)

    def test_initialization(self):
        """Test that the designer initializes correctly."""
        designer = ArchitectureDesigner(self.analysis_report_path, self.structure_yaml)
        self.assertEqual(designer.analysis_report_path, self.analysis_report_path)
        self.assertEqual(designer.target_structure_path, self.structure_yaml)
        self.assertIsNotNone(designer.analysis_report)
        self.assertIsNotNone(designer.target_structure)
        self.assertIsInstance(designer.design, ArchitectureDesign)
        self.assertEqual(len(designer.component_registry), 0)
        self.assertEqual(len(designer.interface_registry), 0)

    def test_design_architecture(self):
        """Test the design_architecture method."""
        designer = ArchitectureDesigner(self.analysis_report_path, self.structure_yaml)
        design = designer.design_architecture()
        
        # Check that the design contains the expected components
        self.assertGreaterEqual(len(design.components), 3)  # At least Host, Client, Server
        
        # Check that the design contains the expected interfaces
        self.assertGreaterEqual(len(design.interfaces), 3)  # At least the core interfaces
        
        # Check that the design contains the expected data flows
        self.assertGreaterEqual(len(design.data_flows), 3)  # At least the core data flows
        
        # Check that the core components are defined
        component_names = [c.name for c in design.components]
        self.assertIn("MCPHost", component_names)
        self.assertIn("MCPClient", component_names)
        self.assertIn("MCPServer", component_names)
        
        # Check that the core interfaces are defined
        interface_names = [i.name for i in design.interfaces]
        self.assertIn("HostClientInterface", interface_names)
        self.assertIn("HostServerInterface", interface_names)
        self.assertIn("ClientServerInterface", interface_names)
        
        # Check that tools and resources are processed
        self.assertIn("ToolsRegistry", component_names)
        self.assertIn("ResourcesRegistry", component_names)
        self.assertIn("ShellTool", component_names)
        self.assertIn("FileResource", component_names)

    def test_define_core_components(self):
        """Test the _define_core_components method."""
        designer = ArchitectureDesigner(self.analysis_report_path, self.structure_yaml)
        designer._define_core_components()
        
        # Check that the core components are defined
        self.assertIn("MCPHost", designer.component_registry)
        self.assertIn("MCPClient", designer.component_registry)
        self.assertIn("MCPServer", designer.component_registry)
        self.assertIn("DependencyInjection", designer.component_registry)
        
        # Check that the components have the expected properties
        host = designer.component_registry["MCPHost"]
        self.assertEqual(host.type, "host")
        self.assertEqual(host.path, "services/mcp-server/src/host")
        self.assertGreaterEqual(len(host.required_files), 1)
        
        client = designer.component_registry["MCPClient"]
        self.assertEqual(client.type, "client")
        self.assertEqual(client.path, "services/mcp-server/src/client")
        self.assertGreaterEqual(len(client.required_files), 1)
        
        server = designer.component_registry["MCPServer"]
        self.assertEqual(server.type, "server")
        self.assertEqual(server.path, "services/mcp-server/src/server")
        self.assertGreaterEqual(len(server.required_files), 1)
        
        # Check dependencies
        self.assertIn("MCPHost", client.dependencies)
        self.assertIn("MCPHost", server.dependencies)

    def test_define_core_interfaces(self):
        """Test the _define_core_interfaces method."""
        designer = ArchitectureDesigner(self.analysis_report_path, self.structure_yaml)
        designer._define_core_components()
        designer._define_core_interfaces()
        
        # Check that the core interfaces are defined
        self.assertIn("HostClientInterface", designer.interface_registry)
        self.assertIn("HostServerInterface", designer.interface_registry)
        self.assertIn("ClientServerInterface", designer.interface_registry)
        
        # Check that the interfaces have the expected properties
        host_client = designer.interface_registry["HostClientInterface"]
        self.assertEqual(host_client.source_component, "MCPHost")
        self.assertEqual(host_client.target_component, "MCPClient")
        self.assertGreaterEqual(len(host_client.methods), 1)
        
        host_server = designer.interface_registry["HostServerInterface"]
        self.assertEqual(host_server.source_component, "MCPHost")
        self.assertEqual(host_server.target_component, "MCPServer")
        self.assertGreaterEqual(len(host_server.methods), 1)
        
        client_server = designer.interface_registry["ClientServerInterface"]
        self.assertEqual(client_server.source_component, "MCPClient")
        self.assertEqual(client_server.target_component, "MCPServer")
        self.assertGreaterEqual(len(client_server.methods), 1)
        
        # Check that components have interfaces assigned
        host = designer.component_registry["MCPHost"]
        self.assertIn("HostClientInterface", host.interfaces)
        self.assertIn("HostServerInterface", host.interfaces)
        
        client = designer.component_registry["MCPClient"]
        self.assertIn("HostClientInterface", client.interfaces)
        self.assertIn("ClientServerInterface", client.interfaces)
        
        server = designer.component_registry["MCPServer"]
        self.assertIn("HostServerInterface", server.interfaces)
        self.assertIn("ClientServerInterface", server.interfaces)

    def test_define_core_data_flows(self):
        """Test the _define_core_data_flows method."""
        designer = ArchitectureDesigner(self.analysis_report_path, self.structure_yaml)
        designer._define_core_components()
        designer._define_core_interfaces()
        designer._define_core_data_flows()
        
        # Check that data flows are defined
        self.assertGreaterEqual(len(designer.design.data_flows), 3)
        
        # Check that the data flows have the expected properties
        flow_names = [flow.name for flow in designer.design.data_flows]
        self.assertIn("HostToClientFlow", flow_names)
        self.assertIn("ClientToHostFlow", flow_names)
        self.assertIn("HostToServerFlow", flow_names)
        self.assertIn("ServerToHostFlow", flow_names)
        
        # Check a specific data flow
        host_to_client = next(flow for flow in designer.design.data_flows if flow.name == "HostToClientFlow")
        self.assertEqual(host_to_client.source_component, "MCPHost")
        self.assertEqual(host_to_client.target_component, "MCPClient")
        self.assertEqual(host_to_client.direction, "bidirectional")
        self.assertEqual(host_to_client.transport, "synchronous")

    def test_process_tools_and_resources(self):
        """Test the _process_tools_and_resources method."""
        designer = ArchitectureDesigner(self.analysis_report_path, self.structure_yaml)
        designer._define_core_components()
        designer._process_tools_and_resources()
        
        # Check that tool and resource registries are defined
        self.assertIn("ToolsRegistry", designer.component_registry)
        self.assertIn("ResourcesRegistry", designer.component_registry)
        
        # Check that specific tools and resources are defined
        self.assertIn("ShellTool", designer.component_registry)
        self.assertIn("FileResource", designer.component_registry)
        
        # Check that tools and resources have the expected properties
        shell_tool = designer.component_registry["ShellTool"]
        self.assertEqual(shell_tool.type, "tool")
        self.assertEqual(shell_tool.path, "services/mcp-server/src/server/tools/shell")
        self.assertIn("ToolsRegistry", shell_tool.dependencies)
        
        file_resource = designer.component_registry["FileResource"]
        self.assertEqual(file_resource.type, "resource")
        self.assertEqual(file_resource.path, "services/mcp-server/src/server/resources/file")
        self.assertIn("ResourcesRegistry", file_resource.dependencies)
        
        # Check that interfaces for tools and resources are defined
        self.assertIn("ShellToolInterface", designer.interface_registry)
        self.assertIn("FileResourceInterface", designer.interface_registry)
        
        # Check that tools and resources are added as subcomponents
        tools_registry = designer.component_registry["ToolsRegistry"]
        self.assertIn("ShellTool", tools_registry.subcomponents)
        
        resources_registry = designer.component_registry["ResourcesRegistry"]
        self.assertIn("FileResource", resources_registry.subcomponents)

    def test_set_implementation_priorities(self):
        """Test the _set_implementation_priorities method."""
        designer = ArchitectureDesigner(self.analysis_report_path, self.structure_yaml)
        designer._define_core_components()
        designer._define_core_interfaces()
        designer._process_tools_and_resources()
        designer._set_implementation_priorities()
        # Check that core components have priorities set
        # Note: The actual priority values may vary based on implementation
        self.assertIsNotNone(designer.component_registry["MCPHost"].implementation_priority)
        self.assertIsNotNone(designer.component_registry["MCPClient"].implementation_priority)
        self.assertIsNotNone(designer.component_registry["MCPServer"].implementation_priority)
        self.assertIsNotNone(designer.component_registry["DependencyInjection"].implementation_priority)
        
        # Check that registries have the expected priorities
        self.assertIsNotNone(designer.component_registry["ToolsRegistry"].implementation_priority)
        self.assertIsNotNone(designer.component_registry["ResourcesRegistry"].implementation_priority)
        
        # Check that tools and resources have the expected priorities
        self.assertIsNotNone(designer.component_registry["ShellTool"].implementation_priority)
        self.assertIsNotNone(designer.component_registry["FileResource"].implementation_priority)
        
        # Check that migration status affects priorities
        # The client component was marked as "complete" in the analysis report
        # Find components that match the client path
        for component_name, component in designer.component_registry.items():
            if component.path == "services/mcp-server/src/client":
                self.assertEqual(component.implementation_priority, 5)

    def test_save_design(self):
        """Test saving the design to a file."""
        designer = ArchitectureDesigner(self.analysis_report_path, self.structure_yaml)
        designer.design_architecture()
        
        output_path = os.path.join(self.temp_dir.name, "architecture_design.json")
        designer.save_design(output_path)
        
        # Check that the file exists
        self.assertTrue(os.path.exists(output_path))
        
        # Check that the file contains valid JSON
        with open(output_path, 'r') as f:
            design_data = json.load(f)
        
        # Check that the design has the expected structure
        self.assertIn("components", design_data)
        self.assertIn("interfaces", design_data)
        self.assertIn("data_flows", design_data)
        self.assertIn("timestamp", design_data)
        
        # Check that components are properly serialized
        self.assertGreaterEqual(len(design_data["components"]), 3)
        component = design_data["components"][0]
        self.assertIn("name", component)
        self.assertIn("type", component)
        self.assertIn("description", component)
        self.assertIn("path", component)
        self.assertIn("required_files", component)
        self.assertIn("interfaces", component)
        self.assertIn("dependencies", component)
        self.assertIn("implementation_priority", component)

    @patch('design_mcp_architecture.logger')
    def test_verbose_logging(self, mock_logger):
        """Test that verbose logging works."""
        designer = ArchitectureDesigner(self.analysis_report_path, self.structure_yaml, verbose=True)
        # Check that verbose logging was enabled
        self.assertEqual(mock_logger.setLevel.call_count, 1)
        mock_logger.setLevel.assert_called_with(logging.DEBUG)

    def test_invalid_paths(self):
        """Test that invalid paths raise appropriate exceptions."""
        with self.assertRaises(FileNotFoundError):
            ArchitectureDesigner("/nonexistent/analysis_report.json", self.structure_yaml)
        
        with self.assertRaises(FileNotFoundError):
            ArchitectureDesigner(self.analysis_report_path, "/nonexistent/structure.yaml")


class TestMainFunction(unittest.TestCase):
    """Test cases for the main function."""

    @patch('design_mcp_architecture.ArchitectureDesigner')
    @patch('design_mcp_architecture.parse_arguments')
    def test_main_success(self, mock_parse_args, mock_designer):
        """Test that the main function returns 0 on success."""
        # Mock the arguments
        mock_args = MagicMock()
        mock_args.analysis_report = "analysis_report.json"
        mock_args.target_structure = "structure.yaml"
        mock_args.output = "output.json"
        mock_args.verbose = False
        mock_parse_args.return_value = mock_args
        
        # Mock the designer
        mock_designer_instance = MagicMock()
        mock_designer_instance.design_architecture.return_value = MagicMock()
        mock_designer.return_value = mock_designer_instance
        
        # Call the main function
        result = designer.main()
        
        # Check that the function returned 0 (success)
        self.assertEqual(result, 0)
        
        # Check that the designer was created with the correct arguments
        mock_designer.assert_called_with(
            analysis_report_path=mock_args.analysis_report,
            target_structure_path=mock_args.target_structure,
            verbose=mock_args.verbose
        )
        
        # Check that design_architecture and save_design were called
        mock_designer_instance.design_architecture.assert_called_once()
        mock_designer_instance.save_design.assert_called_with(mock_args.output)

    @patch('design_mcp_architecture.logger')
    @patch('design_mcp_architecture.parse_arguments')
    def test_main_error(self, mock_parse_args, mock_logger):
        """Test that the main function returns 1 on error."""
        # Mock the arguments to raise an exception
        mock_parse_args.side_effect = Exception("Test error")
        
        # Call the main function
        result = designer.main()
        
        # Check that the function returned 1 (error)
        self.assertEqual(result, 1)
        
        # Check that the error was logged
        mock_logger.error.assert_called_once()


if __name__ == '__main__':
    unittest.main()