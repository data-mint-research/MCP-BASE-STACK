"""
File Structure Validator

This module integrates the file structure standardization functionality with the
quality enforcement system. It provides a validator class that can be used to
validate file structure as part of the quality checks.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Add project root to path to allow importing standardize_file_structure
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))
import standardize_file_structure

class FileStructureValidator:
    """Validator for file structure standards."""
    
    @staticmethod
    def validate() -> Dict[str, Any]:
        """
        Validate file structure and return a report.
        
        Returns:
            Dictionary with validation results
        """
        return standardize_file_structure.validate_file_structure()
    
    @staticmethod
    def fix_naming_conventions(dry_run: bool = False) -> List[Dict[str, Any]]:
        """
        Fix naming convention issues in files.
        
        Args:
            dry_run: If True, only show what would be done without making changes
            
        Returns:
            List of files that were fixed
        """
        return standardize_file_structure.fix_naming_conventions(dry_run)
    
    @staticmethod
    def relocate_files(dry_run: bool = False) -> List[Dict[str, Any]]:
        """
        Relocate files to their ideal directories.
        
        Args:
            dry_run: If True, only show what would be done without making changes
            
        Returns:
            List of files that were relocated
        """
        return standardize_file_structure.relocate_files(dry_run)
    
    @staticmethod
    def get_validation_report() -> Optional[Dict[str, Any]]:
        """
        Get the latest file structure validation report.
        
        Returns:
            Dictionary with validation results, or None if no report exists
        """
        report_path = Path("data/reports/file-structure-report.json")
        if report_path.exists():
            with open(report_path, 'r') as f:
                return json.load(f)
        return None
    
    @staticmethod
    def get_compliance_metrics() -> Dict[str, float]:
        """
        Get compliance metrics from the latest validation report.
        
        Returns:
            Dictionary with compliance metrics
        """
        report = FileStructureValidator.get_validation_report()
        if report:
            return {
                'naming_compliance': report['naming_issues']['compliance_percentage'],
                'directory_compliance': report['directory_issues']['compliance_percentage'],
                'overall_compliance': report['overall_compliance_percentage']
            }
        return {
            'naming_compliance': 0.0,
            'directory_compliance': 0.0,
            'overall_compliance': 0.0
        }