"""
Static Analysis Fixes

This module provides auto-fix capabilities for static analysis issues, including:
- Linting errors (flake8, pylint)
- Type annotation issues (mypy)
- Security vulnerabilities
- Performance optimizations

These fixes can be applied automatically or interactively.
"""

import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

from core.quality.components.base import QualityCheckResult, QualityCheckSeverity


class StaticAnalysisFixes:
    """Provides auto-fix capabilities for static analysis issues."""

    @staticmethod
    def fix_flake8_issues(file_path: str) -> Tuple[bool, List[str], List[str]]:
        """
        Fix flake8 issues in a Python file using autopep8.

        Args:
            file_path: Path to the Python file.

        Returns:
            Tuple of (success, fixed_issues, unfixed_issues)
        """
        try:
            # First, get the list of flake8 issues
            cmd = ["flake8", file_path]
            process = subprocess.run(cmd, capture_output=True, text=True)
            
            if process.returncode == 0:
                # No issues found
                return True, [], []
            
            # Parse the flake8 output to get the list of issues
            issues = []
            for line in process.stdout.splitlines():
                if ":" in line:
                    issues.append(line.strip())
            
            # Run autopep8 to fix the issues
            cmd = ["autopep8", "--in-place", "--aggressive", "--aggressive", file_path]
            process = subprocess.run(cmd, capture_output=True, text=True)
            
            if process.returncode != 0:
                return False, [], issues
            
            # Check which issues were fixed
            cmd = ["flake8", file_path]
            process = subprocess.run(cmd, capture_output=True, text=True)
            
            if process.returncode == 0:
                # All issues fixed
                return True, issues, []
            
            # Some issues remain
            remaining_issues = []
            for line in process.stdout.splitlines():
                if ":" in line:
                    remaining_issues.append(line.strip())
            
            fixed_issues = [issue for issue in issues if issue not in remaining_issues]
            
            return True, fixed_issues, remaining_issues
        except Exception as e:
            return False, [], [str(e)]

    @staticmethod
    def fix_pylint_issues(file_path: str) -> Tuple[bool, List[str], List[str]]:
        """
        Fix pylint issues in a Python file.

        Args:
            file_path: Path to the Python file.

        Returns:
            Tuple of (success, fixed_issues, unfixed_issues)
        """
        try:
            # First, get the list of pylint issues
            cmd = ["pylint", "--output-format=text", file_path]
            process = subprocess.run(cmd, capture_output=True, text=True)
            
            if "Your code has been rated at 10.00/10" in process.stdout:
                # No issues found
                return True, [], []
            
            # Parse the pylint output to get the list of issues
            issues = []
            for line in process.stdout.splitlines():
                if ":" in line and any(code in line for code in ["C", "W", "E", "F"]):
                    issues.append(line.strip())
            
            # Some issues can be fixed automatically
            fixed_issues = []
            unfixed_issues = []
            
            # Fix trailing whitespace
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            # Remove trailing whitespace
            modified = False
            for i, line in enumerate(lines):
                stripped = line.rstrip()
                if stripped + "\n" != line:
                    lines[i] = stripped + "\n"
                    modified = True
            
            if modified:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)
                fixed_issues.append("Fixed trailing whitespace")
            
            # Run autopep8 to fix some PEP8 issues
            cmd = ["autopep8", "--in-place", "--aggressive", file_path]
            process = subprocess.run(cmd, capture_output=True, text=True)
            
            if process.returncode == 0:
                fixed_issues.append("Fixed PEP8 issues with autopep8")
            
            # Check which issues were fixed
            cmd = ["pylint", "--output-format=text", file_path]
            process = subprocess.run(cmd, capture_output=True, text=True)
            
            remaining_issues = []
            for line in process.stdout.splitlines():
                if ":" in line and any(code in line for code in ["C", "W", "E", "F"]):
                    remaining_issues.append(line.strip())
            
            # Add remaining issues to unfixed_issues
            unfixed_issues.extend(remaining_issues)
            
            return True, fixed_issues, unfixed_issues
        except Exception as e:
            return False, [], [str(e)]

    @staticmethod
    def add_type_annotations(file_path: str) -> Tuple[bool, List[str], List[str]]:
        """
        Add type annotations to a Python file using MonkeyType.

        Args:
            file_path: Path to the Python file.

        Returns:
            Tuple of (success, fixed_issues, unfixed_issues)
        """
        try:
            # This is a simplified version that would use MonkeyType in a real implementation
            # MonkeyType requires running the code to collect types, which is beyond the scope
            # of this implementation
            
            # Instead, we'll add basic type annotations for simple cases
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Parse the Python file
            import ast
            tree = ast.parse(content)
            
            # Find functions without type annotations
            functions_to_annotate = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Check if function has type annotations
                    has_return_annotation = node.returns is not None
                    has_arg_annotations = all(arg.annotation is not None for arg in node.args.args)
                    
                    if not has_return_annotation or not has_arg_annotations:
                        functions_to_annotate.append((node.lineno, node.name))
            
            if not functions_to_annotate:
                return True, [], []
            
            # For demonstration purposes, we'll just report the functions that need annotations
            # In a real implementation, we would modify the AST and write it back
            fixed_issues = []
            unfixed_issues = [f"Function {name} at line {lineno} needs type annotations" 
                             for lineno, name in functions_to_annotate]
            
            return True, fixed_issues, unfixed_issues
        except Exception as e:
            return False, [], [str(e)]

    @staticmethod
    def fix_security_issues(file_path: str) -> Tuple[bool, List[str], List[str]]:
        """
        Fix security issues in a Python file using bandit.

        Args:
            file_path: Path to the Python file.

        Returns:
            Tuple of (success, fixed_issues, unfixed_issues)
        """
        try:
            # Run bandit to identify security issues
            cmd = ["bandit", "-r", file_path]
            process = subprocess.run(cmd, capture_output=True, text=True)
            
            if "No issues identified." in process.stdout:
                # No issues found
                return True, [], []
            
            # Parse the bandit output to get the list of issues
            issues = []
            for line in process.stdout.splitlines():
                if ">> Issue: " in line:
                    issues.append(line.strip())
            
            # Some security issues can be fixed automatically
            fixed_issues = []
            unfixed_issues = []
            
            # Read the file content
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            modified = False
            
            # Fix common security issues
            for i, line in enumerate(lines):
                # Fix hardcoded passwords
                if "password" in line.lower() and "=" in line and ("\"" in line or "'" in line):
                    # Replace hardcoded password with environment variable
                    var_name = "PASSWORD"
                    if "db_password" in line.lower():
                        var_name = "DB_PASSWORD"
                    elif "api_password" in line.lower():
                        var_name = "API_PASSWORD"
                    
                    new_line = re.sub(r"['\"]([^'\"]+)['\"]", f"os.environ.get('{var_name}')", line)
                    
                    # Add import os if not present
                    if "import os" not in "".join(lines):
                        lines.insert(0, "import os\n")
                        i += 1  # Adjust index after insertion
                    
                    lines[i] = new_line
                    modified = True
                    fixed_issues.append(f"Replaced hardcoded password with environment variable at line {i+1}")
                
                # Fix insecure use of pickle
                if "pickle.load" in line:
                    # Add a comment warning about pickle security
                    lines[i] = line.rstrip() + "  # SECURITY WARNING: pickle can execute arbitrary code\n"
                    unfixed_issues.append(f"Insecure use of pickle at line {i+1}")
            
            if modified:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)
            
            # Add remaining issues to unfixed_issues
            for issue in issues:
                if not any(fixed_issue in issue for fixed_issue in fixed_issues):
                    unfixed_issues.append(issue)
            
            return True, fixed_issues, unfixed_issues
        except Exception as e:
            return False, [], [str(e)]

    @staticmethod
    def apply_fixes(results: List[QualityCheckResult]) -> Tuple[List[QualityCheckResult], List[QualityCheckResult]]:
        """
        Apply fixes to static analysis issues.

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

        # Fix flake8 issues
        if "flake8" in results_by_check:
            flake8_results = results_by_check["flake8"]
            # Group by file path
            files_to_fix = set(r.file_path for r in flake8_results if r.file_path)
            
            for file_path in files_to_fix:
                success, fixed_issues, unfixed_issues = StaticAnalysisFixes.fix_flake8_issues(file_path)
                
                if success and fixed_issues:
                    # Mark results for this file as fixed
                    for result in flake8_results:
                        if result.file_path == file_path:
                            fixed_results.append(result)
                else:
                    # Mark results for this file as unfixed
                    for result in flake8_results:
                        if result.file_path == file_path:
                            unfixed_results.append(result)

        # Fix pylint issues
        if "pylint" in results_by_check:
            pylint_results = results_by_check["pylint"]
            # Group by file path
            files_to_fix = set(r.file_path for r in pylint_results if r.file_path)
            
            for file_path in files_to_fix:
                success, fixed_issues, unfixed_issues = StaticAnalysisFixes.fix_pylint_issues(file_path)
                
                if success and fixed_issues:
                    # Mark results for this file as fixed
                    for result in pylint_results:
                        if result.file_path == file_path:
                            fixed_results.append(result)
                else:
                    # Mark results for this file as unfixed
                    for result in pylint_results:
                        if result.file_path == file_path:
                            unfixed_results.append(result)

        # Fix mypy issues
        if "mypy" in results_by_check:
            mypy_results = results_by_check["mypy"]
            # Group by file path
            files_to_fix = set(r.file_path for r in mypy_results if r.file_path)
            
            for file_path in files_to_fix:
                success, fixed_issues, unfixed_issues = StaticAnalysisFixes.add_type_annotations(file_path)
                
                if success and fixed_issues:
                    # Mark results for this file as fixed
                    for result in mypy_results:
                        if result.file_path == file_path:
                            fixed_results.append(result)
                else:
                    # Mark results for this file as unfixed
                    for result in mypy_results:
                        if result.file_path == file_path:
                            unfixed_results.append(result)

        # Fix security issues
        if "security" in results_by_check:
            security_results = results_by_check["security"]
            # Group by file path
            files_to_fix = set(r.file_path for r in security_results if r.file_path)
            
            for file_path in files_to_fix:
                success, fixed_issues, unfixed_issues = StaticAnalysisFixes.fix_security_issues(file_path)
                
                if success and fixed_issues:
                    # Mark results for this file as fixed
                    for result in security_results:
                        if result.file_path == file_path:
                            fixed_results.append(result)
                else:
                    # Mark results for this file as unfixed
                    for result in security_results:
                        if result.file_path == file_path:
                            unfixed_results.append(result)

        # Handle other static analysis issues
        for check_id, check_results in results_by_check.items():
            if check_id not in ["flake8", "pylint", "mypy", "security"]:
                unfixed_results.extend(check_results)

        return fixed_results, unfixed_results