"""
Fix Preview Functionality

This module provides functionality for previewing fixes before they are applied, including:
- Generating fix previews (diffs)
- Visualizing changes
- Comparing multiple fix options
- Integration with the interactive mode

This allows users to see the changes that will be made before they are applied.
"""

import difflib
import os
import re
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

from core.quality.components.base import QualityCheckResult, QualityCheckSeverity
from core.quality.components.fixes.code_style import CodeStyleFixes
from core.quality.components.fixes.documentation import DocumentationFixes
from core.quality.components.fixes.static_analysis import StaticAnalysisFixes
from core.quality.components.fixes.structure import StructureFixes


class FixPreview:
    """Provides functionality for previewing fixes."""

    def generate_diff(self, file_path: str, results: List[QualityCheckResult]) -> str:
        """
        Generate a diff for the fixes that would be applied to a file.

        Args:
            file_path: Path to the file.
            results: List of QualityCheckResult objects for the file.

        Returns:
            Diff string showing the changes that would be made.
        """
        if not os.path.exists(file_path):
            return f"File not found: {file_path}"

        # Create a temporary copy of the file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            with open(file_path, "r", encoding="utf-8", errors="replace") as original_file:
                temp_file.write(original_file.read())
            temp_file_path = temp_file.name

        try:
            # Apply fixes to the temporary file
            self._apply_fixes_to_temp_file(temp_file_path, results)

            # Generate diff
            with open(file_path, "r", encoding="utf-8", errors="replace") as original_file:
                original_lines = original_file.readlines()
            with open(temp_file_path, "r", encoding="utf-8", errors="replace") as temp_file:
                temp_lines = temp_file.readlines()

            diff = difflib.unified_diff(
                original_lines,
                temp_lines,
                fromfile=f"a/{file_path}",
                tofile=f"b/{file_path}",
                n=3  # Context lines
            )

            return "".join(diff)
        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)

    def _apply_fixes_to_temp_file(self, temp_file_path: str, results: List[QualityCheckResult]) -> None:
        """
        Apply fixes to a temporary file.

        Args:
            temp_file_path: Path to the temporary file.
            results: List of QualityCheckResult objects for the file.
        """
        # Group results by check_id
        results_by_check: Dict[str, List[QualityCheckResult]] = {}
        for result in results:
            if result.check_id not in results_by_check:
                results_by_check[result.check_id] = []
            results_by_check[result.check_id].append(result)

        # Apply fixes for each check type
        for check_id, check_results in results_by_check.items():
            component = self._get_component_for_check(check_id)
            
            # Create modified results with the temporary file path
            modified_results = []
            for result in check_results:
                modified_result = QualityCheckResult(
                    check_id=result.check_id,
                    severity=result.severity,
                    message=result.message,
                    file_path=temp_file_path,
                    line_number=result.line_number,
                    column=result.column,
                    source=result.source,
                    details=result.details,
                    fix_available=result.fix_available,
                    fix_command=result.fix_command
                )
                modified_results.append(modified_result)
            
            # Apply fixes based on the component
            if component == "code_style":
                CodeStyleFixes.apply_fixes(modified_results)
            elif component == "documentation":
                DocumentationFixes.apply_fixes(modified_results)
            elif component == "structure":
                StructureFixes.apply_fixes(modified_results)
            elif component == "static_analysis":
                StaticAnalysisFixes.apply_fixes(modified_results)

    def generate_multiple_diffs(self, file_path: str, results: List[QualityCheckResult]) -> Dict[str, str]:
        """
        Generate multiple diffs for different fix options.

        Args:
            file_path: Path to the file.
            results: List of QualityCheckResult objects for the file.

        Returns:
            Dictionary mapping fix option names to diff strings.
        """
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}

        # Group results by check_id
        results_by_check: Dict[str, List[QualityCheckResult]] = {}
        for result in results:
            if result.check_id not in results_by_check:
                results_by_check[result.check_id] = []
            results_by_check[result.check_id].append(result)

        diffs = {}

        # Generate a diff for each check type
        for check_id, check_results in results_by_check.items():
            diff = self.generate_diff(file_path, check_results)
            diffs[check_id] = diff

        return diffs

    def visualize_changes(self, diff: str) -> str:
        """
        Visualize changes in a more user-friendly format.

        Args:
            diff: Diff string.

        Returns:
            Formatted string with highlighted changes.
        """
        # This is a simplified version that adds ANSI color codes
        # In a real implementation, this would use a more sophisticated
        # visualization approach, possibly with HTML or terminal colors
        
        lines = diff.splitlines()
        formatted_lines = []
        
        for line in lines:
            if line.startswith("+"):
                # Added line (green)
                formatted_lines.append(f"\033[32m{line}\033[0m")
            elif line.startswith("-"):
                # Removed line (red)
                formatted_lines.append(f"\033[31m{line}\033[0m")
            elif line.startswith("@@"):
                # Hunk header (cyan)
                formatted_lines.append(f"\033[36m{line}\033[0m")
            else:
                # Context line (normal)
                formatted_lines.append(line)
        
        return "\n".join(formatted_lines)

    def compare_fix_options(self, file_path: str, results: List[QualityCheckResult]) -> str:
        """
        Compare multiple fix options for a file.

        Args:
            file_path: Path to the file.
            results: List of QualityCheckResult objects for the file.

        Returns:
            Formatted string comparing different fix options.
        """
        diffs = self.generate_multiple_diffs(file_path, results)
        
        if "error" in diffs:
            return diffs["error"]
        
        comparison = f"Fix options for {file_path}:\n\n"
        
        for check_id, diff in diffs.items():
            comparison += f"=== {check_id} ===\n"
            comparison += diff
            comparison += "\n\n"
        
        return comparison

    def _get_component_for_check(self, check_id: str) -> str:
        """
        Get the component for a check ID.

        Args:
            check_id: The check ID.

        Returns:
            The component name.
        """
        # This is a simplified mapping
        if check_id in ["black", "isort", "line_endings"]:
            return "code_style"
        elif check_id in ["docstrings", "readme", "doc_coverage"]:
            return "documentation"
        elif check_id in ["file_naming", "directory_structure", "import_organization", "circular_dependencies"]:
            return "structure"
        elif check_id in ["flake8", "pylint", "mypy", "security"]:
            return "static_analysis"
        else:
            return "unknown"


def generate_fix_preview(file_path: str, results: List[QualityCheckResult]) -> str:
    """
    Generate a preview of fixes for a file.

    Args:
        file_path: Path to the file.
        results: List of QualityCheckResult objects for the file.

    Returns:
        Diff string showing the changes that would be made.
    """
    preview = FixPreview()
    return preview.generate_diff(file_path, results)


def compare_fix_options(file_path: str, results: List[QualityCheckResult]) -> str:
    """
    Compare multiple fix options for a file.

    Args:
        file_path: Path to the file.
        results: List of QualityCheckResult objects for the file.

    Returns:
        Formatted string comparing different fix options.
    """
    preview = FixPreview()
    return preview.compare_fix_options(file_path, results)