#!/usr/bin/env python3
"""
Static code analysis script that verifies scripts against the specification manifest.

This script provides functionality to:
1. Load the specification manifest
2. Parse Python, Shell, and other script files to extract their structure
3. Compare the actual code structure with the expected structure
4. Identify missing, redundant, or incorrectly implemented functions/code segments
5. Generate a detailed report of compliance and deviations

Usage:
    python analyze_code.py --project-dir /path/to/project --manifest /path/to/manifest.json --output /path/to/report.json
    python analyze_code.py --file /path/to/specific/file.py --manifest /path/to/manifest.json
    python analyze_code.py --project-dir /path/to/project --verbose
    python analyze_code.py --project-dir /path/to/project --dry-run
"""

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set, Union
import datetime
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """
    Class to analyze code structure and compare it against the specification manifest.
    
    This class provides methods to parse Python, Shell, and other script files,
    extract their structure, compare it against the expected structure defined in
    the specification manifest, and generate a detailed report of compliance and deviations.
    
    Attributes:
        project_dir: Path to the project directory
        manifest: The specification manifest
        verbose: Whether to enable verbose logging
        dry_run: Whether to run in dry-run mode (only report issues without making changes)
    """
    
    def __init__(
        self, 
        project_dir: str, 
        manifest: Dict[str, Any], 
        verbose: bool = False, 
        dry_run: bool = False
    ):
        """
        Initialize the CodeAnalyzer.
        
        Args:
            project_dir: Path to the project directory
            manifest: The specification manifest
            verbose: Whether to enable verbose logging
            dry_run: Whether to run in dry-run mode (only report issues without making changes)
        """
        self.project_dir = os.path.abspath(project_dir)
        self.manifest = manifest
        self.verbose = verbose
        self.dry_run = dry_run
        
        # Extract relevant sections from the manifest
        self.code_patterns = manifest["specification_manifest"]["code_patterns"]
        self.naming_conventions = manifest["specification_manifest"]["naming_conventions"]
        
        # Initialize report data structure
        self.report = {
            "project_dir": self.project_dir,
            "timestamp": datetime.datetime.now().isoformat(),
            "summary": {
                "total_files_analyzed": 0,
                "total_python_files": 0,
                "total_shell_files": 0,
                "total_other_files": 0,
                "compliant_files": 0,
                "files_with_issues": 0,
                "total_issues": 0,
                "missing_elements": 0,
                "redundant_elements": 0,
                "incorrect_implementations": 0,
                "compliance_percentage": 0.0
            },
            "python_analysis": {
                "files": {},
                "issues": []
            },
            "shell_analysis": {
                "files": {},
                "issues": []
            },
            "other_analysis": {
                "files": {},
                "issues": []
            }
        }
    
    def log(self, message: str) -> None:
        """
        Log a message if verbose mode is enabled.
        
        Args:
            message: The message to log
        """
        if self.verbose:
            logger.info(message)
    
    def analyze_project(self) -> None:
        """
        Analyze all code files in the project directory.
        
        This method walks through the project directory, identifies code files,
        and analyzes each file based on its type.
        """
        self.log(f"Analyzing code in directory: {self.project_dir}")
        
        # Collect all code files
        python_files = []
        shell_files = []
        other_files = []
        
        for root, _, files in os.walk(self.project_dir):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.project_dir)
                
                if file.endswith(".py"):
                    python_files.append(rel_path)
                elif file.endswith(".sh"):
                    shell_files.append(rel_path)
                elif file.endswith((".js", ".ts", ".jsx", ".tsx", ".rb", ".go")):
                    other_files.append(rel_path)
        
        self.report["summary"]["total_python_files"] = len(python_files)
        self.report["summary"]["total_shell_files"] = len(shell_files)
        self.report["summary"]["total_other_files"] = len(other_files)
        self.report["summary"]["total_files_analyzed"] = len(python_files) + len(shell_files) + len(other_files)
        
        # Analyze each file
        for file_path in python_files:
            self.analyze_python_file(file_path)
        
        for file_path in shell_files:
            self.analyze_shell_file(file_path)
        
        for file_path in other_files:
            self.analyze_other_file(file_path)
        
        # Calculate compliance percentage
        total_issues = self.report["summary"]["total_issues"]
        total_files = self.report["summary"]["total_files_analyzed"]
        
        if total_files > 0:
            compliance = 1.0 - (self.report["summary"]["files_with_issues"] / total_files)
            self.report["summary"]["compliance_percentage"] = round(compliance * 100, 2)
        else:
            self.report["summary"]["compliance_percentage"] = 100.0
    
    def analyze_file(self, file_path: str) -> None:
        """
        Analyze a specific file based on its type.
        
        Args:
            file_path: Path to the file to analyze
        """
        self.log(f"Analyzing file: {file_path}")
        
        abs_path = os.path.join(self.project_dir, file_path) if not os.path.isabs(file_path) else file_path
        rel_path = os.path.relpath(abs_path, self.project_dir)
        
        if not os.path.isfile(abs_path):
            logger.error(f"File not found: {abs_path}")
            return
        
        if file_path.endswith(".py"):
            self.analyze_python_file(rel_path)
            self.report["summary"]["total_python_files"] = 1
        elif file_path.endswith(".sh"):
            self.analyze_shell_file(rel_path)
            self.report["summary"]["total_shell_files"] = 1
        else:
            self.analyze_other_file(rel_path)
            self.report["summary"]["total_other_files"] = 1
        
        self.report["summary"]["total_files_analyzed"] = 1
        
        # Calculate compliance percentage
        total_issues = self.report["summary"]["total_issues"]
        total_files = self.report["summary"]["total_files_analyzed"]
        
        if total_files > 0:
            compliance = 1.0 - (self.report["summary"]["files_with_issues"] / total_files)
            self.report["summary"]["compliance_percentage"] = round(compliance * 100, 2)
        else:
            self.report["summary"]["compliance_percentage"] = 100.0
    
    def analyze_python_file(self, file_path: str) -> None:
        """
        Analyze a Python file to extract its structure and check compliance.
        
        Args:
            file_path: Path to the Python file to analyze
        """
        self.log(f"Analyzing Python file: {file_path}")
        
        abs_path = os.path.join(self.project_dir, file_path)
        
        try:
            with open(abs_path, 'r') as f:
                content = f.read()
            
            # Parse the Python file
            tree = ast.parse(content)
            
            # Extract file structure
            file_structure = {
                "path": file_path,
                "module_docstring": ast.get_docstring(tree),
                "imports": [],
                "classes": [],
                "functions": [],
                "constants": [],
                "has_module_header": False,
                "has_error_handling": False,
                "has_context_manager": False,
                "has_logging": False
            }
            
            # Check for module header pattern
            if "python" in self.code_patterns and "module_header" in self.code_patterns["python"]:
                pattern = self.code_patterns["python"]["module_header"]["validation_regex"]
                file_structure["has_module_header"] = bool(re.search(pattern, content, re.MULTILINE))
            
            # Check for error handling pattern
            if "python" in self.code_patterns and "error_handling" in self.code_patterns["python"]:
                pattern = self.code_patterns["python"]["error_handling"]["validation_regex"]
                file_structure["has_error_handling"] = bool(re.search(pattern, content, re.MULTILINE))
            
            # Check for context manager pattern
            if "python" in self.code_patterns and "context_manager" in self.code_patterns["python"]:
                pattern = self.code_patterns["python"]["context_manager"]["validation_regex"]
                file_structure["has_context_manager"] = bool(re.search(pattern, content, re.MULTILINE))
            
            # Check for logging pattern
            if "python" in self.code_patterns and "logging" in self.code_patterns["python"]:
                pattern = self.code_patterns["python"]["logging"]["validation_regex"]
                file_structure["has_logging"] = bool(re.search(pattern, content, re.MULTILINE))
            
            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        file_structure["imports"].append({
                            "type": "import",
                            "name": name.name,
                            "asname": name.asname
                        })
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for name in node.names:
                        file_structure["imports"].append({
                            "type": "from_import",
                            "module": module,
                            "name": name.name,
                            "asname": name.asname
                        })
            
            # Extract classes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "docstring": ast.get_docstring(node),
                        "bases": [self._get_base_name(base) for base in node.bases],
                        "methods": [],
                        "attributes": [],
                        "has_proper_docstring": False
                    }
                    
                    # Check for class docstring pattern
                    if "python" in self.code_patterns and "class_definition" in self.code_patterns["python"]:
                        pattern = self.code_patterns["python"]["class_definition"]["validation_regex"]
                        class_def = self._get_node_source(node, content)
                        class_info["has_proper_docstring"] = bool(re.search(pattern, class_def, re.MULTILINE))
                    
                    # Extract methods and attributes
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_info = self._extract_function_info(item, content)
                            class_info["methods"].append(method_info)
                        elif isinstance(item, ast.Assign):
                            for target in item.targets:
                                if isinstance(target, ast.Name):
                                    class_info["attributes"].append({
                                        "name": target.id,
                                        "value": self._get_node_source(item.value, content)
                                    })
                    
                    file_structure["classes"].append(class_info)
            
            # Extract functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and not any(
                    node.name == method["name"] 
                    for cls in file_structure["classes"] 
                    for method in cls["methods"]
                ):
                    function_info = self._extract_function_info(node, content)
                    file_structure["functions"].append(function_info)
            
            # Extract constants
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id.isupper():
                            file_structure["constants"].append({
                                "name": target.id,
                                "value": self._get_node_source(node.value, content)
                            })
            
            # Store file structure in report
            self.report["python_analysis"]["files"][file_path] = file_structure
            
            # Check compliance with naming conventions
            self._check_python_naming_conventions(file_structure)
            
            # Check compliance with code patterns
            self._check_python_code_patterns(file_structure)
            
            # Update summary
            if any(issue["file"] == file_path for issue in self.report["python_analysis"]["issues"]):
                self.report["summary"]["files_with_issues"] += 1
            else:
                self.report["summary"]["compliant_files"] += 1
            
        except Exception as e:
            logger.error(f"Error analyzing Python file {file_path}: {e}")
            self.report["python_analysis"]["issues"].append({
                "file": file_path,
                "type": "analysis_error",
                "message": f"Error analyzing file: {str(e)}"
            })
            self.report["summary"]["files_with_issues"] += 1
            self.report["summary"]["total_issues"] += 1
    
    def _extract_function_info(self, node: ast.FunctionDef, content: str) -> Dict[str, Any]:
        """
        Extract information about a function or method.
        
        Args:
            node: The AST node representing the function
            content: The source code content
            
        Returns:
            A dictionary containing information about the function
        """
        function_info = {
            "name": node.name,
            "docstring": ast.get_docstring(node),
            "args": [],
            "returns": None,
            "has_proper_docstring": False,
            "has_type_hints": False
        }
        
        # Check for function docstring pattern
        if "python" in self.code_patterns and "function_definition" in self.code_patterns["python"]:
            pattern = self.code_patterns["python"]["function_definition"]["validation_regex"]
            func_def = self._get_node_source(node, content)
            function_info["has_proper_docstring"] = bool(re.search(pattern, func_def, re.MULTILINE))
        
        # Extract arguments
        for arg in node.args.args:
            arg_info = {
                "name": arg.arg,
                "annotation": self._get_annotation(arg.annotation, content) if arg.annotation else None
            }
            function_info["args"].append(arg_info)
        
        # Extract return type
        if node.returns:
            function_info["returns"] = self._get_annotation(node.returns, content)
            function_info["has_type_hints"] = True
        
        # Check if all arguments have type hints
        if all(arg["annotation"] is not None for arg in function_info["args"]):
            function_info["has_type_hints"] = True
        
        return function_info
    
    def _get_annotation(self, node: ast.AST, content: str) -> str:
        """
        Get the string representation of a type annotation.
        
        Args:
            node: The AST node representing the annotation
            content: The source code content
            
        Returns:
            The string representation of the annotation
        """
        return self._get_node_source(node, content)
    
    def _get_base_name(self, node: ast.AST) -> str:
        """
        Get the name of a base class.
        
        Args:
            node: The AST node representing the base class
            
        Returns:
            The name of the base class
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_base_name(node.value)}.{node.attr}"
        else:
            return str(node)
    
    def _get_node_source(self, node: ast.AST, content: str) -> str:
        """
        Get the source code for an AST node.
        
        Args:
            node: The AST node
            content: The source code content
            
        Returns:
            The source code for the node
        """
        if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
            lines = content.splitlines()
            if node.end_lineno > len(lines):
                return "<<source not available>>"
            
            if node.lineno == node.end_lineno:
                line = lines[node.lineno - 1]
                return line[node.col_offset:node.end_col_offset]
            else:
                result = []
                for i in range(node.lineno - 1, node.end_lineno):
                    if i == node.lineno - 1:
                        result.append(lines[i][node.col_offset:])
                    elif i == node.end_lineno - 1:
                        result.append(lines[i][:node.end_col_offset])
                    else:
                        result.append(lines[i])
                return '\n'.join(result)
        return "<<source not available>>"
    
    def _check_python_naming_conventions(self, file_structure: Dict[str, Any]) -> None:
        """
        Check if Python code elements follow the naming conventions.
        
        Args:
            file_structure: The structure of the Python file
        """
        file_path = file_structure["path"]
        
        # Check class names
        if "python" in self.naming_conventions and "classes" in self.naming_conventions["python"]:
            pattern = self.naming_conventions["python"]["classes"]["regex"]
            for cls in file_structure["classes"]:
                if not re.match(pattern, cls["name"]):
                    self.report["python_analysis"]["issues"].append({
                        "file": file_path,
                        "type": "naming_convention",
                        "element_type": "class",
                        "element_name": cls["name"],
                        "expected_pattern": self.naming_conventions["python"]["classes"]["pattern"],
                        "message": f"Class name '{cls['name']}' does not follow the required pattern '{self.naming_conventions['python']['classes']['pattern']}'"
                    })
                    self.report["summary"]["total_issues"] += 1
        
        # Check function names
        if "python" in self.naming_conventions and "functions" in self.naming_conventions["python"]:
            pattern = self.naming_conventions["python"]["functions"]["regex"]
            for func in file_structure["functions"]:
                if not re.match(pattern, func["name"]):
                    self.report["python_analysis"]["issues"].append({
                        "file": file_path,
                        "type": "naming_convention",
                        "element_type": "function",
                        "element_name": func["name"],
                        "expected_pattern": self.naming_conventions["python"]["functions"]["pattern"],
                        "message": f"Function name '{func['name']}' does not follow the required pattern '{self.naming_conventions['python']['functions']['pattern']}'"
                    })
                    self.report["summary"]["total_issues"] += 1
        
        # Check method names
        if "python" in self.naming_conventions and "functions" in self.naming_conventions["python"]:
            pattern = self.naming_conventions["python"]["functions"]["regex"]
            for cls in file_structure["classes"]:
                for method in cls["methods"]:
                    # Skip special methods like __init__
                    if method["name"].startswith("__") and method["name"].endswith("__"):
                        continue
                    
                    if not re.match(pattern, method["name"]):
                        self.report["python_analysis"]["issues"].append({
                            "file": file_path,
                            "type": "naming_convention",
                            "element_type": "method",
                            "element_name": f"{cls['name']}.{method['name']}",
                            "expected_pattern": self.naming_conventions["python"]["functions"]["pattern"],
                            "message": f"Method name '{cls['name']}.{method['name']}' does not follow the required pattern '{self.naming_conventions['python']['functions']['pattern']}'"
                        })
                        self.report["summary"]["total_issues"] += 1
        
        # Check constant names
        if "python" in self.naming_conventions and "constants" in self.naming_conventions["python"]:
            pattern = self.naming_conventions["python"]["constants"]["regex"]
            for const in file_structure["constants"]:
                if not re.match(pattern, const["name"]):
                    self.report["python_analysis"]["issues"].append({
                        "file": file_path,
                        "type": "naming_convention",
                        "element_type": "constant",
                        "element_name": const["name"],
                        "expected_pattern": self.naming_conventions["python"]["constants"]["pattern"],
                        "message": f"Constant name '{const['name']}' does not follow the required pattern '{self.naming_conventions['python']['constants']['pattern']}'"
                    })
                    self.report["summary"]["total_issues"] += 1
    
    def _check_python_code_patterns(self, file_structure: Dict[str, Any]) -> None:
        """
        Check if Python code follows the required code patterns.
        
        Args:
            file_structure: The structure of the Python file
        """
        file_path = file_structure["path"]
        
        # Check module header
        if "python" in self.code_patterns and "module_header" in self.code_patterns["python"]:
            if self.code_patterns["python"]["module_header"]["required"] and not file_structure["has_module_header"]:
                self.report["python_analysis"]["issues"].append({
                    "file": file_path,
                    "type": "code_pattern",
                    "element_type": "module",
                    "pattern_name": "module_header",
                    "message": f"Module '{file_path}' is missing the required module header pattern"
                })
                self.report["summary"]["total_issues"] += 1
                self.report["summary"]["missing_elements"] += 1
        
        # Check class docstrings
        if "python" in self.code_patterns and "class_definition" in self.code_patterns["python"]:
            for cls in file_structure["classes"]:
                if self.code_patterns["python"]["class_definition"]["required"] and not cls["has_proper_docstring"]:
                    self.report["python_analysis"]["issues"].append({
                        "file": file_path,
                        "type": "code_pattern",
                        "element_type": "class",
                        "element_name": cls["name"],
                        "pattern_name": "class_definition",
                        "message": f"Class '{cls['name']}' in '{file_path}' is missing the required docstring pattern"
                    })
                    self.report["summary"]["total_issues"] += 1
                    self.report["summary"]["missing_elements"] += 1
        
        # Check function docstrings
        if "python" in self.code_patterns and "function_definition" in self.code_patterns["python"]:
            for func in file_structure["functions"]:
                if self.code_patterns["python"]["function_definition"]["required"] and not func["has_proper_docstring"]:
                    self.report["python_analysis"]["issues"].append({
                        "file": file_path,
                        "type": "code_pattern",
                        "element_type": "function",
                        "element_name": func["name"],
                        "pattern_name": "function_definition",
                        "message": f"Function '{func['name']}' in '{file_path}' is missing the required docstring pattern"
                    })
                    self.report["summary"]["total_issues"] += 1
                    self.report["summary"]["missing_elements"] += 1
        
        # Check method docstrings
        if "python" in self.code_patterns and "function_definition" in self.code_patterns["python"]:
            for cls in file_structure["classes"]:
                for method in cls["methods"]:
                    # Skip special methods like __init__ for docstring check
                    if method["name"] == "__init__":
                        continue
                    
                    if self.code_patterns["python"]["function_definition"]["required"] and not method["has_proper_docstring"]:
                        self.report["python_analysis"]["issues"].append({
                            "file": file_path,
                            "type": "code_pattern",
                            "element_type": "method",
                            "element_name": f"{cls['name']}.{method['name']}",
                            "pattern_name": "function_definition",
                            "message": f"Method '{cls['name']}.{method['name']}' in '{file_path}' is missing the required docstring pattern"
                        })
                        self.report["summary"]["total_issues"] += 1
                        self.report["summary"]["missing_elements"] += 1
        
        # Check type hints
        for func in file_structure["functions"]:
            if not func["has_type_hints"]:
                self.report["python_analysis"]["issues"].append({
                    "file": file_path,
                    "type": "code_pattern",
                    "element_type": "function",
                    "element_name": func["name"],
                    "pattern_name": "type_hints",
                    "message": f"Function '{func['name']}' in '{file_path}' is missing type hints"
                })
                self.report["summary"]["total_issues"] += 1
                self.report["summary"]["missing_elements"] += 1
        
        for cls in file_structure["classes"]:
            for method in cls["methods"]:
                # Skip special methods like __init__ for type hint check
                if method["name"] == "__init__":
                    continue
                
                if not method["has_type_hints"]:
                    self.report["python_analysis"]["issues"].append({
                        "file": file_path,
                        "type": "code_pattern",
                        "element_type": "method",
                        "element_name": f"{cls['name']}.{method['name']}",
                        "pattern_name": "type_hints",
                        "message": f"Method '{cls['name']}.{method['name']}' in '{file_path}' is missing type hints"
                    })
                    self.report["summary"]["total_issues"] += 1
                    self.report["summary"]["missing_elements"] += 1
        
        # Check error handling
        if "python" in self.code_patterns and "error_handling" in self.code_patterns["python"]:
            if self.code_patterns["python"]["error_handling"]["required"] and not file_structure["has_error_handling"]:
                self.report["python_analysis"]["issues"].append({
                    "file": file_path,
                    "type": "code_pattern",
                    "element_type": "module",
                    "pattern_name": "error_handling",
                    "message": f"Module '{file_path}' is missing the required error handling pattern"
                })
                self.report["summary"]["total_issues"] += 1
                self.report["summary"]["missing_elements"] += 1
    
    def analyze_shell_file(self, file_path: str) -> None:
        """
        Analyze a Shell script file to extract its structure and check compliance.
        
        Args:
            file_path: Path to the Shell script file to analyze
        """
        self.log(f"Analyzing Shell script: {file_path}")
        
        abs_path = os.path.join(self.project_dir, file_path)
        
        try:
            with open(abs_path, 'r') as f:
                content = f.read()
            
            # Extract file structure
            file_structure = {
                "path": file_path,
                "shebang": None,
                "description": None,
                "functions": [],
                "variables": [],
                "environment_variables": [],
                "has_script_header": False,
                "has_error_handling": False,
                "has_command_checking": False
            }
            
            # Extract shebang
            shebang_match = re.match(r'^#!(.*)$', content, re.MULTILINE)
            if shebang_match:
                file_structure["shebang"] = shebang_match.group(1).strip()
            
            # Extract description
            description_match = re.search(r'^#\s*Description:\s*(.*)$', content, re.MULTILINE)
            if description_match:
                file_structure["description"] = description_match.group(1).strip()
            
            # Check for script header pattern
            if "shell" in self.code_patterns and "script_header" in self.code_patterns["shell"]:
                pattern = self.code_patterns["shell"]["script_header"]["validation_regex"]
                file_structure["has_script_header"] = bool(re.search(pattern, content, re.MULTILINE))
            
            # Check for error handling pattern
            if "shell" in self.code_patterns and "error_handling" in self.code_patterns["shell"]:
                pattern = self.code_patterns["shell"]["error_handling"]["validation_regex"]
                file_structure["has_error_handling"] = bool(re.search(pattern, content, re.MULTILINE))
            
            # Check for command checking pattern
            if "shell" in self.code_patterns and "command_checking" in self.code_patterns["shell"]:
                pattern = self.code_patterns["shell"]["command_checking"]["validation_regex"]
                file_structure["has_command_checking"] = bool(re.search(pattern, content, re.MULTILINE))
            
            # Extract functions
            function_matches = re.finditer(r'function\s+([a-zA-Z0-9_]+)\s*\(\)\s*\{', content)
            for match in function_matches:
                function_name = match.group(1)
                file_structure["functions"].append({
                    "name": function_name
                })
            
            # Extract variables
            variable_matches = re.finditer(r'^([a-zA-Z0-9_]+)=', content, re.MULTILINE)
            for match in variable_matches:
                variable_name = match.group(1)
                if variable_name.isupper():
                    file_structure["environment_variables"].append({
                        "name": variable_name
                    })
                else:
                    file_structure["variables"].append({
                        "name": variable_name
                    })
            # Store file structure in report
            self.report["shell_analysis"]["files"][file_path] = file_structure
            
            # Check compliance with naming conventions
            self._check_shell_naming_conventions(file_structure)
            
            # Check compliance with code patterns
            self._check_shell_code_patterns(file_structure)
            
            # Update summary
            if any(issue["file"] == file_path for issue in self.report["shell_analysis"]["issues"]):
                self.report["summary"]["files_with_issues"] += 1
            else:
                self.report["summary"]["compliant_files"] += 1
            
        except Exception as e:
            logger.error(f"Error analyzing Shell file {file_path}: {e}")
            self.report["shell_analysis"]["issues"].append({
                "file": file_path,
                "type": "analysis_error",
                "message": f"Error analyzing file: {str(e)}"
            })
            self.report["summary"]["files_with_issues"] += 1
            self.report["summary"]["total_issues"] += 1
    
    def _check_shell_naming_conventions(self, file_structure: Dict[str, Any]) -> None:
        """
        Check if Shell script elements follow the naming conventions.
        
        Args:
            file_structure: The structure of the Shell script file
        """
        file_path = file_structure["path"]
        
        # Check function names
        if "shell" in self.naming_conventions and "functions" in self.naming_conventions["shell"]:
            pattern = self.naming_conventions["shell"]["functions"]["regex"]
            for func in file_structure["functions"]:
                if not re.match(pattern, func["name"]):
                    self.report["shell_analysis"]["issues"].append({
                        "file": file_path,
                        "type": "naming_convention",
                        "element_type": "function",
                        "element_name": func["name"],
                        "expected_pattern": self.naming_conventions["shell"]["functions"]["pattern"],
                        "message": f"Shell function name '{func['name']}' does not follow the required pattern '{self.naming_conventions['shell']['functions']['pattern']}'"
                    })
                    self.report["summary"]["total_issues"] += 1
        
        # Check variable names
        if "shell" in self.naming_conventions and "variables" in self.naming_conventions["shell"]:
            pattern = self.naming_conventions["shell"]["variables"]["regex"]
            for var in file_structure["variables"]:
                if not re.match(pattern, var["name"]):
                    self.report["shell_analysis"]["issues"].append({
                        "file": file_path,
                        "type": "naming_convention",
                        "element_type": "variable",
                        "element_name": var["name"],
                        "expected_pattern": self.naming_conventions["shell"]["variables"]["pattern"],
                        "message": f"Shell variable name '{var['name']}' does not follow the required pattern '{self.naming_conventions['shell']['variables']['pattern']}'"
                    })
                    self.report["summary"]["total_issues"] += 1
        
        # Check environment variable names
        if "shell" in self.naming_conventions and "environment_variables" in self.naming_conventions["shell"]:
            pattern = self.naming_conventions["shell"]["environment_variables"]["regex"]
            for var in file_structure["environment_variables"]:
                if not re.match(pattern, var["name"]):
                    self.report["shell_analysis"]["issues"].append({
                        "file": file_path,
                        "type": "naming_convention",
                        "element_type": "environment_variable",
                        "element_name": var["name"],
                        "expected_pattern": self.naming_conventions["shell"]["environment_variables"]["pattern"],
                        "message": f"Shell environment variable name '{var['name']}' does not follow the required pattern '{self.naming_conventions['shell']['environment_variables']['pattern']}'"
                    })
                    self.report["summary"]["total_issues"] += 1
    
    def _check_shell_code_patterns(self, file_structure: Dict[str, Any]) -> None:
        """
        Check if Shell script follows the required code patterns.
        
        Args:
            file_structure: The structure of the Shell script file
        """
        file_path = file_structure["path"]
        
        # Check script header
        if "shell" in self.code_patterns and "script_header" in self.code_patterns["shell"]:
            if self.code_patterns["shell"]["script_header"]["required"] and not file_structure["has_script_header"]:
                self.report["shell_analysis"]["issues"].append({
                    "file": file_path,
                    "type": "code_pattern",
                    "element_type": "script",
                    "pattern_name": "script_header",
                    "message": f"Shell script '{file_path}' is missing the required script header pattern"
                })
                self.report["summary"]["total_issues"] += 1
                self.report["summary"]["missing_elements"] += 1
        
        # Check error handling
        if "shell" in self.code_patterns and "error_handling" in self.code_patterns["shell"]:
            if self.code_patterns["shell"]["error_handling"]["required"] and not file_structure["has_error_handling"]:
                self.report["shell_analysis"]["issues"].append({
                    "file": file_path,
                    "type": "code_pattern",
                    "element_type": "script",
                    "pattern_name": "error_handling",
                    "message": f"Shell script '{file_path}' is missing the required error handling pattern"
                })
                self.report["summary"]["total_issues"] += 1
                self.report["summary"]["missing_elements"] += 1
        
        # Check command checking
        if "shell" in self.code_patterns and "command_checking" in self.code_patterns["shell"]:
            if self.code_patterns["shell"]["command_checking"]["required"] and not file_structure["has_command_checking"]:
                self.report["shell_analysis"]["issues"].append({
                    "file": file_path,
                    "type": "code_pattern",
                    "element_type": "script",
                    "pattern_name": "command_checking",
                    "message": f"Shell script '{file_path}' is missing the required command checking pattern"
                })
                self.report["summary"]["total_issues"] += 1
                self.report["summary"]["missing_elements"] += 1
    
    def analyze_other_file(self, file_path: str) -> None:
        """
        Analyze other script files to extract their structure and check compliance.
        
        Args:
            file_path: Path to the script file to analyze
        """
        self.log(f"Analyzing other script file: {file_path}")
        
        abs_path = os.path.join(self.project_dir, file_path)
        
        try:
            with open(abs_path, 'r') as f:
                content = f.read()
            
            # Extract file structure
            file_structure = {
                "path": file_path,
                "extension": os.path.splitext(file_path)[1],
                "content_length": len(content),
                "line_count": len(content.splitlines())
            }
            
            # Store file structure in report
            self.report["other_analysis"]["files"][file_path] = file_structure
            
            # For now, we just count other files as compliant
            self.report["summary"]["compliant_files"] += 1
            
        except Exception as e:
            logger.error(f"Error analyzing other file {file_path}: {e}")
            self.report["other_analysis"]["issues"].append({
                "file": file_path,
                "type": "analysis_error",
                "message": f"Error analyzing file: {str(e)}"
            })
            self.report["summary"]["files_with_issues"] += 1
            self.report["summary"]["total_issues"] += 1
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a detailed report of the code analysis.
        
        Returns:
            A dictionary containing the detailed report
        """
        # Update timestamp
        self.report["timestamp"] = datetime.datetime.now().isoformat()
        
        return self.report
    
    def save_report(self, output_path: str) -> None:
        """
        Save the report to a JSON file.
        
        Args:
            output_path: Path to save the report to
        """
        with open(output_path, 'w') as f:
            json.dump(self.report, f, indent=2)
        
        self.log(f"Report saved to {output_path}")
    
    def print_summary(self) -> None:
        """Print a summary of the report to the console."""
        print("\n=== Code Analysis Summary ===")
        print(f"Project directory: {self.project_dir}")
        print(f"Total files analyzed: {self.report['summary']['total_files_analyzed']}")
        print(f"  - Python files: {self.report['summary']['total_python_files']}")
        print(f"  - Shell files: {self.report['summary']['total_shell_files']}")
        print(f"  - Other files: {self.report['summary']['total_other_files']}")
        print(f"Compliant files: {self.report['summary']['compliant_files']}")
        print(f"Files with issues: {self.report['summary']['files_with_issues']}")
        print(f"Total issues: {self.report['summary']['total_issues']}")
        print(f"  - Missing elements: {self.report['summary']['missing_elements']}")
        print(f"  - Redundant elements: {self.report['summary']['redundant_elements']}")
        print(f"  - Incorrect implementations: {self.report['summary']['incorrect_implementations']}")
        print(f"Overall compliance: {self.report['summary']['compliance_percentage']}%")
        
        if self.report["python_analysis"]["issues"]:
            print("\n--- Python Issues ---")
            for issue in self.report["python_analysis"]["issues"][:10]:  # Show only first 10 issues
                print(f"- {issue['message']}")
            if len(self.report["python_analysis"]["issues"]) > 10:
                print(f"  ... and {len(self.report['python_analysis']['issues']) - 10} more issues")
        
        if self.report["shell_analysis"]["issues"]:
            print("\n--- Shell Issues ---")
            for issue in self.report["shell_analysis"]["issues"][:10]:  # Show only first 10 issues
                print(f"- {issue['message']}")
            if len(self.report["shell_analysis"]["issues"]) > 10:
                print(f"  ... and {len(self.report['shell_analysis']['issues']) - 10} more issues")
        
        if self.report["other_analysis"]["issues"]:
            print("\n--- Other Issues ---")
            for issue in self.report["other_analysis"]["issues"][:10]:  # Show only first 10 issues
                print(f"- {issue['message']}")
            if len(self.report["other_analysis"]["issues"]) > 10:
                print(f"  ... and {len(self.report['other_analysis']['issues']) - 10} more issues")


def load_json_file(file_path: str) -> Dict[str, Any]:
    """
    Load a JSON file.
    
    Args:
        file_path: Path to the JSON file
    
    Returns:
        The loaded JSON data
    
    Raises:
        FileNotFoundError: If the file does not exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Error: File not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Error: Invalid JSON in {file_path}: {e}")
        sys.exit(1)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Static code analysis script that verifies scripts against the specification manifest."
    )
    
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Path to the project directory (default: current directory)"
    )
    parser.add_argument(
        "--file",
        help="Path to a specific file to analyze"
    )
    parser.add_argument(
        "--manifest",
        default="config/specifications/specification-manifest.json",
        help="Path to the specification manifest (default: config/specifications/specification-manifest.json)"
    )
    parser.add_argument(
        "--output",
        default="code-analysis-report.json",
        help="Path to save the report to (default: code-analysis-report.json)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode (only report issues without making changes)"
    )
    parser.add_argument(
        "--integrate-with-traverse",
        action="store_true",
        help="Integrate with traverse_project.py to analyze only non-compliant files"
    )
    
    args = parser.parse_args()
    
    # Load the manifest
    manifest = load_json_file(args.manifest)
    
    # Create the analyzer
    analyzer = CodeAnalyzer(
        project_dir=args.project_dir,
        manifest=manifest,
        verbose=args.verbose,
        dry_run=args.dry_run
    )
    
    # Analyze the project or a specific file
    if args.file:
        analyzer.analyze_file(args.file)
    else:
        analyzer.analyze_project()
    
    # Generate and save the report
    analyzer.save_report(args.output)
    
    # Print summary
    analyzer.print_summary()
    
    # If integrating with traverse_project.py, check if there's a project structure report
    if args.integrate_with_traverse:
        try:
            project_report = load_json_file("data/reports/project-structure-report.json")
            print("\nIntegrating with traverse_project.py...")
            
            # Find files that are non-compliant in both reports
            code_issues = set(issue["file"] for issue in analyzer.report["python_analysis"]["issues"] +
                             analyzer.report["shell_analysis"]["issues"] +
                             analyzer.report["other_analysis"]["issues"])
            
            structure_issues = set()
            for issue_type in ["directory_structure", "file_presence", "naming_conventions", "location_analysis"]:
                for issue in project_report.get(issue_type, {}).get("issues", []):
                    if "path" in issue:
                        structure_issues.add(issue["path"])
            
            common_issues = code_issues.intersection(structure_issues)
            
            if common_issues:
                print(f"Found {len(common_issues)} files with both structure and code issues:")
                for file in sorted(common_issues)[:10]:  # Show only first 10 files
                    print(f"  - {file}")
                if len(common_issues) > 10:
                    print(f"  ... and {len(common_issues) - 10} more files")
            else:
                print("No files with both structure and code issues found.")
            
        except (FileNotFoundError, json.JSONDecodeError):
            print("No project structure report found. Run traverse_project.py first to enable integration.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
