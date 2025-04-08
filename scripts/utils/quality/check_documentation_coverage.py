#!/usr/bin/env python3
"""
Documentation Coverage Check Script

This script checks the documentation coverage of Python files and can be used
as a pre-commit hook to ensure that new code meets documentation standards.

It uses the EnhancedDocumentationCoverageCheck from the quality components
to analyze documentation coverage at multiple levels:
- Module level (module docstrings)
- Class level (class docstrings)
- Method/function level (function docstrings)
- Parameter level (parameter documentation in docstrings)
- Return value documentation

Usage:
    python check_documentation_coverage.py [file1.py file2.py ...]
    
If no files are provided, it will check all Python files in the project.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Optional

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from core.quality.components.documentation_coverage import EnhancedDocumentationCoverageCheck
from core.quality.components.base import QualityCheckSeverity

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('documentation_coverage')

# Constants
MIN_MODULE_COVERAGE = 0.9  # 90% module docstring coverage
MIN_CLASS_COVERAGE = 0.9   # 90% class docstring coverage
MIN_FUNCTION_COVERAGE = 0.8  # 80% function docstring coverage
MIN_PARAM_COVERAGE = 0.7   # 70% parameter docstring coverage
MIN_RETURN_COVERAGE = 0.7  # 70% return value docstring coverage

def check_documentation_coverage(file_paths: Optional[List[str]] = None) -> bool:
    """
    Check documentation coverage for the specified files.
    
    Args:
        file_paths: Optional list of Python file paths to check.
            If None, check all Python files.
            
    Returns:
        True if all checks pass, False otherwise.
    """
    logger.info(f"Checking documentation coverage for {len(file_paths) if file_paths else 'all'} files")
    
    # Create the documentation coverage checker
    checker = EnhancedDocumentationCoverageCheck()
    
    # Run the checks
    results = checker.run(
        file_paths=file_paths,
        min_module_coverage=MIN_MODULE_COVERAGE,
        min_class_coverage=MIN_CLASS_COVERAGE,
        min_function_coverage=MIN_FUNCTION_COVERAGE,
        min_param_coverage=MIN_PARAM_COVERAGE,
        min_return_coverage=MIN_RETURN_COVERAGE,
        export_metrics=True
    )
    
    # Filter for warnings and errors
    issues = [r for r in results if r.severity in [QualityCheckSeverity.WARNING, QualityCheckSeverity.ERROR]]
    
    # Print results
    if issues:
        logger.warning(f"Found {len(issues)} documentation coverage issues:")
        for issue in issues:
            location = f"{issue.file_path}:{issue.line_number}" if issue.line_number else issue.file_path
            severity = "ERROR" if issue.severity == QualityCheckSeverity.ERROR else "WARNING"
            logger.warning(f"{severity} - {location} - {issue.message}")
        return False
    else:
        logger.info("Documentation coverage check passed!")
        return True

def main() -> int:
    """
    Main entry point for the script.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    # Get file paths from command line arguments
    file_paths = sys.argv[1:] if len(sys.argv) > 1 else None
    
    # Filter for Python files
    if file_paths:
        file_paths = [f for f in file_paths if f.endswith('.py')]
    
    # Check documentation coverage
    if check_documentation_coverage(file_paths):
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())