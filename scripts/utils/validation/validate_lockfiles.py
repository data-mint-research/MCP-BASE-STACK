#!/usr/bin/env python3
"""
Lockfile Validation Script

This script validates that lockfiles are up-to-date with their source dependency files.
It checks:
1. If requirements.lock matches requirements.txt
2. If docker-compose.lock.yml matches the Docker image versions in docker-compose.yml files

Usage:
    python validate_lockfiles.py
    python validate_lockfiles.py --verbose
"""

import argparse
import json
import logging
import os
import re
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/logs/validate_lockfiles.log')
    ]
)
logger = logging.getLogger(__name__)


class LockfileValidator:
    """
    Class to validate lockfiles against their source dependency files.
    
    This class provides methods to check if lockfiles are up-to-date with
    their source dependency files.
    
    Attributes:
        project_dir: Path to the project directory
        verbose: Whether to enable verbose logging
    """
    
    def __init__(
        self,
        project_dir: str,
        verbose: bool = False
    ):
        """
        Initialize the LockfileValidator.
        
        Args:
            project_dir: Path to the project directory
            verbose: Whether to enable verbose logging
        """
        self.project_dir = os.path.abspath(project_dir)
        self.verbose = verbose
        
        # Initialize report data structure
        self.report = {
            "project_dir": self.project_dir,
            "python_lockfile": {
                "status": "not_checked",
                "issues": []
            },
            "docker_lockfile": {
                "status": "not_checked",
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
    
    def _parse_requirements_txt(self, file_path: str) -> Dict[str, str]:
        """
        Parse a requirements.txt file.
        
        Args:
            file_path: Path to the requirements.txt file
            
        Returns:
            Dictionary mapping package names to version specifications
        """
        dependencies = {}
        
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
                        dependencies[name] = version_spec
        
        except Exception as e:
            logger.error(f"Error parsing requirements.txt file {file_path}: {e}")
        
        return dependencies
    
    def _parse_docker_compose_yml(self, file_path: str) -> Dict[str, str]:
        """
        Parse a docker-compose.yml file to extract image versions.
        
        Args:
            file_path: Path to the docker-compose.yml file
            
        Returns:
            Dictionary mapping service names to image versions
        """
        images = {}
        
        try:
            with open(os.path.join(self.project_dir, file_path), 'r') as f:
                compose_data = yaml.safe_load(f)
            
            if compose_data and "services" in compose_data:
                for service_name, service_data in compose_data["services"].items():
                    if "image" in service_data:
                        image = service_data["image"]
                        images[service_name] = image
        
        except Exception as e:
            logger.error(f"Error parsing docker-compose.yml file {file_path}: {e}")
        
        return images
    
    def validate_python_lockfile(self) -> bool:
        """
        Validate that requirements.lock is up-to-date with requirements.txt.
        
        Returns:
            True if the lockfile is valid, False otherwise
        """
        self.log("Validating Python lockfile...")
        
        requirements_txt_path = "requirements.txt"
        requirements_lock_path = "requirements.lock"
        
        # Check if the files exist
        if not os.path.exists(os.path.join(self.project_dir, requirements_txt_path)):
            self.log(f"requirements.txt not found at {requirements_txt_path}")
            self.report["python_lockfile"]["status"] = "error"
            self.report["python_lockfile"]["issues"].append("requirements.txt not found")
            return False
        
        if not os.path.exists(os.path.join(self.project_dir, requirements_lock_path)):
            self.log(f"requirements.lock not found at {requirements_lock_path}")
            self.report["python_lockfile"]["status"] = "error"
            self.report["python_lockfile"]["issues"].append("requirements.lock not found")
            return False
        
        # Parse the files
        requirements_txt = self._parse_requirements_txt(requirements_txt_path)
        requirements_lock = self._parse_requirements_txt(requirements_lock_path)
        
        # Check if all packages in requirements.txt are in requirements.lock
        missing_packages = []
        for package in requirements_txt:
            if package not in requirements_lock:
                missing_packages.append(package)
        
        if missing_packages:
            self.log(f"Missing packages in requirements.lock: {', '.join(missing_packages)}")
            self.report["python_lockfile"]["status"] = "invalid"
            self.report["python_lockfile"]["issues"].append(f"Missing packages: {', '.join(missing_packages)}")
            return False
        
        # Check if the versions match
        version_mismatches = []
        for package, version in requirements_txt.items():
            if package in requirements_lock and requirements_lock[package] != version:
                version_mismatches.append(f"{package}: {version} vs {requirements_lock[package]}")
        
        if version_mismatches:
            self.log(f"Version mismatches between requirements.txt and requirements.lock: {', '.join(version_mismatches)}")
            self.report["python_lockfile"]["status"] = "invalid"
            self.report["python_lockfile"]["issues"].append(f"Version mismatches: {', '.join(version_mismatches)}")
            return False
        
        self.log("Python lockfile is valid")
        self.report["python_lockfile"]["status"] = "valid"
        return True
    
    def validate_docker_lockfile(self) -> bool:
        """
        Validate that docker-compose.lock.yml is up-to-date with docker-compose.yml files.
        
        Returns:
            True if the lockfile is valid, False otherwise
        """
        self.log("Validating Docker lockfile...")
        
        docker_compose_lock_path = "docker-compose.lock.yml"
        
        # Check if the lockfile exists
        if not os.path.exists(os.path.join(self.project_dir, docker_compose_lock_path)):
            self.log(f"docker-compose.lock.yml not found at {docker_compose_lock_path}")
            self.report["docker_lockfile"]["status"] = "error"
            self.report["docker_lockfile"]["issues"].append("docker-compose.lock.yml not found")
            return False
        
        # Find all docker-compose.yml files
        docker_compose_files = []
        for root, _, files in os.walk(self.project_dir):
            for file in files:
                if file in ["docker-compose.yml", "docker-compose.yaml"]:
                    rel_path = os.path.relpath(os.path.join(root, file), self.project_dir)
                    docker_compose_files.append(rel_path)
        
        if not docker_compose_files:
            self.log("No docker-compose.yml files found")
            self.report["docker_lockfile"]["status"] = "error"
            self.report["docker_lockfile"]["issues"].append("No docker-compose.yml files found")
            return False
        
        # Parse the lockfile
        try:
            with open(os.path.join(self.project_dir, docker_compose_lock_path), 'r') as f:
                lock_data = yaml.safe_load(f)
            
            if not lock_data or "services" not in lock_data:
                self.log("Invalid docker-compose.lock.yml format")
                self.report["docker_lockfile"]["status"] = "error"
                self.report["docker_lockfile"]["issues"].append("Invalid docker-compose.lock.yml format")
                return False
            
            locked_images = {}
            for service_name, service_data in lock_data["services"].items():
                if "image" in service_data:
                    locked_images[service_name] = service_data["image"]
        
        except Exception as e:
            logger.error(f"Error parsing docker-compose.lock.yml: {e}")
            self.report["docker_lockfile"]["status"] = "error"
            self.report["docker_lockfile"]["issues"].append(f"Error parsing docker-compose.lock.yml: {e}")
            return False
        
        # Check each docker-compose.yml file
        all_images = {}
        for file_path in docker_compose_files:
            images = self._parse_docker_compose_yml(file_path)
            for service_name, image in images.items():
                all_images[service_name] = image
        
        # Check if all services in docker-compose.yml files are in the lockfile
        missing_services = []
        for service_name in all_images:
            if service_name not in locked_images:
                missing_services.append(service_name)
        
        if missing_services:
            self.log(f"Missing services in docker-compose.lock.yml: {', '.join(missing_services)}")
            self.report["docker_lockfile"]["status"] = "invalid"
            self.report["docker_lockfile"]["issues"].append(f"Missing services: {', '.join(missing_services)}")
            return False
        
        # Check if the image versions match
        version_mismatches = []
        for service_name, image in all_images.items():
            if service_name in locked_images and locked_images[service_name] != image:
                version_mismatches.append(f"{service_name}: {image} vs {locked_images[service_name]}")
        
        if version_mismatches:
            self.log(f"Image version mismatches: {', '.join(version_mismatches)}")
            self.report["docker_lockfile"]["status"] = "invalid"
            self.report["docker_lockfile"]["issues"].append(f"Image version mismatches: {', '.join(version_mismatches)}")
            return False
        
        self.log("Docker lockfile is valid")
        self.report["docker_lockfile"]["status"] = "valid"
        return True
    
    def validate_lockfiles(self) -> bool:
        """
        Validate all lockfiles.
        
        Returns:
            True if all lockfiles are valid, False otherwise
        """
        self.log("Validating lockfiles...")
        
        python_valid = self.validate_python_lockfile()
        docker_valid = self.validate_docker_lockfile()
        
        return python_valid and docker_valid
    
    def print_report(self) -> None:
        """
        Print a summary of the validation results.
        """
        print("\nLockfile Validation Report:")
        
        # Python lockfile
        python_status = self.report["python_lockfile"]["status"]
        print(f"  Python lockfile: {python_status}")
        if python_status != "valid":
            for issue in self.report["python_lockfile"]["issues"]:
                print(f"    - {issue}")
        
        # Docker lockfile
        docker_status = self.report["docker_lockfile"]["status"]
        print(f"  Docker lockfile: {docker_status}")
        if docker_status != "valid":
            for issue in self.report["docker_lockfile"]["issues"]:
                print(f"    - {issue}")
        
        # Overall status
        if python_status == "valid" and docker_status == "valid":
            print("\nAll lockfiles are valid and up-to-date.")
        else:
            print("\nSome lockfiles are invalid or out-of-date. Please update them.")


def main():
    """Main entry point for the script."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Validate lockfiles.")
    parser.add_argument("--project-dir", default=".", help="Path to the project directory")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Create lockfile validator
    validator = LockfileValidator(
        project_dir=args.project_dir,
        verbose=args.verbose
    )
    
    # Validate lockfiles
    valid = validator.validate_lockfiles()
    
    # Print report
    validator.print_report()
    
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())