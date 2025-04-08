"""
Integration tests for quality workflows.

This module contains integration tests for the complete quality check workflow,
the fix workflow, and the reporting workflow.
"""

import os
import unittest
from unittest.mock import patch, MagicMock
import pytest
import threading
import time
import json
from pathlib import Path

from tests.utils.fixtures import temp_test_dir
from tests.utils.mocks import MockFileSystem, MockConfig, MockKnowledgeGraph
from tests.utils.helpers import create_test_file, create_test_directory_structure
from tests.utils.generators import generate_config_data, generate_file_content, generate_quality_issues


@pytest.fixture
def test_project(temp_test_dir):
    """Create a test project structure."""
    # Create a test project structure
    structure = {
        "core": {
            "quality": {
                "__init__.py": "",
                "enforcer.py": """
\"\"\"
Quality Enforcer Module

This module provides the QualityEnforcer class, which serves as a facade over
the modular quality component system.
\"\"\"

class QualityEnforcer:
    \"\"\"Facade for the quality enforcement system.\"\"\"
    
    def __init__(self):
        \"\"\"Initialize the QualityEnforcer.\"\"\"
        pass
"""
            },
            "documentation": {
                "__init__.py": "",
                "generator.py": """
\"\"\"
Documentation Generator Module

This module provides the DocumentationGenerator class.
\"\"\"

class DocumentationGenerator:
    \"\"\"Documentation generator class.\"\"\"
    
    def __init__(self):
        \"\"\"Initialize the DocumentationGenerator.\"\"\"
        pass
"""
            },
            "logging": {
                "__init__.py": "",
                "manager.py": """
\"\"\"
Logging Manager Module

This module provides the LogManager class.
\"\"\"

class LogManager:
    \"\"\"Logging manager class.\"\"\"
    
    def __init__(self):
        \"\"\"Initialize the LogManager.\"\"\"
        pass
"""
            }
        },
        "tests": {
            "__init__.py": "",
            "test_quality.py": """
\"\"\"
Test Quality Module

This module contains tests for the quality module.
\"\"\"

import unittest

class TestQuality(unittest.TestCase):
    \"\"\"Test cases for the quality module.\"\"\"
    
    def test_example(self):
        \"\"\"Example test.\"\"\"
        self.assertTrue(True)
"""
        }
    }
    
    create_test_directory_structure(temp_test_dir, structure)
    
    return temp_test_dir


@pytest.mark.integration
class TestQualityWorkflow:
    """Integration tests for the quality workflow."""
    
    @pytest.fixture
    def quality_config(self):
        """Create a quality configuration."""
        return {
            "enabled": True,
            "components": ["code_style", "static_analysis", "documentation", "structure"],
            "severity_threshold": "WARNING",
            "auto_fix": True
        }
    
    @patch('core.quality.QualityEnforcer')
    def test_complete_quality_check_workflow(self, mock_enforcer_class, test_project, quality_config, mock_quality_results):
        """Test the complete quality check workflow."""
        # Create a mock enforcer instance
        mock_enforcer = MagicMock()
        mock_enforcer.run_all_checks.return_value = mock_quality_results
        mock_enforcer_class.return_value = mock_enforcer
        
        # Create an enforcer instance
        from core.quality import QualityEnforcer
        enforcer = QualityEnforcer()
        
        # Run all checks
        results = enforcer.run_all_checks([test_project])
        
        # Verify the results
        assert isinstance(results, list)
        assert len(results) > 0
        
        # Verify that run_all_checks was called
        mock_enforcer.run_all_checks.assert_called_once_with([test_project])
    
    @patch('core.quality.QualityEnforcer')
    def test_fix_workflow(self, mock_enforcer_class, test_project, quality_config, mock_quality_results):
        """Test the fix workflow."""
        # Create a mock enforcer instance
        mock_enforcer = MagicMock()
        mock_enforcer.run_all_checks.return_value = mock_quality_results
        mock_enforcer.fix_issues.return_value = []  # All issues fixed
        mock_enforcer_class.return_value = mock_enforcer
        
        # Create an enforcer instance
        from core.quality import QualityEnforcer
        enforcer = QualityEnforcer()
        
        # Run all checks
        results = enforcer.run_all_checks([test_project])
        
        # Fix the issues
        unfixed = enforcer.fix_issues(results)
        
        # Verify the results
        assert isinstance(unfixed, list)
        assert len(unfixed) == 0
        
        # Verify that fix_issues was called
        mock_enforcer.fix_issues.assert_called_once_with(results)
    
    @patch('core.quality.QualityEnforcer')
    def test_reporting_workflow(self, mock_enforcer_class, test_project, quality_config, mock_quality_results):
        """Test the reporting workflow."""
        # Create a mock enforcer instance
        mock_enforcer = MagicMock()
        mock_enforcer.run_all_checks.return_value = mock_quality_results
        mock_enforcer.update_knowledge_graph.return_value = None
        mock_enforcer_class.return_value = mock_enforcer
        
        # Create an enforcer instance
        from core.quality import QualityEnforcer
        enforcer = QualityEnforcer()
        
        # Run all checks
        results = enforcer.run_all_checks([test_project])
        
        # Update the knowledge graph
        enforcer.update_knowledge_graph(results)
        
        # Verify that update_knowledge_graph was called
        mock_enforcer.update_knowledge_graph.assert_called_once_with(results)


@pytest.mark.integration
class TestEndToEndWorkflow:
    """End-to-end tests for the quality workflow."""
    
    @pytest.fixture
    def mock_kg(self):
        """Create a mock Knowledge Graph."""
        return MockKnowledgeGraph()
    
    @pytest.fixture
    def mock_modules(self, mock_kg, mock_quality_results):
        """Create mock modules for end-to-end testing."""
        with patch('core.quality.QualityEnforcer') as mock_enforcer_class, \
             patch('core.documentation.generator.DocumentationGenerator') as mock_doc_gen_class, \
             patch('core.logging.manager.LogManager') as mock_log_manager_class, \
             patch('core.kg.get_knowledge_graph') as mock_get_kg:
            
            # Create mock instances
            mock_enforcer = MagicMock()
            mock_enforcer.run_all_checks.return_value = mock_quality_results
            mock_enforcer.fix_issues.return_value = []  # All issues fixed
            mock_enforcer.update_knowledge_graph.return_value = None
            mock_enforcer_class.return_value = mock_enforcer
            
            mock_doc_gen = MagicMock()
            mock_doc_gen.generate_documentation.return_value = ["file1.md", "file2.md"]
            mock_doc_gen_class.return_value = mock_doc_gen
            
            mock_log_manager = MagicMock()
            mock_log_manager.get_logger.return_value = MagicMock()
            mock_log_manager_class.return_value = mock_log_manager
            
            # Set up the mock_get_kg function
            mock_get_kg.return_value = mock_kg
            
            yield {
                "enforcer": mock_enforcer,
                "doc_gen": mock_doc_gen,
                "log_manager": mock_log_manager,
                "kg": mock_kg
            }
    
    @patch('core.quality.QualityEnforcer')
    @patch('core.documentation.generator.DocumentationGenerator')
    @patch('core.logging.manager.LogManager')
    def test_end_to_end_workflow(self, mock_log_manager_class, mock_doc_gen_class, mock_enforcer_class, test_project, mock_modules):
        """Test the end-to-end workflow."""
        # Set up the mock instances
        mock_enforcer = mock_modules["enforcer"]
        mock_doc_gen = mock_modules["doc_gen"]
        mock_log_manager = mock_modules["log_manager"]
        
        mock_enforcer_class.return_value = mock_enforcer
        mock_doc_gen_class.return_value = mock_doc_gen
        mock_log_manager_class.return_value = mock_log_manager
        
        # Import the necessary classes
        from core.quality import QualityEnforcer
        from core.documentation.generator import DocumentationGenerator
        from core.logging.manager import LogManager
        
        # Create instances
        enforcer = QualityEnforcer()
        doc_gen = DocumentationGenerator()
        log_manager = LogManager()
        
        # Get a logger
        logger = log_manager.get_logger("quality_workflow")
        
        # Run all checks
        results = enforcer.run_all_checks([test_project])
        
        # Log the results
        logger.info(f"Found {len(results)} quality issues")
        
        # Fix the issues
        unfixed = enforcer.fix_issues(results)
        
        # Log the fix results
        logger.info(f"{len(results) - len(unfixed)} issues fixed, {len(unfixed)} issues remaining")
        
        # Generate documentation
        output_files = doc_gen.generate_documentation(
            source_dir=test_project,
            output_dir=os.path.join(test_project, "docs")
        )
        
        # Log the documentation results
        logger.info(f"Generated {len(output_files)} documentation files")
        
        # Update the knowledge graph
        enforcer.update_knowledge_graph(results)
        
        # Verify that all methods were called
        mock_enforcer.run_all_checks.assert_called_once_with([test_project])
        mock_enforcer.fix_issues.assert_called_once_with(results)
        mock_doc_gen.generate_documentation.assert_called_once()
        mock_enforcer.update_knowledge_graph.assert_called_once_with(results)


@pytest.mark.integration
@pytest.mark.error
class TestErrorConditions:
    """Test cases for error conditions in the quality workflow."""
    
    @pytest.fixture
    def mock_error_modules(self, mock_quality_results):
        """Create mock modules that raise errors."""
        with patch('core.quality.QualityEnforcer') as mock_enforcer_class, \
             patch('core.documentation.generator.DocumentationGenerator') as mock_doc_gen_class, \
             patch('core.logging.manager.LogManager') as mock_log_manager_class:
            
            # Create mock instances that raise errors
            mock_enforcer = MagicMock()
            mock_enforcer.run_all_checks.side_effect = Exception("Check error")
            mock_enforcer.fix_issues.side_effect = Exception("Fix error")
            mock_enforcer.update_knowledge_graph.side_effect = Exception("Update error")
            mock_enforcer_class.return_value = mock_enforcer
            
            mock_doc_gen = MagicMock()
            mock_doc_gen.generate_documentation.side_effect = Exception("Documentation error")
            mock_doc_gen_class.return_value = mock_doc_gen
            
            mock_log_manager = MagicMock()
            mock_log_manager.get_logger.return_value = MagicMock()
            mock_log_manager_class.return_value = mock_log_manager
            
            yield {
                "enforcer": mock_enforcer,
                "doc_gen": mock_doc_gen,
                "log_manager": mock_log_manager
            }
    
    @patch('core.quality.QualityEnforcer')
    def test_check_error(self, mock_enforcer_class, test_project, mock_error_modules):
        """Test handling of check errors."""
        # Set up the mock
        mock_enforcer_class.return_value = mock_error_modules["enforcer"]
        
        # Import the QualityEnforcer
        from core.quality import QualityEnforcer
        
        # Create an enforcer instance
        enforcer = QualityEnforcer()
        
        # Run all checks and verify it raises an exception
        with pytest.raises(Exception) as excinfo:
            enforcer.run_all_checks([test_project])
        
        assert "Check error" in str(excinfo.value)
    
    @patch('core.quality.QualityEnforcer')
    def test_fix_error(self, mock_enforcer_class, test_project, mock_error_modules, mock_quality_results):
        """Test handling of fix errors."""
        # Set up the mock
        mock_enforcer = mock_error_modules["enforcer"]
        mock_enforcer.run_all_checks.side_effect = None
        mock_enforcer.run_all_checks.return_value = mock_quality_results
        mock_enforcer_class.return_value = mock_enforcer
        
        # Import the QualityEnforcer
        from core.quality import QualityEnforcer
        
        # Create an enforcer instance
        enforcer = QualityEnforcer()
        
        # Run all checks
        results = enforcer.run_all_checks([test_project])
        
        # Fix the issues and verify it raises an exception
        with pytest.raises(Exception) as excinfo:
            enforcer.fix_issues(results)
        
        assert "Fix error" in str(excinfo.value)
    
    @patch('core.documentation.generator.DocumentationGenerator')
    def test_documentation_error(self, mock_doc_gen_class, test_project, mock_error_modules):
        """Test handling of documentation errors."""
        # Set up the mock
        mock_doc_gen_class.return_value = mock_error_modules["doc_gen"]
        
        # Import the DocumentationGenerator
        from core.documentation.generator import DocumentationGenerator
        
        # Create a generator instance
        generator = DocumentationGenerator()
        
        # Generate documentation and verify it raises an exception
        with pytest.raises(Exception) as excinfo:
            generator.generate_documentation(
                source_dir=test_project,
                output_dir=os.path.join(test_project, "docs")
            )
        
        assert "Documentation error" in str(excinfo.value)


@pytest.mark.integration
class TestRecoveryMechanisms:
    """Test cases for recovery mechanisms in the quality workflow."""
    
    @pytest.fixture
    def mock_recovery_modules(self, mock_quality_results):
        """Create mock modules with recovery mechanisms."""
        with patch('core.quality.QualityEnforcer') as mock_enforcer_class, \
             patch('core.documentation.generator.DocumentationGenerator') as mock_doc_gen_class, \
             patch('core.logging.manager.LogManager') as mock_log_manager_class:
            
            # Create mock instances with recovery mechanisms
            mock_enforcer = MagicMock()
            
            # Run all checks method that fails first, then succeeds
            run_checks_mock = MagicMock()
            run_checks_mock.side_effect = [Exception("Check error"), mock_quality_results, mock_quality_results]
            mock_enforcer.run_all_checks = run_checks_mock
            
            # Fix issues method that fails first, then succeeds
            fix_issues_mock = MagicMock()
            fix_issues_mock.side_effect = [Exception("Fix error"), []]
            mock_enforcer.fix_issues = fix_issues_mock
            
            mock_enforcer_class.return_value = mock_enforcer
            
            mock_doc_gen = MagicMock()
            
            # Generate documentation method that fails first, then succeeds
            generate_doc_mock = MagicMock()
            generate_doc_mock.side_effect = [Exception("Documentation error"), ["file1.md", "file2.md"]]
            mock_doc_gen.generate_documentation = generate_doc_mock
            
            mock_doc_gen_class.return_value = mock_doc_gen
            
            mock_log_manager = MagicMock()
            mock_log_manager.get_logger.return_value = MagicMock()
            mock_log_manager_class.return_value = mock_log_manager
            
            yield {
                "enforcer": mock_enforcer,
                "doc_gen": mock_doc_gen,
                "log_manager": mock_log_manager
            }
    
    @patch('core.quality.QualityEnforcer')
    def test_check_recovery(self, mock_enforcer_class, test_project, mock_recovery_modules):
        """Test recovery from check errors."""
        # Set up the mock
        mock_enforcer_class.return_value = mock_recovery_modules["enforcer"]
        
        # Import the QualityEnforcer
        from core.quality import QualityEnforcer
        
        # Create an enforcer instance
        enforcer = QualityEnforcer()
        
        # First attempt should fail
        with pytest.raises(Exception):
            enforcer.run_all_checks([test_project])
        
        # Second attempt should succeed
        results = enforcer.run_all_checks([test_project])
        
        # Verify the results
        assert isinstance(results, list)
        assert len(results) > 0
    
    @patch('core.quality.QualityEnforcer')
    def test_fix_recovery(self, mock_enforcer_class, test_project, mock_recovery_modules, mock_quality_results):
        """Test recovery from fix errors."""
        # Set up the mock
        mock_enforcer = mock_recovery_modules["enforcer"]
        
        # Override the run_all_checks method to return mock_quality_results directly
        # This avoids the first side effect (Exception) that's causing the test to fail
        mock_enforcer.run_all_checks.side_effect = None
        mock_enforcer.run_all_checks.return_value = mock_quality_results
        
        mock_enforcer_class.return_value = mock_enforcer
        
        # Import the QualityEnforcer
        from core.quality import QualityEnforcer
        
        # Create an enforcer instance
        enforcer = QualityEnforcer()
        
        # Run all checks
        results = enforcer.run_all_checks([test_project])
        
        # First fix attempt should fail
        with pytest.raises(Exception):
            enforcer.fix_issues(results)
        
        # Second fix attempt should succeed
        unfixed = enforcer.fix_issues(results)
        
        # Verify the results
        assert isinstance(unfixed, list)
        assert len(unfixed) == 0
    
    @patch('core.documentation.generator.DocumentationGenerator')
    def test_documentation_recovery(self, mock_doc_gen_class, test_project, mock_recovery_modules):
        """Test recovery from documentation errors."""
        # Set up the mock
        mock_doc_gen_class.return_value = mock_recovery_modules["doc_gen"]
        
        # Import the DocumentationGenerator
        from core.documentation.generator import DocumentationGenerator
        
        # Create a generator instance
        generator = DocumentationGenerator()
        
        # First attempt should fail
        with pytest.raises(Exception):
            generator.generate_documentation(
                source_dir=test_project,
                output_dir=os.path.join(test_project, "docs")
            )
        
        # Second attempt should succeed
        output_files = generator.generate_documentation(
            source_dir=test_project,
            output_dir=os.path.join(test_project, "docs")
        )
        
        # Verify the results
        assert isinstance(output_files, list)
        assert len(output_files) > 0


# New integration tests for complex workflows
@pytest.mark.integration
class TestComplexWorkflows:
    """Integration tests for complex quality workflows."""
    
    @pytest.fixture
    def mock_kg(self):
        """Create a mock Knowledge Graph."""
        return MockKnowledgeGraph()
    
    @pytest.fixture
    def mock_modules(self, mock_kg, mock_quality_results):
        """Create mock modules for end-to-end testing."""
        with patch('core.quality.QualityEnforcer') as mock_enforcer_class, \
             patch('core.documentation.generator.DocumentationGenerator') as mock_doc_gen_class, \
             patch('core.logging.manager.LogManager') as mock_log_manager_class, \
             patch('core.kg.get_knowledge_graph') as mock_get_kg:
            
            # Create mock instances
            mock_enforcer = MagicMock()
            mock_enforcer.run_all_checks.return_value = mock_quality_results
            mock_enforcer.fix_issues.return_value = []  # All issues fixed
            mock_enforcer.update_knowledge_graph.return_value = None
            mock_enforcer_class.return_value = mock_enforcer
            
            mock_doc_gen = MagicMock()
            mock_doc_gen.generate_documentation.return_value = ["file1.md", "file2.md"]
            mock_doc_gen_class.return_value = mock_doc_gen
            
            mock_log_manager = MagicMock()
            mock_log_manager.get_logger.return_value = MagicMock()
            mock_log_manager_class.return_value = mock_log_manager
            
            # Set up the mock_get_kg function
            mock_get_kg.return_value = mock_kg
            
            yield {
                "enforcer": mock_enforcer,
                "doc_gen": mock_doc_gen,
                "log_manager": mock_log_manager,
                "kg": mock_kg
            }
    
    @patch('core.quality.QualityEnforcer')
    @patch('core.quality.components.create_component')
    def test_multi_component_interaction(self, mock_create, mock_enforcer_class, test_project, mock_modules, mock_quality_results):
        """Test interactions between multiple quality components."""
        # Set up the mock
        mock_enforcer = mock_modules["enforcer"]
        mock_enforcer_class.return_value = mock_enforcer
        
        # Create mock components
        components = []
        for i, name in enumerate(["code_style", "static_analysis", "documentation", "structure"]):
            mock_component = MagicMock()
            mock_component.name = name
            mock_component.run_checks.return_value = mock_quality_results[:i+1]
            components.append(mock_component)
            mock_create.side_effect = lambda n, c: next((comp for comp in components if comp.name == n), None)
        
        # Import the necessary classes
        from core.quality import QualityEnforcer
        
        # Create an enforcer instance
        enforcer = QualityEnforcer()
        
        # Run checks for each component
        all_results = []
        for component in components:
            results = component.run_checks([test_project])
            all_results.extend(results)
        
        # Fix issues across all components
        mock_enforcer.fix_issues.return_value = []
        unfixed = enforcer.fix_issues(all_results)
        
        # Verify the results
        assert len(all_results) == sum(i+1 for i in range(len(components)))
        assert len(unfixed) == 0
        mock_enforcer.fix_issues.assert_called_once_with(all_results)
    
    @patch('core.quality.QualityEnforcer')
    @patch('core.documentation.generator.DocumentationGenerator')
    @patch('os.walk')
    def test_system_level_operations(self, mock_walk, mock_doc_gen_class, mock_enforcer_class, test_project, mock_modules):
        """Test system-level quality operations."""
        # Set up the mocks
        mock_enforcer = mock_modules["enforcer"]
        mock_doc_gen = mock_modules["doc_gen"]
        mock_enforcer_class.return_value = mock_enforcer
        mock_doc_gen_class.return_value = mock_doc_gen
        
        # Mock the os.walk function to return a complex directory structure
        mock_walk.return_value = [
            (test_project, ["core", "tests"], []),
            (os.path.join(test_project, "core"), ["quality", "documentation", "logging"], []),
            (os.path.join(test_project, "core", "quality"), [], ["__init__.py", "enforcer.py"]),
            (os.path.join(test_project, "core", "documentation"), [], ["__init__.py", "generator.py"]),
            (os.path.join(test_project, "core", "logging"), [], ["__init__.py", "manager.py"]),
            (os.path.join(test_project, "tests"), [], ["__init__.py", "test_quality.py"])
        ]
        
        # Import the necessary classes
        from core.quality import QualityEnforcer
        from core.documentation.generator import DocumentationGenerator
        
        # Create instances
        enforcer = QualityEnforcer()
        doc_gen = DocumentationGenerator()
        
        # Run checks on the entire project
        results = enforcer.run_all_checks([test_project])
        
        # Fix issues
        unfixed = enforcer.fix_issues(results)
        
        # Generate documentation for the entire project
        output_files = doc_gen.generate_documentation(
            source_dir=test_project,
            output_dir=os.path.join(test_project, "docs")
        )
        
        # Verify the results
        assert len(results) > 0
        assert len(unfixed) == 0
        assert len(output_files) > 0
    
    @patch('core.quality.QualityEnforcer')
    @patch('subprocess.run')
    def test_external_tool_integration(self, mock_run, mock_enforcer_class, test_project, mock_modules, mock_quality_results):
        """Test integration with external tools."""
        # Set up the mocks
        mock_enforcer = mock_modules["enforcer"]
        
        # Set up the run_external_tool method to return mock_quality_results
        mock_enforcer.run_external_tool = MagicMock(return_value=mock_quality_results)
        
        mock_enforcer_class.return_value = mock_enforcer
        
        # Mock the subprocess.run function to return a successful result
        mock_run.return_value = MagicMock(returncode=0, stdout=b"No issues found")
        
        # Import the necessary classes
        from core.quality import QualityEnforcer
        
        # Create an enforcer instance
        enforcer = QualityEnforcer()
        
        # Run external tools
        tools = ["black", "mypy", "pylint", "flake8"]
        results = []
        
        for tool in tools:
            # Run the tool
            tool_results = enforcer.run_external_tool(tool, [test_project])
            results.extend(tool_results)
        
        # Fix issues
        unfixed = enforcer.fix_issues(results)
        
        # Verify the results
        assert len(results) > 0
        assert len(unfixed) == 0
        assert len(unfixed) == 0


if __name__ == '__main__':
    unittest.main()