"""
Pytest configuration file.

This file contains pytest fixtures and configuration that are available
to all test modules.
"""

import os
import sys
import pytest
from typing import Dict, List, Optional, Any, Generator

# Import fixtures from utils
from tests.utils.fixtures import (
    temp_test_dir,
    temp_test_file,
    mock_quality_results,
    mock_file_structure,
    mock_kg_schema
)

# Add markers for different test categories
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: mark a test as a unit test")
    config.addinivalue_line("markers", "integration: mark a test as an integration test")
    config.addinivalue_line("markers", "quality: mark a test as a quality test")
    config.addinivalue_line("markers", "documentation: mark a test as a documentation test")
    config.addinivalue_line("markers", "logging: mark a test as a logging test")
    config.addinivalue_line("markers", "kg: mark a test as a knowledge graph test")
    config.addinivalue_line("markers", "hooks: mark a test as a hooks test")
    config.addinivalue_line("markers", "slow: mark a test as slow running")
    config.addinivalue_line("markers", "error: mark a test as testing error conditions")


@pytest.fixture
def test_config() -> Dict[str, Any]:
    """
    Provide a test configuration.
    
    Returns:
        Dict[str, Any]: A dictionary containing test configuration values.
    """
    return {
        "quality": {
            "enabled": True,
            "components": ["code_style", "static_analysis", "documentation", "structure"],
            "severity_threshold": "WARNING",
            "auto_fix": True
        },
        "logging": {
            "level": "INFO",
            "directory": "data/logs",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "documentation": {
            "required": True,
            "coverage_threshold": 80.0,
            "output_directory": "docs/generated"
        },
        "knowledge_graph": {
            "enabled": True,
            "update_on_quality_check": True,
            "metrics_schema_path": "core/kg/quality_metrics_schema.py",
            "metrics_query_path": "core/kg/quality_metrics_query.py"
        }
    }


@pytest.fixture
def test_files(temp_test_dir) -> Dict[str, str]:
    """
    Create test files for testing.
    
    Args:
        temp_test_dir: Temporary test directory fixture.
        
    Returns:
        Dict[str, str]: A dictionary mapping file names to file paths.
    """
    files = {}
    
    # Create a Python file with docstrings
    python_file_path = os.path.join(temp_test_dir, "example.py")
    with open(python_file_path, "w") as f:
        f.write('''"""
Example module.

This module provides an example for testing.
"""

def example_function():
    """Example function docstring."""
    return True

class ExampleClass:
    """Example class docstring."""
    
    def __init__(self):
        """Initialize the example class."""
        self.value = 42
    
    def example_method(self):
        """Example method docstring."""
        return self.value
''')
    files["example.py"] = python_file_path
    
    # Create a Python file without docstrings
    no_docs_file_path = os.path.join(temp_test_dir, "no_docs.py")
    with open(no_docs_file_path, "w") as f:
        f.write('''
def function_without_docstring():
    return True

class ClassWithoutDocstring:
    def __init__(self):
        self.value = 42
    
    def method_without_docstring(self):
        return self.value
''')
    files["no_docs.py"] = no_docs_file_path
    
    # Create a markdown file
    md_file_path = os.path.join(temp_test_dir, "README.md")
    with open(md_file_path, "w") as f:
        f.write('''# Example README

This is an example README file for testing.

## Features

- Feature 1
- Feature 2
- Feature 3

## Usage

```python
from example import ExampleClass

example = ExampleClass()
result = example.example_method()
print(result)  # Output: 42
```
''')
    files["README.md"] = md_file_path
    
    return files


@pytest.fixture
def mock_hooks_dir(temp_test_dir) -> str:
    """
    Create a mock hooks directory for testing.
    
    Args:
        temp_test_dir: Temporary test directory fixture.
        
    Returns:
        str: Path to the mock hooks directory.
    """
    hooks_dir = os.path.join(temp_test_dir, "hooks")
    os.makedirs(hooks_dir, exist_ok=True)
    
    # Create __init__.py
    init_path = os.path.join(hooks_dir, "__init__.py")
    with open(init_path, "w") as f:
        f.write('"""Hooks package."""\n')
    
    # Create validate_file_structure.py
    validate_path = os.path.join(hooks_dir, "validate_file_structure.py")
    with open(validate_path, "w") as f:
        f.write('''"""
File structure validation hook.

This module provides a pre-commit hook for validating file structure.
"""

import os
from typing import Dict, List, Optional, Any


def validate_file_structure(file_paths: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Validate file structure for the specified files.
    
    Args:
        file_paths: Optional list of file paths to check.
            If None, check all relevant files.
            
    Returns:
        Dictionary mapping check types to lists of issues.
    """
    # This is a placeholder implementation
    return {
        "directory_structure": [],
        "file_naming": [],
        "imports": [],
        "dependencies": []
    }
''')
    
    # Create check_documentation_quality.py
    check_docs_path = os.path.join(hooks_dir, "check_documentation_quality.py")
    with open(check_docs_path, "w") as f:
        f.write('''"""
Documentation quality check hook.

This module provides a pre-commit hook for checking documentation quality.
"""

import os
from typing import Dict, List, Optional, Any


def check_documentation_quality(file_paths: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Check documentation quality for the specified files.
    
    Args:
        file_paths: Optional list of file paths to check.
            If None, check all relevant files.
            
    Returns:
        Dictionary mapping check types to lists of issues.
    """
    # This is a placeholder implementation
    return {
        "docstrings": [],
        "readme": [],
        "coverage": []
    }
''')
    
    # Create suggest_improvements.py
    suggest_path = os.path.join(hooks_dir, "suggest_improvements.py")
    with open(suggest_path, "w") as f:
        f.write('''"""
Improvement suggestion hook.

This module provides a pre-commit hook for suggesting improvements.
"""

import os
from typing import Dict, List, Optional, Any


def suggest_improvements(file_paths: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Suggest improvements for the specified files.
    
    Args:
        file_paths: Optional list of file paths to check.
            If None, check all relevant files.
            
    Returns:
        List of suggested improvements.
    """
    # This is a placeholder implementation
    return []
''')
    
    return hooks_dir