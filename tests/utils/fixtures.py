"""
Test fixtures for quality module tests.

This module provides common test fixtures that can be reused across
different test files, including mock files, directories, and quality check results.
"""

import os
import tempfile
import shutil
from typing import Dict, List, Optional, Tuple, Any, Generator
import pytest

from core.quality.components.base import QualityCheckResult, QualityCheckSeverity


@pytest.fixture
def temp_test_dir() -> Generator[str, None, None]:
    """
    Create a temporary directory for tests.
    
    Yields:
        str: Path to the temporary directory.
    """
    temp_dir = tempfile.mkdtemp()
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)


@pytest.fixture
def temp_test_file() -> Generator[Tuple[str, str], None, None]:
    """
    Create a temporary file for tests.
    
    Yields:
        Tuple[str, str]: A tuple containing the directory path and file path.
    """
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, "test_file.py")
    
    with open(file_path, "w") as f:
        f.write("""
def example_function():
    \"\"\"Example function docstring.\"\"\"
    return True

class ExampleClass:
    \"\"\"Example class docstring.\"\"\"
    
    def __init__(self):
        \"\"\"Initialize the example class.\"\"\"
        self.value = 42
    
    def example_method(self):
        \"\"\"Example method docstring.\"\"\"
        return self.value
""")
    
    try:
        yield temp_dir, file_path
    finally:
        shutil.rmtree(temp_dir)


@pytest.fixture
def mock_quality_results() -> List[QualityCheckResult]:
    """
    Create mock quality check results for testing.
    
    Returns:
        List[QualityCheckResult]: A list of mock quality check results.
    """
    return [
        QualityCheckResult(
            check_id="black",
            severity=QualityCheckSeverity.WARNING,
            message="Black formatting issue",
            file_path="test_file.py",
            fix_available=True,
            fix_command="black test_file.py"
        ),
        QualityCheckResult(
            check_id="mypy",
            severity=QualityCheckSeverity.ERROR,
            message="Type error",
            file_path="test_file.py",
            line_number=10
        ),
        QualityCheckResult(
            check_id="docstrings",
            severity=QualityCheckSeverity.INFO,
            message="Missing docstring",
            file_path="test_file.py",
            line_number=5
        ),
        QualityCheckResult(
            check_id="directory_structure",
            severity=QualityCheckSeverity.WARNING,
            message="Missing directory",
            file_path="."
        )
    ]


@pytest.fixture
def mock_file_structure() -> Dict[str, Any]:
    """
    Create a mock file structure for testing.
    
    Returns:
        Dict[str, Any]: A dictionary representing a mock file structure.
    """
    return {
        "core": {
            "quality": {
                "enforcer.py": "# Quality enforcer module",
                "hooks": {
                    "validate_file_structure.py": "# Validate file structure hook",
                    "check_documentation_quality.py": "# Check documentation quality hook",
                    "suggest_improvements.py": "# Suggest improvements hook"
                }
            },
            "documentation": {
                "generator.py": "# Documentation generator module"
            },
            "logging": {
                "manager.py": "# Logging manager module"
            },
            "kg": {
                "quality_metrics_schema.py": "# Quality metrics schema",
                "quality_metrics_query.py": "# Quality metrics query"
            }
        },
        "tests": {
            "unit": {
                "test_quality_enforcer.py": "# Test quality enforcer",
                "test_log_manager.py": "# Test log manager",
                "test_documentation_generator.py": "# Test documentation generator"
            },
            "integration": {
                "test_quality_workflow.py": "# Test quality workflow"
            }
        }
    }


@pytest.fixture
def mock_kg_schema() -> Dict[str, Any]:
    """
    Create a mock knowledge graph schema for testing.
    
    Returns:
        Dict[str, Any]: A dictionary representing a mock knowledge graph schema.
    """
    return {
        "nodes": {
            "QualityMetric": {
                "properties": {
                    "name": "string",
                    "value": "float",
                    "threshold": "float",
                    "status": "string"
                }
            },
            "QualityCheck": {
                "properties": {
                    "check_id": "string",
                    "severity": "string",
                    "message": "string",
                    "file_path": "string",
                    "line_number": "integer",
                    "fix_available": "boolean",
                    "fix_command": "string"
                }
            }
        },
        "relationships": {
            "HAS_METRIC": {
                "source": "File",
                "target": "QualityMetric",
                "properties": {
                    "timestamp": "datetime"
                }
            },
            "HAS_CHECK": {
                "source": "File",
                "target": "QualityCheck",
                "properties": {
                    "timestamp": "datetime"
                }
            }
        }
    }