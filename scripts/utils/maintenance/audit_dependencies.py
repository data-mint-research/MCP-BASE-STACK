#!/usr/bin/env python3
"""
Dependency Audit Script

This script audits project dependencies to:
1. Confirm that all dependency versions are up-to-date
2. Check for known vulnerabilities in dependencies
3. Ensure consistency across the project
4. Update the knowledge graph with dependency information

The script provides functionality to:
1. Scan the project for dependency declarations (requirements.txt, package.json, etc.)
2. Check if dependencies are up-to-date using appropriate tools (pip-audit, npm audit, etc.)
3. Identify known vulnerabilities in dependencies
4. Generate a comprehensive report of findings

Features:
- Detects inconsistent dependency versions across the project
- Recommends updates for outdated dependencies
- Provides security advisories for vulnerable dependencies
- Has a dry-run mode for previewing changes
- Integrates with the QualityEnforcer class
- Updates the knowledge graph with dependency information

Usage:
    python audit_dependencies.py --project-dir /path/to/project
    python audit_dependencies.py --project-dir /path/to/project --dry-run
    python audit_dependencies.py --project-dir /path/to/project --verbose
    python audit_dependencies.py --project-dir /path/to/project --output /path/to/report.json
"""

import argparse
import datetime
import importlib.util
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set, Union, Callable

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/logs/audit_dependencies.log')
    ]
)
logger = logging.getLogger(__name__)


class DependencyAuditor:
    """
    Class to audit project dependencies.
    
    This class provides methods to scan for dependency declarations, check if dependencies
    are up-to-date, identify known vulnerabilities, and generate a comprehensive report.
    
    Attributes:
        project_dir: Path to the project directory
        verbose: Whether to enable verbose logging
        dry_run: Whether to run in dry-run mode (only report issues without making changes)
        output_path: Path to the output report file
    """
    
    def __init__(
        self,
        project_dir: str,
        verbose: bool = False,
        dry_run: bool = False,
        output_path: str = None
    ):
        """
        Initialize the DependencyAuditor.
        
        Args:
            project_dir: Path to the project directory
            verbose: Whether to enable verbose logging
            dry_run: Whether to run in dry-run mode (only report issues without making changes)
            output_path: Path to the output report file
        """
        self.project_dir = os.path.abspath(project_dir)
        self.verbose = verbose
        self.dry_run = dry_run
        self.output_path = output_path or os.path.join(self.project_dir, "data", "reports", "dependency-audit-report.json")
        
        # Initialize report data structure
        self.report = {
            "project_dir": self.project_dir,
            "timestamp": datetime.datetime.now().isoformat(),
            "summary": {
                "dependency_files_scanned": 0,
                "dependencies_checked": 0,
                "outdated_dependencies": 0,
                "vulnerable_dependencies": 0,
                "inconsistent_dependencies": 0,
                "errors": 0
            },
            "dependency_files": [],
            "outdated_dependencies": [],
            "vulnerable_dependencies": [],
            "inconsistent_dependencies": [],
            "recommendations": []
        }
        
        # Try to load the QualityEnforcer for integration
        self.quality_enforcer = self._load_quality_enforcer()
        
        # Initialize dependency managers
        self.dependency_managers = {
            "python": self._check_python_dependencies,
            "node": self._check_node_dependencies,
            "java": self._check_java_dependencies,
            "docker": self._check_docker_dependencies
        }
    
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
    
    def _find_dependency_files(self) -> List[Dict[str, Any]]:
        """
        Find all dependency declaration files in the project.
        
        Returns:
            List of dictionaries with information about dependency files
        """
        self.log("Scanning for dependency declaration files...")
        
        dependency_files = []
        
        # Define patterns for dependency files
        patterns = {
            "python": ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile"],
            "node": ["package.json", "yarn.lock", "package-lock.json"],
            "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
            "docker": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"]
        }
        
        # Walk through the project directory
        for root, _, files in os.walk(self.project_dir):
            # Skip virtual environments and node_modules
            if any(excluded in root for excluded in [".venv", "venv", "node_modules", ".git"]):
                continue
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.project_dir)
                
                # Check if the file matches any of the patterns
                for manager, file_patterns in patterns.items():
                    if any(file == pattern or file.endswith(pattern) for pattern in file_patterns):
                        dependency_files.append({
                            "path": rel_path,
                            "manager": manager,
                            "type": file
                        })
                        self.log(f"Found dependency file: {rel_path} ({manager})")
        
        return dependency_files
    
    def _parse_requirements_txt(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse a requirements.txt file.
        
        Args:
            file_path: Path to the requirements.txt file
            
        Returns:
            List of dictionaries with information about dependencies
        """
        dependencies = []
        
        try:
            with open(os.path.join(self.project_dir, file_path), 'r') as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse the dependency
                    match = re.match(r'^([a-zA-Z0-9_.-]+)([<>=!~].+)?$', line)
                    if match:
                        name = match.group(1)
                        version_spec = match.group(2) or ""
                        
                        dependencies.append({
                            "name": name,
                            "version_spec": version_spec,
                            "file_path": file_path
                        })
        
        except Exception as e:
            logger.error(f"Error parsing requirements.txt file {file_path}: {e}")
            self.report["summary"]["errors"] += 1
        
        return dependencies
    
    def _parse_package_json(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse a package.json file.
        
        Args:
            file_path: Path to the package.json file
            
        Returns:
            List of dictionaries with information about dependencies
        """
        dependencies = []
        
        try:
            with open(os.path.join(self.project_dir, file_path), 'r') as f:
                data = json.load(f)
            
            # Process dependencies
            for dep_type in ["dependencies", "devDependencies"]:
                if dep_type in data:
                    for name, version_spec in data[dep_type].items():
                        dependencies.append({
                            "name": name,
                            "version_spec": version_spec,
                            "type": dep_type,
                            "file_path": file_path
                        })
        
        except Exception as e:
            logger.error(f"Error parsing package.json file {file_path}: {e}")
            self.report["summary"]["errors"] += 1
        
        return dependencies
    
    def _check_python_dependencies(self, file_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Check Python dependencies for updates and vulnerabilities.
        
        Args:
            file_path: Path to the Python dependency file
            
        Returns:
            Tuple of (outdated_dependencies, vulnerable_dependencies)
        """
        self.log(f"Checking Python dependencies in {file_path}...")
        
        outdated = []
        vulnerable = []
        
        # Parse the dependency file
        if file_path.endswith("requirements.txt"):
            dependencies = self._parse_requirements_txt(file_path)
        else:
            # For other Python dependency files, we'll need to implement specific parsers
            self.log(f"Parsing {file_path} is not yet supported")
            return [], []
        
        # Check for outdated dependencies using pip list --outdated
        try:
            if not self.dry_run:
                # Create a temporary requirements file
                temp_req_file = os.path.join(self.project_dir, "temp_requirements.txt")
                with open(temp_req_file, 'w') as f:
                    for dep in dependencies:
                        f.write(f"{dep['name']}{dep['version_spec']}\n")
                
                # Run pip list --outdated
                result = subprocess.run(
                    ["pip", "list", "--outdated", "--format=json", "--requirement", temp_req_file],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                # Remove the temporary file
                os.remove(temp_req_file)
                
                if result.returncode == 0:
                    outdated_deps = json.loads(result.stdout)
                    for dep in outdated_deps:
                        outdated.append({
                            "name": dep["name"],
                            "current_version": dep["version"],
                            "latest_version": dep["latest_version"],
                            "file_path": file_path
                        })
                        self.log(f"Outdated dependency: {dep['name']} (current: {dep['version']}, latest: {dep['latest_version']})")
        
        except Exception as e:
            logger.error(f"Error checking for outdated Python dependencies: {e}")
            self.report["summary"]["errors"] += 1
        
        # Check for vulnerabilities using pip-audit
        try:
            if not self.dry_run and shutil.which("pip-audit"):
                # Create a temporary requirements file
                temp_req_file = os.path.join(self.project_dir, "temp_requirements.txt")
                with open(temp_req_file, 'w') as f:
                    for dep in dependencies:
                        f.write(f"{dep['name']}{dep['version_spec']}\n")
                
                # Run pip-audit
                result = subprocess.run(
                    ["pip-audit", "--requirement", temp_req_file, "--format=json"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                # Remove the temporary file
                os.remove(temp_req_file)
                
                if result.returncode == 0:
                    audit_results = json.loads(result.stdout)
                    for vuln in audit_results.get("vulnerabilities", []):
                        vulnerable.append({
                            "name": vuln["name"],
                            "version": vuln["version"],
                            "vulnerability_id": vuln["id"],
                            "description": vuln["description"],
                            "fix_version": vuln.get("fix_version"),
                            "file_path": file_path
                        })
                        self.log(f"Vulnerable dependency: {vuln['name']} {vuln['version']} ({vuln['id']})")
            else:
                self.log("pip-audit not found, skipping vulnerability check for Python dependencies")
        
        except Exception as e:
            logger.error(f"Error checking for vulnerable Python dependencies: {e}")
            self.report["summary"]["errors"] += 1
        
        return outdated, vulnerable
    
    def _check_node_dependencies(self, file_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Check Node.js dependencies for updates and vulnerabilities.
        
        Args:
            file_path: Path to the Node.js dependency file
            
        Returns:
            Tuple of (outdated_dependencies, vulnerable_dependencies)
        """
        self.log(f"Checking Node.js dependencies in {file_path}...")
        
        outdated = []
        vulnerable = []
        
        # Parse the dependency file
        if file_path.endswith("package.json"):
            dependencies = self._parse_package_json(file_path)
        else:
            # For other Node.js dependency files, we'll need to implement specific parsers
            self.log(f"Parsing {file_path} is not yet supported")
            return [], []
        
        # Check for outdated dependencies using npm outdated
        try:
            if not self.dry_run and shutil.which("npm"):
                # Get the directory containing the package.json file
                package_dir = os.path.dirname(os.path.join(self.project_dir, file_path))
                
                # Run npm outdated
                result = subprocess.run(
                    ["npm", "outdated", "--json"],
                    cwd=package_dir,
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if result.returncode == 1:  # npm outdated returns 1 if there are outdated dependencies
                    outdated_deps = json.loads(result.stdout)
                    for name, info in outdated_deps.items():
                        outdated.append({
                            "name": name,
                            "current_version": info["current"],
                            "latest_version": info["latest"],
                            "file_path": file_path
                        })
                        self.log(f"Outdated dependency: {name} (current: {info['current']}, latest: {info['latest']})")
        
        except Exception as e:
            logger.error(f"Error checking for outdated Node.js dependencies: {e}")
            self.report["summary"]["errors"] += 1
        
        # Check for vulnerabilities using npm audit
        try:
            if not self.dry_run and shutil.which("npm"):
                # Get the directory containing the package.json file
                package_dir = os.path.dirname(os.path.join(self.project_dir, file_path))
                
                # Run npm audit
                result = subprocess.run(
                    ["npm", "audit", "--json"],
                    cwd=package_dir,
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if result.returncode == 0:
                    audit_results = json.loads(result.stdout)
                    for vuln_id, vuln in audit_results.get("vulnerabilities", {}).items():
                        vulnerable.append({
                            "name": vuln["name"],
                            "version": vuln["version"],
                            "vulnerability_id": vuln_id,
                            "description": vuln["overview"],
                            "severity": vuln["severity"],
                            "fix_version": vuln.get("fixAvailable", {}).get("version"),
                            "file_path": file_path
                        })
                        self.log(f"Vulnerable dependency: {vuln['name']} {vuln['version']} ({vuln_id})")
        
        except Exception as e:
            logger.error(f"Error checking for vulnerable Node.js dependencies: {e}")
            self.report["summary"]["errors"] += 1
        
        return outdated, vulnerable
    
    def _check_java_dependencies(self, file_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Check Java dependencies for updates and vulnerabilities.
        
        Args:
            file_path: Path to the Java dependency file
            
        Returns:
            Tuple of (outdated_dependencies, vulnerable_dependencies)
        """
        self.log(f"Checking Java dependencies in {file_path} is not yet implemented")
        return [], []
    
    def _check_docker_dependencies(self, file_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Check Docker dependencies for updates and vulnerabilities.
        
        Args:
            file_path: Path to the Docker dependency file
            
        Returns:
            Tuple of (outdated_dependencies, vulnerable_dependencies)
        """
        self.log(f"Checking Docker dependencies in {file_path} is not yet implemented")
        return [], []
    
    def _detect_inconsistent_dependencies(self, dependency_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect inconsistent dependency versions across the project.
        
        Args:
            dependency_files: List of dictionaries with information about dependency files
            
        Returns:
            List of dictionaries with information about inconsistent dependencies
        """
        self.log("Detecting inconsistent dependency versions...")
        
        inconsistent = []
        
        # Group dependencies by name and manager
        dependencies_by_name = {}
        
        for dep_file in dependency_files:
            file_path = dep_file["path"]
            manager = dep_file["manager"]
            
            # Parse the dependency file
            if manager == "python" and file_path.endswith("requirements.txt"):
                deps = self._parse_requirements_txt(file_path)
            elif manager == "node" and file_path.endswith("package.json"):
                deps = self._parse_package_json(file_path)
            else:
                continue
            
            # Group dependencies by name
            for dep in deps:
                key = f"{manager}:{dep['name']}"
                if key not in dependencies_by_name:
                    dependencies_by_name[key] = []
                dependencies_by_name[key].append(dep)
        
        # Check for inconsistent versions
        for key, deps in dependencies_by_name.items():
            if len(deps) > 1:
                # Check if all versions are the same
                versions = set(dep.get("version_spec", "") for dep in deps)
                if len(versions) > 1:
                    inconsistent.append({
                        "name": deps[0]["name"],
                        "manager": key.split(":")[0],
                        "versions": [
                            {
                                "version_spec": dep.get("version_spec", ""),
                                "file_path": dep["file_path"]
                            }
                            for dep in deps
                        ]
                    })
                    self.log(f"Inconsistent dependency: {deps[0]['name']} has multiple versions across the project")
        
        return inconsistent
    
    def _generate_recommendations(self, outdated: List[Dict[str, Any]], vulnerable: List[Dict[str, Any]], inconsistent: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate recommendations for fixing dependency issues.
        
        Args:
            outdated: List of dictionaries with information about outdated dependencies
            vulnerable: List of dictionaries with information about vulnerable dependencies
            inconsistent: List of dictionaries with information about inconsistent dependencies
            
        Returns:
            List of dictionaries with recommendations
        """
        self.log("Generating recommendations...")
        
        recommendations = []
        
        # Recommendations for outdated dependencies
        for dep in outdated:
            recommendations.append({
                "type": "update",
                "name": dep["name"],
                "current_version": dep["current_version"],
                "recommended_version": dep["latest_version"],
                "file_path": dep["file_path"],
                "message": f"Update {dep['name']} from {dep['current_version']} to {dep['latest_version']}"
            })
        
        # Recommendations for vulnerable dependencies
        for dep in vulnerable:
            fix_version = dep.get("fix_version")
            if fix_version:
                recommendations.append({
                    "type": "security",
                    "name": dep["name"],
                    "current_version": dep["version"],
                    "recommended_version": fix_version,
                    "vulnerability_id": dep["vulnerability_id"],
                    "file_path": dep["file_path"],
                    "message": f"Update {dep['name']} to {fix_version} to fix vulnerability {dep['vulnerability_id']}"
                })
            else:
                recommendations.append({
                    "type": "security",
                    "name": dep["name"],
                    "current_version": dep["version"],
                    "vulnerability_id": dep["vulnerability_id"],
                    "file_path": dep["file_path"],
                    "message": f"Vulnerability {dep['vulnerability_id']} found in {dep['name']} {dep['version']}, but no fix version is available"
                })
        
        # Recommendations for inconsistent dependencies
        for dep in inconsistent:
            versions = [v["version_spec"] for v in dep["versions"]]
            file_paths = [v["file_path"] for v in dep["versions"]]
            
            recommendations.append({
                "type": "consistency",
                "name": dep["name"],
                "versions": versions,
                "file_paths": file_paths,
                "message": f"Standardize {dep['name']} version across the project: {', '.join(versions)}"
            })
        
        return recommendations
    
    def _update_knowledge_graph(self) -> bool:
        """
        Update the knowledge graph with dependency information.
        
        Returns:
            True if the update was successful, False otherwise
        """
        if self.dry_run:
            self.log("[DRY RUN] Would update knowledge graph")
            return True
        
        self.log("Updating knowledge graph...")
        
        try:
            # Use the QualityEnforcer if available
            if self.quality_enforcer:
                self.log("Updating knowledge graph via QualityEnforcer...")
                # Import QualityCheckResult and QualityCheckSeverity
                from core.quality.components.base import QualityCheckResult, QualityCheckSeverity
                
                # Create QualityCheckResult objects for the findings
                results = []
                
                # Add results for outdated dependencies
                for dep in self.report["outdated_dependencies"]:
                    result = QualityCheckResult(
                        check_id="dependency_audit",
                        severity=QualityCheckSeverity.WARNING,
                        message=f"Outdated dependency: {dep['name']} (current: {dep['current_version']}, latest: {dep['latest_version']})",
                        file_path=dep["file_path"],
                        source="DependencyAuditor"
                    )
                    results.append(result)
                
                # Add results for vulnerable dependencies
                for dep in self.report["vulnerable_dependencies"]:
                    result = QualityCheckResult(
                        check_id="dependency_audit",
                        severity=QualityCheckSeverity.ERROR,
                        message=f"Vulnerable dependency: {dep['name']} {dep['version']} ({dep['vulnerability_id']})",
                        file_path=dep["file_path"],
                        source="DependencyAuditor"
                    )
                    results.append(result)
                
                # Add results for inconsistent dependencies
                for dep in self.report["inconsistent_dependencies"]:
                    result = QualityCheckResult(
                        check_id="dependency_audit",
                        severity=QualityCheckSeverity.WARNING,
                        message=f"Inconsistent dependency: {dep['name']} has multiple versions across the project",
                        file_path=dep["versions"][0]["file_path"],
                        source="DependencyAuditor"
                    )
                    results.append(result)
                
                # Update the knowledge graph
                if results:
                    self.quality_enforcer.update_knowledge_graph(results)
                    self.log(f"Updated knowledge graph with {len(results)} findings")
                
                return True
            else:
                # Try to run a script to update the knowledge graph
                update_script = os.path.join(self.project_dir, "core/kg/scripts/update_knowledge_graph.py")
                if os.path.exists(update_script):
                    self.log("Updating knowledge graph via update_knowledge_graph.py...")
                    result = subprocess.run(["python", update_script], cwd=self.project_dir)
                    if result.returncode == 0:
                        self.log("Successfully updated knowledge graph")
                        return True
                    else:
                        logger.error("Failed to update knowledge graph")
                        self.report["summary"]["errors"] += 1
                        return False
                else:
                    self.log("No knowledge graph update mechanism found")
                    return False
        except Exception as e:
            logger.error(f"Error updating knowledge graph: {e}")
            self.report["summary"]["errors"] += 1
            return False
    
    def audit_dependencies(self) -> bool:
        """
        Audit project dependencies.
        
        Returns:
            True if the audit was successful, False otherwise
        """
        self.log("Starting dependency audit...")
        
        success = True
        
        # Find dependency files
        dependency_files = self._find_dependency_files()
        self.report["dependency_files"] = dependency_files
        self.report["summary"]["dependency_files_scanned"] = len(dependency_files)
        
        # Check dependencies for each file
        all_outdated = []
        all_vulnerable = []
        
        for dep_file in dependency_files:
            file_path = dep_file["path"]
            manager = dep_file["manager"]
            
            # Check dependencies using the appropriate manager
            if manager in self.dependency_managers:
                outdated, vulnerable = self.dependency_managers[manager](file_path)
                all_outdated.extend(outdated)
                all_vulnerable.extend(vulnerable)
                
                # Update summary
                self.report["summary"]["dependencies_checked"] += len(outdated) + len(vulnerable)
            else:
                self.log(f"No dependency manager available for {manager}")
        
        # Detect inconsistent dependencies
        inconsistent = self._detect_inconsistent_dependencies(dependency_files)
        
        # Update report
        self.report["outdated_dependencies"] = all_outdated
        self.report["vulnerable_dependencies"] = all_vulnerable
        self.report["inconsistent_dependencies"] = inconsistent
        self.report["summary"]["outdated_dependencies"] = len(all_outdated)
        self.report["summary"]["vulnerable_dependencies"] = len(all_vulnerable)
        self.report["summary"]["inconsistent_dependencies"] = len(inconsistent)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(all_outdated, all_vulnerable, inconsistent)
        self.report["recommendations"] = recommendations
        
        # Update knowledge graph
        if not self.dry_run:
            if not self._update_knowledge_graph():
                logger.warning("Failed to update knowledge graph, but audit was successful")
        
        return success
    
    def save_report(self) -> bool:
        """
        Save the report to a file.
        
        Returns:
            True if the save was successful, False otherwise
        """
        try:
            # Create directory structure if needed
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            
            with open(self.output_path, 'w') as f:
                json.dump(self.report, f, indent=2)
            
            logger.info(f"Saved report to {self.output_path}")
            return True
        
        except (IOError, OSError) as e:
            logger.error(f"Error saving report to {self.output_path}: {e}")
            return False


def main():
    """Main entry point for the script."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Audit project dependencies.")
    parser.add_argument("--project-dir", default=".", help="Path to the project directory")
    parser.add_argument("--output", help="Path to the output report file")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode (don't update knowledge graph)")
    
    args = parser.parse_args()
    
    # Create dependency auditor
    auditor = DependencyAuditor(
        project_dir=args.project_dir,
        verbose=args.verbose,
        dry_run=args.dry_run,
        output_path=args.output
    )
    
    # Audit dependencies
    success = auditor.audit_dependencies()
    
    # Save report
    auditor.save_report()
    
    # Print summary
    print("\nDependency Audit Summary:")
    print(f"  Dependency files scanned: {auditor.report['summary']['dependency_files_scanned']}")
    print(f"  Dependencies checked: {auditor.report['summary']['dependencies_checked']}")
    print(f"  Outdated dependencies: {auditor.report['summary']['outdated_dependencies']}")
    print(f"  Vulnerable dependencies: {auditor.report['summary']['vulnerable_dependencies']}")
    print(f"  Inconsistent dependencies: {auditor.report['summary']['inconsistent_dependencies']}")
    print(f"  Errors: {auditor.report['summary']['errors']}")
    
    if auditor.dry_run:
        print("\nDry run mode: No changes were made to the knowledge graph.")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
