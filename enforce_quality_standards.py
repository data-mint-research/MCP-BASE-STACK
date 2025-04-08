#!/usr/bin/env python3
"""
Quality Standards Enforcement Script

This script orchestrates the execution of all quality enforcement scripts in an iterative cycle,
continuing until no further changes are needed, and then generates a final summary report and
updates the knowledge graph with the final state.

The script executes the following quality enforcement scripts in order:
1. Static code analysis script for verifying code structure
2. Enhanced file cleanup script for managing file locations and orphaned files
3. Script for updating essential files
4. Enhanced code formatting and linting enforcement scripts
5. Dependency audit script for checking dependencies

Features:
- Iterative execution until no further changes are needed
- Comprehensive final report generation
- Knowledge graph update with the final state
- Detailed logging of the process
- Error handling and graceful failure

Usage:
    python enforce_quality_standards.py --project-dir /path/to/project
    python enforce_quality_standards.py --project-dir /path/to/project --max-iterations 5
    python enforce_quality_standards.py --project-dir /path/to/project --verbose
    python enforce_quality_standards.py --project-dir /path/to/project --dry-run
    python enforce_quality_standards.py --project-dir /path/to/project --skip-kg-update
"""

import argparse
import datetime
import importlib.util
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set, Union, Callable

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/logs/enforce_quality_standards.log')
    ]
)
logger = logging.getLogger(__name__)


class QualityStandardsEnforcer:
    """
    Class to orchestrate the execution of all quality enforcement scripts in an iterative cycle.
    
    This class provides methods to execute each script in the correct order, track changes made by each script,
    determine when the process is complete (no changes needed), and generate a final summary report.
    
    Attributes:
        project_dir: Path to the project directory
        max_iterations: Maximum number of iterations to perform
        verbose: Whether to enable verbose logging
        dry_run: Whether to run in dry-run mode (only report issues without making changes)
        skip_kg_update: Whether to skip updating the knowledge graph
    """
    
    def __init__(
        self,
        project_dir: str,
        max_iterations: int = 10,
        verbose: bool = False,
        dry_run: bool = False,
        skip_kg_update: bool = False
    ):
        """
        Initialize the QualityStandardsEnforcer.
        
        Args:
            project_dir: Path to the project directory
            max_iterations: Maximum number of iterations to perform
            verbose: Whether to enable verbose logging
            dry_run: Whether to run in dry-run mode (only report issues without making changes)
            skip_kg_update: Whether to skip updating the knowledge graph
        """
        self.project_dir = os.path.abspath(project_dir)
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.dry_run = dry_run
        self.skip_kg_update = skip_kg_update
        
        # Initialize report data structure
        self.report = {
            "project_dir": self.project_dir,
            "timestamp": datetime.datetime.now().isoformat(),
            "summary": {
                "total_iterations": 0,
                "total_changes": 0,
                "scripts_executed": 0,
                "scripts_succeeded": 0,
                "scripts_failed": 0,
                "total_execution_time": 0
            },
            "iterations": [],
            "final_state": {
                "code_quality": {},
                "file_structure": {},
                "essential_files": {},
                "dependencies": {}
            }
        }
        
        # Initialize script paths
        self.script_paths = {
            "code_structure": "scripts/utils/quality/check_code_quality.sh",
            "file_cleanup": "scripts/utils/cleanup/cleanup_files.py",
            "essential_files": "scripts/utils/maintenance/update_essential_files.py",
            "code_formatting": "scripts/utils/quality/fix_code_quality.sh",
            "dependency_audit": "scripts/utils/maintenance/audit_dependencies.py"
        }
        
        # Initialize script arguments
        self.script_args = {
            "code_structure": ["--project-dir", self.project_dir],
            "file_cleanup": ["--project-dir", self.project_dir, "--manifest", "config/specifications/specification-manifest.json", "--batch"],
            "essential_files": ["--project-dir", self.project_dir, "--manifest", "config/specifications/specification-manifest.json"],
            "code_formatting": ["--project-dir", self.project_dir],
            "dependency_audit": ["--project-dir", self.project_dir]
        }
        
        # Add dry-run flag if needed
        if self.dry_run:
            for script in ["file_cleanup", "essential_files", "dependency_audit"]:
                self.script_args[script].append("--dry-run")
        
        # Add verbose flag if needed
        if self.verbose:
            for script in ["file_cleanup", "essential_files", "dependency_audit"]:
                self.script_args[script].append("--verbose")
        
        # Try to load the QualityEnforcer for integration
        self.quality_enforcer = self._load_quality_enforcer()
    
    def log(self, message: str) -> None:
        """
        Log a message if verbose mode is enabled.
        
        Args:
            message: The message to log
        """
        if self.verbose:
            logger.info(message)
    
    def _load_quality_enforcer(self) -> Optional[Any]:
        """
        Load the QualityEnforcer class if available.
        
        Returns:
            The QualityEnforcer instance, or None if not available
        """
        try:
            # Try to import the QualityEnforcer
            spec = importlib.util.spec_from_file_location(
                "enforcer",
                os.path.join(self.project_dir, "core/quality/enforcer.py")
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, "enforcer"):
                    self.log("Successfully loaded QualityEnforcer")
                    return module.enforcer
            self.log("QualityEnforcer not found, continuing without integration")
            return None
        except Exception as e:
            logger.error(f"Error loading QualityEnforcer: {e}")
            return None
    
    def _execute_script(self, script_name: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Execute a script and return its result.
        
        Args:
            script_name: The name of the script to execute
            
        Returns:
            A tuple of (success, result) where success is a boolean indicating whether the script
            succeeded, and result is a dictionary containing the script's output
        """
        script_path = os.path.join(self.project_dir, self.script_paths[script_name])
        script_args = self.script_args[script_name]
        
        self.log(f"Executing script: {script_path} {' '.join(script_args)}")
        
        # Check if the script exists
        if not os.path.exists(script_path):
            logger.error(f"Script not found: {script_path}")
            return False, {"error": f"Script not found: {script_path}"}
        
        # Determine the script type (Python or shell)
        is_python = script_path.endswith(".py")
        
        # Prepare the command
        if is_python:
            cmd = ["python3", script_path] + script_args
        else:
            cmd = ["bash", script_path] + script_args
        
        # Execute the script
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            execution_time = time.time() - start_time
            
            # Check if the script succeeded
            if result.returncode == 0:
                self.log(f"Script {script_name} succeeded in {execution_time:.2f} seconds")
                
                # Try to parse the output as JSON
                try:
                    output = json.loads(result.stdout)
                except json.JSONDecodeError:
                    output = {"stdout": result.stdout, "stderr": result.stderr}
                
                return True, {
                    "success": True,
                    "execution_time": execution_time,
                    "output": output
                }
            else:
                logger.error(f"Script {script_name} failed with return code {result.returncode}")
                logger.error(f"Error: {result.stderr}")
                
                return False, {
                    "success": False,
                    "execution_time": execution_time,
                    "error": result.stderr,
                    "stdout": result.stdout
                }
        
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error executing script {script_name}: {e}")
            
            return False, {
                "success": False,
                "execution_time": execution_time,
                "error": str(e)
            }
    
    def _detect_changes(self, script_name: str, result: Dict[str, Any]) -> bool:
        """
        Detect if a script made any changes.
        
        Args:
            script_name: The name of the script
            result: The result of the script execution
            
        Returns:
            True if the script made changes, False otherwise
        """
        # Check if the script succeeded
        if not result.get("success", False):
            return False
        
        # Different scripts report changes differently
        if script_name == "code_structure":
            # Check if there were any issues reported
            output = result.get("output", {})
            if isinstance(output, dict):
                issues = output.get("issues", [])
                return len(issues) > 0
            return False
        
        elif script_name == "file_cleanup":
            # Check if any files were moved, removed, or archived
            output = result.get("output", {})
            if isinstance(output, dict):
                summary = output.get("summary", {})
                files_moved = summary.get("files_moved", 0)
                files_removed = summary.get("files_removed", 0)
                files_archived = summary.get("files_archived", 0)
                return files_moved > 0 or files_removed > 0 or files_archived > 0
            return False
        
        elif script_name == "essential_files":
            # Check if any files were updated or created
            output = result.get("output", {})
            if isinstance(output, dict):
                summary = output.get("summary", {})
                files_updated = summary.get("files_updated", 0)
                files_created = summary.get("files_created", 0)
                return files_updated > 0 or files_created > 0
            return False
        
        elif script_name == "code_formatting":
            # Check if any files were formatted
            output = result.get("output", {})
            if isinstance(output, dict):
                formatted_files = output.get("formatted_files", [])
                return len(formatted_files) > 0
            return False
        
        elif script_name == "dependency_audit":
            # Check if any dependencies were updated
            output = result.get("output", {})
            if isinstance(output, dict):
                updated_dependencies = output.get("updated_dependencies", [])
                return len(updated_dependencies) > 0
            return False
        
        # Default: assume no changes
        return False
    
    def _update_knowledge_graph(self) -> bool:
        """
        Update the knowledge graph with the final state.
        
        Returns:
            True if the update was successful, False otherwise
        """
        if self.dry_run:
            self.log("[DRY RUN] Would update knowledge graph")
            return True
        
        if self.skip_kg_update:
            self.log("Skipping knowledge graph update")
            return True
        
        self.log("Updating knowledge graph...")
        
        try:
            # Use the QualityEnforcer if available
            if self.quality_enforcer:
                self.log("Updating knowledge graph via QualityEnforcer...")
                
                # Create a summary of the quality enforcement process
                summary = {
                    "total_iterations": self.report["summary"]["total_iterations"],
                    "total_changes": self.report["summary"]["total_changes"],
                    "scripts_executed": self.report["summary"]["scripts_executed"],
                    "scripts_succeeded": self.report["summary"]["scripts_succeeded"],
                    "scripts_failed": self.report["summary"]["scripts_failed"],
                    "total_execution_time": self.report["summary"]["total_execution_time"],
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
                # Update the knowledge graph
                try:
                    # Import QualityCheckResult and QualityCheckSeverity
                    from core.quality.components.base import QualityCheckResult, QualityCheckSeverity
                    
                    # Create a QualityCheckResult for the quality enforcement process
                    result = QualityCheckResult(
                        check_id="quality_enforcement",
                        severity=QualityCheckSeverity.INFO,
                        message=f"Quality enforcement completed with {summary['total_iterations']} iterations and {summary['total_changes']} changes",
                        source="QualityStandardsEnforcer"
                    )
                    
                    # Update the knowledge graph
                    self.quality_enforcer.update_knowledge_graph([result])
                    self.log("Successfully updated knowledge graph")
                    return True
                except Exception as e:
                    logger.error(f"Error updating knowledge graph via QualityEnforcer: {e}")
                    return False
            else:
                # Try to run the update_knowledge_graph.py script
                update_script = os.path.join(self.project_dir, "core/kg/scripts/update_knowledge_graph.py")
                if os.path.exists(update_script):
                    self.log("Updating knowledge graph via update_knowledge_graph.py...")
                    result = subprocess.run(["python", update_script], cwd=self.project_dir)
                    if result.returncode == 0:
                        self.log("Successfully updated knowledge graph")
                        return True
                    else:
                        logger.error("Failed to update knowledge graph")
                        return False
                else:
                    self.log("No knowledge graph update mechanism found")
                    return False
        except Exception as e:
            logger.error(f"Error updating knowledge graph: {e}")
            return False
    
    def _generate_final_report(self) -> Dict[str, Any]:
        """
        Generate a final report of the quality enforcement process.
        
        Returns:
            A dictionary containing the final report
        """
        self.log("Generating final report...")
        
        # Calculate summary statistics
        total_iterations = len(self.report["iterations"])
        total_changes = sum(iteration["changes_made"] for iteration in self.report["iterations"])
        scripts_executed = sum(len(iteration["scripts"]) for iteration in self.report["iterations"])
        scripts_succeeded = sum(sum(1 for script in iteration["scripts"] if script["success"]) for iteration in self.report["iterations"])
        scripts_failed = scripts_executed - scripts_succeeded
        total_execution_time = sum(iteration["execution_time"] for iteration in self.report["iterations"])
        
        # Update the report summary
        self.report["summary"]["total_iterations"] = total_iterations
        self.report["summary"]["total_changes"] = total_changes
        self.report["summary"]["scripts_executed"] = scripts_executed
        self.report["summary"]["scripts_succeeded"] = scripts_succeeded
        self.report["summary"]["scripts_failed"] = scripts_failed
        self.report["summary"]["total_execution_time"] = total_execution_time
        
        # Generate the final state
        self._generate_final_state()
        
        return self.report
    
    def _generate_final_state(self) -> None:
        """
        Generate the final state of the project after quality enforcement.
        
        This method collects information about the final state of the project,
        including code quality, file structure, essential files, and dependencies.
        """
        self.log("Generating final state...")
        
        # Collect code quality information
        try:
            code_quality_report_path = os.path.join(self.project_dir, "data/reports/code_quality_report.json")
            if os.path.exists(code_quality_report_path):
                with open(code_quality_report_path, 'r') as f:
                    self.report["final_state"]["code_quality"] = json.load(f)
        except Exception as e:
            logger.error(f"Error loading code quality report: {e}")
        
        # Collect file structure information
        try:
            file_structure_report_path = os.path.join(self.project_dir, "data/reports/project-structure-report.json")
            if os.path.exists(file_structure_report_path):
                with open(file_structure_report_path, 'r') as f:
                    self.report["final_state"]["file_structure"] = json.load(f)
        except Exception as e:
            logger.error(f"Error loading file structure report: {e}")
        
        # Collect essential files information
        try:
            essential_files_report_path = os.path.join(self.project_dir, "data/reports/essential-files-report.json")
            if os.path.exists(essential_files_report_path):
                with open(essential_files_report_path, 'r') as f:
                    self.report["final_state"]["essential_files"] = json.load(f)
        except Exception as e:
            logger.error(f"Error loading essential files report: {e}")
        
        # Collect dependency information
        try:
            dependency_report_path = os.path.join(self.project_dir, "data/reports/dependency-audit-report.json")
            if os.path.exists(dependency_report_path):
                with open(dependency_report_path, 'r') as f:
                    self.report["final_state"]["dependencies"] = json.load(f)
        except Exception as e:
            logger.error(f"Error loading dependency report: {e}")
    
    def save_report(self, output_path: str) -> bool:
        """
        Save the report to a file.
        
        Args:
            output_path: Path to the output report file
            
        Returns:
            True if the save was successful, False otherwise
        """
        try:
            # Create directory structure if needed
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(self.report, f, indent=2)
            
            logger.info(f"Saved report to {output_path}")
            return True
        
        except (IOError, OSError) as e:
            logger.error(f"Error saving report to {output_path}: {e}")
            return False
    
    def enforce_quality_standards(self) -> bool:
        """
        Enforce quality standards by executing all quality enforcement scripts in an iterative cycle.
        
        Returns:
            True if the enforcement was successful, False otherwise
        """
        self.log("Starting quality standards enforcement...")
        
        iteration = 0
        changes_made = True
        
        while changes_made and iteration < self.max_iterations:
            iteration += 1
            self.log(f"Starting iteration {iteration}...")
            
            # Initialize iteration data
            iteration_data = {
                "iteration": iteration,
                "timestamp": datetime.datetime.now().isoformat(),
                "scripts": [],
                "changes_made": False,
                "execution_time": 0
            }
            
            # Execute each script in order
            iteration_changes = False
            iteration_start_time = time.time()
            
            for script_name in ["code_structure", "file_cleanup", "essential_files", "code_formatting", "dependency_audit"]:
                self.log(f"Executing {script_name} script...")
                
                # Execute the script
                success, result = self._execute_script(script_name)
                
                # Detect if the script made any changes
                script_changes = self._detect_changes(script_name, result)
                
                # Update iteration data
                iteration_data["scripts"].append({
                    "name": script_name,
                    "success": success,
                    "changes_made": script_changes,
                    "result": result
                })
                
                # Update iteration changes
                if script_changes:
                    iteration_changes = True
            
            # Calculate iteration execution time
            iteration_execution_time = time.time() - iteration_start_time
            iteration_data["execution_time"] = iteration_execution_time
            
            # Update iteration changes
            iteration_data["changes_made"] = iteration_changes
            
            # Add iteration data to report
            self.report["iterations"].append(iteration_data)
            
            # Update changes_made for next iteration
            changes_made = iteration_changes
            
            self.log(f"Iteration {iteration} completed in {iteration_execution_time:.2f} seconds")
            self.log(f"Changes made: {changes_made}")
        
        # Generate final report
        self._generate_final_report()
        
        # Update knowledge graph
        if not self.skip_kg_update:
            self._update_knowledge_graph()
        
        return True


def main():
    """Main entry point for the script."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Enforce quality standards by executing all quality enforcement scripts in an iterative cycle.")
    parser.add_argument("--project-dir", default=".", help="Path to the project directory")
    parser.add_argument("--max-iterations", type=int, default=10, help="Maximum number of iterations to perform")
    parser.add_argument("--output", default="data/reports/quality-standards-report.json", help="Path to the output report file")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode (don't actually modify files)")
    parser.add_argument("--skip-kg-update", action="store_true", help="Skip updating the knowledge graph")
    
    args = parser.parse_args()
    
    # Create quality standards enforcer
    enforcer = QualityStandardsEnforcer(
        project_dir=args.project_dir,
        max_iterations=args.max_iterations,
        verbose=args.verbose,
        dry_run=args.dry_run,
        skip_kg_update=args.skip_kg_update
    )
    
    # Enforce quality standards
    success = enforcer.enforce_quality_standards()
    
    # Save report
    enforcer.save_report(args.output)
    
    # Print summary
    print("\nQuality Standards Enforcement Summary:")
    print(f"  Total iterations: {enforcer.report['summary']['total_iterations']}")
    print(f"  Total changes: {enforcer.report['summary']['total_changes']}")
    print(f"  Scripts executed: {enforcer.report['summary']['scripts_executed']}")
    print(f"  Scripts succeeded: {enforcer.report['summary']['scripts_succeeded']}")
    print(f"  Scripts failed: {enforcer.report['summary']['scripts_failed']}")
    print(f"  Total execution time: {enforcer.report['summary']['total_execution_time']:.2f} seconds")
    
    if args.dry_run:
        print("\nDry run mode: No files were modified.")
        print(f"Check the report at {args.output} for details.")
    else:
        if success:
            print("\nQuality standards enforcement completed successfully.")
        else:
            print("\nQuality standards enforcement completed with errors. Check the log for details.")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())