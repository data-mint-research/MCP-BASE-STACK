"""
Project Structure Quality Component

This module provides quality checks for project structure, including:
- Directory structure validation
- File naming conventions
- Import organization
- Dependency management

These checks ensure that the project follows consistent structural patterns
and organizational principles.
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


class DirectoryStructureCheck(QualityCheck):
    """Check for proper directory structure."""
    
    @property
    def id(self) -> str:
        return "directory_structure"
    
    @property
    def name(self) -> str:
        return "Directory Structure Checker"
    
    @property
    def description(self) -> str:
        return "Checks for proper directory structure in the project."
    
    def run(self, file_paths: Optional[List[str]] = None, **kwargs) -> List[QualityCheckResult]:
        """
        Check for proper directory structure.
        
        Args:
            file_paths: Optional list of directory paths to check.
                If None, check the entire project structure.
            **kwargs: Additional arguments.
            
        Returns:
            List of QualityCheckResult objects.
        """
        results = []
        
        # Define expected top-level directories
        expected_dirs = {
            "core": "Core application code",
            "tests": "Test files",
            "docs": "Documentation",
            "config": "Configuration files",
            "scripts": "Utility scripts"
        }
        
        # Check for expected top-level directories
        for dir_name, description in expected_dirs.items():
            if not os.path.exists(dir_name) or not os.path.isdir(dir_name):
                results.append(QualityCheckResult(
                    check_id=self.id,
                    severity=self.severity,
                    message=f"Missing expected top-level directory: {dir_name} ({description})",
                    file_path=".",
                    source=self.name
                ))
        
        # Check for tests directory structure
        if os.path.exists("tests") and os.path.isdir("tests"):
            # Check for unit and integration test directories
            for test_dir in ["unit", "integration"]:
                test_path = os.path.join("tests", test_dir)
                if not os.path.exists(test_path) or not os.path.isdir(test_path):
                    results.append(QualityCheckResult(
                        check_id=self.id,
                        severity=self.severity,
                        message=f"Missing expected test directory: {test_path}",
                        file_path="tests",
                        source=self.name
                    ))
        
        # Check for docs directory structure
        if os.path.exists("docs") and os.path.isdir("docs"):
            # Check for README.md in docs
            readme_path = os.path.join("docs", "README.md")
            if not os.path.exists(readme_path):
                results.append(QualityCheckResult(
                    check_id=self.id,
                    severity=self.severity,
                    message=f"Missing README.md in docs directory",
                    file_path="docs",
                    source=self.name
                ))
        
        return results


class FileNamingCheck(QualityCheck):
    """Check for consistent file naming conventions."""
    
    @property
    def id(self) -> str:
        return "file_naming"
    
    @property
    def name(self) -> str:
        return "File Naming Checker"
    
    @property
    def description(self) -> str:
        return "Checks for consistent file naming conventions."
    
    def run(self, file_paths: Optional[List[str]] = None, **kwargs) -> List[QualityCheckResult]:
        """
        Check for consistent file naming conventions.
        
        Args:
            file_paths: Optional list of file paths to check.
                If None, check all files.
            **kwargs: Additional arguments.
            
        Returns:
            List of QualityCheckResult objects.
        """
        results = []
        
        # If no file paths provided, find all files
        if not file_paths:
            file_paths = self._find_all_files()
        
        # Define naming conventions for different file types
        conventions = {
            ".py": r'^[a-z][a-z0-9_]*\.py$',  # snake_case for Python files
            ".js": r'^[a-z][a-zA-Z0-9]*\.js$',  # camelCase for JavaScript files
            ".ts": r'^[a-z][a-zA-Z0-9]*\.ts$',  # camelCase for TypeScript files
            ".jsx": r'^[A-Z][a-zA-Z0-9]*\.jsx$',  # PascalCase for React JSX files
            ".tsx": r'^[A-Z][a-zA-Z0-9]*\.tsx$',  # PascalCase for React TSX files
            ".md": r'^[A-Z][a-zA-Z0-9-]*\.md$',  # PascalCase or hyphenated for Markdown
            ".sh": r'^[a-z][a-z0-9_-]*\.sh$'  # lowercase with hyphens or underscores for shell scripts
        }
        
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            _, ext = os.path.splitext(file_name)
            
            if ext in conventions:
                pattern = conventions[ext]
                if not re.match(pattern, file_name):
                    results.append(QualityCheckResult(
                        check_id=self.id,
                        severity=self.severity,
                        message=f"File name does not follow naming convention for {ext} files",
                        file_path=file_path,
                        source=self.name,
                        details={"expected_pattern": pattern}
                    ))
        
        return results
    
    def _find_all_files(self) -> List[str]:
        """Find all files in the project."""
        all_files = []
        for root, _, files in os.walk("."):
            if any(excluded in root for excluded in ["/venv/", "/.git/", "/node_modules/"]):
                continue
            for file in files:
                all_files.append(os.path.join(root, file))
        return all_files


class ImportOrganizationCheck(QualityCheck):
    """Check for proper organization of imports in Python files."""
    
    @property
    def id(self) -> str:
        return "import_organization"
    
    @property
    def name(self) -> str:
        return "Import Organization Checker"
    
    @property
    def description(self) -> str:
        return "Checks for proper organization of imports in Python files."
    
    def run(self, file_paths: Optional[List[str]] = None, **kwargs) -> List[QualityCheckResult]:
        """
        Check for proper organization of imports in Python files.
        
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
                
                # Extract import statements
                import_lines = []
                for line_num, line in enumerate(content.splitlines(), 1):
                    if re.match(r'^\s*(import|from)\s+', line):
                        import_lines.append((line_num, line.strip()))
                
                if not import_lines:
                    continue
                
                # Check for grouping of imports
                groups = self._group_imports(import_lines)
                
                # Check for proper ordering within groups
                for group_name, group_imports in groups.items():
                    if len(group_imports) <= 1:
                        continue
                    
                    sorted_imports = sorted(group_imports, key=lambda x: x[1])
                    if group_imports != sorted_imports:
                        # Find the first out-of-order import
                        for i, ((line_num, line), (_, sorted_line)) in enumerate(zip(group_imports, sorted_imports)):
                            if line != sorted_line:
                                results.append(QualityCheckResult(
                                    check_id=self.id,
                                    severity=self.severity,
                                    message=f"Imports in {group_name} group are not alphabetically sorted",
                                    file_path=file_path,
                                    line_number=line_num,
                                    source=self.name
                                ))
                                break
                
                # Check for blank lines between import groups
                prev_line_num = None
                for i, (line_num, _) in enumerate(import_lines):
                    if prev_line_num is not None and line_num > prev_line_num + 1:
                        # There's a blank line, check if it's between different groups
                        prev_group = self._get_import_group(import_lines[i-1][1])
                        curr_group = self._get_import_group(import_lines[i][1])
                        
                        if prev_group == curr_group:
                            results.append(QualityCheckResult(
                                check_id=self.id,
                                severity=self.severity,
                                message=f"Unnecessary blank line between imports in the same group",
                                file_path=file_path,
                                line_number=prev_line_num + 1,
                                source=self.name
                            ))
                    
                    prev_line_num = line_num
            
            except Exception as e:
                results.append(QualityCheckResult(
                    check_id=self.id,
                    severity=QualityCheckSeverity.ERROR,
                    message=f"Error checking import organization: {str(e)}",
                    file_path=file_path,
                    source=self.name
                ))
        
        return results
    
    def _group_imports(self, import_lines: List[Tuple[int, str]]) -> Dict[str, List[Tuple[int, str]]]:
        """Group import statements by type."""
        groups = {
            "stdlib": [],
            "third-party": [],
            "local": []
        }
        
        for line_num, line in import_lines:
            group = self._get_import_group(line)
            groups[group].append((line_num, line))
        
        return groups
    
    def _get_import_group(self, import_line: str) -> str:
        """Determine the group for an import statement."""
        # Extract the module name
        if import_line.startswith('from '):
            match = re.match(r'from\s+([^\s.]+)(?:\.[^\s]+)?\s+import', import_line)
            if match:
                module = match.group(1)
            else:
                return "local"  # Relative import
        else:
            match = re.match(r'import\s+([^\s.]+)(?:\.[^\s]+)?', import_line)
            if match:
                module = match.group(1)
            else:
                return "local"  # Couldn't parse
        
        # Standard library modules
        if module in self._get_stdlib_modules():
            return "stdlib"
        
        # Local modules (assuming they start with the project name)
        if module in ["core", "tests", "scripts", "config"]:
            return "local"
        
        # Third-party modules
        return "third-party"
    
    def _get_stdlib_modules(self) -> Set[str]:
        """Get a set of standard library module names."""
        # This is a simplified list, not comprehensive
        return {
            "abc", "argparse", "asyncio", "collections", "contextlib", "copy", "csv", "datetime",
            "enum", "functools", "glob", "io", "itertools", "json", "logging", "math", "os",
            "pathlib", "random", "re", "shutil", "subprocess", "sys", "tempfile", "time",
            "typing", "unittest", "uuid", "warnings", "xml", "zipfile"
        }
    
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


class CircularDependencyCheck(QualityCheck):
    """Check for circular dependencies in Python imports."""
    
    @property
    def id(self) -> str:
        return "circular_dependencies"
    
    @property
    def name(self) -> str:
        return "Circular Dependency Checker"
    
    @property
    def description(self) -> str:
        return "Checks for circular dependencies in Python imports."
    
    def run(self, file_paths: Optional[List[str]] = None, **kwargs) -> List[QualityCheckResult]:
        """
        Check for circular dependencies in Python imports.
        
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
        
        # Build dependency graph
        dependency_graph = {}
        file_to_module = {}
        
        for file_path in file_paths:
            # Convert file path to module name
            module_name = self._file_path_to_module_name(file_path)
            file_to_module[file_path] = module_name
            dependency_graph[module_name] = set()
            
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Extract import statements
                for line in content.splitlines():
                    if line.strip().startswith('#'):
                        continue
                    
                    # Handle 'import module' statements
                    import_match = re.match(r'^\s*import\s+([a-zA-Z0-9_.]+)', line)
                    if import_match:
                        imported_module = import_match.group(1).split('.')[0]
                        dependency_graph[module_name].add(imported_module)
                        continue
                    
                    # Handle 'from module import ...' statements
                    from_match = re.match(r'^\s*from\s+([a-zA-Z0-9_.]+)\s+import', line)
                    if from_match:
                        imported_module = from_match.group(1).split('.')[0]
                        dependency_graph[module_name].add(imported_module)
            
            except Exception as e:
                results.append(QualityCheckResult(
                    check_id=self.id,
                    severity=QualityCheckSeverity.ERROR,
                    message=f"Error checking dependencies: {str(e)}",
                    file_path=file_path,
                    source=self.name
                ))
        
        # Find circular dependencies
        for module in dependency_graph:
            visited = set()
            path = [module]
            self._find_cycles(module, dependency_graph, visited, path, results, file_to_module)
        
        return results
    
    def _find_cycles(self, module: str, graph: Dict[str, Set[str]], visited: Set[str], 
                    path: List[str], results: List[QualityCheckResult], 
                    file_to_module: Dict[str, str]) -> None:
        """
        Find cycles in the dependency graph using DFS.
        
        Args:
            module: Current module being checked
            graph: Dependency graph
            visited: Set of visited modules
            path: Current path in the DFS
            results: List to add results to
            file_to_module: Mapping from file paths to module names
        """
        visited.add(module)
        
        for dependency in graph.get(module, set()):
            if dependency not in graph:
                continue  # External dependency
            
            if dependency in path:
                # Found a cycle
                cycle_start = path.index(dependency)
                cycle = path[cycle_start:] + [dependency]
                
                # Find the file path for the current module
                file_path = None
                for fp, mod in file_to_module.items():
                    if mod == module:
                        file_path = fp
                        break
                
                if file_path:
                    results.append(QualityCheckResult(
                        check_id=self.id,
                        severity=self.severity,
                        message=f"Circular dependency detected: {' -> '.join(cycle)}",
                        file_path=file_path,
                        source=self.name,
                        details={"cycle": cycle}
                    ))
                continue
            
            if dependency not in visited:
                path.append(dependency)
                self._find_cycles(dependency, graph, visited, path, results, file_to_module)
                path.pop()
    
    def _file_path_to_module_name(self, file_path: str) -> str:
        """Convert a file path to a module name."""
        # Remove .py extension
        if file_path.endswith('.py'):
            file_path = file_path[:-3]
        
        # Replace directory separators with dots
        module_name = file_path.replace(os.path.sep, '.')
        
        # Remove leading dots
        module_name = module_name.lstrip('.')
        
        # Handle __init__.py files
        if module_name.endswith('.__init__'):
            module_name = module_name[:-9]
        
        return module_name
    
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


class StructureComponent(QualityComponent):
    """Component for project structure quality checks."""
    
    @property
    def name(self) -> str:
        return "Project Structure"
    
    @property
    def description(self) -> str:
        return "Checks for proper project structure and organization."
    
    def _initialize_checks(self) -> None:
        """Initialize the project structure checks."""
        self._checks = [
            DirectoryStructureCheck(),
            FileNamingCheck(),
            ImportOrganizationCheck(),
            CircularDependencyCheck()
        ]