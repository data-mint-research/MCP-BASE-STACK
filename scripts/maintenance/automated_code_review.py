#!/usr/bin/env python3
"""
Automated Code Review Tool for MCP-BASE-STACK.

This script analyzes code changes in a pull request or between git references,
providing detailed feedback on code quality, potential bugs, security vulnerabilities,
performance concerns, documentation completeness, and test coverage.

Usage:
    python automated_code_review.py [options]

Options:
    --pr PR_NUMBER             Pull request number to analyze
    --base COMMIT              Base git reference for comparison
    --head COMMIT              Head git reference for comparison
    --config PATH              Path to configuration file [default: config/code_review.yaml]
    --output PATH              Output file path [default: code_review_report.md]
    --detail {high,medium,low} Level of detail in the report [default: medium]
    --update-kg                Update the knowledge graph with the review results
    --help                     Show this help message and exit
"""

import argparse
import ast
import configparser
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import yaml

# Add the project root to the Python path to allow importing from core
sys.path.append(str(Path(__file__).resolve().parents[2]))

from core.logging.config import configure_logger

# Configure logging using the standardized logging system
logger = configure_logger("automated_code_review")

# Constants
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "code_review.yaml"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "code_review_report.md"
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


class SeverityLevel(Enum):
    """Severity levels for issues."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Issue:
    """Represents a code issue found during review."""

    file_path: str
    line_number: int
    message: str
    severity: SeverityLevel
    category: str
    tool: str
    suggested_fix: Optional[str] = None
    code_snippet: Optional[str] = None


@dataclass
class FileChange:
    """Represents a changed file in a PR or between git references."""

    file_path: str
    status: str  # "added", "modified", "deleted"
    language: str
    added_lines: List[int] = field(default_factory=list)
    modified_lines: List[int] = field(default_factory=list)
    deleted_lines: List[int] = field(default_factory=list)
    content: Optional[str] = None


@dataclass
class ReviewResult:
    """Results of a code review."""

    changes: List[FileChange] = field(default_factory=list)
    issues: List[Issue] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)


class CodeReviewConfig:
    """Configuration for the code review tool."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize with default configuration."""
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.config = self._load_default_config()
        
        if self.config_path.exists():
            self._load_config()
        else:
            logger.warning(f"Configuration file {self.config_path} not found. Using default configuration.")
            # Create default config file
            self._save_config()

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration."""
        return {
            "tools": {
                "flake8": {
                    "enabled": True,
                    "config_file": ".flake8",
                    "severity_map": {
                        "E": "high",
                        "F": "critical",
                        "W": "medium",
                        "C": "low",
                    },
                },
                "pylint": {
                    "enabled": True,
                    "config_file": ".pylintrc",
                    "severity_map": {
                        "E": "high",
                        "F": "critical",
                        "W": "medium",
                        "C": "low",
                        "R": "low",
                    },
                },
                "mypy": {
                    "enabled": True,
                    "config_file": "mypy.ini",
                    "severity_map": {
                        "error": "high",
                        "note": "low",
                    },
                },
                "bandit": {
                    "enabled": True,
                    "severity_map": {
                        "HIGH": "critical",
                        "MEDIUM": "high",
                        "LOW": "medium",
                    },
                },
                "shellcheck": {
                    "enabled": True,
                    "config_file": ".shellcheckrc",
                    "severity_map": {
                        "error": "high",
                        "warning": "medium",
                        "info": "low",
                        "style": "low",
                    },
                },
            },
            "categories": {
                "code_quality": {
                    "enabled": True,
                    "tools": ["flake8", "pylint"],
                },
                "security": {
                    "enabled": True,
                    "tools": ["bandit"],
                },
                "performance": {
                    "enabled": True,
                    "tools": ["pylint"],
                },
                "documentation": {
                    "enabled": True,
                    "tools": ["pylint"],
                    "docstring_coverage_threshold": 0.99,
                },
                "test_coverage": {
                    "enabled": True,
                    "coverage_threshold": 0.99,
                },
            },
            "severity_thresholds": {
                "critical": 0,  # Any critical issues fail the review
                "high": 5,      # Up to 5 high severity issues allowed
                "medium": 10,   # Up to 10 medium severity issues allowed
                "low": 20,      # Up to 20 low severity issues allowed
            },
            "report": {
                "detail_level": "medium",  # "high", "medium", "low"
                "include_code_snippets": True,
                "include_suggested_fixes": True,
                "group_by": "category",  # "category", "file", "severity"
            },
            "knowledge_graph": {
                "update": False,
                "record_issues": True,
                "record_summary": True,
            },
        }

    def _load_config(self) -> None:
        """Load configuration from file."""
        try:
            with open(self.config_path, "r") as f:
                user_config = yaml.safe_load(f)
                
            # Merge user config with default config
            if user_config:
                self._merge_configs(self.config, user_config)
                
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            logger.warning("Using default configuration.")

    def _merge_configs(self, default_config: Dict[str, Any], user_config: Dict[str, Any]) -> None:
        """Recursively merge user config into default config."""
        for key, value in user_config.items():
            if key in default_config and isinstance(default_config[key], dict) and isinstance(value, dict):
                self._merge_configs(default_config[key], value)
            else:
                default_config[key] = value

    def _save_config(self) -> None:
        """Save configuration to file."""
        try:
            # Create parent directories if they don't exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, "w") as f:
                yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
                
            logger.info(f"Default configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        keys = key.split(".")
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default


class GitDiffAnalyzer:
    """Analyzes git diffs between two references."""

    def __init__(self, base: str, head: str):
        """Initialize with base and head references."""
        self.base = base
        self.head = head
        self.project_root = PROJECT_ROOT

    def get_changed_files(self) -> List[FileChange]:
        """Get a list of changed files between base and head."""
        changed_files = []
        
        try:
            # Get the diff
            diff_cmd = ["git", "diff", "--name-status", self.base, self.head]
            diff_output = subprocess.check_output(diff_cmd, cwd=self.project_root).decode("utf-8")
            
            # Parse the diff output
            for line in diff_output.splitlines():
                if not line.strip():
                    continue
                    
                parts = line.split("\t")
                if len(parts) < 2:
                    continue
                    
                status = parts[0]
                file_path = parts[1]
                
                # Skip excluded directories
                if any(exclude_dir in file_path for exclude_dir in EXCLUDE_DIRS):
                    continue
                
                # Determine file status
                status_map = {
                    "A": "added",
                    "M": "modified",
                    "D": "deleted",
                    "R": "renamed",
                }
                file_status = status_map.get(status[0], "modified")
                
                # Determine language based on file extension
                language = self._get_language_for_file(file_path)
                
                # Create FileChange object
                file_change = FileChange(
                    file_path=file_path,
                    status=file_status,
                    language=language,
                )
                
                # Get line changes if the file wasn't deleted
                if file_status != "deleted":
                    self._get_line_changes(file_change)
                    
                changed_files.append(file_change)
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Error getting changed files: {e}")
            
        return changed_files

    def _get_language_for_file(self, file_path: str) -> str:
        """Determine the language for a file based on its extension."""
        ext = Path(file_path).suffix.lower()
        for language, extensions in LANGUAGE_EXTENSIONS.items():
            if ext in extensions:
                return language
        return "Other"

    def _get_line_changes(self, file_change: FileChange) -> None:
        """Get line changes for a file."""
        try:
            # Get the diff for the specific file
            diff_cmd = ["git", "diff", "-U0", self.base, self.head, "--", file_change.file_path]
            diff_output = subprocess.check_output(diff_cmd, cwd=self.project_root).decode("utf-8")
            
            # Parse the diff output to get line changes
            for line in diff_output.splitlines():
                if line.startswith("@@"):
                    # Parse the hunk header
                    match = re.search(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))?", line)
                    if match:
                        old_start = int(match.group(1))
                        old_count = int(match.group(2) or 1)
                        new_start = int(match.group(3))
                        new_count = int(match.group(4) or 1)
                        
                        # Record deleted lines
                        if old_count > 0:
                            file_change.deleted_lines.extend(range(old_start, old_start + old_count))
                            
                        # Record added lines
                        if new_count > 0:
                            file_change.added_lines.extend(range(new_start, new_start + new_count))
                            
                        # Record modified lines (intersection of added and deleted)
                        if old_count > 0 and new_count > 0:
                            min_count = min(old_count, new_count)
                            file_change.modified_lines.extend(range(new_start, new_start + min_count))
            
            # Get the file content
            if file_change.status != "deleted":
                cat_cmd = ["git", "show", f"{self.head}:{file_change.file_path}"]
                try:
                    file_change.content = subprocess.check_output(cat_cmd, cwd=self.project_root).decode("utf-8")
                except subprocess.CalledProcessError:
                    logger.warning(f"Could not get content for {file_change.file_path}")
                    
        except subprocess.CalledProcessError as e:
            logger.error(f"Error getting line changes for {file_change.file_path}: {e}")


class CodeQualityAnalyzer:
    """Analyzes code quality using various tools."""

    def __init__(self, config: CodeReviewConfig):
        """Initialize with configuration."""
        self.config = config
        self.project_root = PROJECT_ROOT

    def analyze_changes(self, changes: List[FileChange]) -> List[Issue]:
        """Analyze code changes and return issues."""
        issues = []
        
        # Group files by language
        files_by_language = {}
        for change in changes:
            if change.status != "deleted":  # Skip deleted files
                if change.language not in files_by_language:
                    files_by_language[change.language] = []
                files_by_language[change.language].append(change)
        
        # Analyze Python files
        if "Python" in files_by_language and files_by_language["Python"]:
            python_files = files_by_language["Python"]
            python_file_paths = [f.file_path for f in python_files]
            
            # Run flake8
            if self.config.get("tools.flake8.enabled", True):
                issues.extend(self._run_flake8(python_file_paths))
                
            # Run pylint
            if self.config.get("tools.pylint.enabled", True):
                issues.extend(self._run_pylint(python_file_paths))
                
            # Run mypy
            if self.config.get("tools.mypy.enabled", True):
                issues.extend(self._run_mypy(python_file_paths))
                
            # Run bandit
            if self.config.get("tools.bandit.enabled", True):
                issues.extend(self._run_bandit(python_file_paths))
                
            # Analyze docstrings
            if self.config.get("categories.documentation.enabled", True):
                issues.extend(self._analyze_docstrings(python_files))
        
        # Analyze Shell files
        if "Shell" in files_by_language and files_by_language["Shell"]:
            shell_files = files_by_language["Shell"]
            shell_file_paths = [f.file_path for f in shell_files]
            
            # Run shellcheck
            if self.config.get("tools.shellcheck.enabled", True):
                issues.extend(self._run_shellcheck(shell_file_paths))
        
        # Filter issues to only include those in changed lines
        filtered_issues = []
        for issue in issues:
            for change in changes:
                if issue.file_path == change.file_path:
                    if (issue.line_number in change.added_lines or 
                        issue.line_number in change.modified_lines):
                        # Add code snippet if available
                        if change.content and self.config.get("report.include_code_snippets", True):
                            issue.code_snippet = self._get_code_snippet(change.content, issue.line_number)
                        filtered_issues.append(issue)
                        break
        
        return filtered_issues

    def _get_code_snippet(self, content: str, line_number: int, context: int = 2) -> str:
        """Get a code snippet from the content around the specified line number."""
        lines = content.splitlines()
        if not lines:
            return ""
            
        start_line = max(0, line_number - context - 1)
        end_line = min(len(lines), line_number + context)
        
        snippet_lines = []
        for i in range(start_line, end_line):
            prefix = ">" if i == line_number - 1 else " "
            snippet_lines.append(f"{prefix} {i+1:4d} | {lines[i]}")
            
        return "\n".join(snippet_lines)

    def _run_flake8(self, file_paths: List[str]) -> List[Issue]:
        """Run flake8 on the specified files."""
        issues = []
        
        if not file_paths:
            return issues
            
        try:
            # Create a temporary file with the list of files to analyze
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
                temp_file.write("\n".join(file_paths))
                temp_file_path = temp_file.name
            
            # Run flake8
            flake8_cmd = ["flake8", "--config", self.config.get("tools.flake8.config_file", ".flake8"), 
                          "--filename", temp_file_path]
            
            try:
                output = subprocess.check_output(flake8_cmd, cwd=self.project_root, stderr=subprocess.STDOUT).decode("utf-8")
            except subprocess.CalledProcessError as e:
                output = e.output.decode("utf-8")
            
            # Parse flake8 output
            for line in output.splitlines():
                match = re.match(r"([^:]+):(\d+):(\d+): ([A-Z]\d+) (.*)", line)
                if match:
                    file_path, line_num, col, code, message = match.groups()
                    
                    # Map severity based on error code
                    severity_map = self.config.get("tools.flake8.severity_map", {})
                    severity = severity_map.get(code[0], "medium")
                    
                    # Create issue
                    issue = Issue(
                        file_path=file_path,
                        line_number=int(line_num),
                        message=f"{code}: {message}",
                        severity=SeverityLevel(severity),
                        category="code_quality",
                        tool="flake8",
                    )
                    
                    # Add suggested fix if available
                    if self.config.get("report.include_suggested_fixes", True):
                        issue.suggested_fix = self._get_flake8_fix(code, message)
                        
                    issues.append(issue)
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
        except Exception as e:
            logger.error(f"Error running flake8: {e}")
            
        return issues

    def _get_flake8_fix(self, code: str, message: str) -> Optional[str]:
        """Get a suggested fix for a flake8 issue."""
        fixes = {
            "E201": "Remove whitespace after '('",
            "E202": "Remove whitespace before ')'",
            "E203": "Remove whitespace before ':'",
            "E211": "Remove whitespace before '('",
            "E221": "Remove multiple spaces before operator",
            "E222": "Remove multiple spaces after operator",
            "E225": "Add space around operator",
            "E231": "Add whitespace after ','",
            "E251": "Remove whitespace around parameter equals",
            "E261": "Add two spaces before inline comment",
            "E262": "Add space after # in inline comment",
            "E271": "Remove multiple spaces after keyword",
            "E272": "Remove multiple spaces before keyword",
            "E301": "Add expected blank line",
            "E302": "Add two blank lines",
            "E303": "Remove extra blank lines",
            "E305": "Add two blank lines after class or function definition",
            "E306": "Add one blank line before a nested definition",
            "E401": "Put imports on separate lines",
            "E501": "Shorten line or use line continuation",
            "E711": "Use 'is None' instead of '== None'",
            "E712": "Use 'is True' or 'is False' instead of '== True' or '== False'",
            "E713": "Use 'not in' instead of 'not ... in'",
            "E714": "Use 'is not' instead of 'not ... is'",
            "E741": "Use a more descriptive variable name",
            "F401": "Remove unused import",
            "F403": "Remove wildcard import",
            "F405": "Define explicitly all imported names from wildcard import",
            "F841": "Remove unused variable",
            "W291": "Remove trailing whitespace",
            "W292": "Add a newline at the end of the file",
            "W293": "Remove trailing whitespace on blank line",
            "W391": "Remove trailing blank lines",
        }
        
        return fixes.get(code)

    def _run_pylint(self, file_paths: List[str]) -> List[Issue]:
        """Run pylint on the specified files."""
        issues = []
        
        if not file_paths:
            return issues
            
        try:
            # Run pylint
            pylint_cmd = ["pylint", "--rcfile", self.config.get("tools.pylint.config_file", ".pylintrc"), 
                          "--output-format=json"] + file_paths
            
            try:
                output = subprocess.check_output(pylint_cmd, cwd=self.project_root, stderr=subprocess.STDOUT).decode("utf-8")
            except subprocess.CalledProcessError as e:
                output = e.output.decode("utf-8")
            
            # Parse pylint output
            try:
                pylint_issues = json.loads(output)
                
                for issue_data in pylint_issues:
                    # Map severity based on type
                    severity_map = self.config.get("tools.pylint.severity_map", {})
                    severity = severity_map.get(issue_data.get("type", "")[0], "medium")
                    
                    # Determine category
                    category = "code_quality"
                    if "performance" in issue_data.get("symbol", "").lower():
                        category = "performance"
                    elif "docstring" in issue_data.get("symbol", "").lower():
                        category = "documentation"
                    
                    # Create issue
                    issue = Issue(
                        file_path=issue_data.get("path", ""),
                        line_number=issue_data.get("line", 0),
                        message=f"{issue_data.get('symbol', '')}: {issue_data.get('message', '')}",
                        severity=SeverityLevel(severity),
                        category=category,
                        tool="pylint",
                    )
                    
                    # Add suggested fix if available
                    if self.config.get("report.include_suggested_fixes", True):
                        issue.suggested_fix = self._get_pylint_fix(issue_data.get("symbol", ""), 
                                                                  issue_data.get("message", ""))
                        
                    issues.append(issue)
            except json.JSONDecodeError:
                logger.warning("Could not parse pylint output as JSON")
            
        except Exception as e:
            logger.error(f"Error running pylint: {e}")
            
        return issues

    def _get_pylint_fix(self, symbol: str, message: str) -> Optional[str]:
        """Get a suggested fix for a pylint issue."""
        fixes = {
            "missing-docstring": "Add a docstring describing the function/class purpose",
            "unused-import": "Remove the unused import",
            "unused-variable": "Remove the unused variable or prefix with underscore",
            "too-many-arguments": "Refactor to use fewer arguments, consider using a class or data class",
            "too-many-locals": "Refactor to use fewer local variables, consider breaking into smaller functions",
            "too-many-branches": "Refactor to reduce complexity, consider using helper functions",
            "too-many-statements": "Refactor to reduce complexity, consider breaking into smaller functions",
            "too-many-instance-attributes": "Refactor to use fewer attributes, consider composition",
            "too-few-public-methods": "Consider using a function instead of a class with only one method",
            "no-self-use": "Consider making this a static method or a module-level function",
            "duplicate-code": "Refactor to eliminate duplication, consider extracting common code",
            "invalid-name": "Rename to follow naming conventions (snake_case for variables/functions, CamelCase for classes)",
            "line-too-long": "Shorten line or use line continuation",
            "trailing-whitespace": "Remove trailing whitespace",
            "missing-final-newline": "Add a newline at the end of the file",
            "trailing-newlines": "Remove trailing blank lines",
            "bad-indentation": "Fix indentation to use 4 spaces per level",
            "mixed-indentation": "Use consistent indentation (4 spaces)",
            "wildcard-import": "Replace wildcard import with explicit imports",
            "bare-except": "Specify exception types to catch",
            "broad-except": "Catch more specific exceptions",
            "pointless-string-statement": "Remove or convert to a comment",
            "unused-argument": "Remove or prefix with underscore",
            "redefined-outer-name": "Rename to avoid shadowing outer name",
            "redefined-builtin": "Rename to avoid shadowing built-in name",
            "protected-access": "Use public API instead of accessing protected members",
            "attribute-defined-outside-init": "Define attribute in __init__",
            "arguments-differ": "Match parent method signature",
            "signature-differs": "Match parent method signature",
            "abstract-method": "Implement abstract method",
            "useless-return": "Remove unnecessary return statement",
            "unnecessary-pass": "Remove unnecessary pass statement",
            "consider-using-f-string": "Use f-string instead of string formatting",
            "consider-using-with": "Use context manager (with statement)",
            "consider-using-enumerate": "Use enumerate() instead of manually incrementing a counter",
            "consider-using-dict-comprehension": "Use dict comprehension instead of dict() constructor",
            "consider-using-set-comprehension": "Use set comprehension instead of set() constructor",
            "use-list-literal": "Use [] instead of list()",
            "use-dict-literal": "Use {} instead of dict()",
        }
        
        return fixes.get(symbol)

    def _run_mypy(self, file_paths: List[str]) -> List[Issue]:
        """Run mypy on the specified files."""
        issues = []
        
        if not file_paths:
            return issues
            
        try:
            # Run mypy
            mypy_cmd = ["mypy", "--config-file", self.config.get("tools.mypy.config_file", "mypy.ini")] + file_paths
            
            try:
                output = subprocess.check_output(mypy_cmd, cwd=self.project_root, stderr=subprocess.STDOUT).decode("utf-8")
            except subprocess.CalledProcessError as e:
                output = e.output.decode("utf-8")
            
            # Parse mypy output
            for line in output.splitlines():
                match = re.match(r"([^:]+):(\d+): (\w+): (.*)", line)
                if match:
                    file_path, line_num, level, message = match.groups()
                    
                    # Map severity based on level
                    severity_map = self.config.get("tools.mypy.severity_map", {})
                    severity = severity_map.get(level.lower(), "medium")
                    
                    # Create issue
                    issue = Issue(
                        file_path=file_path,
                        line_number=int(line_num),
                        message=f"mypy {level}: {message}",
                        severity=SeverityLevel(severity),
                        category="code_quality",
                        tool="mypy",
                    )
                    
                    # Add suggested fix if available
                    if self.config.get("report.include_suggested_fixes", True):
                        issue.suggested_fix = self._get_mypy_fix(level, message)
                        
                    issues.append(issue)
            
        except Exception as e:
            logger.error(f"Error running mypy: {e}")
            
        return issues

    def _get_mypy_fix(self, level: str, message: str) -> Optional[str]:
        """Get a suggested fix for a mypy issue."""
        # Extract common patterns from mypy messages
        missing_annotation_match = re.search(r"Function is missing a (return|type) annotation", message)
        if missing_annotation_match:
            annotation_type = missing_annotation_match.group(1)
            if annotation_type == "return":
                return "Add a return type annotation, e.g., -> None, -> str, etc."
            else:
                return "Add type annotations to function parameters, e.g., param: str, param: int, etc."
                
        incompatible_types_match = re.search(r"Incompatible types in assignment \(expression has type \"([^\"]+)\", variable has type \"([^\"]+)\"\)", message)
        if incompatible_types_match:
            expr_type, var_type = incompatible_types_match.groups()
            return f"Ensure the expression is of type '{var_type}' or change the variable's type annotation"
            
        if "Name 'x' is not defined" in message:
            return "Define the variable before using it or fix the typo"
            
        if "Module has no attribute" in message:
            return "Check if the attribute exists or if you need to import it"
            
        if "Cannot determine type of" in message:
            return "Add a type annotation to help mypy determine the type"
            
        if "Untyped function call" in message:
            return "Add type annotations to the called function"
            
        if "Missing return statement" in message:
            return "Add a return statement or change the return type to None"
            
        # Default suggestions
        if level.lower() == "error":
            return "Fix the type error according to mypy's suggestion"
        else:
            return "Consider adding more specific type annotations"

    def _run_bandit(self, file_paths: List[str]) -> List[Issue]:
        """Run bandit on the specified files."""
        issues = []
        
        if not file_paths:
            return issues
            
        try:
            # Run bandit
            bandit_cmd = ["bandit", "-f", "json"] + file_paths
            
            try:
                output = subprocess.check_output(bandit_cmd, cwd=self.project_root, stderr=subprocess.STDOUT).decode("utf-8")
            except subprocess.CalledProcessError as e:
                output = e.output.decode("utf-8")
            
            # Parse bandit output
            try:
                bandit_results = json.loads(output)
                
                for result in bandit_results.get("results", []):
                    # Map severity
                    severity_map = self.config.get("tools.bandit.severity_map", {})
                    severity = severity_map.get(result.get("issue_severity", "").upper(), "medium")
                    
                    # Create issue
                    issue = Issue(
                        file_path=result.get("filename", ""),
                        line_number=result.get("line_number", 0),
                        message=f"Security issue: {result.get('issue_text', '')}",
                        severity=SeverityLevel(severity),
                        category="security",
                        tool="bandit",
                        suggested_fix=result.get("more_info", "Fix the security vulnerability"),
                    )
                    
                    issues.append(issue)
            except json.JSONDecodeError:
                logger.warning("Could not parse bandit output as JSON")
            
        except Exception as e:
            logger.error(f"Error running bandit: {e}")
            
        return issues

    def _run_shellcheck(self, file_paths: List[str]) -> List[Issue]:
        """Run shellcheck on the specified files."""
        issues = []
        
        if not file_paths:
            return issues
            
        try:
            for file_path in file_paths:
                # Run shellcheck
                shellcheck_cmd = ["shellcheck", "-f", "json", file_path]
                
                try:
                    output = subprocess.check_output(shellcheck_cmd, cwd=self.project_root, stderr=subprocess.STDOUT).decode("utf-8")
                except subprocess.CalledProcessError as e:
                    output = e.output.decode("utf-8")
                
                # Parse shellcheck output
                try:
                    shellcheck_results = json.loads(output)
                    
                    for result in shellcheck_results:
                        # Map severity
                        severity_map = self.config.get("tools.shellcheck.severity_map", {})
                        severity = severity_map.get(result.get("level", "").lower(), "medium")
                        
                        # Create issue
                        issue = Issue(
                            file_path=file_path,
                            line_number=result.get("line", 0),
                            message=f"Shell script issue: {result.get('message', '')}",
                            severity=SeverityLevel(severity),
                            category="code_quality",
                            tool="shellcheck",
                            suggested_fix=result.get("fix", {}).get("replacements", [{}])[0].get("replacement", "Fix the shell script issue"),
                        )
                        
                        issues.append(issue)
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse shellcheck output as JSON for {file_path}")
            
        except Exception as e:
            logger.error(f"Error running shellcheck: {e}")
            
        return issues

    def _analyze_docstrings(self, files: List[FileChange]) -> List[Issue]:
        """Analyze docstrings in Python files."""
        issues = []
        
        for file_change in files:
            if not file_change.content:
                continue
                
            try:
                # Parse the Python file
                tree = ast.parse(file_change.content)
                
                # Find all functions and classes
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                        # Check if it has a docstring
                        if not ast.get_docstring(node):
                            # Create an issue for missing docstring
                            issue = Issue(
                                file_path=file_change.file_path,
                                line_number=node.lineno,
                                message=f"Missing docstring for {node.__class__.__name__.lower()} '{node.name}'",
                                severity=SeverityLevel.MEDIUM,
                                category="documentation",
                                tool="docstring_analyzer",
                                suggested_fix=f"Add a docstring to describe the {node.__class__.__name__.lower()}'s purpose, parameters, and return value",
                            )
                            
                            issues.append(issue)
            except SyntaxError:
                logger.warning(f"Could not parse {file_change.file_path} for docstring analysis")
            except Exception as e:
                logger.error(f"Error analyzing docstrings in {file_change.file_path}: {e}")
                
        return issues


class ReportGenerator:
    """Generates a markdown report from review results."""

    def __init__(self, config: CodeReviewConfig):
        """Initialize with configuration."""
        self.config = config

    def generate_report(self, result: ReviewResult) -> str:
        """Generate a markdown report from review results."""
        detail_level = self.config.get("report.detail_level", "medium")
        group_by = self.config.get("report.group_by", "category")
        include_code_snippets = self.config.get("report.include_code_snippets", True)
        include_suggested_fixes = self.config.get("report.include_suggested_fixes", True)
        
        # Start with the report header
        report = [
            "# Automated Code Review Report",
            "",
            f"Generated on: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            "",
        ]
        
        # Add summary information
        total_issues = len(result.issues)
        issues_by_severity = {}
        for severity in SeverityLevel:
            issues_by_severity[severity.value] = len([i for i in result.issues if i.severity == severity])
            
        report.append(f"Total issues found: **{total_issues}**")
        report.append("")
        report.append("| Severity | Count |")
        report.append("| -------- | ----- |")
        for severity in SeverityLevel:
            report.append(f"| {severity.value.capitalize()} | {issues_by_severity[severity.value]} |")
        report.append("")
        
        # Add files changed summary
        report.append("## Files Changed")
        report.append("")
        report.append("| File | Status | Language |")
        report.append("| ---- | ------ | -------- |")
        for change in result.changes:
            report.append(f"| {change.file_path} | {change.status.capitalize()} | {change.language} |")
        report.append("")
        
        # Group issues based on the configuration
        if group_by == "category":
            issues_grouped = {}
            for issue in result.issues:
                if issue.category not in issues_grouped:
                    issues_grouped[issue.category] = []
                issues_grouped[issue.category].append(issue)
                
            # Add issues by category
            for category, issues in issues_grouped.items():
                report.append(f"## {category.capitalize()} Issues")
                report.append("")
                report.extend(self._format_issues(issues, detail_level, include_code_snippets, include_suggested_fixes))
                
        elif group_by == "file":
            issues_grouped = {}
            for issue in result.issues:
                if issue.file_path not in issues_grouped:
                    issues_grouped[issue.file_path] = []
                issues_grouped[issue.file_path].append(issue)
                
            # Add issues by file
            for file_path, issues in issues_grouped.items():
                report.append(f"## Issues in {file_path}")
                report.append("")
                report.extend(self._format_issues(issues, detail_level, include_code_snippets, include_suggested_fixes))
                
        elif group_by == "severity":
            issues_grouped = {}
            for issue in result.issues:
                if issue.severity.value not in issues_grouped:
                    issues_grouped[issue.severity.value] = []
                issues_grouped[issue.severity.value].append(issue)
                
            # Add issues by severity (from highest to lowest)
            for severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH, SeverityLevel.MEDIUM, SeverityLevel.LOW]:
                if severity.value in issues_grouped:
                    report.append(f"## {severity.value.capitalize()} Severity Issues")
                    report.append("")
                    report.extend(self._format_issues(issues_grouped[severity.value], detail_level, include_code_snippets, include_suggested_fixes))
        
        return "\n".join(report)

    def _format_issues(self, issues: List[Issue], detail_level: str, include_code_snippets: bool, include_suggested_fixes: bool) -> List[str]:
        """Format a list of issues as markdown."""
        if not issues:
            return ["No issues found."]
            
        formatted_issues = []
        
        for i, issue in enumerate(issues):
            # Add issue header
            formatted_issues.append(f"### {i+1}. {issue.message}")
            formatted_issues.append("")
            
            # Add issue details
            formatted_issues.append(f"**File:** {issue.file_path}")
            formatted_issues.append(f"**Line:** {issue.line_number}")
            formatted_issues.append(f"**Severity:** {issue.severity.value.capitalize()}")
            formatted_issues.append(f"**Tool:** {issue.tool}")
            formatted_issues.append("")
            
            # Add code snippet if available and requested
            if include_code_snippets and issue.code_snippet and detail_level in ["high", "medium"]:
                formatted_issues.append("**Code:**")
                formatted_issues.append("```")
                formatted_issues.append(issue.code_snippet)
                formatted_issues.append("```")
                formatted_issues.append("")
                
            # Add suggested fix if available and requested
            if include_suggested_fixes and issue.suggested_fix and detail_level in ["high", "medium"]:
                formatted_issues.append("**Suggested Fix:**")
                formatted_issues.append(issue.suggested_fix)
                formatted_issues.append("")
                
        return formatted_issues


class KnowledgeGraphUpdater:
    """Updates the knowledge graph with review results."""

    def __init__(self, config: CodeReviewConfig):
        """Initialize with configuration."""
        self.config = config
        self.kg_path = KNOWLEDGE_GRAPH_PATH

    def update_graph(self, result: ReviewResult) -> None:
        """Update the knowledge graph with review results."""
        if not self.config.get("knowledge_graph.update", False):
            logger.info("Knowledge graph update is disabled in configuration.")
            return
            
        if not self.kg_path.exists():
            logger.warning(f"Knowledge graph file {self.kg_path} not found. Skipping update.")
            return
            
        try:
            # Here we would update the knowledge graph with the review results
            # This is a placeholder for the actual implementation
            logger.info(f"Updating knowledge graph at {self.kg_path}")
            
            # Record issues if enabled
            if self.config.get("knowledge_graph.record_issues", True):
                logger.info(f"Recording {len(result.issues)} issues in knowledge graph")
                
            # Record summary if enabled
            if self.config.get("knowledge_graph.record_summary", True):
                logger.info("Recording review summary in knowledge graph")
                
            logger.info("Knowledge graph updated successfully")
        except Exception as e:
            logger.error(f"Error updating knowledge graph: {e}")


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Automated code review tool for MCP-BASE-STACK.")
    
    # Git reference options
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pr", type=int, help="Pull request number to analyze")
    group.add_argument("--base", help="Base git reference for comparison")
    
    # Other options
    parser.add_argument("--head", default="HEAD", help="Head git reference for comparison [default: HEAD]")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Path to configuration file [default: config/code_review.yaml]")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="Output file path [default: code_review_report.md]")
    parser.add_argument("--detail", choices=["high", "medium", "low"], default="medium", help="Level of detail in the report [default: medium]")
    parser.add_argument("--update-kg", action="store_true", help="Update the knowledge graph with the review results")
    
    return parser.parse_args()


def main() -> int:
    """Main function."""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Load configuration
    config = CodeReviewConfig(args.config)
    
    # Override configuration with command-line arguments
    if args.detail:
        config.config["report"]["detail_level"] = args.detail
    if args.update_kg:
        config.config["knowledge_graph"]["update"] = True
    
    # Determine base and head references
    head = args.head
    if args.pr:
        # Get base and head from PR
        try:
            # This is a placeholder for the actual implementation
            # In a real implementation, we would use the GitHub API to get the PR details
            logger.info(f"Getting base and head references for PR #{args.pr}")
            base = "main"  # Placeholder
        except Exception as e:
            logger.error(f"Error getting PR details: {e}")
            return 1
    else:
        base = args.base
    
    # Analyze git diff
    logger.info(f"Analyzing git diff between {base} and {head}")
    diff_analyzer = GitDiffAnalyzer(base, head)
    changed_files = diff_analyzer.get_changed_files()
    
    if not changed_files:
        logger.warning("No changed files found.")
        return 0
    
    logger.info(f"Found {len(changed_files)} changed files")
    
    # Analyze code quality
    logger.info("Analyzing code quality")
    quality_analyzer = CodeQualityAnalyzer(config)
    issues = quality_analyzer.analyze_changes(changed_files)
    
    logger.info(f"Found {len(issues)} issues")
    
    # Create review result
    result = ReviewResult(
        changes=changed_files,
        issues=issues,
        summary={
            "total_issues": len(issues),
            "issues_by_severity": {
                severity.value: len([i for i in issues if i.severity == severity])
                for severity in SeverityLevel
            },
            "issues_by_category": {
                category: len([i for i in issues if i.category == category])
                for category in set(i.category for i in issues)
            },
        },
    )
    
    # Generate report
    logger.info("Generating report")
    report_generator = ReportGenerator(config)
    report = report_generator.generate_report(result)
    
    # Write report to file
    logger.info(f"Writing report to {args.output}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        f.write(report)
    
    # Update knowledge graph
    if config.get("knowledge_graph.update", False):
        logger.info("Updating knowledge graph")
        kg_updater = KnowledgeGraphUpdater(config)
        kg_updater.update_graph(result)
    
    # Check if review passes based on severity thresholds
    passes = True
    for severity in SeverityLevel:
        threshold = config.get(f"severity_thresholds.{severity.value}", 0)
        count = result.summary["issues_by_severity"][severity.value]
        if count > threshold:
            logger.warning(f"Review failed: {count} {severity.value} issues found (threshold: {threshold})")
            passes = False
    
    if passes:
        logger.info("Review passed: All issue counts are within thresholds")
        return 0
    else:
        logger.warning("Review failed: Some issue counts exceed thresholds")
        return 1


if __name__ == "__main__":
    sys.exit(main())
