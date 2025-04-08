"""
Helper functions for tests.

This module provides helper functions for test setup and teardown,
including functions for creating test files, setting up test environments,
and cleaning up after tests.
"""

import os
import shutil
import tempfile
from typing import Dict, List, Optional, Tuple, Any, Generator, Callable
import pytest

from core.quality import QualityCheckResult, QualityCheckSeverity


def create_test_file(directory: str, filename: str, content: str) -> str:
    """
    Create a test file with the specified content.
    
    Args:
        directory: The directory to create the file in.
        filename: The name of the file.
        content: The content of the file.
        
    Returns:
        The path to the created file.
    """
    file_path = os.path.join(directory, filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, "w") as f:
        f.write(content)
    
    return file_path


def create_test_directory_structure(base_dir: str, structure: Dict[str, Any]) -> None:
    """
    Create a test directory structure.
    
    Args:
        base_dir: The base directory to create the structure in.
        structure: A dictionary representing the directory structure.
            Keys are file/directory names, values are either strings (file content)
            or dictionaries (subdirectories).
    """
    for name, content in structure.items():
        path = os.path.join(base_dir, name)
        
        if isinstance(content, dict):
            os.makedirs(path, exist_ok=True)
            create_test_directory_structure(path, content)
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(content)


def create_python_module(directory: str, module_name: str, content: Optional[str] = None) -> str:
    """
    Create a Python module with the specified content.
    
    Args:
        directory: The directory to create the module in.
        module_name: The name of the module.
        content: Optional content of the module.
            If None, a default module template is used.
            
    Returns:
        The path to the created module.
    """
    if content is None:
        content = f'''"""
{module_name} module.

This module provides functionality for {module_name}.
"""

def main():
    """Main function."""
    print("Hello from {module_name}!")


if __name__ == "__main__":
    main()
'''
    
    return create_test_file(directory, f"{module_name}.py", content)


def create_test_quality_results(
    file_path: str,
    num_results: int = 5,
    severity: Optional[QualityCheckSeverity] = None
) -> List[QualityCheckResult]:
    """
    Create test quality check results.
    
    Args:
        file_path: The file path to use in the results.
        num_results: The number of results to create.
        severity: Optional severity to use for all results.
            If None, severities are varied.
            
    Returns:
        A list of QualityCheckResult objects.
    """
    results = []
    
    check_ids = ["black", "mypy", "docstrings", "directory_structure", "import_organization"]
    messages = [
        "Black formatting issue",
        "Type error",
        "Missing docstring",
        "Missing directory",
        "Import organization issue"
    ]
    
    for i in range(num_results):
        check_idx = i % len(check_ids)
        
        if severity is None:
            # Cycle through severities
            severities = [
                QualityCheckSeverity.INFO,
                QualityCheckSeverity.WARNING,
                QualityCheckSeverity.ERROR,
                QualityCheckSeverity.CRITICAL
            ]
            result_severity = severities[i % len(severities)]
        else:
            result_severity = severity
        
        result = QualityCheckResult(
            check_id=check_ids[check_idx],
            severity=result_severity,
            message=f"{messages[check_idx]} #{i+1}",
            file_path=file_path,
            line_number=i * 10 + 1 if i < 3 else None,
            fix_available=i % 2 == 0,
            fix_command=f"fix_{check_ids[check_idx]} {file_path}" if i % 2 == 0 else None
        )
        
        results.append(result)
    
    return results


def setup_test_environment() -> Tuple[str, Dict[str, str]]:
    """
    Set up a test environment with a directory structure and files.
    
    Returns:
        A tuple containing the base directory path and a dictionary
        mapping file names to file paths.
    """
    base_dir = tempfile.mkdtemp()
    
    # Create directory structure
    structure = {
        "core": {
            "quality": {
                "enforcer.py": "# Quality enforcer module",
                "hooks": {
                    "__init__.py": "",
                    "validate_file_structure.py": "# Validate file structure hook",
                    "check_documentation_quality.py": "# Check documentation quality hook",
                    "suggest_improvements.py": "# Suggest improvements hook"
                }
            },
            "documentation": {
                "__init__.py": "",
                "generator.py": "# Documentation generator module"
            },
            "logging": {
                "__init__.py": "",
                "manager.py": "# Logging manager module"
            },
            "kg": {
                "__init__.py": "",
                "quality_metrics_schema.py": "# Quality metrics schema",
                "quality_metrics_query.py": "# Quality metrics query"
            }
        },
        "tests": {
            "unit": {
                "__init__.py": "",
                "test_quality_enforcer.py": "# Test quality enforcer"
            },
            "integration": {
                "__init__.py": "",
                "test_quality_workflow.py": "# Test quality workflow"
            }
        }
    }
    
    create_test_directory_structure(base_dir, structure)
    
    # Create a dictionary mapping file names to file paths
    file_paths = {}
    for root, _, files in os.walk(base_dir):
        for file in files:
            file_path = os.path.join(root, file)
            file_paths[file] = file_path
    
    return base_dir, file_paths


def cleanup_test_environment(base_dir: str) -> None:
    """
    Clean up a test environment.
    
    Args:
        base_dir: The base directory of the test environment.
    """
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)


def with_environment(func: Callable) -> Callable:
    """
    Decorator to set up and tear down a test environment.
    
    Args:
        func: The function to decorate.
        
    Returns:
        The decorated function.
    """
    def wrapper(*args, **kwargs):
        base_dir, file_paths = setup_test_environment()
        try:
            return func(*args, base_dir=base_dir, file_paths=file_paths, **kwargs)
        finally:
            cleanup_test_environment(base_dir)
    
    return wrapper