"""
Enhanced Documentation Coverage Checker Module

This module provides an enhanced implementation of the documentation coverage checker
that provides more detailed feedback on documentation coverage across the codebase.
It analyzes documentation at multiple levels:
- Module level (module docstrings)
- Class level (class docstrings)
- Method/function level (function docstrings)
- Parameter level (parameter documentation in docstrings)
- Return value documentation

The checker generates detailed metrics and can identify specific areas where
documentation is missing or incomplete.
"""

import ast
import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any
from datetime import datetime

from core.quality.components.base import (
    QualityCheck,
    QualityCheckResult,
    QualityCheckSeverity,
    QualityComponent
)

logger = logging.getLogger(__name__)

# Constants
REPORTS_DIR = Path("data/reports")


class EnhancedDocumentationCoverageCheck(QualityCheck):
    """
    Enhanced check for documentation coverage with detailed metrics and feedback.
    
    This check analyzes Python files to determine documentation coverage at multiple levels:
    - Module level (module docstrings)
    - Class level (class docstrings)
    - Method/function level (function docstrings)
    - Parameter level (parameter documentation in docstrings)
    - Return value documentation
    
    It generates detailed metrics and provides specific feedback on areas where
    documentation is missing or incomplete.
    """
    
    @property
    def id(self) -> str:
        """
        Get the unique identifier for this check.
        
        Returns:
            The check ID.
        """
        return "enhanced_doc_coverage"
    
    @property
    def name(self) -> str:
        """
        Get the display name for this check.
        
        Returns:
            The check name.
        """
        return "Enhanced Documentation Coverage Checker"
    
    @property
    def description(self) -> str:
        """
        Get the description for this check.
        
        Returns:
            The check description.
        """
        return "Checks for detailed documentation coverage in the project with enhanced metrics."
    
    def run(self, file_paths: Optional[List[str]] = None, **kwargs) -> List[QualityCheckResult]:
        """
        Check for detailed documentation coverage.
        
        Args:
            file_paths: Optional list of Python file paths to check.
                If None, check all Python files.
            **kwargs: Additional arguments.
                - min_module_coverage: Minimum required module docstring coverage (default: 0.9)
                - min_class_coverage: Minimum required class docstring coverage (default: 0.9)
                - min_function_coverage: Minimum required function docstring coverage (default: 0.8)
                - min_param_coverage: Minimum required parameter docstring coverage (default: 0.7)
                - min_return_coverage: Minimum required return value docstring coverage (default: 0.7)
                - export_metrics: Whether to export metrics to a JSON file (default: True)
            
        Returns:
            List of QualityCheckResult objects.
        """
        results = []
        
        # Get configuration from kwargs
        min_module_coverage = kwargs.get("min_module_coverage", 0.9)
        min_class_coverage = kwargs.get("min_class_coverage", 0.9)
        min_function_coverage = kwargs.get("min_function_coverage", 0.8)
        min_param_coverage = kwargs.get("min_param_coverage", 0.7)
        min_return_coverage = kwargs.get("min_return_coverage", 0.7)
        export_metrics = kwargs.get("export_metrics", True)
        
        # If no file paths provided, use all Python files
        if not file_paths:
            file_paths = self._find_python_files()
        else:
            # Filter for Python files
            file_paths = [f for f in file_paths if f.endswith('.py')]
        
        if not file_paths:
            return results
        
        # Initialize metrics
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "overall_metrics": {
                "total_files": len(file_paths),
                "documented_files": 0,
                "total_modules": 0,
                "documented_modules": 0,
                "total_classes": 0,
                "documented_classes": 0,
                "total_functions": 0,
                "documented_functions": 0,
                "total_parameters": 0,
                "documented_parameters": 0,
                "total_returns": 0,
                "documented_returns": 0
            },
            "file_metrics": {},
            "component_metrics": {}
        }
        
        # Process each file
        for file_path in file_paths:
            try:
                file_metrics = self._analyze_file(file_path)
                
                # Add file metrics to overall metrics
                metrics["overall_metrics"]["documented_files"] += 1 if file_metrics["has_module_docstring"] else 0
                metrics["overall_metrics"]["total_modules"] += 1
                metrics["overall_metrics"]["documented_modules"] += file_metrics["documented_modules"]
                metrics["overall_metrics"]["total_modules"] += file_metrics["total_modules"]
                metrics["overall_metrics"]["documented_classes"] += file_metrics["documented_classes"]
                metrics["overall_metrics"]["total_classes"] += file_metrics["total_classes"]
                metrics["overall_metrics"]["documented_functions"] += file_metrics["documented_functions"]
                metrics["overall_metrics"]["total_functions"] += file_metrics["total_functions"]
                metrics["overall_metrics"]["documented_parameters"] += file_metrics["documented_parameters"]
                metrics["overall_metrics"]["total_parameters"] += file_metrics["total_parameters"]
                metrics["overall_metrics"]["documented_returns"] += file_metrics["documented_returns"]
                metrics["overall_metrics"]["total_returns"] += file_metrics["total_returns"]
                
                # Store file metrics
                metrics["file_metrics"][file_path] = file_metrics
                
                # Add component metrics
                component_name = self._get_component_name(file_path)
                if component_name not in metrics["component_metrics"]:
                    metrics["component_metrics"][component_name] = {
                        "total_files": 0,
                        "documented_files": 0,
                        "total_modules": 0,
                        "documented_modules": 0,
                        "total_classes": 0,
                        "documented_classes": 0,
                        "total_functions": 0,
                        "documented_functions": 0,
                        "total_parameters": 0,
                        "documented_parameters": 0,
                        "total_returns": 0,
                        "documented_returns": 0
                    }
                
                metrics["component_metrics"][component_name]["total_files"] += 1
                metrics["component_metrics"][component_name]["documented_files"] += 1 if file_metrics["has_module_docstring"] else 0
                metrics["component_metrics"][component_name]["total_modules"] += 1
                metrics["component_metrics"][component_name]["documented_modules"] += file_metrics["documented_modules"]
                metrics["component_metrics"][component_name]["total_classes"] += file_metrics["total_classes"]
                metrics["component_metrics"][component_name]["documented_classes"] += file_metrics["documented_classes"]
                metrics["component_metrics"][component_name]["total_functions"] += file_metrics["total_functions"]
                metrics["component_metrics"][component_name]["documented_functions"] += file_metrics["documented_functions"]
                metrics["component_metrics"][component_name]["total_parameters"] += file_metrics["total_parameters"]
                metrics["component_metrics"][component_name]["documented_parameters"] += file_metrics["documented_parameters"]
                metrics["component_metrics"][component_name]["total_returns"] += file_metrics["total_returns"]
                metrics["component_metrics"][component_name]["documented_returns"] += file_metrics["documented_returns"]
                
                # Generate results for this file
                file_results = self._generate_file_results(file_path, file_metrics, 
                                                          min_module_coverage, min_class_coverage,
                                                          min_function_coverage, min_param_coverage,
                                                          min_return_coverage)
                results.extend(file_results)
                
            except Exception as e:
                logger.error(f"Error analyzing documentation coverage for {file_path}: {e}")
                results.append(QualityCheckResult(
                    check_id=self.id,
                    severity=QualityCheckSeverity.ERROR,
                    message=f"Error analyzing documentation coverage: {str(e)}",
                    file_path=file_path,
                    source=self.name
                ))
        
        # Calculate coverage percentages
        self._calculate_coverage_percentages(metrics)
        
        # Export metrics if requested
        if export_metrics:
            self._export_metrics(metrics)
        
        # Add overall coverage results
        overall_results = self._generate_overall_results(metrics, 
                                                        min_module_coverage, min_class_coverage,
                                                        min_function_coverage, min_param_coverage,
                                                        min_return_coverage)
        results.extend(overall_results)
        
        return results
    
    def _analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a Python file for documentation coverage.
        
        Args:
            file_path: Path to the Python file.
            
        Returns:
            Dictionary containing documentation coverage metrics for the file.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Parse the Python file
        tree = ast.parse(content)
        
        # Initialize metrics
        metrics = {
            "has_module_docstring": bool(ast.get_docstring(tree)),
            "documented_modules": 1 if ast.get_docstring(tree) else 0,
            "total_modules": 1,
            "documented_classes": 0,
            "total_classes": 0,
            "documented_functions": 0,
            "total_functions": 0,
            "documented_parameters": 0,
            "total_parameters": 0,
            "documented_returns": 0,
            "total_returns": 0,
            "undocumented_classes": [],
            "undocumented_functions": [],
            "undocumented_parameters": [],
            "undocumented_returns": []
        }
        
        # Analyze classes
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                metrics["total_classes"] += 1
                class_docstring = ast.get_docstring(node)
                
                if class_docstring:
                    metrics["documented_classes"] += 1
                else:
                    metrics["undocumented_classes"].append(node.name)
                
                # Analyze methods
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        metrics["total_functions"] += 1
                        method_docstring = ast.get_docstring(item)
                        
                        if method_docstring:
                            metrics["documented_functions"] += 1
                            
                            # Analyze parameter documentation
                            param_metrics = self._analyze_parameter_docs(item, method_docstring)
                            metrics["documented_parameters"] += param_metrics["documented"]
                            metrics["total_parameters"] += param_metrics["total"]
                            
                            if param_metrics["undocumented"]:
                                metrics["undocumented_parameters"].append({
                                    "function": f"{node.name}.{item.name}",
                                    "parameters": param_metrics["undocumented"]
                                })
                            
                            # Analyze return documentation
                            return_metrics = self._analyze_return_docs(item, method_docstring)
                            metrics["documented_returns"] += return_metrics["documented"]
                            metrics["total_returns"] += return_metrics["total"]
                            
                            if not return_metrics["documented"] and return_metrics["total"] > 0:
                                metrics["undocumented_returns"].append(f"{node.name}.{item.name}")
                        else:
                            metrics["undocumented_functions"].append(f"{node.name}.{item.name}")
            
            # Analyze top-level functions - check if it's not inside a class
            elif isinstance(node, ast.FunctionDef) and not any(
                isinstance(parent, ast.ClassDef)
                for parent in ast.walk(tree)
                if hasattr(parent, 'body') and node in parent.body
            ):
                metrics["total_functions"] += 1
                function_docstring = ast.get_docstring(node)
                
                if function_docstring:
                    metrics["documented_functions"] += 1
                    
                    # Analyze parameter documentation
                    param_metrics = self._analyze_parameter_docs(node, function_docstring)
                    metrics["documented_parameters"] += param_metrics["documented"]
                    metrics["total_parameters"] += param_metrics["total"]
                    
                    if param_metrics["undocumented"]:
                        metrics["undocumented_parameters"].append({
                            "function": node.name,
                            "parameters": param_metrics["undocumented"]
                        })
                    
                    # Analyze return documentation
                    return_metrics = self._analyze_return_docs(node, function_docstring)
                    metrics["documented_returns"] += return_metrics["documented"]
                    metrics["total_returns"] += return_metrics["total"]
                    
                    if not return_metrics["documented"] and return_metrics["total"] > 0:
                        metrics["undocumented_returns"].append(node.name)
                else:
                    metrics["undocumented_functions"].append(node.name)
        
        return metrics
    
    def _analyze_parameter_docs(self, func_node: ast.FunctionDef, docstring: str) -> Dict[str, Any]:
        """
        Analyze parameter documentation in a function docstring.
        
        Args:
            func_node: AST node for the function.
            docstring: Function docstring.
            
        Returns:
            Dictionary containing parameter documentation metrics.
        """
        # Get parameter names
        param_names = []
        for arg in func_node.args.args:
            if arg.arg != "self" and arg.arg != "cls":
                param_names.append(arg.arg)
        
        # Check for parameter documentation
        documented_params = set()
        
        # Check for Google style docstrings
        args_section = re.search(r"Args:(.*?)(?:\n\s*\n|\n\s*[A-Z][a-z]+:)", docstring, re.DOTALL)
        if args_section:
            args_text = args_section.group(1)
            for param in param_names:
                if re.search(rf"\n\s*{param}:", args_text):
                    documented_params.add(param)
        
        # Check for Sphinx style docstrings
        for param in param_names:
            if re.search(rf":param\s+{param}:", docstring):
                documented_params.add(param)
        
        # Calculate metrics
        total_params = len(param_names)
        documented_count = len(documented_params)
        undocumented_params = [p for p in param_names if p not in documented_params]
        
        return {
            "total": total_params,
            "documented": documented_count,
            "undocumented": undocumented_params
        }
    
    def _analyze_return_docs(self, func_node: ast.FunctionDef, docstring: str) -> Dict[str, Any]:
        """
        Analyze return value documentation in a function docstring.
        
        Args:
            func_node: AST node for the function.
            docstring: Function docstring.
            
        Returns:
            Dictionary containing return documentation metrics.
        """
        # Check if function has a return value
        has_return = False
        for node in ast.walk(func_node):
            if isinstance(node, ast.Return) and node.value is not None:
                has_return = True
                break
        
        # Check if function has a return type annotation
        has_return_annotation = func_node.returns is not None
        
        # If function doesn't return anything and doesn't have a return annotation, no need for return docs
        if not has_return and not has_return_annotation:
            return {"total": 0, "documented": 0}
        
        # Check for return documentation
        has_return_docs = False
        
        # Check for Google style docstrings
        if re.search(r"Returns:(.*?)(?:\n\s*\n|\n\s*[A-Z][a-z]+:|$)", docstring, re.DOTALL):
            has_return_docs = True
        
        # Check for Sphinx style docstrings
        if re.search(r":returns?:", docstring):
            has_return_docs = True
        
        return {
            "total": 1,
            "documented": 1 if has_return_docs else 0
        }
    
    def _get_component_name(self, file_path: str) -> str:
        """
        Get the component name for a file path.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            Component name.
        """
        parts = file_path.split(os.path.sep)
        if len(parts) > 1:
            return parts[0]
        return "root"
    
    def _calculate_coverage_percentages(self, metrics: Dict[str, Any]) -> None:
        """
        Calculate coverage percentages for all metrics.
        
        Args:
            metrics: Metrics dictionary to update with percentages.
        """
        # Calculate overall percentages
        overall = metrics["overall_metrics"]
        overall["module_coverage"] = overall["documented_modules"] / overall["total_modules"] if overall["total_modules"] > 0 else 1.0
        overall["class_coverage"] = overall["documented_classes"] / overall["total_classes"] if overall["total_classes"] > 0 else 1.0
        overall["function_coverage"] = overall["documented_functions"] / overall["total_functions"] if overall["total_functions"] > 0 else 1.0
        overall["parameter_coverage"] = overall["documented_parameters"] / overall["total_parameters"] if overall["total_parameters"] > 0 else 1.0
        overall["return_coverage"] = overall["documented_returns"] / overall["total_returns"] if overall["total_returns"] > 0 else 1.0
        
        # Calculate overall documentation coverage
        total_items = (overall["total_modules"] + overall["total_classes"] + 
                      overall["total_functions"] + overall["total_parameters"] + 
                      overall["total_returns"])
        documented_items = (overall["documented_modules"] + overall["documented_classes"] + 
                           overall["documented_functions"] + overall["documented_parameters"] + 
                           overall["documented_returns"])
        
        overall["overall_coverage"] = documented_items / total_items if total_items > 0 else 1.0
        
        # Calculate component percentages
        for component, comp_metrics in metrics["component_metrics"].items():
            comp_metrics["module_coverage"] = comp_metrics["documented_modules"] / comp_metrics["total_modules"] if comp_metrics["total_modules"] > 0 else 1.0
            comp_metrics["class_coverage"] = comp_metrics["documented_classes"] / comp_metrics["total_classes"] if comp_metrics["total_classes"] > 0 else 1.0
            comp_metrics["function_coverage"] = comp_metrics["documented_functions"] / comp_metrics["total_functions"] if comp_metrics["total_functions"] > 0 else 1.0
            comp_metrics["parameter_coverage"] = comp_metrics["documented_parameters"] / comp_metrics["total_parameters"] if comp_metrics["total_parameters"] > 0 else 1.0
            comp_metrics["return_coverage"] = comp_metrics["documented_returns"] / comp_metrics["total_returns"] if comp_metrics["total_returns"] > 0 else 1.0
            
            # Calculate component overall documentation coverage
            total_items = (comp_metrics["total_modules"] + comp_metrics["total_classes"] + 
                          comp_metrics["total_functions"] + comp_metrics["total_parameters"] + 
                          comp_metrics["total_returns"])
            documented_items = (comp_metrics["documented_modules"] + comp_metrics["documented_classes"] + 
                               comp_metrics["documented_functions"] + comp_metrics["documented_parameters"] + 
                               comp_metrics["documented_returns"])
            
            comp_metrics["overall_coverage"] = documented_items / total_items if total_items > 0 else 1.0
    
    def _export_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Export metrics to a JSON file.
        
        Args:
            metrics: Metrics dictionary to export.
        """
        # Ensure reports directory exists
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Write metrics to file
        with open(REPORTS_DIR / "documentation_coverage_metrics.json", "w") as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Documentation coverage metrics exported to {REPORTS_DIR}/documentation_coverage_metrics.json")
    
    def _generate_file_results(self, file_path: str, metrics: Dict[str, Any],
                              min_module_coverage: float, min_class_coverage: float,
                              min_function_coverage: float, min_param_coverage: float,
                              min_return_coverage: float) -> List[QualityCheckResult]:
        """
        Generate QualityCheckResult objects for a file.
        
        Args:
            file_path: Path to the file.
            metrics: Metrics dictionary for the file.
            min_module_coverage: Minimum required module docstring coverage.
            min_class_coverage: Minimum required class docstring coverage.
            min_function_coverage: Minimum required function docstring coverage.
            min_param_coverage: Minimum required parameter docstring coverage.
            min_return_coverage: Minimum required return value docstring coverage.
            
        Returns:
            List of QualityCheckResult objects.
        """
        results = []
        
        # Check module docstring
        if not metrics["has_module_docstring"]:
            results.append(QualityCheckResult(
                check_id=self.id,
                severity=QualityCheckSeverity.WARNING,
                message=f"Missing module docstring",
                file_path=file_path,
                line_number=1,
                source=self.name,
                fix_available=True,
                fix_command=f"python -m core.quality.components.fixes.documentation fix_missing_module_docstring {file_path}"
            ))
        
        # Check class docstrings
        for class_name in metrics["undocumented_classes"]:
            results.append(QualityCheckResult(
                check_id=self.id,
                severity=QualityCheckSeverity.WARNING,
                message=f"Missing docstring for class {class_name}",
                file_path=file_path,
                source=self.name
            ))
        
        # Check function docstrings
        for func_name in metrics["undocumented_functions"]:
            results.append(QualityCheckResult(
                check_id=self.id,
                severity=QualityCheckSeverity.WARNING,
                message=f"Missing docstring for function/method {func_name}",
                file_path=file_path,
                source=self.name
            ))
        
        # Check parameter docstrings
        for param_info in metrics["undocumented_parameters"]:
            func_name = param_info["function"]
            for param_name in param_info["parameters"]:
                results.append(QualityCheckResult(
                    check_id=self.id,
                    severity=QualityCheckSeverity.INFO,
                    message=f"Missing parameter documentation for '{param_name}' in {func_name}",
                    file_path=file_path,
                    source=self.name
                ))
        
        # Check return docstrings
        for func_name in metrics["undocumented_returns"]:
            results.append(QualityCheckResult(
                check_id=self.id,
                severity=QualityCheckSeverity.INFO,
                message=f"Missing return value documentation in {func_name}",
                file_path=file_path,
                source=self.name
            ))
        
        return results
    
    def _generate_overall_results(self, metrics: Dict[str, Any],
                                 min_module_coverage: float, min_class_coverage: float,
                                 min_function_coverage: float, min_param_coverage: float,
                                 min_return_coverage: float) -> List[QualityCheckResult]:
        """
        Generate overall QualityCheckResult objects.
        
        Args:
            metrics: Overall metrics dictionary.
            min_module_coverage: Minimum required module docstring coverage.
            min_class_coverage: Minimum required class docstring coverage.
            min_function_coverage: Minimum required function docstring coverage.
            min_param_coverage: Minimum required parameter docstring coverage.
            min_return_coverage: Minimum required return value docstring coverage.
            
        Returns:
            List of QualityCheckResult objects.
        """
        results = []
        overall = metrics["overall_metrics"]
        
        # Check overall coverage
        if overall["overall_coverage"] < 0.8:
            results.append(QualityCheckResult(
                check_id=self.id,
                severity=QualityCheckSeverity.WARNING,
                message=f"Overall documentation coverage is {overall['overall_coverage']:.1%}, which is below the recommended 80%",
                source=self.name
            ))
        
        # Check module coverage
        if overall["module_coverage"] < min_module_coverage:
            results.append(QualityCheckResult(
                check_id=self.id,
                severity=QualityCheckSeverity.WARNING,
                message=f"Module docstring coverage is {overall['module_coverage']:.1%}, which is below the minimum {min_module_coverage:.1%}",
                source=self.name
            ))
        
        # Check class coverage
        if overall["class_coverage"] < min_class_coverage:
            results.append(QualityCheckResult(
                check_id=self.id,
                severity=QualityCheckSeverity.WARNING,
                message=f"Class docstring coverage is {overall['class_coverage']:.1%}, which is below the minimum {min_class_coverage:.1%}",
                source=self.name
            ))
        
        # Check function coverage
        if overall["function_coverage"] < min_function_coverage:
            results.append(QualityCheckResult(
                check_id=self.id,
                severity=QualityCheckSeverity.WARNING,
                message=f"Function docstring coverage is {overall['function_coverage']:.1%}, which is below the minimum {min_function_coverage:.1%}",
                source=self.name
            ))
        
        # Check parameter coverage
        if overall["parameter_coverage"] < min_param_coverage:
            results.append(QualityCheckResult(
                check_id=self.id,
                severity=QualityCheckSeverity.INFO,
                message=f"Parameter docstring coverage is {overall['parameter_coverage']:.1%}, which is below the minimum {min_param_coverage:.1%}",
                source=self.name
            ))
        
        # Check return coverage
        if overall["return_coverage"] < min_return_coverage:
            results.append(QualityCheckResult(
                check_id=self.id,
                severity=QualityCheckSeverity.INFO,
                message=f"Return value docstring coverage is {overall['return_coverage']:.1%}, which is below the minimum {min_return_coverage:.1%}",
                source=self.name
            ))
        
        # Add component-specific results
        for component, comp_metrics in metrics["component_metrics"].items():
            if comp_metrics["overall_coverage"] < 0.7:
                results.append(QualityCheckResult(
                    check_id=self.id,
                    severity=QualityCheckSeverity.WARNING,
                    message=f"Component '{component}' has documentation coverage of {comp_metrics['overall_coverage']:.1%}, which is below the recommended 70%",
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