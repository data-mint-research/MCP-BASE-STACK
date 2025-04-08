"""
Quality Enforcer Module

This module provides the QualityEnforcer class, which serves as a facade over
the modular quality component system. It maintains backward compatibility with
the existing hooks while leveraging the new component-based architecture.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable

from core.config.settings import get_config
from core.quality.components.fixes.code_style import CodeStyleFixes
from core.quality.components.fixes.documentation import DocumentationFixes
from core.quality.components.fixes.static_analysis import StaticAnalysisFixes
from core.quality.components.fixes.structure import StructureFixes
from core.quality.components.interactive import run_interactive_fix
from core.quality.components.preview import generate_fix_preview, compare_fix_options
from core.quality.components.verification import verify_and_apply_fixes

from core.config.settings import get_config
from core.quality.components.base import (
    QualityCheckRegistry,
    QualityCheckResult,
    QualityCheckSeverity,
    QualityComponent
)
from core.quality.components.code_style import CodeStyleComponent
from core.quality.components.documentation import DocumentationComponent
from core.quality.components.static_analysis import StaticAnalysisComponent
from core.quality.components.structure import StructureComponent

logger = logging.getLogger(__name__)


class QualityEnforcer:
    """
    Facade for the quality enforcement system.
    
    This class provides a unified interface for running quality checks and
    enforcing quality standards across the codebase. It maintains backward
    compatibility with the existing hooks while leveraging the new
    component-based architecture.
    """
    
    def __init__(self):
        """Initialize the QualityEnforcer."""
        self._registry = QualityCheckRegistry()
        self._registry.initialize()
        
        # Initialize components
        self._components = {
            "code_style": CodeStyleComponent(),
            "static_analysis": StaticAnalysisComponent(),
            "documentation": DocumentationComponent(),
            "structure": StructureComponent()
        }
        
        # Load custom components from plugins
        self._load_custom_components()
    
    def _load_custom_components(self) -> None:
        """Load custom components from plugins."""
        for name, component_class in self._registry.get_all_components().items():
            if name not in self._components:
                self._components[name] = component_class()
    
    def get_component(self, component_name: str) -> Optional[QualityComponent]:
        """
        Get a quality component by name.
        
        Args:
            component_name: The name of the component to get.
            
        Returns:
            The QualityComponent instance, or None if not found.
        """
        return self._components.get(component_name)
    
    def get_all_components(self) -> Dict[str, QualityComponent]:
        """
        Get all quality components.
        
        Returns:
            Dictionary mapping component names to QualityComponent instances.
        """
        return self._components.copy()
    
    def run_all_checks(self, file_paths: Optional[List[str]] = None, **kwargs) -> List[QualityCheckResult]:
        """
        Run all quality checks.
        
        Args:
            file_paths: Optional list of file paths to check.
                If None, check all relevant files.
            **kwargs: Additional arguments for the checks.
            
        Returns:
            List of QualityCheckResult objects.
        """
        results = []
        
        for component in self._components.values():
            component_results = component.run_checks(file_paths, **kwargs)
            results.extend(component_results)
        
        return results
    
    def run_component_checks(self, component_name: str, file_paths: Optional[List[str]] = None, **kwargs) -> List[QualityCheckResult]:
        """
        Run checks for a specific component.
        
        Args:
            component_name: The name of the component to run checks for.
            file_paths: Optional list of file paths to check.
                If None, check all relevant files.
            **kwargs: Additional arguments for the checks.
            
        Returns:
            List of QualityCheckResult objects.
        """
        component = self._components.get(component_name)
        if not component:
            logger.warning(f"Component not found: {component_name}")
            return []
        
        return component.run_checks(file_paths, **kwargs)
    
    def run_check(self, check_id: str, file_paths: Optional[List[str]] = None, **kwargs) -> List[QualityCheckResult]:
        """
        Run a specific quality check.
        
        Args:
            check_id: The ID of the check to run.
            file_paths: Optional list of file paths to check.
                If None, check all relevant files.
            **kwargs: Additional arguments for the check.
            
        Returns:
            List of QualityCheckResult objects.
        """
        check = self._registry.get_check(check_id)
        if not check:
            logger.warning(f"Check not found: {check_id}")
            return []
        
        return check.run(file_paths, **kwargs)
    
    def fix_issues(self, results: List[QualityCheckResult], interactive: bool = False,
                  preview: bool = False, verify: bool = True) -> List[QualityCheckResult]:
        """
        Fix issues identified by quality checks.
        
        Args:
            results: List of QualityCheckResult objects to fix.
            interactive: Whether to use interactive mode.
            preview: Whether to preview fixes before applying them.
            verify: Whether to verify fixes after applying them.
            
        Returns:
            List of QualityCheckResult objects that couldn't be fixed.
        """
        if interactive:
            # Use interactive mode
            fixed_results, unfixed_results = run_interactive_fix(results)
            return unfixed_results
        
        # Group results by component
        results_by_component: Dict[str, List[QualityCheckResult]] = {}
        for result in results:
            component_name = self._get_component_for_check(result.check_id)
            if component_name:
                if component_name not in results_by_component:
                    results_by_component[component_name] = []
                results_by_component[component_name].append(result)
        
        # Fix issues for each component
        remaining_results = []
        for component_name, component_results in results_by_component.items():
            component = self._components.get(component_name)
            if component:
                if verify:
                    # Group results by file
                    results_by_file: Dict[str, List[QualityCheckResult]] = {}
                    for result in component_results:
                        if result.file_path:
                            if result.file_path not in results_by_file:
                                results_by_file[result.file_path] = []
                            results_by_file[result.file_path].append(result)
                    
                    # Apply fixes with verification for each file
                    for file_path, file_results in results_by_file.items():
                        # Create a function to apply fixes
                        def apply_fixes_func(results: List[QualityCheckResult]) -> Tuple[List[QualityCheckResult], List[QualityCheckResult]]:
                            return self._apply_component_fixes(component_name, results)
                        
                        # Create a function to run checks
                        def run_checks_func(file_paths: List[str]) -> List[QualityCheckResult]:
                            return self.run_component_checks(component_name, file_paths)
                        
                        # Apply fixes with verification
                        success, fixed, unfixed = verify_and_apply_fixes(
                            file_path, file_results, apply_fixes_func, run_checks_func
                        )
                        
                        remaining_results.extend(unfixed)
                else:
                    # Apply fixes without verification
                    unfixed = component.fix_issues(component_results)
                    remaining_results.extend(unfixed)
            else:
                remaining_results.extend(component_results)
        
        return remaining_results
    
    def _apply_component_fixes(self, component_name: str, results: List[QualityCheckResult]) -> Tuple[List[QualityCheckResult], List[QualityCheckResult]]:
        """
        Apply fixes for a specific component.
        
        Args:
            component_name: The name of the component.
            results: List of QualityCheckResult objects to fix.
            
        Returns:
            Tuple of (fixed_results, unfixed_results)
        """
        if component_name == "code_style":
            fixed, unfixed = CodeStyleFixes.apply_fixes(results)
            return fixed, unfixed
        elif component_name == "documentation":
            fixed, unfixed = DocumentationFixes.apply_fixes(results)
            return fixed, unfixed
        elif component_name == "structure":
            fixed, unfixed = StructureFixes.apply_fixes(results)
            return fixed, unfixed
        elif component_name == "static_analysis":
            fixed, unfixed = StaticAnalysisFixes.apply_fixes(results)
            return fixed, unfixed
        else:
            # Fallback to the component's fix_issues method
            component = self._components.get(component_name)
            if component:
                unfixed = component.fix_issues(results)
                fixed = [r for r in results if r not in unfixed]
                return fixed, unfixed
            else:
                return [], results
    
    def _get_component_for_check(self, check_id: str) -> Optional[str]:
        """
        Get the component name for a check ID.
        
        Args:
            check_id: The ID of the check.
            
        Returns:
            The name of the component that contains the check, or None if not found.
        """
        for component_name, component in self._components.items():
            for check in component.checks:
                if check.id == check_id:
                    return component_name
        return None
    
    # Backward compatibility methods for existing hooks
    
    def check_code_quality(self, file_paths: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Check code quality for the specified files.
        
        This method provides backward compatibility with the existing hooks.
        
        Args:
            file_paths: Optional list of file paths to check.
                If None, check all relevant files.
            
        Returns:
            Dictionary mapping check types to lists of issues.
        """
        # Run code style and static analysis checks
        code_style_results = self.run_component_checks("code_style", file_paths)
        static_analysis_results = self.run_component_checks("static_analysis", file_paths)
        
        # Convert results to the format expected by existing hooks
        issues = {
            "style": [],
            "lint": [],
            "type": []
        }
        
        for result in code_style_results:
            if result.check_id in ["black", "isort"]:
                issues["style"].append({
                    "file": result.file_path,
                    "line": result.line_number,
                    "message": result.message,
                    "severity": result.severity.value
                })
        
        for result in static_analysis_results:
            if result.check_id in ["flake8", "pylint"]:
                issues["lint"].append({
                    "file": result.file_path,
                    "line": result.line_number,
                    "message": result.message,
                    "severity": result.severity.value
                })
            elif result.check_id == "mypy":
                issues["type"].append({
                    "file": result.file_path,
                    "line": result.line_number,
                    "message": result.message,
                    "severity": result.severity.value
                })
        
        return issues
    
    def check_documentation_quality(self, file_paths: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Check documentation quality for the specified files.
        
        This method provides backward compatibility with the existing hooks.
        
        Args:
            file_paths: Optional list of file paths to check.
                If None, check all relevant files.
            
        Returns:
            Dictionary mapping check types to lists of issues.
        """
        # Run documentation checks
        documentation_results = self.run_component_checks("documentation", file_paths)
        
        # Convert results to the format expected by existing hooks
        issues = {
            "docstrings": [],
            "readme": [],
            "coverage": []
        }
        
        for result in documentation_results:
            if result.check_id == "docstrings":
                issues["docstrings"].append({
                    "file": result.file_path,
                    "line": result.line_number,
                    "message": result.message,
                    "severity": result.severity.value
                })
            elif result.check_id == "readme":
                issues["readme"].append({
                    "file": result.file_path,
                    "message": result.message,
                    "severity": result.severity.value
                })
            elif result.check_id == "doc_coverage":
                issues["coverage"].append({
                    "file": result.file_path,
                    "message": result.message,
                    "severity": result.severity.value
                })
        
        return issues
    
    def validate_file_structure(self, file_paths: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Validate file structure for the specified files.
        
        This method provides backward compatibility with the existing hooks.
        
        Args:
            file_paths: Optional list of file paths to check.
                If None, check all relevant files.
            
        Returns:
            Dictionary mapping check types to lists of issues.
        """
        # Run structure checks
        structure_results = self.run_component_checks("structure", file_paths)
        
        # Convert results to the format expected by existing hooks
        issues = {
            "directory_structure": [],
            "file_naming": [],
            "imports": [],
            "dependencies": []
        }
        
        for result in structure_results:
            if result.check_id == "directory_structure":
                issues["directory_structure"].append({
                    "file": result.file_path,
                    "message": result.message,
                    "severity": result.severity.value
                })
            elif result.check_id == "file_naming":
                issues["file_naming"].append({
                    "file": result.file_path,
                    "message": result.message,
                    "severity": result.severity.value
                })
            elif result.check_id == "import_organization":
                issues["imports"].append({
                    "file": result.file_path,
                    "line": result.line_number,
                    "message": result.message,
                    "severity": result.severity.value
                })
            elif result.check_id == "circular_dependencies":
                issues["dependencies"].append({
                    "file": result.file_path,
                    "message": result.message,
                    "severity": result.severity.value
                })
        
        return issues
    
    def suggest_improvements(self, file_paths: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Suggest improvements for the specified files.
        
        This method provides backward compatibility with the existing hooks.
        
        Args:
            file_paths: Optional list of file paths to check.
                If None, check all relevant files.
            
        Returns:
            List of suggested improvements.
        """
        # Run all checks
        all_results = self.run_all_checks(file_paths)
        
        # Convert results to the format expected by existing hooks
        suggestions = []
        
        for result in all_results:
            if result.severity in [QualityCheckSeverity.INFO, QualityCheckSeverity.WARNING]:
                suggestion = {
                    "file": result.file_path,
                    "message": result.message,
                    "severity": result.severity.value,
                    "check_id": result.check_id,
                    "source": result.source
                }
                
                if result.line_number:
                    suggestion["line"] = result.line_number
                
                if result.fix_available:
                    suggestion["fix_available"] = True
                    suggestion["fix_command"] = result.fix_command
                
                suggestions.append(suggestion)
        
        return suggestions
    
    def preview_fixes(self, results: List[QualityCheckResult]) -> Dict[str, str]:
        """
        Preview fixes for quality check results.
        
        Args:
            results: List of QualityCheckResult objects to preview.
            
        Returns:
            Dictionary mapping file paths to diff strings.
        """
        # Group results by file
        results_by_file: Dict[str, List[QualityCheckResult]] = {}
        for result in results:
            if result.file_path:
                if result.file_path not in results_by_file:
                    results_by_file[result.file_path] = []
                results_by_file[result.file_path].append(result)
        
        # Generate previews for each file
        previews = {}
        for file_path, file_results in results_by_file.items():
            diff = generate_fix_preview(file_path, file_results)
            previews[file_path] = diff
        
        return previews
    
    def compare_fix_options(self, results: List[QualityCheckResult]) -> Dict[str, Dict[str, str]]:
        """
        Compare different fix options for quality check results.
        
        Args:
            results: List of QualityCheckResult objects to compare.
            
        Returns:
            Dictionary mapping file paths to dictionaries of fix option diffs.
        """
        # Group results by file
        results_by_file: Dict[str, List[QualityCheckResult]] = {}
        for result in results:
            if result.file_path:
                if result.file_path not in results_by_file:
                    results_by_file[result.file_path] = []
                results_by_file[result.file_path].append(result)
        
        # Compare fix options for each file
        comparisons = {}
        for file_path, file_results in results_by_file.items():
            comparison = compare_fix_options(file_path, file_results)
            comparisons[file_path] = comparison
        
        return comparisons
    
    def auto_fix_issues(self, file_paths: Optional[List[str]] = None, interactive: bool = False,
                      preview: bool = False, verify: bool = True) -> Tuple[int, int]:
        """
        Automatically fix quality issues in the specified files.
        
        Args:
            file_paths: Optional list of file paths to fix.
                If None, fix all relevant files.
            interactive: Whether to use interactive mode.
            preview: Whether to preview fixes before applying them.
            verify: Whether to verify fixes after applying them.
            
        Returns:
            Tuple of (fixed_count, unfixed_count)
        """
        # Run all checks
        results = self.run_all_checks(file_paths)
        
        # Filter for fixable issues
        fixable_results = [r for r in results if r.fix_available]
        
        if not fixable_results:
            return 0, len(results)
        
        # Preview fixes if requested
        if preview and not interactive:
            previews = self.preview_fixes(fixable_results)
            for file_path, diff in previews.items():
                print(f"\nPreview of fixes for {file_path}:")
                print(diff)
        
        # Fix issues
        unfixed_results = self.fix_issues(fixable_results, interactive, preview, verify)
        
        # Calculate counts
        fixed_count = len(fixable_results) - len(unfixed_results)
        unfixed_count = len(unfixed_results) + (len(results) - len(fixable_results))
        
        return fixed_count, unfixed_count
    
    def run_external_tool(self, tool_name: str, file_paths: Optional[List[str]] = None) -> List[QualityCheckResult]:
        """
        Run an external quality tool.
        
        Args:
            tool_name: The name of the external tool to run (e.g., "black", "mypy", "pylint", "flake8")
            file_paths: Optional list of file paths to check. If None, check all relevant files.
            
        Returns:
            List of QualityCheckResult objects.
        """
        import subprocess
        import shlex
        
        logger.info(f"Running external tool: {tool_name}")
        
        # Prepare file paths argument
        files_arg = " ".join(file_paths) if file_paths else "."
        
        # Map tool names to commands
        tool_commands = {
            "black": f"black --check {files_arg}",
            "mypy": f"mypy {files_arg}",
            "pylint": f"pylint {files_arg}",
            "flake8": f"flake8 {files_arg}"
        }
        
        if tool_name not in tool_commands:
            logger.warning(f"Unknown external tool: {tool_name}")
            return []
        
        command = tool_commands[tool_name]
        logger.info(f"Running command: {command}")
        
        try:
            # Run the command
            process = subprocess.run(
                shlex.split(command),
                capture_output=True,
                text=True,
                check=False
            )
            
            # Parse the output
            results = []
            if process.returncode != 0:
                # Tool found issues
                output_lines = process.stdout.splitlines() + process.stderr.splitlines()
                
                for line in output_lines:
                    # Parse the line based on the tool
                    if tool_name == "black":
                        if "would reformat" in line:
                            file_path = line.split("would reformat")[1].strip()
                            results.append(QualityCheckResult(
                                check_id="black",
                                severity=QualityCheckSeverity.WARNING,
                                message="Black formatting issue",
                                file_path=file_path,
                                fix_available=True,
                                fix_command=f"black {file_path}"
                            ))
                    elif tool_name == "mypy":
                        if ":" in line and "error:" in line:
                            parts = line.split(":", 2)
                            if len(parts) >= 3:
                                file_path = parts[0]
                                try:
                                    line_number = int(parts[1])
                                    message = parts[2].strip()
                                    results.append(QualityCheckResult(
                                        check_id="mypy",
                                        severity=QualityCheckSeverity.ERROR,
                                        message=message,
                                        file_path=file_path,
                                        line_number=line_number
                                    ))
                                except ValueError:
                                    pass
                    elif tool_name == "pylint":
                        if ":" in line and any(level in line for level in ["C:", "W:", "E:", "F:"]):
                            parts = line.split(":", 2)
                            if len(parts) >= 3:
                                file_path = parts[0]
                                try:
                                    line_number = int(parts[1])
                                    message = parts[2].strip()
                                    severity = QualityCheckSeverity.INFO
                                    if "C:" in message:
                                        severity = QualityCheckSeverity.INFO
                                    elif "W:" in message:
                                        severity = QualityCheckSeverity.WARNING
                                    elif "E:" in message:
                                        severity = QualityCheckSeverity.ERROR
                                    elif "F:" in message:
                                        severity = QualityCheckSeverity.CRITICAL
                                    results.append(QualityCheckResult(
                                        check_id="pylint",
                                        severity=severity,
                                        message=message,
                                        file_path=file_path,
                                        line_number=line_number
                                    ))
                                except ValueError:
                                    pass
                    elif tool_name == "flake8":
                        if ":" in line:
                            parts = line.split(":", 3)
                            if len(parts) >= 4:
                                file_path = parts[0]
                                try:
                                    line_number = int(parts[1])
                                    column = int(parts[2])
                                    message = parts[3].strip()
                                    results.append(QualityCheckResult(
                                        check_id="flake8",
                                        severity=QualityCheckSeverity.WARNING,
                                        message=message,
                                        file_path=file_path,
                                        line_number=line_number,
                                        column=column
                                    ))
                                except ValueError:
                                    pass
            
            logger.info(f"External tool {tool_name} found {len(results)} issues")
            return results
        
        except Exception as e:
            logger.error(f"Error running external tool {tool_name}: {e}")
            return [QualityCheckResult(
                check_id=tool_name,
                severity=QualityCheckSeverity.ERROR,
                message=f"Error running tool: {str(e)}"
            )]
    
    def update_knowledge_graph(self, results: List[QualityCheckResult]) -> None:
        """
        Update the knowledge graph with quality check results.
        
        This method exports quality check results to a JSON file that can be
        processed by the knowledge graph update script.
        
        Args:
            results: List of QualityCheckResult objects.
        """
        import json
        import os
        import datetime
        from pathlib import Path
        
        logger.info(f"Updating knowledge graph with {len(results)} quality check results")
        
        # Group results by severity
        results_by_severity = {
            QualityCheckSeverity.INFO: [],
            QualityCheckSeverity.WARNING: [],
            QualityCheckSeverity.ERROR: [],
            QualityCheckSeverity.CRITICAL: []
        }
        
        for result in results:
            results_by_severity[result.severity].append(result)
        
        # Log summary
        logger.info(f"Quality check summary:")
        logger.info(f"  INFO: {len(results_by_severity[QualityCheckSeverity.INFO])}")
        logger.info(f"  WARNING: {len(results_by_severity[QualityCheckSeverity.WARNING])}")
        logger.info(f"  ERROR: {len(results_by_severity[QualityCheckSeverity.ERROR])}")
        logger.info(f"  CRITICAL: {len(results_by_severity[QualityCheckSeverity.CRITICAL])}")
        
        # Prepare data for export
        serializable_results = []
        for result in results:
            serializable_result = {
                "check_id": result.check_id,
                "severity": result.severity.value,
                "message": result.message,
                "file_path": result.file_path,
                "line_number": result.line_number,
                "column": result.column,
                "source": result.source,
                "details": result.details,
                "fix_available": result.fix_available,
                "fix_command": result.fix_command
            }
            serializable_results.append(serializable_result)
        
        # Create report data
        report_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "results": serializable_results,
            "summary": {
                "total_checks": len(results),
                "passed": len([r for r in results if r.severity in [QualityCheckSeverity.INFO]]),
                "failed": len([r for r in results if r.severity in [QualityCheckSeverity.WARNING, QualityCheckSeverity.ERROR, QualityCheckSeverity.CRITICAL]])
            }
        }
        
        # Ensure reports directory exists
        reports_dir = Path("data/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = reports_dir / f"code_quality_report_{timestamp}.json"
        
        # Write report to file
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Quality report written to {report_path}")
        
        # Trigger knowledge graph update
        try:
            import subprocess
            logger.info("Triggering knowledge graph update...")
            subprocess.run(["python", "core/kg/scripts/update_knowledge_graph.py"], check=True)
            logger.info("Knowledge graph updated successfully")
        except Exception as e:
            logger.error(f"Failed to update knowledge graph: {e}")


# Create a singleton instance
enforcer = QualityEnforcer()