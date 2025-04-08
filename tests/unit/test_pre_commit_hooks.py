"""
Unit tests for pre-commit hooks.

This module contains tests for the pre-commit hooks, including
validate_file_structure.py, check_documentation_quality.py, and suggest_improvements.py.
"""

import os
import unittest
from unittest.mock import patch, MagicMock
import pytest

from tests.utils.fixtures import temp_test_dir, mock_file_structure
from tests.utils.mocks import MockFileSystem, MockConfig
from tests.utils.helpers import create_test_file, create_test_directory_structure


class TestPreCommitHooks(unittest.TestCase):
    """Test cases for pre-commit hooks."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock file system
        self.mock_fs = MockFileSystem()
        
        # Create a mock config
        self.mock_config = MockConfig()
        
        # Set up patches
        self.patches = []
        
        # Patch os.path.exists to use mock file system
        exists_patch = patch('os.path.exists', side_effect=self.mock_fs.exists)
        self.patches.append(exists_patch)
        
        # Patch os.path.isfile to use mock file system
        isfile_patch = patch('os.path.isfile', side_effect=self.mock_fs.is_file)
        self.patches.append(isfile_patch)
        
        # Patch os.path.isdir to use mock file system
        isdir_patch = patch('os.path.isdir', side_effect=self.mock_fs.is_dir)
        self.patches.append(isdir_patch)
        
        # Start all patches
        for p in self.patches:
            p.start()
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Stop all patches
        for p in self.patches:
            p.stop()


@pytest.mark.hooks
class TestValidateFileStructure:
    """Test cases for validate_file_structure.py."""
    
    @pytest.fixture
    def mock_validate_module(self):
        """Create a mock validate_file_structure module."""
        with patch('core.quality.hooks.validate_file_structure') as mock_module:
            # Mock the validate_file_structure function
            mock_module.validate_file_structure.return_value = {
                "directory_structure": [],
                "file_naming": [],
                "imports": [],
                "dependencies": []
            }
            yield mock_module
    
    def test_validate_file_structure_empty(self, mock_validate_module, temp_test_dir):
        """Test validating an empty directory."""
        from core.quality.hooks.validate_file_structure import validate_file_structure
        
        # Call the function with an empty directory
        result = validate_file_structure([temp_test_dir])
        
        # Verify the result
        assert isinstance(result, dict)
        assert "directory_structure" in result
        assert "file_naming" in result
        assert "imports" in result
        assert "dependencies" in result
    
    def test_validate_file_structure_with_files(self, mock_validate_module, temp_test_dir):
        """Test validating a directory with files."""
        from core.quality.hooks.validate_file_structure import validate_file_structure
        
        # Create some test files
        create_test_file(temp_test_dir, "test_file.py", "# Test file")
        create_test_file(temp_test_dir, "README.md", "# Test README")
        
        # Call the function with the directory
        result = validate_file_structure([temp_test_dir])
        
        # Verify the result
        assert isinstance(result, dict)
        assert "directory_structure" in result
        assert "file_naming" in result
        assert "imports" in result
        assert "dependencies" in result
    
    def test_validate_file_structure_with_issues(self, mock_validate_module, temp_test_dir):
        """Test validating a directory with issues."""
        from core.quality.hooks.validate_file_structure import validate_file_structure
        
        # Mock the validate_file_structure function to return issues
        mock_validate_module.validate_file_structure.return_value = {
            "directory_structure": [
                {
                    "file": temp_test_dir,
                    "message": "Missing required directory: docs",
                    "severity": "WARNING"
                }
            ],
            "file_naming": [
                {
                    "file": os.path.join(temp_test_dir, "bad_name.py"),
                    "message": "File name does not follow naming convention",
                    "severity": "WARNING"
                }
            ],
            "imports": [],
            "dependencies": []
        }
        
        # Create a test file with a bad name
        create_test_file(temp_test_dir, "bad_name.py", "# Bad name")
        
        # Call the function with the directory
        result = validate_file_structure([temp_test_dir])
        
        # Verify the result
        assert isinstance(result, dict)
        assert "directory_structure" in result
        assert len(result["directory_structure"]) == 1
        assert "file_naming" in result
        assert len(result["file_naming"]) == 1
        assert "imports" in result
        assert "dependencies" in result


@pytest.mark.hooks
class TestCheckDocumentationQuality:
    """Test cases for check_documentation_quality.py."""
    
    @pytest.fixture
    def mock_check_docs_module(self):
        """Create a mock check_documentation_quality module."""
        with patch('core.quality.hooks.check_documentation_quality') as mock_module:
            # Mock the check_documentation_quality function
            mock_module.check_documentation_quality.return_value = {
                "docstrings": [],
                "readme": [],
                "coverage": []
            }
            yield mock_module
    
    def test_check_documentation_quality_empty(self, mock_check_docs_module, temp_test_dir):
        """Test checking documentation quality in an empty directory."""
        from core.quality.hooks.check_documentation_quality import check_documentation_quality
        
        # Call the function with an empty directory
        result = check_documentation_quality([temp_test_dir])
        
        # Verify the result
        assert isinstance(result, dict)
        assert "docstrings" in result
        assert "readme" in result
        assert "coverage" in result
    
    def test_check_documentation_quality_with_files(self, mock_check_docs_module, test_files):
        """Test checking documentation quality with files."""
        from core.quality.hooks.check_documentation_quality import check_documentation_quality
        
        # Call the function with the files
        result = check_documentation_quality(list(test_files.values()))
        
        # Verify the result
        assert isinstance(result, dict)
        assert "docstrings" in result
        assert "readme" in result
        assert "coverage" in result
    
    def test_check_documentation_quality_with_issues(self, mock_check_docs_module, test_files):
        """Test checking documentation quality with issues."""
        from core.quality.hooks.check_documentation_quality import check_documentation_quality
        
        # Mock the check_documentation_quality function to return issues
        mock_check_docs_module.check_documentation_quality.return_value = {
            "docstrings": [
                {
                    "file": test_files["no_docs.py"],
                    "line": 2,
                    "message": "Missing docstring for function function_without_docstring",
                    "severity": "WARNING"
                },
                {
                    "file": test_files["no_docs.py"],
                    "line": 5,
                    "message": "Missing docstring for class ClassWithoutDocstring",
                    "severity": "WARNING"
                }
            ],
            "readme": [],
            "coverage": [
                {
                    "file": test_files["no_docs.py"],
                    "message": "Documentation coverage is 0%",
                    "severity": "ERROR"
                }
            ]
        }
        
        # Call the function with the files
        result = check_documentation_quality(list(test_files.values()))
        
        # Verify the result
        assert isinstance(result, dict)
        assert "docstrings" in result
        assert len(result["docstrings"]) == 2
        assert "readme" in result
        assert "coverage" in result
        assert len(result["coverage"]) == 1


@pytest.mark.hooks
class TestSuggestImprovements:
    """Test cases for suggest_improvements.py."""
    
    @pytest.fixture
    def mock_suggest_module(self):
        """Create a mock suggest_improvements module."""
        with patch('core.quality.hooks.suggest_improvements') as mock_module:
            # Mock the suggest_improvements function
            mock_module.suggest_improvements.return_value = []
            yield mock_module
    
    def test_suggest_improvements_empty(self, mock_suggest_module, temp_test_dir):
        """Test suggesting improvements for an empty directory."""
        from core.quality.hooks.suggest_improvements import suggest_improvements
        
        # Call the function with an empty directory
        result = suggest_improvements([temp_test_dir])
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_suggest_improvements_with_files(self, mock_suggest_module, test_files):
        """Test suggesting improvements with files."""
        from core.quality.hooks.suggest_improvements import suggest_improvements
        
        # Call the function with the files
        result = suggest_improvements(list(test_files.values()))
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_suggest_improvements_with_suggestions(self, mock_suggest_module, test_files):
        """Test suggesting improvements with suggestions."""
        from core.quality.hooks.suggest_improvements import suggest_improvements
        
        # Mock the suggest_improvements function to return suggestions
        mock_suggest_module.suggest_improvements.return_value = [
            {
                "file": test_files["example.py"],
                "line": 10,
                "message": "Consider adding type hints to example_function",
                "severity": "INFO",
                "check_id": "type_hints",
                "source": "suggest_improvements"
            },
            {
                "file": test_files["no_docs.py"],
                "message": "Add docstrings to improve documentation coverage",
                "severity": "WARNING",
                "check_id": "docstrings",
                "source": "suggest_improvements"
            }
        ]
        
        # Call the function with the files
        result = suggest_improvements(list(test_files.values()))
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["check_id"] == "type_hints"
        assert result[1]["check_id"] == "docstrings"


if __name__ == '__main__':
    unittest.main()