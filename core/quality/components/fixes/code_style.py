"""
Code Style Fixes

This module provides auto-fix capabilities for code style issues, including:
- Automatic formatting with Black
- Import sorting with isort
- Line ending normalization
- Whitespace cleanup

These fixes can be applied automatically or interactively.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

from core.quality.components.base import QualityCheckResult, QualityCheckSeverity


class CodeStyleFixes:
    """Provides auto-fix capabilities for code style issues."""

    @staticmethod
    def fix_black_formatting(file_paths: List[str]) -> Tuple[List[str], List[str]]:
        """
        Fix Python code formatting using Black.

        Args:
            file_paths: List of Python file paths to fix.

        Returns:
            Tuple of (fixed_files, error_files)
        """
        if not file_paths:
            return [], []

        fixed_files = []
        error_files = []

        # Run Black to fix formatting
        cmd = ["black"] + file_paths
        process = subprocess.run(cmd, capture_output=True, text=True)

        if process.returncode != 0:
            # If Black failed, return all files as errors
            return [], file_paths

        # Check which files were actually fixed
        for line in process.stderr.splitlines() + process.stdout.splitlines():
            if "reformatted" in line:
                file_path = line.split("reformatted", 1)[1].strip()
                fixed_files.append(file_path)
            elif "would reformat" in line:
                file_path = line.split("would reformat", 1)[1].strip()
                fixed_files.append(file_path)
            elif "error" in line.lower() and ".py" in line:
                # Extract file path from error message
                for part in line.split():
                    if part.endswith(".py"):
                        error_files.append(part)
                        break

        # Files that weren't mentioned in the output are considered unchanged
        unchanged = [f for f in file_paths if f not in fixed_files and f not in error_files]

        return fixed_files, error_files

    @staticmethod
    def fix_isort_imports(file_paths: List[str]) -> Tuple[List[str], List[str]]:
        """
        Fix Python import sorting using isort.

        Args:
            file_paths: List of Python file paths to fix.

        Returns:
            Tuple of (fixed_files, error_files)
        """
        if not file_paths:
            return [], []

        fixed_files = []
        error_files = []

        # Run isort to fix import sorting
        cmd = ["isort"] + file_paths
        process = subprocess.run(cmd, capture_output=True, text=True)

        if process.returncode != 0:
            # If isort failed, return all files as errors
            return [], file_paths

        # Check which files were actually modified
        # isort doesn't provide detailed output, so we assume all files were fixed
        fixed_files = file_paths

        return fixed_files, error_files

    @staticmethod
    def fix_line_endings(file_paths: List[str], line_ending: str = "\n") -> Tuple[List[str], List[str]]:
        """
        Fix line endings in text files.

        Args:
            file_paths: List of file paths to fix.
            line_ending: The line ending to use ("\n" for LF, "\r\n" for CRLF).

        Returns:
            Tuple of (fixed_files, error_files)
        """
        if not file_paths:
            return [], []

        fixed_files = []
        error_files = []

        for file_path in file_paths:
            try:
                # Read the file content
                with open(file_path, "rb") as f:
                    content = f.read()

                # Normalize line endings
                if b"\r\n" in content:
                    # Convert CRLF to LF first
                    content = content.replace(b"\r\n", b"\n")

                # Then convert to the desired line ending
                if line_ending == "\r\n":
                    content = content.replace(b"\n", b"\r\n")

                # Write the content back to the file
                with open(file_path, "wb") as f:
                    f.write(content)

                fixed_files.append(file_path)
            except Exception as e:
                error_files.append(file_path)

        return fixed_files, error_files

    @staticmethod
    def fix_trailing_whitespace(file_paths: List[str]) -> Tuple[List[str], List[str]]:
        """
        Fix trailing whitespace in text files.

        Args:
            file_paths: List of file paths to fix.

        Returns:
            Tuple of (fixed_files, error_files)
        """
        if not file_paths:
            return [], []

        fixed_files = []
        error_files = []

        for file_path in file_paths:
            try:
                # Read the file content
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()

                # Remove trailing whitespace
                fixed_lines = [line.rstrip() + "\n" for line in lines]

                # Check if any changes were made
                if fixed_lines != lines:
                    # Write the content back to the file
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.writelines(fixed_lines)
                    fixed_files.append(file_path)
            except Exception as e:
                error_files.append(file_path)

        return fixed_files, error_files

    @staticmethod
    def apply_fixes(results: List[QualityCheckResult]) -> Tuple[List[QualityCheckResult], List[QualityCheckResult]]:
        """
        Apply fixes to code style issues.

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

        # Fix Black formatting issues
        if "black" in results_by_check:
            black_results = results_by_check["black"]
            file_paths = [r.file_path for r in black_results if r.file_path]
            fixed_files, error_files = CodeStyleFixes.fix_black_formatting(file_paths)

            for result in black_results:
                if result.file_path in fixed_files:
                    fixed_results.append(result)
                else:
                    unfixed_results.append(result)

        # Fix isort import sorting issues
        if "isort" in results_by_check:
            isort_results = results_by_check["isort"]
            file_paths = [r.file_path for r in isort_results if r.file_path]
            fixed_files, error_files = CodeStyleFixes.fix_isort_imports(file_paths)

            for result in isort_results:
                if result.file_path in fixed_files:
                    fixed_results.append(result)
                else:
                    unfixed_results.append(result)

        # Fix line ending issues
        if "line_endings" in results_by_check:
            line_ending_results = results_by_check["line_endings"]
            file_paths = [r.file_path for r in line_ending_results if r.file_path]
            fixed_files, error_files = CodeStyleFixes.fix_line_endings(file_paths)

            for result in line_ending_results:
                if result.file_path in fixed_files:
                    fixed_results.append(result)
                else:
                    unfixed_results.append(result)

        # Handle other code style issues
        for check_id, check_results in results_by_check.items():
            if check_id not in ["black", "isort", "line_endings"]:
                unfixed_results.extend(check_results)

        return fixed_results, unfixed_results