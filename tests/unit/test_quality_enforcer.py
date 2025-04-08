"""
Unit tests for the QualityEnforcer class.
"""

import unittest
from unittest.mock import patch, MagicMock, call

from core.quality import QualityEnforcer, QualityCheckResult, QualityCheckSeverity


class TestQualityEnforcer(unittest.TestCase):
    """Test cases for the QualityEnforcer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a fresh QualityEnforcer instance for each test
        self.enforcer = QualityEnforcer()
    
    def test_initialization(self):
        """Test that the QualityEnforcer initializes correctly."""
        # Check that components are initialized
        components = self.enforcer.get_all_components()
        self.assertIn("code_style", components)
        self.assertIn("static_analysis", components)
        self.assertIn("documentation", components)
        self.assertIn("structure", components)
    
    def test_get_component(self):
        """Test getting a component by name."""
        # Get an existing component
        component = self.enforcer.get_component("code_style")
        self.assertIsNotNone(component)
        self.assertEqual(component.name, "Code Style")
        
        # Get a non-existent component
        component = self.enforcer.get_component("non_existent")
        self.assertIsNone(component)
    
    @patch("core.quality.components.code_style.CodeStyleComponent.run_checks")
    def test_run_component_checks(self, mock_run_checks):
        """Test running checks for a specific component."""
        # Mock the component's run_checks method
        mock_result = QualityCheckResult(
            check_id="test_check",
            severity=QualityCheckSeverity.WARNING,
            message="Test message",
            file_path="test_file.py"
        )
        mock_run_checks.return_value = [mock_result]
        
        # Run checks for the code_style component
        results = self.enforcer.run_component_checks("code_style", ["test_file.py"])
        
        # Verify that the component's run_checks method was called
        mock_run_checks.assert_called_once_with(["test_file.py"])
        
        # Verify the results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].check_id, "test_check")
        self.assertEqual(results[0].message, "Test message")
    
    @patch("core.quality.components.code_style.CodeStyleComponent.run_checks")
    @patch("core.quality.components.static_analysis.StaticAnalysisComponent.run_checks")
    @patch("core.quality.components.documentation.DocumentationComponent.run_checks")
    @patch("core.quality.components.structure.StructureComponent.run_checks")
    def test_run_all_checks(self, mock_structure, mock_documentation, mock_static_analysis, mock_code_style):
        """Test running all checks."""
        # Mock each component's run_checks method
        mock_code_style.return_value = [
            QualityCheckResult(
                check_id="black",
                severity=QualityCheckSeverity.WARNING,
                message="Black formatting issue",
                file_path="test_file.py"
            )
        ]
        mock_static_analysis.return_value = [
            QualityCheckResult(
                check_id="mypy",
                severity=QualityCheckSeverity.ERROR,
                message="Type error",
                file_path="test_file.py",
                line_number=10
            )
        ]
        mock_documentation.return_value = [
            QualityCheckResult(
                check_id="docstrings",
                severity=QualityCheckSeverity.INFO,
                message="Missing docstring",
                file_path="test_file.py",
                line_number=5
            )
        ]
        mock_structure.return_value = [
            QualityCheckResult(
                check_id="directory_structure",
                severity=QualityCheckSeverity.WARNING,
                message="Missing directory",
                file_path="."
            )
        ]
        
        # Run all checks
        results = self.enforcer.run_all_checks(["test_file.py"])
        
        # Verify that each component's run_checks method was called
        mock_code_style.assert_called_once_with(["test_file.py"])
        mock_static_analysis.assert_called_once_with(["test_file.py"])
        mock_documentation.assert_called_once_with(["test_file.py"])
        mock_structure.assert_called_once_with(["test_file.py"])
        
        # Verify the results
        self.assertEqual(len(results), 4)
        check_ids = [result.check_id for result in results]
        self.assertIn("black", check_ids)
        self.assertIn("mypy", check_ids)
        self.assertIn("docstrings", check_ids)
        self.assertIn("directory_structure", check_ids)
    
    def test_fix_issues_direct(self):
        """Test fixing issues directly."""
        # Create a test instance with a mock component
        enforcer = QualityEnforcer()
        
        # Create a mock code_style component
        mock_component = MagicMock()
        mock_component.fix_issues.return_value = []  # All issues fixed
        enforcer._components["code_style"] = mock_component
        
        # Create a mock _get_component_for_check method
        original_method = enforcer._get_component_for_check
        enforcer._get_component_for_check = lambda check_id: "code_style" if check_id == "black" else "static_analysis"
        
        # Create some results to fix
        results = [
            QualityCheckResult(
                check_id="black",
                severity=QualityCheckSeverity.WARNING,
                message="Black formatting issue",
                file_path="test_file.py",
                fix_available=True
            ),
            QualityCheckResult(
                check_id="mypy",
                severity=QualityCheckSeverity.ERROR,
                message="Type error",
                file_path="test_file.py",
                line_number=10
            )
        ]
        
        # Fix the issues
        unfixed = enforcer.fix_issues(results, verify=False)
        
        # Restore the original method
        enforcer._get_component_for_check = original_method
        
        # Verify that only the mypy result is unfixed (since it doesn't have a fix method)
        self.assertEqual(len(unfixed), 1)
        self.assertEqual(unfixed[0].check_id, "mypy")
    
    def test_backward_compatibility_methods(self):
        """Test backward compatibility methods."""
        # Create a mock for run_component_checks
        with patch.object(self.enforcer, 'run_component_checks') as mock_run_component_checks:
            # Mock the return value for code_style checks
            mock_run_component_checks.return_value = [
                QualityCheckResult(
                    check_id="black",
                    severity=QualityCheckSeverity.WARNING,
                    message="Black formatting issue",
                    file_path="test_file.py"
                )
            ]
            
            # Test check_code_quality
            result = self.enforcer.check_code_quality(["test_file.py"])
            self.assertIn("style", result)
            self.assertEqual(len(result["style"]), 1)
            
            # Test check_documentation_quality
            mock_run_component_checks.return_value = [
                QualityCheckResult(
                    check_id="docstrings",
                    severity=QualityCheckSeverity.INFO,
                    message="Missing docstring",
                    file_path="test_file.py",
                    line_number=5
                )
            ]
            result = self.enforcer.check_documentation_quality(["test_file.py"])
            self.assertIn("docstrings", result)
            self.assertEqual(len(result["docstrings"]), 1)
            
            # Test validate_file_structure
            mock_run_component_checks.return_value = [
                QualityCheckResult(
                    check_id="directory_structure",
                    severity=QualityCheckSeverity.WARNING,
                    message="Missing directory",
                    file_path="."
                )
            ]
            result = self.enforcer.validate_file_structure(["test_file.py"])
            self.assertIn("directory_structure", result)
            self.assertEqual(len(result["directory_structure"]), 1)


if __name__ == '__main__':
    unittest.main()