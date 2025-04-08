#!/usr/bin/env python3
"""
Unit tests for the MCP Migration Plan Creation Script.

This module contains unit tests for the create_migration_plan.py script.
"""

import os
import sys
import json
import unittest
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path to import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from create_migration_plan import (
    MigrationPlanner, MigrationPlan, Phase, Task, Dependency, Timeline, Risk,
    RiskLevel, TaskStatus, parse_arguments, main
)


class TestMigrationPlanner(unittest.TestCase):
    """Test cases for the MigrationPlanner class."""

    def setUp(self):
        """Set up test fixtures."""
        # Sample architecture design
        self.architecture_design = {
            "components": [
                {"name": "MCPHost", "description": "Host component"},
                {"name": "MCPClient", "description": "Client component"},
                {"name": "MCPServer", "description": "Server component"},
                {"name": "ToolsRegistry", "description": "Tools registry component"},
                {"name": "ResourcesRegistry", "description": "Resources registry component"}
            ]
        }
        
        # Sample analysis report
        self.analysis_report = {
            "components": [
                {"name": "MCPHost", "status": "not_implemented"},
                {"name": "MCPClient", "status": "not_implemented"},
                {"name": "MCPServer", "status": "not_implemented"},
                {"name": "ToolsRegistry", "status": "not_implemented"},
                {"name": "ResourcesRegistry", "status": "not_implemented"}
            ]
        }
        
        # Mock file paths
        self.architecture_design_path = "data/migration/mcp/architecture_design.json"
        self.analysis_report_path = "data/migration/mcp/analysis_report.json"
        self.output_path = "data/migration/mcp/migration_plan.json"

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_initialization(self, mock_file, mock_exists):
        """Test initialization of MigrationPlanner."""
        # Mock file existence
        mock_exists.return_value = True
        
        # Mock file content
        mock_file.return_value.__enter__.return_value.read.return_value = json.dumps(self.architecture_design)
        
        # Create planner
        planner = MigrationPlanner(
            architecture_design_path=self.architecture_design_path,
            analysis_report_path=self.analysis_report_path,
            verbose=True
        )
        
        # Assert attributes
        self.assertEqual(planner.architecture_design_path, self.architecture_design_path)
        self.assertEqual(planner.analysis_report_path, self.analysis_report_path)
        self.assertTrue(planner.verbose)
        self.assertIsInstance(planner.plan, MigrationPlan)
        self.assertEqual(planner.plan.architecture_design_path, self.architecture_design_path)
        self.assertEqual(planner.plan.analysis_report_path, self.analysis_report_path)

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_validate_paths(self, mock_file, mock_exists):
        """Test path validation."""
        # Mock file existence
        mock_exists.return_value = True
        
        # Mock file content
        mock_file.return_value.__enter__.return_value.read.return_value = json.dumps(self.architecture_design)
        
        # Create planner
        planner = MigrationPlanner(
            architecture_design_path=self.architecture_design_path,
            analysis_report_path=self.analysis_report_path
        )
        
        # Assert validation passes
        try:
            planner._validate_paths()
        except Exception as e:
            self.fail(f"_validate_paths() raised {type(e).__name__} unexpectedly!")
        
        # Test validation failure
        mock_exists.return_value = False
        with self.assertRaises(FileNotFoundError):
            planner._validate_paths()

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_architecture_design(self, mock_file, mock_exists):
        """Test loading architecture design."""
        # Mock file existence
        mock_exists.return_value = True
        
        # Mock file content
        mock_file.return_value.__enter__.return_value.read.return_value = json.dumps(self.architecture_design)
        
        # Create planner
        planner = MigrationPlanner(
            architecture_design_path=self.architecture_design_path,
            analysis_report_path=self.analysis_report_path
        )
        
        # Load architecture design
        design = planner._load_architecture_design()
        
        # Assert design is loaded correctly
        self.assertEqual(design, self.architecture_design)
        self.assertEqual(len(design["components"]), 5)

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_analysis_report(self, mock_file, mock_exists):
        """Test loading analysis report."""
        # Mock file existence
        mock_exists.return_value = True
        
        # Mock file content
        mock_file.return_value.__enter__.return_value.read.return_value = json.dumps(self.analysis_report)
        
        # Create planner
        planner = MigrationPlanner(
            architecture_design_path=self.architecture_design_path,
            analysis_report_path=self.analysis_report_path
        )
        
        # Load analysis report
        report = planner._load_analysis_report()
        
        # Assert report is loaded correctly
        self.assertEqual(report, self.analysis_report)
        self.assertEqual(len(report["components"]), 5)

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_define_migration_phases(self, mock_file, mock_exists):
        """Test defining migration phases."""
        # Mock file existence
        mock_exists.return_value = True
        
        # Mock file content for architecture design
        mock_file.return_value.__enter__.return_value.read.side_effect = [
            json.dumps(self.architecture_design),
            json.dumps(self.analysis_report)
        ]
        
        # Create planner
        planner = MigrationPlanner(
            architecture_design_path=self.architecture_design_path,
            analysis_report_path=self.analysis_report_path
        )
        
        # Define migration phases
        planner._define_migration_phases()
        
        # Assert phases are defined correctly
        self.assertEqual(len(planner.phase_registry), 10)
        self.assertIn("phase_sdk_adoption", planner.phase_registry)
        self.assertIn("phase_protocol_conformance", planner.phase_registry)
        self.assertIn("phase_host_implementation", planner.phase_registry)
        self.assertIn("phase_client_implementation", planner.phase_registry)
        self.assertIn("phase_server_implementation", planner.phase_registry)
        self.assertIn("phase_tools_resources", planner.phase_registry)
        self.assertIn("phase_security_model", planner.phase_registry)
        self.assertIn("phase_testing_validation", planner.phase_registry)
        self.assertIn("phase_documentation_training", planner.phase_registry)
        self.assertIn("phase_deployment", planner.phase_registry)
        
        # Assert phase dependencies
        self.assertEqual(planner.phase_registry["phase_protocol_conformance"].dependencies, ["phase_sdk_adoption"])
        self.assertEqual(planner.phase_registry["phase_host_implementation"].dependencies, ["phase_protocol_conformance"])
        self.assertEqual(planner.phase_registry["phase_client_implementation"].dependencies, ["phase_host_implementation"])
        self.assertEqual(planner.phase_registry["phase_server_implementation"].dependencies, ["phase_client_implementation"])
        self.assertEqual(planner.phase_registry["phase_tools_resources"].dependencies, ["phase_server_implementation"])
        self.assertEqual(
            sorted(planner.phase_registry["phase_security_model"].dependencies),
            sorted(["phase_host_implementation", "phase_client_implementation", "phase_server_implementation"])
        )
        self.assertEqual(
            sorted(planner.phase_registry["phase_testing_validation"].dependencies),
            sorted(["phase_tools_resources", "phase_security_model"])
        )
        self.assertEqual(planner.phase_registry["phase_documentation_training"].dependencies, ["phase_testing_validation"])
        self.assertEqual(planner.phase_registry["phase_deployment"].dependencies, ["phase_documentation_training"])

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_plan(self, mock_file, mock_exists):
        """Test saving migration plan."""
        # Mock file existence
        mock_exists.return_value = True
        
        # Mock file content
        mock_file.return_value.__enter__.return_value.read.return_value = json.dumps(self.architecture_design)
        
        # Create planner
        planner = MigrationPlanner(
            architecture_design_path=self.architecture_design_path,
            analysis_report_path=self.analysis_report_path
        )
        
        # Create a simple plan
        planner.plan.phases = [Phase(id="phase1", name="Phase 1", description="Phase 1", order=1)]
        planner.plan.tasks = [Task(
            id="task1",
            name="Task 1",
            description="Task 1",
            phase_id="phase1",
            component_name="Component 1",
            estimated_effort_days=1.0
        )]
        planner.plan.dependencies = [Dependency(
            source_task_id="task1",
            target_task_id="task2",
            type="finish-to-start"
        )]
        planner.plan.timeline = Timeline(
            start_date=datetime.now().date().isoformat(),
            end_date=(datetime.now().date() + timedelta(days=30)).isoformat()
        )
        
        # Save plan
        planner.save_plan(self.output_path)
        
        # Assert file was opened for writing
        mock_file.assert_called_with(self.output_path, 'w')
        
        # Assert json.dump was called
        handle = mock_file()
        handle.write.assert_called()


class TestParseArguments(unittest.TestCase):
    """Test cases for the parse_arguments function."""

    @patch('sys.argv', ['create_migration_plan.py'])
    def test_default_arguments(self):
        """Test parsing default arguments."""
        args = parse_arguments()
        self.assertEqual(args.architecture_design, "data/migration/mcp/architecture_design.json")
        self.assertEqual(args.analysis_report, "data/migration/mcp/analysis_report.json")
        self.assertEqual(args.output, "data/migration/mcp/migration_plan.json")
        self.assertFalse(args.verbose)

    @patch('sys.argv', [
        'create_migration_plan.py',
        '--architecture-design', 'custom_design.json',
        '--analysis-report', 'custom_report.json',
        '--output', 'custom_output.json',
        '--verbose'
    ])
    def test_custom_arguments(self):
        """Test parsing custom arguments."""
        args = parse_arguments()
        self.assertEqual(args.architecture_design, "custom_design.json")
        self.assertEqual(args.analysis_report, "custom_report.json")
        self.assertEqual(args.output, "custom_output.json")
        self.assertTrue(args.verbose)


class TestMain(unittest.TestCase):
    """Test cases for the main function."""

    @patch('create_migration_plan.parse_arguments')
    @patch('create_migration_plan.MigrationPlanner')
    def test_main_success(self, mock_planner_class, mock_parse_arguments):
        """Test main function success case."""
        # Mock arguments
        mock_args = MagicMock()
        mock_args.architecture_design = self.architecture_design_path
        mock_args.analysis_report = self.analysis_report_path
        mock_args.output = self.output_path
        mock_args.verbose = False
        mock_parse_arguments.return_value = mock_args
        
        # Mock planner
        mock_planner = MagicMock()
        mock_plan = MagicMock()
        mock_plan.phases = [MagicMock()]
        mock_plan.tasks = [MagicMock()]
        mock_plan.dependencies = [MagicMock()]
        mock_plan.timeline = MagicMock()
        mock_plan.timeline.start_date = "2025-01-01"
        mock_plan.timeline.end_date = "2025-12-31"
        mock_planner.create_migration_plan.return_value = mock_plan
        mock_planner_class.return_value = mock_planner
        
        # Call main
        result = main()
        
        # Assert success
        self.assertEqual(result, 0)
        mock_planner_class.assert_called_once_with(
            architecture_design_path=mock_args.architecture_design,
            analysis_report_path=mock_args.analysis_report,
            verbose=mock_args.verbose
        )
        mock_planner.create_migration_plan.assert_called_once()
        mock_planner.save_plan.assert_called_once_with(mock_args.output)

    @patch('create_migration_plan.parse_arguments')
    @patch('create_migration_plan.MigrationPlanner')
    def test_main_failure(self, mock_planner_class, mock_parse_arguments):
        """Test main function failure case."""
        # Mock arguments
        mock_args = MagicMock()
        mock_args.architecture_design = self.architecture_design_path
        mock_args.analysis_report = self.analysis_report_path
        mock_args.output = self.output_path
        mock_args.verbose = False
        mock_parse_arguments.return_value = mock_args
        
        # Mock planner to raise exception
        mock_planner_class.side_effect = Exception("Test exception")
        
        # Call main
        result = main()
        
        # Assert failure
        self.assertEqual(result, 1)


if __name__ == '__main__':
    unittest.main()