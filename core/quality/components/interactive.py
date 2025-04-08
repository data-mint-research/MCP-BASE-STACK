"""
Interactive Fix Mode

This module provides an interactive mode for fixing quality issues, including:
- User confirmation of fixes
- Selection of which fixes to apply
- Customization of fix options
- Integration with the command-line interface

This allows users to review and approve fixes before they are applied.
"""

import os
import sys
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Union, Callable

from core.quality.components.base import QualityCheckResult, QualityCheckSeverity
from core.quality.components.fixes.code_style import CodeStyleFixes
from core.quality.components.fixes.documentation import DocumentationFixes
from core.quality.components.fixes.static_analysis import StaticAnalysisFixes
from core.quality.components.fixes.structure import StructureFixes
from core.quality.components.preview import FixPreview


class FixConfirmation(Enum):
    """Enum for fix confirmation options."""
    YES = "yes"
    NO = "no"
    ALL = "all"
    NONE = "none"
    PREVIEW = "preview"
    CUSTOMIZE = "customize"
    QUIT = "quit"


class InteractiveFixMode:
    """Interactive mode for fixing quality issues."""

    def __init__(self, results: List[QualityCheckResult]):
        """
        Initialize the interactive fix mode.

        Args:
            results: List of QualityCheckResult objects to fix.
        """
        self.results = results
        self.preview = FixPreview()
        self.fixed_results: List[QualityCheckResult] = []
        self.unfixed_results: List[QualityCheckResult] = []
        self.fix_options: Dict[str, bool] = {}
        
        # Initialize fix options
        self._initialize_fix_options()

    def _initialize_fix_options(self) -> None:
        """Initialize fix options based on the results."""
        # Group results by check_id
        check_ids = set(result.check_id for result in self.results)
        
        # Set default options
        for check_id in check_ids:
            self.fix_options[check_id] = True

    def run(self) -> Tuple[List[QualityCheckResult], List[QualityCheckResult]]:
        """
        Run the interactive fix mode.

        Returns:
            Tuple of (fixed_results, unfixed_results)
        """
        # Group results by component
        results_by_component: Dict[str, List[QualityCheckResult]] = {}
        
        for result in self.results:
            component = self._get_component_for_check(result.check_id)
            if component not in results_by_component:
                results_by_component[component] = []
            results_by_component[component].append(result)
        
        # Process each component
        for component, component_results in results_by_component.items():
            self._process_component(component, component_results)
        
        return self.fixed_results, self.unfixed_results

    def _process_component(self, component: str, results: List[QualityCheckResult]) -> None:
        """
        Process results for a component.

        Args:
            component: The component name.
            results: List of QualityCheckResult objects for the component.
        """
        print(f"\n=== {component.upper()} ISSUES ===")
        print(f"Found {len(results)} issues to fix.")
        
        # Group results by file
        results_by_file: Dict[str, List[QualityCheckResult]] = {}
        for result in results:
            if result.file_path:
                if result.file_path not in results_by_file:
                    results_by_file[result.file_path] = []
                results_by_file[result.file_path].append(result)
            else:
                # Handle results without a file path
                if "global" not in results_by_file:
                    results_by_file["global"] = []
                results_by_file["global"].append(result)
        
        # Process each file
        for file_path, file_results in results_by_file.items():
            self._process_file(file_path, file_results)

    def _process_file(self, file_path: str, results: List[QualityCheckResult]) -> None:
        """
        Process results for a file.

        Args:
            file_path: The file path.
            results: List of QualityCheckResult objects for the file.
        """
        print(f"\nFile: {file_path}")
        print(f"Found {len(results)} issues to fix.")
        
        # Group results by check_id
        results_by_check: Dict[str, List[QualityCheckResult]] = {}
        for result in results:
            if result.check_id not in results_by_check:
                results_by_check[result.check_id] = []
            results_by_check[result.check_id].append(result)
        
        # Process each check
        for check_id, check_results in results_by_check.items():
            self._process_check(check_id, check_results)

    def _process_check(self, check_id: str, results: List[QualityCheckResult]) -> None:
        """
        Process results for a check.

        Args:
            check_id: The check ID.
            results: List of QualityCheckResult objects for the check.
        """
        print(f"\nCheck: {check_id}")
        print(f"Found {len(results)} issues to fix.")
        
        # Display the issues
        for i, result in enumerate(results):
            print(f"{i+1}. {result.message}")
            if result.file_path and result.line_number:
                print(f"   Location: {result.file_path}:{result.line_number}")
        
        # Ask for confirmation
        confirmation = self._get_confirmation(check_id, results)
        
        if confirmation == FixConfirmation.YES:
            # Fix the issues
            fixed, unfixed = self._apply_fixes(check_id, results)
            self.fixed_results.extend(fixed)
            self.unfixed_results.extend(unfixed)
        elif confirmation == FixConfirmation.ALL:
            # Fix all issues
            self.fix_options[check_id] = True
            fixed, unfixed = self._apply_fixes(check_id, results)
            self.fixed_results.extend(fixed)
            self.unfixed_results.extend(unfixed)
        elif confirmation == FixConfirmation.PREVIEW:
            # Preview the fixes
            self._preview_fixes(check_id, results)
            # Ask again after preview
            confirmation = self._get_confirmation(check_id, results)
            if confirmation in [FixConfirmation.YES, FixConfirmation.ALL]:
                fixed, unfixed = self._apply_fixes(check_id, results)
                self.fixed_results.extend(fixed)
                self.unfixed_results.extend(unfixed)
            else:
                self.unfixed_results.extend(results)
        elif confirmation == FixConfirmation.CUSTOMIZE:
            # Customize fix options
            self._customize_fix_options(check_id)
            # Apply fixes with customized options
            fixed, unfixed = self._apply_fixes(check_id, results)
            self.fixed_results.extend(fixed)
            self.unfixed_results.extend(unfixed)
        else:
            # Skip fixing these issues
            self.unfixed_results.extend(results)

    def _get_confirmation(self, check_id: str, results: List[QualityCheckResult]) -> FixConfirmation:
        """
        Get confirmation from the user.

        Args:
            check_id: The check ID.
            results: List of QualityCheckResult objects for the check.

        Returns:
            FixConfirmation enum value.
        """
        while True:
            print("\nFix options:")
            print("  (y)es    - Fix these issues")
            print("  (n)o     - Skip these issues")
            print("  (a)ll    - Fix all issues of this type")
            print("  (p)review - Preview the fixes")
            print("  (c)ustomize - Customize fix options")
            print("  (q)uit   - Quit interactive mode")
            
            choice = input("What would you like to do? [y/n/a/p/c/q]: ").lower()
            
            if choice in ["y", "yes"]:
                return FixConfirmation.YES
            elif choice in ["n", "no"]:
                return FixConfirmation.NO
            elif choice in ["a", "all"]:
                return FixConfirmation.ALL
            elif choice in ["p", "preview"]:
                return FixConfirmation.PREVIEW
            elif choice in ["c", "customize"]:
                return FixConfirmation.CUSTOMIZE
            elif choice in ["q", "quit"]:
                return FixConfirmation.QUIT
            else:
                print("Invalid choice. Please try again.")

    def _preview_fixes(self, check_id: str, results: List[QualityCheckResult]) -> None:
        """
        Preview the fixes for a check.

        Args:
            check_id: The check ID.
            results: List of QualityCheckResult objects for the check.
        """
        # Get unique file paths
        file_paths = set(result.file_path for result in results if result.file_path)
        
        for file_path in file_paths:
            # Generate a preview for the file
            diff = self.preview.generate_diff(file_path, [r for r in results if r.file_path == file_path])
            
            # Display the diff
            print(f"\nPreview of fixes for {file_path}:")
            print(diff)

    def _customize_fix_options(self, check_id: str) -> None:
        """
        Customize fix options for a check.

        Args:
            check_id: The check ID.
        """
        print(f"\nCustomize fix options for {check_id}:")
        
        if check_id == "black":
            print("Black formatting options:")
            print("  1. Line length (default: 88)")
            choice = input("Enter new line length (or press Enter for default): ")
            if choice.strip():
                try:
                    line_length = int(choice)
                    print(f"Set line length to {line_length}")
                    # In a real implementation, we would store this option
                except ValueError:
                    print("Invalid value. Using default.")
        elif check_id == "isort":
            print("isort options:")
            print("  1. Profile (default: black)")
            choice = input("Enter profile (black, django, pycharm, google, or press Enter for default): ")
            if choice.strip() in ["black", "django", "pycharm", "google"]:
                print(f"Set profile to {choice}")
                # In a real implementation, we would store this option
        elif check_id == "flake8":
            print("flake8 options:")
            print("  1. Ignore specific errors")
            choice = input("Enter comma-separated error codes to ignore (or press Enter for none): ")
            if choice.strip():
                print(f"Ignoring errors: {choice}")
                # In a real implementation, we would store this option
        else:
            print(f"No customizable options for {check_id}")

    def _apply_fixes(self, check_id: str, results: List[QualityCheckResult]) -> Tuple[List[QualityCheckResult], List[QualityCheckResult]]:
        """
        Apply fixes for a check.

        Args:
            check_id: The check ID.
            results: List of QualityCheckResult objects for the check.

        Returns:
            Tuple of (fixed_results, unfixed_results)
        """
        component = self._get_component_for_check(check_id)
        
        if component == "code_style":
            return CodeStyleFixes.apply_fixes(results)
        elif component == "documentation":
            return DocumentationFixes.apply_fixes(results)
        elif component == "structure":
            return StructureFixes.apply_fixes(results)
        elif component == "static_analysis":
            return StaticAnalysisFixes.apply_fixes(results)
        else:
            return [], results

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


def run_interactive_fix(results: List[QualityCheckResult]) -> Tuple[List[QualityCheckResult], List[QualityCheckResult]]:
    """
    Run the interactive fix mode.

    Args:
        results: List of QualityCheckResult objects to fix.

    Returns:
        Tuple of (fixed_results, unfixed_results)
    """
    interactive_mode = InteractiveFixMode(results)
    return interactive_mode.run()