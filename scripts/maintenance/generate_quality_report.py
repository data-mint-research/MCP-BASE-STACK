#!/usr/bin/env python3
"""
Code Quality Metrics Dashboard Generator.

This script analyzes the codebase for various quality metrics and generates
a comprehensive HTML report with summary statistics, trend graphs, component
breakdowns, and hotspots that need attention. Historical data is stored in
a SQLite database for trend analysis.

Usage:
    python generate_quality_report.py [options]

Options:
    --format FORMAT       Output format (html, json, csv) [default: html]
    --output PATH         Output file path [default: code_quality_report.html]
    --type TYPE           Report type (full, summary, trends) [default: full]
    --components COMP     Comma-separated list of components to analyze
    --since DATE          Analyze changes since DATE (YYYY-MM-DD)
    --database PATH       Path to SQLite database [default: code_quality_history.db]
    --no-store            Don't store results in the database
    --help                Show this help message and exit
"""

import argparse
import ast
import csv
import datetime
import json
import logging
import os
import re
import sqlite3
import subprocess
import sys
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.figure import Figure
import base64
from io import BytesIO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "code_quality_history.db"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "code_quality_report.html"
KNOWLEDGE_GRAPH_PATH = PROJECT_ROOT / "core" / "kg" / "data" / "knowledge_graph.graphml"

# File extensions by language
LANGUAGE_EXTENSIONS = {
    "Python": [".py"],
    "JavaScript": [".js", ".jsx", ".ts", ".tsx"],
    "HTML": [".html", ".htm"],
    "CSS": [".css", ".scss", ".sass"],
    "Shell": [".sh", ".bash"],
    "Markdown": [".md"],
    "YAML": [".yaml", ".yml"],
    "JSON": [".json"],
    "Other": [],  # Catch-all for other extensions
}

# Directories to exclude from analysis
EXCLUDE_DIRS = [
    ".git",
    "__pycache__",
    "venv",
    "node_modules",
    "dist",
    "build",
    ".venv",
]


@dataclass
class FileMetrics:
    """Metrics for a single file."""

    path: str
    language: str
    component: str
    lines_total: int = 0
    lines_code: int = 0
    lines_comment: int = 0
    lines_blank: int = 0
    lines_docstring: int = 0
    complexity_cyclomatic: int = 0
    complexity_cognitive: int = 0
    has_type_hints: bool = False
    type_hint_coverage: float = 0.0
    functions_count: int = 0
    classes_count: int = 0
    documented_functions: int = 0
    documented_classes: int = 0
    test_coverage: float = 0.0
    issues: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ComponentMetrics:
    """Metrics for a component."""

    name: str
    files: List[FileMetrics] = field(default_factory=list)
    languages: Counter = field(default_factory=Counter)
    lines_total: int = 0
    lines_code: int = 0
    lines_comment: int = 0
    lines_blank: int = 0
    lines_docstring: int = 0
    complexity_cyclomatic: int = 0
    complexity_cognitive: int = 0
    type_hint_coverage: float = 0.0
    documentation_coverage: float = 0.0
    test_coverage: float = 0.0
    issues_count: int = 0

    def add_file(self, file_metrics: FileMetrics) -> None:
        """Add file metrics to component metrics."""
        self.files.append(file_metrics)
        self.languages[file_metrics.language] += 1
        self.lines_total += file_metrics.lines_total
        self.lines_code += file_metrics.lines_code
        self.lines_comment += file_metrics.lines_comment
        self.lines_blank += file_metrics.lines_blank
        self.lines_docstring += file_metrics.lines_docstring
        self.complexity_cyclomatic += file_metrics.complexity_cyclomatic
        self.complexity_cognitive += file_metrics.complexity_cognitive
        self.issues_count += len(file_metrics.issues)

    def calculate_averages(self) -> None:
        """Calculate average metrics for the component."""
        if not self.files:
            return

        # Calculate type hint coverage
        files_with_functions = [f for f in self.files if f.functions_count > 0]
        if files_with_functions:
            self.type_hint_coverage = sum(
                f.type_hint_coverage * f.functions_count for f in files_with_functions
            ) / sum(f.functions_count for f in files_with_functions)
        else:
            self.type_hint_coverage = 0.0

        # Calculate documentation coverage
        total_functions = sum(f.functions_count for f in self.files)
        total_classes = sum(f.classes_count for f in self.files)
        documented_functions = sum(f.documented_functions for f in self.files)
        documented_classes = sum(f.documented_classes for f in self.files)

        if total_functions + total_classes > 0:
            self.documentation_coverage = (
                documented_functions + documented_classes
            ) / (total_functions + total_classes)
        else:
            self.documentation_coverage = 0.0

        # Calculate test coverage (placeholder - would be populated from coverage tool)
        python_files = [f for f in self.files if f.language == "Python"]
        if python_files:
            self.test_coverage = sum(f.test_coverage for f in python_files) / len(
                python_files
            )
        else:
            self.test_coverage = 0.0


@dataclass
class CodebaseMetrics:
    """Metrics for the entire codebase."""

    components: Dict[str, ComponentMetrics] = field(default_factory=dict)
    languages: Counter = field(default_factory=Counter)
    lines_total: int = 0
    lines_code: int = 0
    lines_comment: int = 0
    lines_blank: int = 0
    lines_docstring: int = 0
    complexity_cyclomatic: int = 0
    complexity_cognitive: int = 0
    type_hint_coverage: float = 0.0
    documentation_coverage: float = 0.0
    test_coverage: float = 0.0
    issues_count: int = 0
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)

    def add_component(self, component_metrics: ComponentMetrics) -> None:
        """Add component metrics to codebase metrics."""
        self.components[component_metrics.name] = component_metrics
        self.lines_total += component_metrics.lines_total
        self.lines_code += component_metrics.lines_code
        self.lines_comment += component_metrics.lines_comment
        self.lines_blank += component_metrics.lines_blank
        self.lines_docstring += component_metrics.lines_docstring
        self.complexity_cyclomatic += component_metrics.complexity_cyclomatic
        self.complexity_cognitive += component_metrics.complexity_cognitive
        self.issues_count += component_metrics.issues_count

        # Update language counts
        for language, count in component_metrics.languages.items():
            self.languages[language] += count

    def calculate_averages(self) -> None:
        """Calculate average metrics for the codebase."""
        if not self.components:
            return

        # Calculate weighted averages
        total_files = sum(len(c.files) for c in self.components.values())
        if total_files > 0:
            self.type_hint_coverage = sum(
                c.type_hint_coverage * len(c.files) for c in self.components.values()
            ) / total_files
            self.documentation_coverage = sum(
                c.documentation_coverage * len(c.files) for c in self.components.values()
            ) / total_files
            self.test_coverage = sum(
                c.test_coverage * len(c.files) for c in self.components.values()
            ) / total_files


class CodeQualityAnalyzer:
    """Analyzer for code quality metrics."""

    def __init__(self, project_root: Path = PROJECT_ROOT):
        """Initialize the analyzer."""
        self.project_root = project_root
        self.metrics = CodebaseMetrics()
        self.component_map = self._load_component_map()

    def _load_component_map(self) -> Dict[str, str]:
        """
        Load component mapping from knowledge graph.
        
        Returns a dictionary mapping file paths to component names.
        Falls back to directory-based mapping if knowledge graph is not available.
        """
        component_map = {}
        
        try:
            # Try to load from knowledge graph
            if KNOWLEDGE_GRAPH_PATH.exists():
                g = nx.read_graphml(KNOWLEDGE_GRAPH_PATH)
                
                # Extract file to component mappings
                for source, target, attrs in g.edges(data=True):
                    if attrs.get("relation") == "contains":
                        # Component contains file relationship
                        source_node = g.nodes.get(source, {})
                        target_node = g.nodes.get(target, {})
                        
                        if (source_node.get("type") == "component" and 
                            target_node.get("type") == "file"):
                            file_path = target_node.get("path")
                            if file_path:
                                component_map[file_path] = source_node.get("name", source)
                
                logger.info(f"Loaded {len(component_map)} file-to-component mappings from knowledge graph")
                return component_map
        except Exception as e:
            logger.warning(f"Failed to load component map from knowledge graph: {e}")
        
        # Fallback: Use directory structure to determine components
        logger.info("Using directory structure for component mapping")
        return {}

    def _get_component_for_file(self, file_path: str) -> str:
        """Determine the component for a file."""
        # Check if we have a direct mapping from the knowledge graph
        rel_path = str(Path(file_path).relative_to(self.project_root))
        if rel_path in self.component_map:
            return self.component_map[rel_path]
        
        # Fallback: Use directory structure
        parts = Path(rel_path).parts
        if not parts:
            return "root"
        
        # Use first directory as component
        return parts[0]

    def _get_language_for_file(self, file_path: str) -> str:
        """Determine the language for a file based on its extension."""
        ext = Path(file_path).suffix.lower()
        for language, extensions in LANGUAGE_EXTENSIONS.items():
            if ext in extensions:
                return language
        return "Other"

    def _count_lines(self, file_path: str) -> Tuple[int, int, int, int]:
        """
        Count lines in a file.
        
        Returns:
            Tuple of (total_lines, code_lines, comment_lines, blank_lines)
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            # Skip binary files
            return 0, 0, 0, 0

        lines = content.splitlines()
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())
        
        # Language-specific comment detection
        ext = Path(file_path).suffix.lower()
        comment_lines = 0
        
        if ext in [".py"]:
            # Python comments and docstrings
            comment_pattern = re.compile(r'^\s*#.*$')
            comment_lines = sum(1 for line in lines if comment_pattern.match(line))
            
            # Docstrings are handled separately in analyze_python_file
            
        elif ext in [".js", ".jsx", ".ts", ".tsx"]:
            # JavaScript/TypeScript comments
            single_comment = re.compile(r'^\s*//.*$')
            comment_lines = sum(1 for line in lines if single_comment.match(line))
            
            # Handle multi-line comments
            in_comment = False
            for i, line in enumerate(lines):
                if "/*" in line and "*/" in line:
                    # Comment starts and ends on same line
                    if not single_comment.match(line):  # Don't double count
                        comment_lines += 1
                elif "/*" in line:
                    in_comment = True
                    comment_lines += 1
                elif "*/" in line:
                    in_comment = False
                    comment_lines += 1
                elif in_comment:
                    comment_lines += 1
                    
        elif ext in [".html", ".htm"]:
            # HTML comments
            in_comment = False
            for line in lines:
                if "<!--" in line and "-->" in line:
                    comment_lines += 1
                elif "<!--" in line:
                    in_comment = True
                    comment_lines += 1
                elif "-->" in line:
                    in_comment = False
                    comment_lines += 1
                elif in_comment:
                    comment_lines += 1
                    
        elif ext in [".sh", ".bash"]:
            # Shell comments
            comment_pattern = re.compile(r'^\s*#.*$')
            comment_lines = sum(1 for line in lines if comment_pattern.match(line))
            
        code_lines = total_lines - blank_lines - comment_lines
        
        return total_lines, code_lines, comment_lines, blank_lines

    def analyze_python_file(self, file_path: str) -> FileMetrics:
        """Analyze a Python file for metrics."""
        component = self._get_component_for_file(file_path)
        metrics = FileMetrics(
            path=str(Path(file_path).relative_to(self.project_root)),
            language="Python",
            component=component,
        )
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Count lines
            total_lines, code_lines, comment_lines, blank_lines = self._count_lines(file_path)
            metrics.lines_total = total_lines
            metrics.lines_code = code_lines
            metrics.lines_comment = comment_lines
            metrics.lines_blank = blank_lines
            
            # Parse the AST
            try:
                tree = ast.parse(content)
                
                # Count functions and classes
                function_nodes = []
                class_nodes = []
                docstring_lines = 0
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        function_nodes.append(node)
                        # Check for docstring
                        if (node.body and isinstance(node.body[0], ast.Expr) and 
                            isinstance(node.body[0].value, ast.Str)):
                            metrics.documented_functions += 1
                            docstring_lines += len(node.body[0].value.s.splitlines())
                            
                    elif isinstance(node, ast.ClassDef):
                        class_nodes.append(node)
                        # Check for docstring
                        if (node.body and isinstance(node.body[0], ast.Expr) and 
                            isinstance(node.body[0].value, ast.Str)):
                            metrics.documented_classes += 1
                            docstring_lines += len(node.body[0].value.s.splitlines())
                
                # Check for module docstring
                if (tree.body and isinstance(tree.body[0], ast.Expr) and 
                    isinstance(tree.body[0].value, ast.Str)):
                    docstring_lines += len(tree.body[0].value.s.splitlines())
                
                metrics.lines_docstring = docstring_lines
                metrics.functions_count = len(function_nodes)
                metrics.classes_count = len(class_nodes)
                
                # Calculate complexity metrics
                metrics.complexity_cyclomatic = self._calculate_cyclomatic_complexity(tree)
                metrics.complexity_cognitive = self._calculate_cognitive_complexity(tree)
                
                # Check type hints
                if function_nodes:
                    typed_functions = 0
                    for node in function_nodes:
                        # Check if function has type annotations
                        has_return_annotation = node.returns is not None
                        has_arg_annotation = any(arg.annotation is not None for arg in node.args.args)
                        if has_return_annotation or has_arg_annotation:
                            typed_functions += 1
                            
                    metrics.has_type_hints = typed_functions > 0
                    metrics.type_hint_coverage = typed_functions / len(function_nodes)
                
            except SyntaxError:
                # Handle syntax errors in Python files
                metrics.issues.append({
                    "type": "syntax_error",
                    "message": "Syntax error in file",
                    "severity": "high"
                })
                
        except Exception as e:
            logger.error(f"Error analyzing Python file {file_path}: {e}")
            metrics.issues.append({
                "type": "analysis_error",
                "message": f"Error analyzing file: {str(e)}",
                "severity": "medium"
            })
            
        return metrics

    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity for an AST node."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            # Statements that increase complexity
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(child, ast.BoolOp) and isinstance(child.op, ast.And):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.BoolOp) and isinstance(child.op, ast.Or):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.Try):
                complexity += len(child.handlers)  # Each except block
                
        return complexity

    def _calculate_cognitive_complexity(self, node: ast.AST) -> int:
        """Calculate cognitive complexity for an AST node."""
        complexity = 0
        nesting_level = 0
        
        def process_node(node, level):
            nonlocal complexity
            
            # Increment for control flow structures
            if isinstance(node, (ast.If, ast.While, ast.For, ast.Try)):
                complexity += level + 1
                
            # Recursively process children with increased nesting level
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.Try)):
                    process_node(child, level + 1)
                else:
                    process_node(child, level)
        
        process_node(node, nesting_level)
        return complexity

    def analyze_file(self, file_path: str) -> Optional[FileMetrics]:
        """Analyze a file for metrics."""
        ext = Path(file_path).suffix.lower()
        
        # Skip excluded directories
        if any(exclude_dir in str(file_path) for exclude_dir in EXCLUDE_DIRS):
            return None
            
        # Handle different file types
        if ext in [".py"]:
            return self.analyze_python_file(file_path)
        else:
            # Basic analysis for other file types
            language = self._get_language_for_file(file_path)
            component = self._get_component_for_file(file_path)
            
            total_lines, code_lines, comment_lines, blank_lines = self._count_lines(file_path)
            
            return FileMetrics(
                path=str(Path(file_path).relative_to(self.project_root)),
                language=language,
                component=component,
                lines_total=total_lines,
                lines_code=code_lines,
                lines_comment=comment_lines,
                lines_blank=blank_lines,
            )

    def analyze_codebase(self) -> CodebaseMetrics:
        """Analyze the entire codebase."""
        logger.info(f"Analyzing codebase at {self.project_root}")
        
        # Track components
        components: Dict[str, ComponentMetrics] = {}
        
        # Walk through the project directory
        for root, dirs, files in os.walk(self.project_root):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                # Skip files without extensions
                if not Path(file).suffix:
                    continue
                    
                # Analyze the file
                file_metrics = self.analyze_file(file_path)
                if file_metrics:
                    # Get or create component metrics
                    if file_metrics.component not in components:
                        components[file_metrics.component] = ComponentMetrics(
                            name=file_metrics.component
                        )
                    
                    # Add file metrics to component
                    components[file_metrics.component].add_file(file_metrics)
        
        # Calculate component averages
        for component in components.values():
            component.calculate_averages()
            self.metrics.add_component(component)
            
        # Calculate codebase averages
        self.metrics.calculate_averages()
        
        logger.info(f"Analysis complete. Found {len(components)} components.")
        return self.metrics

    def get_hotspots(self) -> List[Dict[str, Any]]:
        """Identify hotspots that need attention."""
        hotspots = []
        
        # Files with high complexity
        for component in self.metrics.components.values():
            for file in component.files:
                # High cyclomatic complexity
                if file.complexity_cyclomatic > 15:
                    hotspots.append({
                        "file": file.path,
                        "component": component.name,
                        "issue": "High cyclomatic complexity",
                        "value": file.complexity_cyclomatic,
                        "threshold": 15,
                        "severity": "high"
                    })
                
                # High cognitive complexity
                if file.complexity_cognitive > 20:
                    hotspots.append({
                        "file": file.path,
                        "component": component.name,
                        "issue": "High cognitive complexity",
                        "value": file.complexity_cognitive,
                        "threshold": 20,
                        "severity": "high"
                    })
                
                # Low type hint coverage for Python files
                if file.language == "Python" and file.functions_count > 3 and file.type_hint_coverage < 0.5:
                    hotspots.append({
                        "file": file.path,
                        "component": component.name,
                        "issue": "Low type hint coverage",
                        "value": f"{file.type_hint_coverage:.1%}",
                        "threshold": "50%",
                        "severity": "medium"
                    })
                
                # Low documentation coverage
                if (file.functions_count + file.classes_count > 3 and 
                    (file.documented_functions + file.documented_classes) / 
                    (file.functions_count + file.classes_count) < 0.7):
                    hotspots.append({
                        "file": file.path,
                        "component": component.name,
                        "issue": "Low documentation coverage",
                        "value": f"{(file.documented_functions + file.documented_classes) / (file.functions_count + file.classes_count):.1%}",
                        "threshold": "70%",
                        "severity": "medium"
                    })
                
                # Files with specific issues
                for issue in file.issues:
                    hotspots.append({
                        "file": file.path,
                        "component": component.name,
                        "issue": issue["message"],
                        "severity": issue["severity"]
                    })
        
        return hotspots


class DatabaseManager:
    """Manager for the SQLite database."""

    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        """Initialize the database manager."""
        self.db_path = db_path
        self._ensure_db_exists()

    def _ensure_db_exists(self) -> None:
        """Ensure the database exists and has the required tables."""
        # Create directory if it doesn't exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Connect to the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS codebase_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            lines_total INTEGER,
            lines_code INTEGER,
            lines_comment INTEGER,
            lines_blank INTEGER,
            lines_docstring INTEGER,
            complexity_cyclomatic INTEGER,
            complexity_cognitive INTEGER,
            type_hint_coverage REAL,
            documentation_coverage REAL,
            test_coverage REAL,
            issues_count INTEGER
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS component_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codebase_id INTEGER,
            name TEXT,
            lines_total INTEGER,
            lines_code INTEGER,
            lines_comment INTEGER,
            lines_blank INTEGER,
            lines_docstring INTEGER,
            complexity_cyclomatic INTEGER,
            complexity_cognitive INTEGER,
            type_hint_coverage REAL,
            documentation_coverage REAL,
            test_coverage REAL,
            issues_count INTEGER,
            FOREIGN KEY (codebase_id) REFERENCES codebase_metrics (id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS language_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codebase_id INTEGER,
            language TEXT,
            file_count INTEGER,
            lines_total INTEGER,
            FOREIGN KEY (codebase_id) REFERENCES codebase_metrics (id)
        )
        ''')
        
        conn.commit()
        conn.close()

    def store_metrics(self, metrics: CodebaseMetrics) -> int:
        """Store metrics in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Store codebase metrics
        cursor.execute('''
        INSERT INTO codebase_metrics (
            timestamp, lines_total, lines_code, lines_comment, lines_blank,
            lines_docstring, complexity_cyclomatic, complexity_cognitive,
            type_hint_coverage, documentation_coverage, test_coverage, issues_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metrics.timestamp.isoformat(),
            metrics.lines_total,
            metrics.lines_code,
            metrics.lines_comment,
            metrics.lines_blank,
            metrics.lines_docstring,
            metrics.complexity_cyclomatic,
            metrics.complexity_cognitive,
            metrics.type_hint_coverage,
            metrics.documentation_coverage,
            metrics.test_coverage,
            metrics.issues_count
        ))
        
        codebase_id = cursor.lastrowid
        
        # Store component metrics
        for component in metrics.components.values():
            cursor.execute('''
            INSERT INTO component_metrics (
                codebase_id, name, lines_total, lines_code, lines_comment, lines_blank,
                lines_docstring, complexity_cyclomatic, complexity_cognitive,
                type_hint_coverage, documentation_coverage, test_coverage, issues_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                codebase_id,
                component.name,
                component.lines_total,
                component.lines_code,
                component.lines_comment,
                component.lines_blank,
                component.lines_docstring,
                component.complexity_cyclomatic,
                component.complexity_cognitive,
                component.type_hint_coverage,
                component.documentation_coverage,
                component.test_coverage,
                component.issues_count
            ))
        
        # Store language metrics
        for language, count in metrics.languages.items():
            cursor.execute('''
            INSERT INTO language_metrics (
                codebase_id, language, file_count, lines_total
            ) VALUES (?, ?, ?, ?)
            ''', (
                codebase_id,
                language,
                count,
                sum(f.lines_total for c in metrics.components.values() 
                    for f in c.files if f.language == language)
            ))
        
        conn.commit()
        conn.close()
        
        return codebase_id

    def get_historical_metrics(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get historical metrics for trend analysis."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get metrics from the last N days
        cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
        
        cursor.execute('''
        SELECT * FROM codebase_metrics
        WHERE timestamp >= ?
        ORDER BY timestamp
        ''', (cutoff_date,))
        
        metrics = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return metrics

    def get_component_history(self, component_name: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get historical metrics for a specific component."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get metrics from the last N days
        cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
        
        cursor.execute('''
        SELECT cm.*, c.timestamp
        FROM component_metrics cm
        JOIN codebase_metrics c ON cm.codebase_id = c.id
        WHERE cm.name = ? AND c.timestamp >= ?
        ORDER BY c.timestamp
        ''', (component_name, cutoff_date))
        
        metrics = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return metrics


class ReportGenerator:
    """Generator for code quality reports."""

        """Initialize the report generator."""
        self.metrics = metrics
        self.db_manager = db_manager
        
    def _create_figure(self, title: str, x_data: List, y_data: List, 
                      xlabel: str, ylabel: str) -> str:
        """Create a base64-encoded figure for embedding in HTML."""
        fig = plt.figure(figsize=(10, 6))
        plt.plot(x_data, y_data, marker='o')
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.grid(True)
        plt.tight_layout()
        
        # Convert plot to base64 string
        buf = BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return f'data:image/png;base64,{img_str}'
        
    def _create_pie_chart(self, title: str, labels: List[str], 
                         sizes: List[float]) -> str:
        """Create a base64-encoded pie chart for embedding in HTML."""
        fig = plt.figure(figsize=(8, 8))
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        plt.title(title)
        plt.tight_layout()
        
        # Convert plot to base64 string
        buf = BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return f'data:image/png;base64,{img_str}'
    
    def _create_bar_chart(self, title: str, labels: List[str], 
                         values: List[float], xlabel: str, ylabel: str) -> str:
        """Create a base64-encoded bar chart for embedding in HTML."""
        fig = plt.figure(figsize=(12, 6))
        plt.bar(labels, values)
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Convert plot to base64 string
        buf = BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return f'data:image/png;base64,{img_str}'
    
    def _generate_trend_graphs(self, historical_metrics: List[Dict[str, Any]]) -> Dict[str, str]:
        """Generate trend graphs from historical metrics."""
        if not historical_metrics:
            return {}
            
        # Extract timestamps and convert to datetime objects
        timestamps = [datetime.datetime.fromisoformat(m['timestamp']) for m in historical_metrics]
        dates = [ts.strftime('%Y-%m-%d') for ts in timestamps]
        
        # Generate trend graphs
        graphs = {}
        
        # Lines of code trend
        graphs['lines_code'] = self._create_figure(
            'Lines of Code Over Time',
            dates,
            [m['lines_code'] for m in historical_metrics],
            'Date',
            'Lines of Code'
        )
        
        # Type hint coverage trend
        graphs['type_hint_coverage'] = self._create_figure(
            'Type Hint Coverage Over Time',
            dates,
            [m['type_hint_coverage'] * 100 for m in historical_metrics],
            'Date',
            'Type Hint Coverage (%)'
        )
        
        # Documentation coverage trend
        graphs['documentation_coverage'] = self._create_figure(
            'Documentation Coverage Over Time',
            dates,
            [m['documentation_coverage'] * 100 for m in historical_metrics],
            'Date',
            'Documentation Coverage (%)'
        )
        
        # Complexity trend
        graphs['complexity'] = self._create_figure(
            'Complexity Over Time',
            dates,
            [m['complexity_cyclomatic'] for m in historical_metrics],
            'Date',
            'Cyclomatic Complexity'
        )
        
        # Issues count trend
        graphs['issues'] = self._create_figure(
            'Issues Over Time',
            dates,
            [m['issues_count'] for m in historical_metrics],
            'Date',
            'Number of Issues'
        )
        
        return graphs
    
    def _generate_component_graphs(self) -> Dict[str, str]:
        """Generate graphs for component metrics."""
        graphs = {}
        
        # Component lines of code
        component_names = list(self.metrics.components.keys())
        component_loc = [c.lines_code for c in self.metrics.components.values()]
        
        if component_names:
            graphs['component_loc'] = self._create_bar_chart(
                'Lines of Code by Component',
                component_names,
                component_loc,
                'Component',
                'Lines of Code'
            )
        
        # Language distribution
        language_names = list(self.metrics.languages.keys())
        language_counts = list(self.metrics.languages.values())
        
        if language_names:
            graphs['language_distribution'] = self._create_pie_chart(
                'Language Distribution',
                language_names,
                language_counts
            )
        
        # Component complexity
        component_complexity = [c.complexity_cyclomatic for c in self.metrics.components.values()]
        
        if component_names:
            graphs['component_complexity'] = self._create_bar_chart(
                'Cyclomatic Complexity by Component',
                component_names,
                component_complexity,
                'Component',
                'Cyclomatic Complexity'
            )
        
        # Component documentation coverage
        component_doc_coverage = [c.documentation_coverage * 100 for c in self.metrics.components.values()]
        
        if component_names:
            graphs['component_doc_coverage'] = self._create_bar_chart(
                'Documentation Coverage by Component',
                component_names,
                component_doc_coverage,
                'Component',
                'Documentation Coverage (%)'
            )
        
        # Component type hint coverage
        component_type_coverage = [c.type_hint_coverage * 100 for c in self.metrics.components.values()]
        
        if component_names:
            graphs['component_type_coverage'] = self._create_bar_chart(
                'Type Hint Coverage by Component',
                component_names,
                component_type_coverage,
                'Component',
                'Type Hint Coverage (%)'
            )
        
        return graphs
    
    def generate_html_report(self, output_path: Path, report_type: str = 'full') -> None:
        """Generate an HTML report."""
        logger.info(f'Generating {report_type} HTML report at {output_path}')
        
        # Get historical metrics for trend analysis
        historical_metrics = self.db_manager.get_historical_metrics()
        
        # Generate graphs
        trend_graphs = self._generate_trend_graphs(historical_metrics)
        component_graphs = self._generate_component_graphs()
        
        # Get hotspots
        hotspots = CodeQualityAnalyzer().get_hotspots()
        
        # Generate HTML content
        html_content = f'''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Code Quality Report - {datetime.datetime.now().strftime('%Y-%m-%d')}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                h1, h2, h3 {{
                    color: #2c3e50;
                }}
                .summary-box {{
                    background-color: #f8f9fa;
                    border-radius: 5px;
                    padding: 20px;
                    margin-bottom: 20px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }}
                .metric {{
                    display: inline-block;
                    width: 30%;
                    margin: 10px;
                    text-align: center;
                }}
                .metric-value {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #3498db;
                }}
                .metric-label {{
                    font-size: 14px;
                    color: #7f8c8d;
                }}
                .graph-container {{
                    margin: 20px 0;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th, td {{
                    padding: 12px 15px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
                tr:hover {{
                    background-color: #f5f5f5;
                }}
                .severity-high {{
                    color: #e74c3c;
                    font-weight: bold;
                }}
                .severity-medium {{
                    color: #f39c12;
                }}
                .severity-low {{
                    color: #3498db;
                }}
                .footer {{
                    margin-top: 40px;
                    text-align: center;
                    font-size: 12px;
                    color: #7f8c8d;
                }}
            </style>
        </head>
        <body>
            <h1>Code Quality Report</h1>
            <p>Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div class="summary-box">
                <h2>Summary</h2>
                <div class="metric">
                    <div class="metric-value">{self.metrics.lines_total:,}</div>
                    <div class="metric-label">Total Lines</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{self.metrics.lines_code:,}</div>
                    <div class="metric-label">Lines of Code</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{len(self.metrics.components)}</div>
                    <div class="metric-label">Components</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{self.metrics.type_hint_coverage:.1%}</div>
                    <div class="metric-label">Type Hint Coverage</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{self.metrics.documentation_coverage:.1%}</div>
                    <div class="metric-label">Documentation Coverage</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{self.metrics.issues_count}</div>
                    <div class="metric-label">Issues</div>
                </div>
            </div>
        '''
        
        # Add trend graphs if available and report type includes trends
        if trend_graphs and report_type in ['full', 'trends']:
            html_content += '''
            <h2>Trends</h2>
            <div class="graph-container">
            '''
            
            for name, graph in trend_graphs.items():
                html_content += f'''
                <div>
                    <img src="{graph}" alt="{name} trend" style="max-width: 100%;">
                </div>
                '''
                
            html_content += '</div>'
        
        # Add component breakdown if report type includes it
        if report_type in ['full', 'summary']:
            html_content += '''
            <h2>Component Breakdown</h2>
            <div class="graph-container">
            '''
            
            for name, graph in component_graphs.items():
                html_content += f'''
                <div>
                    <img src="{graph}" alt="{name}" style="max-width: 100%;">
                </div>
                '''
                
            html_content += '''
            </div>
            
            <h3>Component Details</h3>
            <table>
                <tr>
                    <th>Component</th>
                    <th>Files</th>
                    <th>Lines of Code</th>
                    <th>Cyclomatic Complexity</th>
                    <th>Type Hint Coverage</th>
                    <th>Documentation Coverage</th>
                    <th>Issues</th>
                </tr>
            '''
            
            for name, component in self.metrics.components.items():
                html_content += f'''
                <tr>
                    <td>{name}</td>
                    <td>{len(component.files)}</td>
                    <td>{component.lines_code:,}</td>
                    <td>{component.complexity_cyclomatic}</td>
                    <td>{component.type_hint_coverage:.1%}</td>
                    <td>{component.documentation_coverage:.1%}</td>
                    <td>{component.issues_count}</td>
                </tr>
                '''
                
            html_content += '</table>'
        
        # Add hotspots if report type includes them
        if hotspots and report_type in ['full', 'summary']:
            html_content += '''
            <h2>Hotspots</h2>
            <p>Files that need attention based on code quality metrics.</p>
            <table>
                <tr>
                    <th>File</th>
                    <th>Component</th>
                    <th>Issue</th>
                    <th>Severity</th>
                </tr>
            '''
            
            for hotspot in hotspots:
                severity_class = f'severity-{hotspot.get("severity", "medium")}'
                html_content += f'''
                <tr>
                    <td>{hotspot.get("file", "")}</td>
                    <td>{hotspot.get("component", "")}</td>
                    <td>{hotspot.get("issue", "")} {hotspot.get("value", "")}</td>
                    <td class="{severity_class}">{hotspot.get("severity", "").upper()}</td>
                </tr>
                '''
                
            html_content += '</table>'
        
        # Close HTML
        html_content += '''
            <div class="footer">
                <p>Generated by Code Quality Metrics Dashboard Generator</p>
            </div>
        </body>
        </html>
        '''
        
        # Write HTML to file
        with open(output_path, 'w') as f:
            f.write(html_content)
            
        logger.info(f'HTML report generated at {output_path}')
    
    def generate_json_report(self, output_path: Path) -> None:
        """Generate a JSON report."""
        logger.info(f'Generating JSON report at {output_path}')
        
        # Create a serializable representation of the metrics
        report_data = {
            'timestamp': self.metrics.timestamp.isoformat(),
            'summary': {
                'lines_total': self.metrics.lines_total,
                'lines_code': self.metrics.lines_code,
                'lines_comment': self.metrics.lines_comment,
                'lines_blank': self.metrics.lines_blank,
                'lines_docstring': self.metrics.lines_docstring,
                'complexity_cyclomatic': self.metrics.complexity_cyclomatic,
                'complexity_cognitive': self.metrics.complexity_cognitive,
                'type_hint_coverage': self.metrics.type_hint_coverage,
                'documentation_coverage': self.metrics.documentation_coverage,
                'test_coverage': self.metrics.test_coverage,
                'issues_count': self.metrics.issues_count,
                'components_count': len(self.metrics.components),
                'languages': dict(self.metrics.languages)
            },
            'components': {}
        }
        
        # Add component data
        for name, component in self.metrics.components.items():
            report_data['components'][name] = {
                'files_count': len(component.files),
                'lines_total': component.lines_total,
                'lines_code': component.lines_code,
                'lines_comment': component.lines_comment,
                'lines_blank': component.lines_blank,
                'lines_docstring': component.lines_docstring,
                'complexity_cyclomatic': component.complexity_cyclomatic,
                'complexity_cognitive': component.complexity_cognitive,
                'type_hint_coverage': component.type_hint_coverage,
                'documentation_coverage': component.documentation_coverage,
                'test_coverage': component.test_coverage,
                'issues_count': component.issues_count,
                'languages': dict(component.languages)
            }
        
        # Add hotspots
        report_data['hotspots'] = CodeQualityAnalyzer().get_hotspots()
        
        # Write JSON to file
        with open(output_path, 'w') as f:
            json.dump(report_data, f, indent=2)
            
        logger.info(f'JSON report generated at {output_path}')
    
    def generate_csv_report(self, output_path: Path) -> None:
        """Generate a CSV report."""
        logger.info(f'Generating CSV report at {output_path}')
        
        # Create CSV file
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'Component',
                'Files',
                'Lines Total',
                'Lines Code',
                'Lines Comment',
                'Lines Blank',
                'Lines Docstring',
                'Cyclomatic Complexity',
                'Cognitive Complexity',
                'Type Hint Coverage',
                'Documentation Coverage',
                'Test Coverage',
                'Issues'
            ])
            
            # Write summary row
            writer.writerow([
                'TOTAL',
                sum(len(c.files) for c in self.metrics.components.values()),
                self.metrics.lines_total,
                self.metrics.lines_code,
                self.metrics.lines_comment,
                self.metrics.lines_blank,
                self.metrics.lines_docstring,
                self.metrics.complexity_cyclomatic,
                self.metrics.complexity_cognitive,
                f'{self.metrics.type_hint_coverage:.1%}',
                f'{self.metrics.documentation_coverage:.1%}',
                f'{self.metrics.test_coverage:.1%}',
                self.metrics.issues_count
            ])
            
            # Write component rows
            for name, component in self.metrics.components.items():
                writer.writerow([
                    name,
                    len(component.files),
                    component.lines_total,
                    component.lines_code,
                    component.lines_comment,
                    component.lines_blank,
                    component.lines_docstring,
                    component.complexity_cyclomatic,
                    component.complexity_cognitive,
                    f'{component.type_hint_coverage:.1%}',
                    f'{component.documentation_coverage:.1%}',
                    f'{component.test_coverage:.1%}',
                    component.issues_count
                ])
                
        logger.info(f'CSV report generated at {output_path}')
    
    def generate_report(self, output_path: Path, format_type: str = 'html', 
                       report_type: str = 'full') -> None:
        """Generate a report in the specified format."""
        if format_type == 'html':
            self.generate_html_report(output_path, report_type)
        elif format_type == 'json':
            self.generate_json_report(output_path)
        elif format_type == 'csv':
            self.generate_csv_report(output_path)
        else:
            logger.error(f'Unsupported format: {format_type}')
            raise ValueError(f'Unsupported format: {format_type}')


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate code quality metrics report',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--format',
        choices=['html', 'json', 'csv'],
        default='html',
        help='Output format'
    )
    
    parser.add_argument(
        '--output',
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help='Output file path'
    )
    
    parser.add_argument(
        '--type',
        choices=['full', 'summary', 'trends'],
        default='full',
        help='Report type'
    )
    
    parser.add_argument(
        '--components',
        help='Comma-separated list of components to analyze'
    )
    
    parser.add_argument(
        '--since',
        help='Analyze changes since DATE (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--database',
        type=Path,
        default=DEFAULT_DB_PATH,
        help='Path to SQLite database'
    )
    
    parser.add_argument(
        '--no-store',
        action='store_true',
        help='Don\'t store results in the database'
    )
    
    return parser.parse_args()


def main() -> None:
    """Main function."""
    # Parse command line arguments
    args = parse_args()
    
    # Initialize database manager
    db_manager = DatabaseManager(args.database)
    
    # Initialize analyzer
    analyzer = CodeQualityAnalyzer()
    
    # Analyze codebase
    metrics = analyzer.analyze_codebase()
    
    # Store metrics in database if not disabled
    if not args.no_store:
        db_manager.store_metrics(metrics)
    
    # Initialize report generator
    report_generator = ReportGenerator(metrics, db_manager)
    
    # Generate report
    report_generator.generate_report(args.output, args.format, args.type)
    
    logger.info(f'Report generated at {args.output}')


if __name__ == '__main__':
    main()
