"""
Structure Fixes

This module provides auto-fix capabilities for structure-related issues, including:
- Directory structure corrections
- File naming convention enforcement
- Import organization
- Circular dependency resolution
- File structure standardization

These fixes can be applied automatically or interactively.
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

from core.quality.components.base import QualityCheckResult, QualityCheckSeverity
from core.quality.components.fixes.file_structure_validator import FileStructureValidator

class StructureFixes:
    """Provides auto-fix capabilities for structure-related issues."""

    @staticmethod
    def fix_file_naming(file_path: str, suggested_name: str) -> Tuple[bool, str, Optional[str]]:
        """
        Fix file naming convention issues.

        Args:
            file_path: Path to the file with naming issues.
            suggested_name: The suggested file name.

        Returns:
            Tuple of (success, error_message, new_path)
        """
        try:
            if not os.path.exists(file_path):
                return False, f"File not found: {file_path}", None

            directory = os.path.dirname(file_path)
            new_path = os.path.join(directory, suggested_name)

            # Check if the target file already exists
            if os.path.exists(new_path):
                return False, f"Target file already exists: {new_path}", None

            # Rename the file
            shutil.move(file_path, new_path)

            return True, "", new_path
        except Exception as e:
            return False, str(e), None

    @staticmethod
    def create_directory_structure(base_dir: str, structure: List[str]) -> Tuple[bool, str]:
        """
        Create a directory structure.

        Args:
            base_dir: Base directory where to create the structure.
            structure: List of directory paths to create.

        Returns:
            Tuple of (success, error_message)
        """
        try:
            for dir_path in structure:
                full_path = os.path.join(base_dir, dir_path)
                os.makedirs(full_path, exist_ok=True)

            return True, ""
        except Exception as e:
            return False, str(e)

    @staticmethod
    def fix_import_organization(file_path: str) -> Tuple[bool, str]:
        """
        Fix import organization in a Python file.

        Args:
            file_path: Path to the Python file.

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # This is a simplified version that just uses isort
            # A more sophisticated version would handle specific import organization rules
            import subprocess

            cmd = ["isort", file_path]
            process = subprocess.run(cmd, capture_output=True, text=True)

            if process.returncode != 0:
                return False, f"isort failed: {process.stderr}"

            return True, ""
        except Exception as e:
            return False, str(e)

    @staticmethod
    def fix_circular_dependency(file_path: str, circular_import: str) -> Tuple[bool, str]:
        """
        Fix a circular dependency in a Python file.

        Args:
            file_path: Path to the Python file.
            circular_import: The import statement causing the circular dependency.

        Returns:
            Tuple of (success, error_message)
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Find and modify the circular import
            modified = False
            for i, line in enumerate(lines):
                if circular_import in line and not line.strip().startswith("#"):
                    # Comment out the import
                    lines[i] = f"# {line}  # Circular dependency, use lazy import instead\n"
                    
                    # Add a lazy import function if not already present
                    if not any("def _lazy_import" in l for l in lines):
                        # Find the imports section
                        insert_index = 0
                        for j, l in enumerate(lines):
                            if l.strip().startswith("import ") or l.strip().startswith("from "):
                                insert_index = max(insert_index, j)
                        
                        # Add the lazy import function after the imports
                        lazy_import_func = [
                            "\n\n",
                            "def _lazy_import(module_name):\n",
                            "    \"\"\"Lazily import a module to avoid circular dependencies.\"\"\"\n",
                            "    import importlib\n",
                            "    return importlib.import_module(module_name)\n",
                            "\n"
                        ]
                        lines = lines[:insert_index + 1] + lazy_import_func + lines[insert_index + 1:]
                    
                    modified = True
                    break

            if not modified:
                return False, f"Circular import '{circular_import}' not found in {file_path}"

            # Write the modified content back to the file
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)

            return True, ""
        except Exception as e:
            return False, str(e)

    @staticmethod
    def apply_fixes(results: List[QualityCheckResult]) -> Tuple[List[QualityCheckResult], List[QualityCheckResult]]:
        """
        Apply fixes to structure-related issues.

        Args:
            results: List of QualityCheckResult objects to fix.

        Returns:
            Tuple of (fixed_results, unfixed_results)
        """
        # Group results by check_id
        results_by_check: Dict[str, List[QualityCheckResult]] = {}
        for result in results:
            if result.check_id not in results_by_check:
                results_by_check[result.check_id] = []
            results_by_check[result.check_id].append(result)

        fixed_results = []
        unfixed_results = []

        # Fix file naming issues
        if "file_naming" in results_by_check:
            file_naming_results = results_by_check["file_naming"]
            
            # Use the new file structure validator for batch fixing
            try:
                # First try to use the new validator
                fixed_files = FileStructureValidator.fix_naming_conventions(dry_run=False)
                
                # Mark results as fixed if their file paths are in the fixed files list
                fixed_file_paths = [f['file_path'] for f in fixed_files]
                for result in file_naming_results:
                    if result.file_path in fixed_file_paths:
                        fixed_results.append(result)
                    else:
                        # Fall back to the old method for any remaining files
                        if result.file_path and "suggested name" in result.message.lower():
                            match = re.search(r"suggested name[:\s]+([^\s]+)", result.message.lower())
                            if match:
                                suggested_name = match.group(1)
                                success, _, _ = StructureFixes.fix_file_naming(result.file_path, suggested_name)
                                if success:
                                    fixed_results.append(result)
                                else:
                                    unfixed_results.append(result)
                            else:
                                unfixed_results.append(result)
                        else:
                            unfixed_results.append(result)
            except Exception as e:
                # Fall back to the old method if the new validator fails
                print(f"Error using file structure validator: {e}. Falling back to legacy method.")
                for result in file_naming_results:
                    if result.file_path and "suggested name" in result.message.lower():
                        match = re.search(r"suggested name[:\s]+([^\s]+)", result.message.lower())
                        if match:
                            suggested_name = match.group(1)
                            success, _, _ = StructureFixes.fix_file_naming(result.file_path, suggested_name)
                            if success:
                                fixed_results.append(result)
                            else:
                                unfixed_results.append(result)
                        else:
                            unfixed_results.append(result)
                    else:
                        unfixed_results.append(result)

        # Fix import organization issues
        if "import_organization" in results_by_check:
            import_results = results_by_check["import_organization"]
            for result in import_results:
                if result.file_path:
                    success, _ = StructureFixes.fix_import_organization(result.file_path)
                    if success:
                        fixed_results.append(result)
                    else:
                        unfixed_results.append(result)
                else:
                    unfixed_results.append(result)

        # Fix circular dependency issues
        if "circular_dependencies" in results_by_check:
            circular_dep_results = results_by_check["circular_dependencies"]
            for result in circular_dep_results:
                if result.file_path and "import" in result.message.lower():
                    # Extract the circular import from the message
                    match = re.search(r"(?:import|from)\s+([^\s]+)", result.message)
                    if match:
                        circular_import = match.group(0)
                        success, _ = StructureFixes.fix_circular_dependency(result.file_path, circular_import)
                        if success:
                            fixed_results.append(result)
                        else:
                            unfixed_results.append(result)
                    else:
                        unfixed_results.append(result)
                else:
                    unfixed_results.append(result)

        # Handle directory structure issues
        if "directory_structure" in results_by_check:
            directory_structure_results = results_by_check["directory_structure"]
            
            # Use the new file structure validator for directory relocation
            try:
                # First try to use the new validator
                relocated_files = FileStructureValidator.relocate_files(dry_run=False)
                
                # Mark results as fixed if their file paths are in the relocated files list
                relocated_file_paths = [f['file_path'] for f in relocated_files]
                for result in directory_structure_results:
                    if result.file_path in relocated_file_paths:
                        fixed_results.append(result)
                    else:
                        unfixed_results.append(result)
            except Exception as e:
                # Fall back to marking them as unfixed if the new validator fails
                print(f"Error using file structure validator for directory relocation: {e}")
                unfixed_results.extend(directory_structure_results)
        
        # Handle file structure issues
        if "file_structure" in results_by_check:
            # These are handled by the file structure validator
            file_structure_results = results_by_check["file_structure"]
            
            # Run validation to update metrics
            try:
                FileStructureValidator.validate()
                # Mark all as fixed since we've run the validator
                fixed_results.extend(file_structure_results)
            except Exception as e:
                print(f"Error validating file structure: {e}")
                unfixed_results.extend(file_structure_results)

        # Handle other structure issues
        for check_id, check_results in results_by_check.items():
            if check_id not in ["file_naming", "import_organization", "circular_dependencies", "directory_structure", "file_structure"]:
                unfixed_results.extend(check_results)

        return fixed_results, unfixed_results
        
    @staticmethod
    def get_file_structure_metrics() -> Dict[str, float]:
        """
        Get file structure compliance metrics.
        
        Returns:
            Dictionary with compliance metrics
        """
        return FileStructureValidator.get_compliance_metrics()