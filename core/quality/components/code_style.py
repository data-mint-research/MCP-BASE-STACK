"""
Code Style Quality Component

This module provides quality checks for code style, including:
- Black (Python formatter)
- isort (Python import sorter)
- Formatting consistency checks

These checks ensure that code follows consistent formatting standards.
"""

import os
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

from core.quality.components.base import (
    QualityCheck,
    QualityCheckResult,
    QualityCheckSeverity,
    QualityComponent
)


class BlackCheck(QualityCheck):
    """Check Python code formatting using Black."""
    
    @property
    def id(self) -> str:
        return "black"
    
    @property
    def name(self) -> str:
        return "Black Formatter"
    
    @property
    def description(self) -> str:
        return "Checks Python code formatting using Black."
    
    def can_fix(self) -> bool:
        return True
    
    def run(self, file_paths: Optional[List[str]] = None, **kwargs) -> List[QualityCheckResult]:
        """
        Run Black to check Python code formatting.
        
        Args:
            file_paths: Optional list of Python file paths to check.
                If None, check all Python files.
            **kwargs: Additional arguments for Black.
            
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
        
        # Run Black in check mode
        cmd = ["black", "--check"] + file_paths
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        if process.returncode != 0:
            # Parse Black output to extract file paths and line numbers
            for line in process.stderr.splitlines() + process.stdout.splitlines():
                if "would reformat" in line:
                    file_path = line.split("would reformat", 1)[1].strip()
                    results.append(QualityCheckResult(
                        check_id=self.id,
                        severity=self.severity,
                        message="File needs reformatting with Black",
                        file_path=file_path,
                        source=self.name,
                        fix_available=True,
                        fix_command=f"black {file_path}"
                    ))
        
        return results
    
    def fix(self, results: List[QualityCheckResult]) -> List[QualityCheckResult]:
        """
        Fix formatting issues using Black.
        
        Args:
            results: List of QualityCheckResult objects to fix.
            
        Returns:
            List of QualityCheckResult objects that couldn't be fixed.
        """
        unfixed = []
        file_paths = set()
        
        # Collect unique file paths
        for result in results:
            if result.check_id == self.id and result.file_path:
                file_paths.add(result.file_path)
        
        if not file_paths:
            return results
        
        # Run Black to fix formatting
        cmd = ["black"] + list(file_paths)
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        if process.returncode != 0:
            # If Black failed, return all results as unfixed
            return results
        
        # Check which files were actually fixed
        fixed_files = set()
        for line in process.stderr.splitlines() + process.stdout.splitlines():
            if "reformatted" in line:
                file_path = line.split("reformatted", 1)[1].strip()
                fixed_files.add(file_path)
        
        # Return results for files that weren't fixed
        for result in results:
            if result.check_id == self.id and result.file_path not in fixed_files:
                unfixed.append(result)
        
        return unfixed
    
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


class IsortCheck(QualityCheck):
    """Check Python import sorting using isort."""
    
    @property
    def id(self) -> str:
        return "isort"
    
    @property
    def name(self) -> str:
        return "Import Sorter"
    
    @property
    def description(self) -> str:
        return "Checks Python import sorting using isort."
    
    def can_fix(self) -> bool:
        return True
    
    def run(self, file_paths: Optional[List[str]] = None, **kwargs) -> List[QualityCheckResult]:
        """
        Run isort to check Python import sorting.
        
        Args:
            file_paths: Optional list of Python file paths to check.
                If None, check all Python files.
            **kwargs: Additional arguments for isort.
            
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
        
        # Run isort in check mode
        cmd = ["isort", "--check-only"] + file_paths
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        if process.returncode != 0:
            # Parse isort output to extract file paths
            for line in process.stderr.splitlines() + process.stdout.splitlines():
                if "ERROR" in line and ".py" in line:
                    parts = line.split("ERROR", 1)[1].strip().split(" ", 1)
                    if len(parts) > 0:
                        file_path = parts[0].strip()
                        results.append(QualityCheckResult(
                            check_id=self.id,
                            severity=self.severity,
                            message="Imports need sorting with isort",
                            file_path=file_path,
                            source=self.name,
                            fix_available=True,
                            fix_command=f"isort {file_path}"
                        ))
        
        return results
    
    def fix(self, results: List[QualityCheckResult]) -> List[QualityCheckResult]:
        """
        Fix import sorting issues using isort.
        
        Args:
            results: List of QualityCheckResult objects to fix.
            
        Returns:
            List of QualityCheckResult objects that couldn't be fixed.
        """
        unfixed = []
        file_paths = set()
        
        # Collect unique file paths
        for result in results:
            if result.check_id == self.id and result.file_path:
                file_paths.add(result.file_path)
        
        if not file_paths:
            return results
        
        # Run isort to fix import sorting
        cmd = ["isort"] + list(file_paths)
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        if process.returncode != 0:
            # If isort failed, return all results as unfixed
            return results
        
        # Assume all files were fixed if isort succeeded
        return []
    
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


class LineEndingCheck(QualityCheck):
    """Check for consistent line endings."""
    
    @property
    def id(self) -> str:
        return "line_endings"
    
    @property
    def name(self) -> str:
        return "Line Ending Checker"
    
    @property
    def description(self) -> str:
        return "Checks for consistent line endings (CRLF vs LF)."
    
    def run(self, file_paths: Optional[List[str]] = None, **kwargs) -> List[QualityCheckResult]:
        """
        Check for consistent line endings.
        
        Args:
            file_paths: Optional list of file paths to check.
                If None, check all text files.
            **kwargs: Additional arguments.
            
        Returns:
            List of QualityCheckResult objects.
        """
        results = []
        
        # If no file paths provided, find all text files
        if not file_paths:
            file_paths = self._find_text_files()
        
        if not file_paths:
            return results
        
        for file_path in file_paths:
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                crlf_count = content.count(b'\r\n')
                lf_count = content.count(b'\n') - crlf_count
                
                # If mixed line endings
                if crlf_count > 0 and lf_count > 0:
                    results.append(QualityCheckResult(
                        check_id=self.id,
                        severity=self.severity,
                        message=f"Mixed line endings: {crlf_count} CRLF, {lf_count} LF",
                        file_path=file_path,
                        source=self.name
                    ))
            except Exception as e:
                results.append(QualityCheckResult(
                    check_id=self.id,
                    severity=QualityCheckSeverity.ERROR,
                    message=f"Error checking line endings: {str(e)}",
                    file_path=file_path,
                    source=self.name
                ))
        
        return results
    
    def _find_text_files(self) -> List[str]:
        """Find all text files in the project."""
        text_extensions = ['.py', '.js', '.ts', '.html', '.css', '.md', '.txt', '.json', '.yml', '.yaml', '.sh']
        text_files = []
        for root, _, files in os.walk("."):
            if any(excluded in root for excluded in ["/venv/", "/.git/", "/node_modules/"]):
                continue
            for file in files:
                if any(file.endswith(ext) for ext in text_extensions):
                    text_files.append(os.path.join(root, file))
        return text_files


class CodeStyleComponent(QualityComponent):
    """Component for code style quality checks."""
    
    @property
    def name(self) -> str:
        return "Code Style"
    
    @property
    def description(self) -> str:
        return "Checks for code style and formatting consistency."
    
    def _initialize_checks(self) -> None:
        """Initialize the code style checks."""
        self._checks = [
            BlackCheck(),
            IsortCheck(),
            LineEndingCheck()
        ]