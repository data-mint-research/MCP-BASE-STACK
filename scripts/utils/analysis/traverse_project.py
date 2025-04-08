#!/usr/bin/env python3
"""
Recursively traverse a project directory and compare it against the specification manifest.

This script provides functionality to:
1. Load the specification manifest
2. Recursively traverse the project directory
3. Compare each directory and file against the expected structure
4. Generate a detailed report of compliance and deviations
5. Output a structured JSON report

Usage:
    python traverse_project.py --project-dir /path/to/project --manifest /path/to/manifest.json --output /path/to/report.json
    python traverse_project.py --project-dir /path/to/project --verbose
    python traverse_project.py --project-dir /path/to/project --dry-run
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set


class ProjectTraverser:
    """
    Class to traverse a project directory and compare it against the specification manifest.
    
    This class provides methods to recursively traverse a project directory,
    compare it against the expected structure defined in the specification manifest,
    and generate a detailed report of compliance and deviations.
    
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
        Initialize the ProjectTraverser.
        
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
        self.dir_structure = manifest["specification_manifest"]["directory_structure"]
        self.file_templates = manifest["specification_manifest"]["file_templates"]
        self.naming_conventions = manifest["specification_manifest"]["naming_conventions"]
        
        # Initialize report data structure
        self.report = {
            "project_dir": self.project_dir,
            "timestamp": None,  # Will be set when generating the report
            "summary": {
                "total_directories": 0,
                "total_files": 0,
                "compliant_directories": 0,
                "compliant_files": 0,
                "directory_issues": 0,
                "file_issues": 0,
                "naming_issues": 0,
                "location_issues": 0,
                "compliance_percentage": 0.0
            },
            "directory_structure": {
                "expected": {},
                "actual": {},
                "issues": []
            },
            "file_presence": {
                "expected": {},
                "actual": {},
                "issues": []
            },
            "naming_conventions": {
                "issues": []
            },
            "location_analysis": {
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
            print(message)
    
    def traverse_directory(self) -> None:
        """
        Recursively traverse the project directory and collect information.
        
        This method walks through the project directory, collecting information
        about the actual directory structure and files, and compares them against
        the expected structure defined in the specification manifest.
        """
        self.log(f"Traversing directory: {self.project_dir}")
        
        # Collect actual directory structure
        actual_dirs = set()
        actual_files = set()
        
        for root, dirs, files in os.walk(self.project_dir):
            rel_root = os.path.relpath(root, self.project_dir)
            if rel_root == ".":
                rel_root = "root"
            else:
                actual_dirs.add(rel_root)
            
            for file in files:
                file_path = os.path.join(rel_root, file)
                actual_files.add(file_path)
        
        self.report["summary"]["total_directories"] = len(actual_dirs) + 1  # +1 for root
        self.report["summary"]["total_files"] = len(actual_files)
        
        # Store actual structure in report
        self.report["directory_structure"]["actual"] = {
            "root": {"path": self.project_dir, "subdirectories": [d for d in actual_dirs if "/" not in d]}
        }
        
        for dir_path in actual_dirs:
            parent_dir = os.path.dirname(dir_path) or "root"
            dir_name = os.path.basename(dir_path)
            
            if parent_dir not in self.report["directory_structure"]["actual"]:
                self.report["directory_structure"]["actual"][parent_dir] = {
                    "path": os.path.join(self.project_dir, parent_dir),
                    "subdirectories": []
                }
            
            if dir_path not in self.report["directory_structure"]["actual"]:
                self.report["directory_structure"]["actual"][dir_path] = {
                    "path": os.path.join(self.project_dir, dir_path),
                    "subdirectories": []
                }
            
            subdirs = self.report["directory_structure"]["actual"][parent_dir]["subdirectories"]
            if dir_name not in subdirs:
                subdirs.append(dir_name)
        
        # Store actual files in report
        for file_path in actual_files:
            dir_path = os.path.dirname(file_path) or "root"
            file_name = os.path.basename(file_path)
            
            if dir_path not in self.report["file_presence"]["actual"]:
                self.report["file_presence"]["actual"][dir_path] = []
            
            self.report["file_presence"]["actual"][dir_path].append(file_name)
        
        # Compare against expected structure
        self.compare_directory_structure()
        self.compare_file_presence()
        self.check_naming_conventions()
        self.analyze_file_locations()
        
        # Calculate compliance percentage
        total_items = self.report["summary"]["total_directories"] + self.report["summary"]["total_files"]
        total_issues = (
            self.report["summary"]["directory_issues"] + 
            self.report["summary"]["file_issues"] + 
            self.report["summary"]["naming_issues"] + 
            self.report["summary"]["location_issues"]
        )
        
        if total_items > 0:
            compliance = 1.0 - (total_issues / total_items)
            self.report["summary"]["compliance_percentage"] = round(compliance * 100, 2)
        else:
            self.report["summary"]["compliance_percentage"] = 100.0
    
    def compare_directory_structure(self) -> None:
        """
        Compare the actual directory structure against the expected structure.
        
        This method checks if all required directories exist and reports any missing directories.
        """
        self.log("Comparing directory structure...")
        
        # Store expected structure in report
        self.report["directory_structure"]["expected"] = {}
        
        for dir_path, dir_info in self.dir_structure.items():
            if dir_path == "root":
                full_path = self.project_dir
            else:
                full_path = os.path.join(self.project_dir, dir_path)
            
            parent_dir = os.path.dirname(dir_path) or "root"
            dir_name = os.path.basename(dir_path)
            
            if parent_dir not in self.report["directory_structure"]["expected"]:
                self.report["directory_structure"]["expected"][parent_dir] = {
                    "path": os.path.join(self.project_dir, parent_dir),
                    "subdirectories": []
                }
            
            if dir_path not in self.report["directory_structure"]["expected"]:
                self.report["directory_structure"]["expected"][dir_path] = {
                    "path": full_path,
                    "subdirectories": []
                }
            
            if dir_path != "root":
                subdirs = self.report["directory_structure"]["expected"][parent_dir]["subdirectories"]
                if dir_name not in subdirs:
                    subdirs.append(dir_name)
            
            # Add required subdirectories
            if "required_subdirectories" in dir_info:
                for subdir in dir_info["required_subdirectories"]:
                    subdir_path = os.path.join(dir_path, subdir) if dir_path != "root" else subdir
                    
                    if subdir_path not in self.report["directory_structure"]["expected"]:
                        self.report["directory_structure"]["expected"][subdir_path] = {
                            "path": os.path.join(full_path, subdir),
                            "subdirectories": []
                        }
                    
                    subdirs = self.report["directory_structure"]["expected"][dir_path]["subdirectories"]
                    if subdir not in subdirs:
                        subdirs.append(subdir)
        
        # Check for missing required directories
        for dir_path, dir_info in self.dir_structure.items():
            if dir_path == "root":
                full_path = self.project_dir
            else:
                full_path = os.path.join(self.project_dir, dir_path)
            
            if not os.path.isdir(full_path):
                self.report["directory_structure"]["issues"].append({
                    "type": "missing_directory",
                    "path": dir_path,
                    "severity": "error",
                    "message": f"Required directory '{dir_path}' is missing"
                })
                self.report["summary"]["directory_issues"] += 1
                continue
            
            self.report["summary"]["compliant_directories"] += 1
            
            if "required_subdirectories" in dir_info:
                for subdir in dir_info["required_subdirectories"]:
                    subdir_path = os.path.join(full_path, subdir)
                    rel_subdir_path = os.path.join(dir_path, subdir) if dir_path != "root" else subdir
                    
                    if not os.path.isdir(subdir_path):
                        self.report["directory_structure"]["issues"].append({
                            "type": "missing_subdirectory",
                            "path": rel_subdir_path,
                            "parent": dir_path,
                            "severity": "error",
                            "message": f"Required subdirectory '{subdir}' is missing in '{dir_path}'"
                        })
                        self.report["summary"]["directory_issues"] += 1
                    else:
                        self.report["summary"]["compliant_directories"] += 1
    
    def compare_file_presence(self) -> None:
        """
        Compare the actual file presence against the expected files.
        
        This method checks if all required files exist and reports any missing files.
        """
        self.log("Comparing file presence...")
        
        # Store expected files in report
        self.report["file_presence"]["expected"] = {}
        
        for dir_path, dir_info in self.file_templates.items():
            if dir_path == "root":
                full_path = self.project_dir
            else:
                full_path = os.path.join(self.project_dir, dir_path)
            
            if "required_files" in dir_info:
                if dir_path not in self.report["file_presence"]["expected"]:
                    self.report["file_presence"]["expected"][dir_path] = []
                
                for file_name in dir_info["required_files"]:
                    self.report["file_presence"]["expected"][dir_path].append(file_name)
        
        # Check for missing required files
        for dir_path, dir_info in self.file_templates.items():
            if dir_path == "root":
                full_path = self.project_dir
            else:
                full_path = os.path.join(self.project_dir, dir_path)
            
            if not os.path.isdir(full_path):
                continue  # Skip if directory doesn't exist (already reported by compare_directory_structure)
            
            if "required_files" in dir_info:
                for file_name in dir_info["required_files"]:
                    file_path = os.path.join(full_path, file_name)
                    
                    if not os.path.isfile(file_path):
                        self.report["file_presence"]["issues"].append({
                            "type": "missing_file",
                            "path": os.path.join(dir_path, file_name) if dir_path != "root" else file_name,
                            "directory": dir_path,
                            "severity": "error",
                            "message": f"Required file '{file_name}' is missing in '{dir_path}'"
                        })
                        self.report["summary"]["file_issues"] += 1
                    else:
                        self.report["summary"]["compliant_files"] += 1
    
    def check_naming_conventions(self) -> None:
        """
        Check if files follow the naming conventions defined in the manifest.
        
        This method checks if files follow the naming conventions for their respective types.
        """
        self.log("Checking naming conventions...")
        
        # Python files
        python_files = []
        for root, _, files in os.walk(self.project_dir):
            for file in files:
                if file.endswith(".py"):
                    rel_path = os.path.relpath(os.path.join(root, file), self.project_dir)
                    python_files.append((rel_path, file))
        
        # Check Python module names
        if "python" in self.naming_conventions and "modules" in self.naming_conventions["python"]:
            module_pattern = self.naming_conventions["python"]["modules"]["regex"]
            for rel_path, file_name in python_files:
                if not re.match(module_pattern, file_name):
                    self.report["naming_conventions"]["issues"].append({
                        "type": "invalid_python_module_name",
                        "path": rel_path,
                        "name": file_name,
                        "pattern": self.naming_conventions["python"]["modules"]["pattern"],
                        "severity": "error",
                        "message": f"Python module name '{file_name}' does not follow the required pattern '{self.naming_conventions['python']['modules']['pattern']}'"
                    })
                    self.report["summary"]["naming_issues"] += 1
        
        # Shell script files
        shell_files = []
        for root, _, files in os.walk(self.project_dir):
            for file in files:
                if file.endswith(".sh"):
                    rel_path = os.path.relpath(os.path.join(root, file), self.project_dir)
                    shell_files.append((rel_path, file))
        
        # Check shell script names
        if "shell" in self.naming_conventions and "scripts" in self.naming_conventions["shell"]:
            script_pattern = self.naming_conventions["shell"]["scripts"]["regex"]
            for rel_path, file_name in shell_files:
                if not re.match(script_pattern, file_name):
                    self.report["naming_conventions"]["issues"].append({
                        "type": "invalid_shell_script_name",
                        "path": rel_path,
                        "name": file_name,
                        "pattern": self.naming_conventions["shell"]["scripts"]["pattern"],
                        "severity": "error",
                        "message": f"Shell script name '{file_name}' does not follow the required pattern '{self.naming_conventions['shell']['scripts']['pattern']}'"
                    })
                    self.report["summary"]["naming_issues"] += 1
        
        # Markdown files
        markdown_files = []
        for root, _, files in os.walk(self.project_dir):
            for file in files:
                if file.endswith(".md"):
                    rel_path = os.path.relpath(os.path.join(root, file), self.project_dir)
                    markdown_files.append((rel_path, file))
        
        # Check markdown file names
        if "documentation" in self.naming_conventions and "markdown_files" in self.naming_conventions["documentation"]:
            markdown_pattern = self.naming_conventions["documentation"]["markdown_files"]["regex"]
            for rel_path, file_name in markdown_files:
                if not re.match(markdown_pattern, file_name) and file_name != "README.md":
                    self.report["naming_conventions"]["issues"].append({
                        "type": "invalid_markdown_file_name",
                        "path": rel_path,
                        "name": file_name,
                        "pattern": self.naming_conventions["documentation"]["markdown_files"]["pattern"],
                        "severity": "error",
                        "message": f"Markdown file name '{file_name}' does not follow the required pattern '{self.naming_conventions['documentation']['markdown_files']['pattern']}'"
                    })
                    self.report["summary"]["naming_issues"] += 1
    
    def analyze_file_locations(self) -> None:
        """
        Analyze if files are in their ideal locations.
        
        This method checks if files are in the directories where they would be expected
        based on the project structure and naming conventions.
        """
        self.log("Analyzing file locations...")
        
        # Map of file extensions to their ideal directories
        extension_to_dir = {
            ".py": ["core", "services", "scripts", "tests"],
            ".sh": ["scripts"],
            ".md": ["docs"],
            ".json": ["config"],
            ".yaml": ["config"],
            ".yml": ["config"]
        }
        
        # Check all files
        for root, _, files in os.walk(self.project_dir):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), self.project_dir)
                
                # Skip files in the root directory
                if os.path.dirname(rel_path) == "":
                    continue
                
                # Check if file is in an ideal location based on extension
                _, ext = os.path.splitext(file)
                if ext in extension_to_dir:
                    ideal_dirs = extension_to_dir[ext]
                    in_ideal_dir = False
                    
                    for ideal_dir in ideal_dirs:
                        if rel_path.startswith(ideal_dir):
                            in_ideal_dir = True
                            break
                    
                    if not in_ideal_dir:
                        self.report["location_analysis"]["issues"].append({
                            "type": "non_ideal_location",
                            "path": rel_path,
                            "name": file,
                            "extension": ext,
                            "ideal_directories": ideal_dirs,
                            "severity": "warning",
                            "message": f"File '{rel_path}' with extension '{ext}' is not in an ideal directory. Consider moving to one of: {', '.join(ideal_dirs)}"
                        })
                        self.report["summary"]["location_issues"] += 1
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a detailed report of the project structure analysis.
        
        Returns:
            A dictionary containing the detailed report
        """
        import datetime
        
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
        print("\n=== Project Structure Analysis Summary ===")
        print(f"Project directory: {self.project_dir}")
        print(f"Total directories: {self.report['summary']['total_directories']}")
        print(f"Total files: {self.report['summary']['total_files']}")
        print(f"Compliant directories: {self.report['summary']['compliant_directories']}")
        print(f"Compliant files: {self.report['summary']['compliant_files']}")
        print(f"Directory issues: {self.report['summary']['directory_issues']}")
        print(f"File issues: {self.report['summary']['file_issues']}")
        print(f"Naming issues: {self.report['summary']['naming_issues']}")
        print(f"Location issues: {self.report['summary']['location_issues']}")
        print(f"Overall compliance: {self.report['summary']['compliance_percentage']}%")
        
        if self.report["directory_structure"]["issues"]:
            print("\n--- Directory Structure Issues ---")
            for issue in self.report["directory_structure"]["issues"]:
                print(f"- {issue['message']}")
        
        if self.report["file_presence"]["issues"]:
            print("\n--- File Presence Issues ---")
            for issue in self.report["file_presence"]["issues"]:
                print(f"- {issue['message']}")
        
        if self.report["naming_conventions"]["issues"]:
            print("\n--- Naming Convention Issues ---")
            for issue in self.report["naming_conventions"]["issues"]:
                print(f"- {issue['message']}")
        
        if self.report["location_analysis"]["issues"]:
            print("\n--- File Location Issues ---")
            for issue in self.report["location_analysis"]["issues"]:
                print(f"- {issue['message']}")


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
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {file_path}: {e}")
        sys.exit(1)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Recursively traverse a project directory and compare it against the specification manifest."
    )
    
    parser.add_argument(
        "--project-dir", 
        default=".", 
        help="Path to the project directory (default: current directory)"
    )
    parser.add_argument(
        "--manifest",
        default="config/specifications/specification-manifest.json",
        help="Path to the specification manifest (default: config/specifications/specification-manifest.json)"
    )
    parser.add_argument(
        "--output",
        default="data/reports/project-structure-report.json",
        help="Path to save the report to (default: data/reports/project-structure-report.json)"
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
    
    args = parser.parse_args()
    
    # Load the manifest
    manifest = load_json_file(args.manifest)
    
    # Create the traverser
    traverser = ProjectTraverser(
        project_dir=args.project_dir,
        manifest=manifest,
        verbose=args.verbose,
        dry_run=args.dry_run
    )
    
    # Traverse the directory
    traverser.traverse_directory()
    
    # Generate and save the report
    traverser.save_report(args.output)
    
    # Print summary
    traverser.print_summary()


if __name__ == "__main__":
    main()