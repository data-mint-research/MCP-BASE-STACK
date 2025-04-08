"""
Fix Verification

This module provides functionality for verifying fixes, including:
- Verifying fixes don't introduce new issues
- Validating fix results
- Rolling back if verification fails
- Integration with the fix workflow

This ensures that fixes are safe and effective.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

from core.quality.components.base import QualityCheckResult, QualityCheckSeverity


class FixVerification:
    """Provides functionality for verifying fixes."""

    def __init__(self):
        """Initialize the fix verification."""
        self.backup_files: Dict[str, str] = {}

    def backup_file(self, file_path: str) -> bool:
        """
        Create a backup of a file before applying fixes.

        Args:
            file_path: Path to the file.

        Returns:
            True if backup was successful, False otherwise.
        """
        if not os.path.exists(file_path):
            return False

        try:
            # Create a temporary file for the backup
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
                with open(file_path, "r", encoding="utf-8", errors="replace") as original_file:
                    temp_file.write(original_file.read())
                self.backup_files[file_path] = temp_file.name
            return True
        except Exception:
            return False

    def restore_file(self, file_path: str) -> bool:
        """
        Restore a file from backup.

        Args:
            file_path: Path to the file.

        Returns:
            True if restore was successful, False otherwise.
        """
        if file_path not in self.backup_files:
            return False

        try:
            backup_path = self.backup_files[file_path]
            shutil.copy2(backup_path, file_path)
            os.unlink(backup_path)
            del self.backup_files[file_path]
            return True
        except Exception:
            return False

    def cleanup_backups(self) -> None:
        """Clean up all backup files."""
        for file_path, backup_path in self.backup_files.items():
            try:
                os.unlink(backup_path)
            except Exception:
                pass
        self.backup_files.clear()

    def verify_fixes(self, file_path: str, original_results: List[QualityCheckResult], 
                    run_checks_func: callable) -> Tuple[bool, List[QualityCheckResult]]:
        """
        Verify that fixes don't introduce new issues.

        Args:
            file_path: Path to the file.
            original_results: Original QualityCheckResult objects before fixes.
            run_checks_func: Function to run checks on the file.

        Returns:
            Tuple of (success, new_results)
        """
        if not os.path.exists(file_path):
            return False, []

        # Run checks on the fixed file
        new_results = run_checks_func([file_path])

        # Check if any new issues were introduced
        original_issues = set()
        for result in original_results:
            if result.file_path == file_path:
                key = (result.check_id, result.message, result.line_number)
                original_issues.add(key)

        new_issues = set()
        for result in new_results:
            if result.file_path == file_path:
                key = (result.check_id, result.message, result.line_number)
                new_issues.add(key)

        # If there are new issues that weren't in the original results
        introduced_issues = new_issues - original_issues
        if introduced_issues:
            return False, [r for r in new_results if (r.check_id, r.message, r.line_number) in introduced_issues]

        return True, new_results

    def validate_fix_results(self, file_path: str, fixed_results: List[QualityCheckResult], 
                           run_checks_func: callable) -> Tuple[bool, List[QualityCheckResult]]:
        """
        Validate that fixes resolved the issues they were supposed to.

        Args:
            file_path: Path to the file.
            fixed_results: QualityCheckResult objects that were fixed.
            run_checks_func: Function to run checks on the file.

        Returns:
            Tuple of (success, remaining_results)
        """
        if not os.path.exists(file_path):
            return False, []

        # Run checks on the fixed file
        new_results = run_checks_func([file_path])

        # Check if the fixed issues are still present
        fixed_issues = set()
        for result in fixed_results:
            if result.file_path == file_path:
                key = (result.check_id, result.message, result.line_number)
                fixed_issues.add(key)

        remaining_issues = []
        for result in new_results:
            if result.file_path == file_path:
                key = (result.check_id, result.message, result.line_number)
                if key in fixed_issues:
                    remaining_issues.append(result)

        if remaining_issues:
            return False, remaining_issues

        return True, []

    def apply_with_verification(self, file_path: str, results: List[QualityCheckResult], 
                              apply_fixes_func: callable, run_checks_func: callable) -> Tuple[bool, List[QualityCheckResult], List[QualityCheckResult]]:
        """
        Apply fixes with verification and rollback if needed.

        Args:
            file_path: Path to the file.
            results: QualityCheckResult objects to fix.
            apply_fixes_func: Function to apply fixes.
            run_checks_func: Function to run checks on the file.

        Returns:
            Tuple of (success, fixed_results, unfixed_results)
        """
        if not os.path.exists(file_path):
            return False, [], results

        # Backup the file
        if not self.backup_file(file_path):
            return False, [], results

        try:
            # Apply fixes
            fixed_results, unfixed_results = apply_fixes_func(results)

            # Verify fixes
            verification_success, new_issues = self.verify_fixes(file_path, results, run_checks_func)
            if not verification_success:
                # Rollback if verification fails
                self.restore_file(file_path)
                return False, [], results

            # Validate fix results
            validation_success, remaining_issues = self.validate_fix_results(file_path, fixed_results, run_checks_func)
            if not validation_success:
                # Some issues weren't fixed properly
                # We'll keep the changes but report the issues that weren't fixed
                unfixed_results.extend(remaining_issues)
                return True, [r for r in fixed_results if r not in remaining_issues], unfixed_results

            return True, fixed_results, unfixed_results
        except Exception as e:
            # Rollback if an exception occurs
            self.restore_file(file_path)
            return False, [], results
        finally:
            # Clean up the backup
            self.cleanup_backups()


def verify_and_apply_fixes(file_path: str, results: List[QualityCheckResult], 
                         apply_fixes_func: callable, run_checks_func: callable) -> Tuple[bool, List[QualityCheckResult], List[QualityCheckResult]]:
    """
    Verify and apply fixes to a file.

    Args:
        file_path: Path to the file.
        results: QualityCheckResult objects to fix.
        apply_fixes_func: Function to apply fixes.
        run_checks_func: Function to run checks on the file.

    Returns:
        Tuple of (success, fixed_results, unfixed_results)
    """
    verification = FixVerification()
    return verification.apply_with_verification(file_path, results, apply_fixes_func, run_checks_func)