"""
Documentation Quality Component

This module provides quality checks for documentation, including:
- Docstring presence and completeness
- README presence and completeness
- Documentation coverage
- Documentation formatting

These checks ensure that code is properly documented and that documentation
follows consistent standards.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from core.quality.components.base import (
    QualityCheck,
    QualityCheckResult,
    QualityCheckSeverity,
    QualityComponent
)


class DocstringCheck(QualityCheck):
    """Check for presence and completeness of docstrings."""
    
    @property
    def id(self) -> str:
        return "docstrings"
    
    @property
    def name(self) -> str:
        return "Docstring Checker"
    
    @property
    def description(self) -> str:
        return "Checks for presence and completeness of docstrings in Python files."
    
    def run(self, file_paths: Optional[List[str]] = None, **kwargs) -> List[QualityCheckResult]:
        """
        Check for presence and completeness of docstrings.
        
        Args:
            file_paths: Optional list of Python file paths to check.
                If None, check all Python files.
            **kwargs: Additional arguments.
            
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
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Check for module docstring
                if not self._has_module_docstring(content):
                    results.append(QualityCheckResult(
                        check_id=self.id,
                        severity=self.severity,
                        message="Missing module docstring",
                        file_path=file_path,
                        line_number=1,
                        source=self.name
                    ))
                
                # Check for class and function docstrings
                class_matches = re.finditer(r'class\s+(\w+)\s*(?:\([^)]*\))?\s*:', content)
                for match in class_matches:
                    class_name = match.group(1)
                    class_start = match.start()
                    line_number = content[:class_start].count('\n') + 1
                    
                    if not self._has_docstring_after(content, match.end()):
                        results.append(QualityCheckResult(
                            check_id=self.id,
                            severity=self.severity,
                            message=f"Missing docstring for class {class_name}",
                            file_path=file_path,
                            line_number=line_number,
                            source=self.name
                        ))
                
                # Check for function docstrings (both regular and methods)
                func_matches = re.finditer(r'def\s+(\w+)\s*\([^)]*\)\s*(?:->.*?)?\s*:', content)
                for match in func_matches:
                    func_name = match.group(1)
                    func_start = match.start()
                    line_number = content[:func_start].count('\n') + 1
                    
                    # Skip dunder methods and private methods
                    if func_name.startswith('__') or (func_name.startswith('_') and not func_name.startswith('__')):
                        continue
                    
                    if not self._has_docstring_after(content, match.end()):
                        results.append(QualityCheckResult(
                            check_id=self.id,
                            severity=self.severity,
                            message=f"Missing docstring for function/method {func_name}",
                            file_path=file_path,
                            line_number=line_number,
                            source=self.name
                        ))
            
            except Exception as e:
                results.append(QualityCheckResult(
                    check_id=self.id,
                    severity=QualityCheckSeverity.ERROR,
                    message=f"Error checking docstrings: {str(e)}",
                    file_path=file_path,
                    source=self.name
                ))
        
        return results
    
    def _has_module_docstring(self, content: str) -> bool:
        """Check if a module has a docstring."""
        # Skip any shebang or encoding declarations
        content = re.sub(r'^#!.*?\n', '', content)
        content = re.sub(r'^#.*?coding[:=].*?\n', '', content)
        content = content.lstrip()
        
        # Check for triple-quoted string at the beginning
        return bool(re.match(r'(\'\'\'|""").*?(\'\'\'|""")', content, re.DOTALL))
    
    def _has_docstring_after(self, content: str, pos: int) -> bool:
        """Check if there's a docstring after the given position."""
        # Find the next non-whitespace character
        match = re.search(r'\S', content[pos:])
        if not match:
            return False
        
        # Check if it's the start of a triple-quoted string
        start_pos = pos + match.start()
        return bool(re.match(r'(\'\'\'|""").*?(\'\'\'|""")', content[start_pos:], re.DOTALL))
    
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


class ReadmeCheck(QualityCheck):
    """Check for presence and completeness of README files."""
    
    @property
    def id(self) -> str:
        return "readme"
    
    @property
    def name(self) -> str:
        return "README Checker"
    
    @property
    def description(self) -> str:
        return "Checks for presence and completeness of README files in directories."
    
    def run(self, file_paths: Optional[List[str]] = None, **kwargs) -> List[QualityCheckResult]:
        """
        Check for presence and completeness of README files.
        
        Args:
            file_paths: Optional list of directory paths to check.
                If None, check all directories.
            **kwargs: Additional arguments.
            
        Returns:
            List of QualityCheckResult objects.
        """
        results = []
        
        # Get directories to check
        if file_paths:
            dirs_to_check = [path for path in file_paths if os.path.isdir(path)]
        else:
            dirs_to_check = self._find_important_directories()
        
        for dir_path in dirs_to_check:
            # Check if README exists
            readme_path = None
            for readme_name in ["README.md", "README.rst", "README.txt", "README"]:
                potential_path = os.path.join(dir_path, readme_name)
                if os.path.exists(potential_path):
                    readme_path = potential_path
                    break
            
            if not readme_path:
                results.append(QualityCheckResult(
                    check_id=self.id,
                    severity=self.severity,
                    message=f"Missing README file in directory",
                    file_path=dir_path,
                    source=self.name
                ))
                continue
            
            # Check README content
            try:
                with open(readme_path, 'r') as f:
                    content = f.read()
                
                # Check for minimum content length
                if len(content) < 100:
                    results.append(QualityCheckResult(
                        check_id=self.id,
                        severity=self.severity,
                        message=f"README is too short (less than 100 characters)",
                        file_path=readme_path,
                        source=self.name
                    ))
                
                # Check for headings in markdown
                if readme_path.endswith(".md") and not re.search(r'^#\s+\w+', content, re.MULTILINE):
                    results.append(QualityCheckResult(
                        check_id=self.id,
                        severity=self.severity,
                        message=f"README is missing headings (# Title)",
                        file_path=readme_path,
                        source=self.name
                    ))
            
            except Exception as e:
                results.append(QualityCheckResult(
                    check_id=self.id,
                    severity=QualityCheckSeverity.ERROR,
                    message=f"Error checking README: {str(e)}",
                    file_path=readme_path,
                    source=self.name
                ))
        
        return results
    
    def _find_important_directories(self) -> List[str]:
        """Find important directories that should have README files."""
        important_dirs = ["."]  # Root directory
        
        # Add top-level directories
        for item in os.listdir("."):
            if os.path.isdir(item) and not item.startswith(".") and item not in ["venv", "node_modules"]:
                important_dirs.append(item)
        
        return important_dirs


class DocumentationCoverageCheck(QualityCheck):
    """Check for documentation coverage."""
    
    @property
    def id(self) -> str:
        return "doc_coverage"
    
    @property
    def name(self) -> str:
        return "Documentation Coverage Checker"
    
    @property
    def description(self) -> str:
        return "Checks for documentation coverage in the project."
    
    def run(self, file_paths: Optional[List[str]] = None, **kwargs) -> List[QualityCheckResult]:
        """
        Check for documentation coverage.
        
        Args:
            file_paths: Optional list of file paths to check.
                If None, check all relevant files.
            **kwargs: Additional arguments.
            
        Returns:
            List of QualityCheckResult objects.
        """
        results = []
        
        # Get directories to check
        if file_paths:
            dirs_to_check = set()
            for path in file_paths:
                if os.path.isdir(path):
                    dirs_to_check.add(path)
                else:
                    dirs_to_check.add(os.path.dirname(path))
        else:
            dirs_to_check = self._find_code_directories()
        
        for dir_path in dirs_to_check:
            # Skip if it's not a code directory
            if not self._is_code_directory(dir_path):
                continue
            
            # Check if documentation exists for this directory
            doc_exists = self._has_documentation(dir_path)
            
            if not doc_exists:
                results.append(QualityCheckResult(
                    check_id=self.id,
                    severity=self.severity,
                    message=f"Missing documentation for code directory",
                    file_path=dir_path,
                    source=self.name
                ))
        
        return results
    
    def _find_code_directories(self) -> Set[str]:
        """Find directories containing code."""
        code_dirs = set()
        for root, _, files in os.walk("."):
            if any(excluded in root for excluded in ["/venv/", "/.git/", "/node_modules/"]):
                continue
            
            # Check if directory contains code files
            if any(f.endswith((".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".hpp")) for f in files):
                code_dirs.add(root)
        
        return code_dirs
    
    def _is_code_directory(self, dir_path: str) -> bool:
        """Check if a directory contains code files."""
        for _, _, files in os.walk(dir_path):
            if any(f.endswith((".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".hpp")) for f in files):
                return True
        return False
    
    def _has_documentation(self, dir_path: str) -> bool:
        """Check if documentation exists for a directory."""
        # Check for README
        for readme_name in ["README.md", "README.rst", "README.txt", "README"]:
            if os.path.exists(os.path.join(dir_path, readme_name)):
                return True
        
        # Check for docs directory
        docs_dir = os.path.join(dir_path, "docs")
        if os.path.exists(docs_dir) and os.path.isdir(docs_dir):
            return True
        
        # Check for documentation in parent directory
        parent_dir = os.path.dirname(dir_path)
        if parent_dir and parent_dir != dir_path:
            docs_dir = os.path.join(parent_dir, "docs")
            if os.path.exists(docs_dir) and os.path.isdir(docs_dir):
                return True
        
        return False


class DocumentationComponent(QualityComponent):
    """Component for documentation quality checks."""
    
    @property
    def name(self) -> str:
        return "Documentation"
    
    @property
    def description(self) -> str:
        return "Checks for documentation quality and coverage."
    
    def _initialize_checks(self) -> None:
        """Initialize the documentation checks."""
        # Import here to avoid circular imports
        from core.quality.components.documentation_coverage import EnhancedDocumentationCoverageCheck
        
        self._checks = [
            DocstringCheck(),
            ReadmeCheck(),
            DocumentationCoverageCheck(),
            EnhancedDocumentationCoverageCheck()
        ]