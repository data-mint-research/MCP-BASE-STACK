"""
Static Analysis Quality Component

This module provides quality checks for static code analysis, including:
- mypy (Python type checker)
- pylint (Python linter)
- flake8 (Python linter)

These checks help identify potential bugs, code smells, and other issues
through static analysis of the code.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from core.quality.components.base import (
    QualityCheck,
    QualityCheckResult,
    QualityCheckSeverity,
    QualityComponent
)


class MypyCheck(QualityCheck):
    """Check Python type annotations using mypy."""
    
    @property
    def id(self) -> str:
        return "mypy"
    
    @property
    def name(self) -> str:
        return "Type Checker"
    
    @property
    def description(self) -> str:
        return "Checks Python type annotations using mypy."
    
    def run(self, file_paths: Optional[List[str]] = None, **kwargs) -> List[QualityCheckResult]:
        """
        Run mypy to check Python type annotations.
        
        Args:
            file_paths: Optional list of Python file paths to check.
                If None, check all Python files.
            **kwargs: Additional arguments for mypy.
            
        Returns:
            List of QualityCheckResult objects.
        """
        results = []
        
        # If no file paths provided, use all Python files
        if not file_paths:
            file_paths = self._find_python_files()
        else:
            # Filter for Python files
            file_paths = [f for f in file_paths if f.endswith('.py')]
        
        if not file_paths:
            return results
        
        # Run mypy
        cmd = ["mypy"] + file_paths
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        # Parse mypy output
        for line in process.stdout.splitlines():
            # mypy output format: file:line: error: message
            match = re.match(r'(.+?):(\d+): (\w+): (.+)', line)
            if match:
                file_path, line_num, error_type, message = match.groups()
                
                # Determine severity based on error type
                severity = QualityCheckSeverity.ERROR
                if error_type == "note":
                    severity = QualityCheckSeverity.INFO
                elif error_type == "warning":
                    severity = QualityCheckSeverity.WARNING
                
                results.append(QualityCheckResult(
                    check_id=self.id,
                    severity=severity,
                    message=message,
                    file_path=file_path,
                    line_number=int(line_num),
                    source=self.name
                ))
        
        return results
    
    def _find_python_files(self) -> List[str]:
        """Find all Python files in the project."""
        python_files = []
        for root, _, files in os.walk("."):
            if any(excluded in root for excluded in ["/venv/", "/.git/", "/node_modules/"]):
                continue
            for file in files:
                if file.endswith(".py"):
                    python_files.append(os.path.join(root, file))
        return python_files


class PylintCheck(QualityCheck):
    """Check Python code quality using pylint."""
    
    @property
    def id(self) -> str:
        return "pylint"
    
    @property
    def name(self) -> str:
        return "Pylint Linter"
    
    @property
    def description(self) -> str:
        return "Checks Python code quality using pylint."
    
    def run(self, file_paths: Optional[List[str]] = None, **kwargs) -> List[QualityCheckResult]:
        """
        Run pylint to check Python code quality.
        
        Args:
            file_paths: Optional list of Python file paths to check.
                If None, check all Python files.
            **kwargs: Additional arguments for pylint.
            
        Returns:
            List of QualityCheckResult objects.
        """
        results = []
        
        # If no file paths provided, use all Python files
        if not file_paths:
            file_paths = self._find_python_files()
        else:
            # Filter for Python files
            file_paths = [f for f in file_paths if f.endswith('.py')]
        
        if not file_paths:
            return results
        
        # Run pylint
        cmd = ["pylint", "--output-format=text"] + file_paths
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        # Parse pylint output
        for line in process.stdout.splitlines():
            # pylint output format: file:line:column: [message_type/message_id] message
            match = re.match(r'(.+?):(\d+):(\d+): \[(\w+)/(\w+)\] (.+)', line)
            if match:
                file_path, line_num, col_num, msg_type, msg_id, message = match.groups()
                
                # Determine severity based on message type
                severity = QualityCheckSeverity.WARNING
                if msg_type in ["error", "fatal"]:
                    severity = QualityCheckSeverity.ERROR
                elif msg_type == "convention":
                    severity = QualityCheckSeverity.INFO
                
                results.append(QualityCheckResult(
                    check_id=self.id,
                    severity=severity,
                    message=f"{message} ({msg_id})",
                    file_path=file_path,
                    line_number=int(line_num),
                    column=int(col_num),
                    source=self.name,
                    details={"message_type": msg_type, "message_id": msg_id}
                ))
        
        return results
    
    def _find_python_files(self) -> List[str]:
        """Find all Python files in the project."""
        python_files = []
        for root, _, files in os.walk("."):
            if any(excluded in root for excluded in ["/venv/", "/.git/", "/node_modules/"]):
                continue
            for file in files:
                if file.endswith(".py"):
                    python_files.append(os.path.join(root, file))
        return python_files


class Flake8Check(QualityCheck):
    """Check Python code style using flake8."""
    
    @property
    def id(self) -> str:
        return "flake8"
    
    @property
    def name(self) -> str:
        return "Flake8 Linter"
    
    @property
    def description(self) -> str:
        return "Checks Python code style using flake8."
    
    def run(self, file_paths: Optional[List[str]] = None, **kwargs) -> List[QualityCheckResult]:
        """
        Run flake8 to check Python code style.
        
        Args:
            file_paths: Optional list of Python file paths to check.
                If None, check all Python files.
            **kwargs: Additional arguments for flake8.
            
        Returns:
            List of QualityCheckResult objects.
        """
        results = []
        
        # If no file paths provided, use all Python files
        if not file_paths:
            file_paths = self._find_python_files()
        else:
            # Filter for Python files
            file_paths = [f for f in file_paths if f.endswith('.py')]
        
        if not file_paths:
            return results
        
        # Run flake8
        cmd = ["flake8"] + file_paths
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        # Parse flake8 output
        for line in process.stdout.splitlines():
            # flake8 output format: file:line:column: error_code message
            match = re.match(r'(.+?):(\d+):(\d+): (\w+) (.+)', line)
            if match:
                file_path, line_num, col_num, error_code, message = match.groups()
                
                # Determine severity based on error code
                severity = QualityCheckSeverity.WARNING
                if error_code.startswith("F"):  # Flake8 errors
                    severity = QualityCheckSeverity.ERROR
                elif error_code.startswith("E"):  # PEP8 errors
                    severity = QualityCheckSeverity.WARNING
                elif error_code.startswith("W"):  # PEP8 warnings
                    severity = QualityCheckSeverity.INFO
                
                results.append(QualityCheckResult(
                    check_id=self.id,
                    severity=severity,
                    message=f"{message} ({error_code})",
                    file_path=file_path,
                    line_number=int(line_num),
                    column=int(col_num),
                    source=self.name,
                    details={"error_code": error_code}
                ))
        
        return results
    
    def _find_python_files(self) -> List[str]:
        """Find all Python files in the project."""
        python_files = []
        for root, _, files in os.walk("."):
            if any(excluded in root for excluded in ["/venv/", "/.git/", "/node_modules/"]):
                continue
            for file in files:
                if file.endswith(".py"):
                    python_files.append(os.path.join(root, file))
        return python_files


class ShellcheckCheck(QualityCheck):
    """Check shell scripts using shellcheck."""
    
    @property
    def id(self) -> str:
        return "shellcheck"
    
    @property
    def name(self) -> str:
        return "Shellcheck Linter"
    
    @property
    def description(self) -> str:
        return "Checks shell scripts using shellcheck."
    
    def run(self, file_paths: Optional[List[str]] = None, **kwargs) -> List[QualityCheckResult]:
        """
        Run shellcheck to check shell scripts.
        
        Args:
            file_paths: Optional list of shell script paths to check.
                If None, check all shell scripts.
            **kwargs: Additional arguments for shellcheck.
            
        Returns:
            List of QualityCheckResult objects.
        """
        results = []
        
        # If no file paths provided, use all shell scripts
        if not file_paths:
            file_paths = self._find_shell_scripts()
        else:
            # Filter for shell scripts
            file_paths = [f for f in file_paths if f.endswith('.sh')]
        
        if not file_paths:
            return results
        
        # Run shellcheck
        cmd = ["shellcheck", "--format=gcc"] + file_paths
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        # Parse shellcheck output
        for line in process.stderr.splitlines():
            # shellcheck output format: file:line:column: [severity]: message [SC####]
            match = re.match(r'(.+?):(\d+):(\d+): (\w+): (.+) \[SC(\d+)\]', line)
            if match:
                file_path, line_num, col_num, severity_str, message, sc_code = match.groups()
                
                # Determine severity
                severity = QualityCheckSeverity.WARNING
                if severity_str.lower() == "error":
                    severity = QualityCheckSeverity.ERROR
                elif severity_str.lower() == "warning":
                    severity = QualityCheckSeverity.WARNING
                elif severity_str.lower() == "info":
                    severity = QualityCheckSeverity.INFO
                
                results.append(QualityCheckResult(
                    check_id=self.id,
                    severity=severity,
                    message=f"{message} (SC{sc_code})",
                    file_path=file_path,
                    line_number=int(line_num),
                    column=int(col_num),
                    source=self.name,
                    details={"sc_code": sc_code}
                ))
        
        return results
    
    def _find_shell_scripts(self) -> List[str]:
        """Find all shell scripts in the project."""
        shell_scripts = []
        for root, _, files in os.walk("."):
            if any(excluded in root for excluded in ["/venv/", "/.git/", "/node_modules/"]):
                continue
            for file in files:
                if file.endswith(".sh"):
                    shell_scripts.append(os.path.join(root, file))
        return shell_scripts


class StaticAnalysisComponent(QualityComponent):
    """Component for static analysis quality checks."""
    
    @property
    def name(self) -> str:
        return "Static Analysis"
    
    @property
    def description(self) -> str:
        return "Performs static analysis of code to identify potential issues."
    
    def _initialize_checks(self) -> None:
        """Initialize the static analysis checks."""
        self._checks = [
            MypyCheck(),
            PylintCheck(),
            Flake8Check(),
            ShellcheckCheck()
        ]