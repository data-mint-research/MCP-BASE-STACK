#!/usr/bin/env python3
"""
Essential Files Update Script

This script updates or creates essential files according to the specification manifest:
1. README.md
2. .gitignore
3. requirements.txt
4. Knowledge Graph

The script provides functionality to:
1. Load the specification manifest to get templates for essential files
2. Check if essential files exist and are up-to-date
3. Create or update these files as needed
4. Update the knowledge graph with changes made

Features:
- Creates backups before modifying existing files
- Provides a detailed report of changes made
- Has a dry-run mode for previewing changes
- Integrates with the QualityEnforcer class

Usage:
    python update_essential_files.py --project-dir /path/to/project --manifest /path/to/manifest.json
    python update_essential_files.py --project-dir /path/to/project --dry-run
    python update_essential_files.py --project-dir /path/to/project --verbose
    python update_essential_files.py --project-dir /path/to/project --backup-dir /path/to/backup
"""

import argparse
import datetime
import importlib.util
import json
import logging
import os
import re
import shutil
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
        logging.FileHandler('data/logs/update_essential_files.log')
    ]
)
logger = logging.getLogger(__name__)


class EssentialFilesUpdater:
    """
    Class to update or create essential files according to the specification manifest.
    
    This class provides methods to check if essential files exist and are up-to-date,
    create or update these files as needed, and update the knowledge graph with changes made.
    
    Attributes:
        project_dir: Path to the project directory
        manifest: The specification manifest
        verbose: Whether to enable verbose logging
        dry_run: Whether to run in dry-run mode (only report issues without making changes)
        backup_dir: Directory to store backups of files before modification
    """
    
    def __init__(
        self,
        project_dir: str,
        manifest: Dict[str, Any],
        verbose: bool = False,
        dry_run: bool = False,
        backup_dir: str = None
    ):
        """
        Initialize the EssentialFilesUpdater.
        
        Args:
            project_dir: Path to the project directory
            manifest: The specification manifest
            verbose: Whether to enable verbose logging
            dry_run: Whether to run in dry-run mode (only report issues without making changes)
            backup_dir: Directory to store backups of files before modification
        """
        self.project_dir = os.path.abspath(project_dir)
        self.manifest = manifest
        self.verbose = verbose
        self.dry_run = dry_run
        
        # Set up backup directory
        if backup_dir:
            self.backup_dir = os.path.abspath(backup_dir)
        else:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.backup_dir = os.path.join(self.project_dir, "data", "backup", f"essential_files_{timestamp}")
        
        # Create backup directory if it doesn't exist and not in dry-run mode
        if not os.path.exists(self.backup_dir) and not self.dry_run:
            os.makedirs(self.backup_dir, exist_ok=True)
            self.log(f"Created backup directory: {self.backup_dir}")
        
        # Extract relevant sections from the manifest
        self.file_templates = manifest["specification_manifest"]["file_templates"]
        
        # Initialize report data structure
        self.report = {
            "project_dir": self.project_dir,
            "timestamp": datetime.datetime.now().isoformat(),
            "summary": {
                "files_checked": 0,
                "files_up_to_date": 0,
                "files_updated": 0,
                "files_created": 0,
                "files_backed_up": 0,
                "errors": 0
            },
            "files": [],
            "actions_taken": [],
            "rollback_info": {
                "backup_dir": self.backup_dir,
                "files_backed_up": []
            }
        }
        
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
    
    def _backup_file(self, file_path: str) -> bool:
        """
        Create a backup of a file before modification.
        
        Args:
            file_path: Path to the file to backup
            
        Returns:
            True if the backup was successful, False otherwise
        """
        if self.dry_run:
            self.log(f"[DRY RUN] Would backup file: {file_path}")
            return True
        
        abs_path = os.path.join(self.project_dir, file_path)
        backup_path = os.path.join(self.backup_dir, file_path)
        
        try:
            # Create directory structure in backup directory
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Copy the file
            shutil.copy2(abs_path, backup_path)
            
            # Add to report
            self.report["rollback_info"]["files_backed_up"].append({
                "original_path": file_path,
                "backup_path": os.path.relpath(backup_path, self.project_dir)
            })
            
            self.report["summary"]["files_backed_up"] += 1
            self.log(f"Backed up file: {file_path} to {backup_path}")
            return True
        
        except (IOError, OSError) as e:
            logger.error(f"Error backing up file {file_path}: {e}")
            self.report["summary"]["errors"] += 1
            return False
    
    def _write_file(self, file_path: str, content: str) -> bool:
        """
        Write content to a file.
        
        Args:
            file_path: Path to the file to write
            content: Content to write to the file
            
        Returns:
            True if the write was successful, False otherwise
        """
        if self.dry_run:
            self.log(f"[DRY RUN] Would write to file: {file_path}")
            return True
        
        abs_path = os.path.join(self.project_dir, file_path)
        
        try:
            # Create directory structure if needed
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            
            # Write the file
            with open(abs_path, 'w') as f:
                f.write(content)
            
            # Add to report
            self.report["actions_taken"].append({
                "action": "write",
                "path": file_path,
                "timestamp": datetime.datetime.now().isoformat()
            })
            
            self.log(f"Wrote to file: {file_path}")
            return True
        
        except (IOError, OSError) as e:
            logger.error(f"Error writing to file {file_path}: {e}")
            self.report["summary"]["errors"] += 1
            return False
    
    def _file_needs_update(self, file_path: str, template_content: str) -> bool:
        """
        Check if a file needs to be updated.
        
        Args:
            file_path: Path to the file to check
            template_content: Template content to compare against
            
        Returns:
            True if the file needs to be updated, False otherwise
        """
        abs_path = os.path.join(self.project_dir, file_path)
        
        if not os.path.exists(abs_path):
            return True
        
        try:
            with open(abs_path, 'r') as f:
                current_content = f.read()
            
            return current_content != template_content
        
        except (IOError, OSError) as e:
            logger.error(f"Error reading file {file_path}: {e}")
            self.report["summary"]["errors"] += 1
            return True
    
    def _update_readme(self) -> bool:
        """
        Update the README.md file based on the template in the manifest.
        
        Returns:
            True if the update was successful, False otherwise
        """
        self.log("Updating README.md...")
        
        file_path = "README.md"
        template = self.file_templates["root"]["required_files"]["README.md"]["template"]
        
        # Check if the file needs to be updated
        if self._file_needs_update(file_path, template):
            # Backup the file if it exists
            if os.path.exists(os.path.join(self.project_dir, file_path)):
                if not self._backup_file(file_path):
                    return False
                
                # Write the file
                if self._write_file(file_path, template):
                    self.report["summary"]["files_updated"] += 1
                    self.report["files"].append({
                        "path": file_path,
                        "status": "updated",
                        "reason": "Content did not match template"
                    })
                    return True
                else:
                    return False
            else:
                # Create the file
                if self._write_file(file_path, template):
                    self.report["summary"]["files_created"] += 1
                    self.report["files"].append({
                        "path": file_path,
                        "status": "created",
                        "reason": "File did not exist"
                    })
                    return True
                else:
                    return False
        else:
            self.report["summary"]["files_up_to_date"] += 1
            self.report["files"].append({
                "path": file_path,
                "status": "up_to_date",
                "reason": "Content matches template"
            })
            return True
    
    def _update_gitignore(self) -> bool:
        """
        Update the .gitignore file based on the template in the manifest.
        
        Returns:
            True if the update was successful, False otherwise
        """
        self.log("Updating .gitignore...")
        
        file_path = ".gitignore"
        template = self.file_templates["root"]["required_files"][".gitignore"]["template"]
        
        # Check if the file needs to be updated
        if self._file_needs_update(file_path, template):
            # Backup the file if it exists
            if os.path.exists(os.path.join(self.project_dir, file_path)):
                if not self._backup_file(file_path):
                    return False
                
                # Write the file
                if self._write_file(file_path, template):
                    self.report["summary"]["files_updated"] += 1
                    self.report["files"].append({
                        "path": file_path,
                        "status": "updated",
                        "reason": "Content did not match template"
                    })
                    return True
                else:
                    return False
            else:
                # Create the file
                if self._write_file(file_path, template):
                    self.report["summary"]["files_created"] += 1
                    self.report["files"].append({
                        "path": file_path,
                        "status": "created",
                        "reason": "File did not exist"
                    })
                    return True
                else:
                    return False
        else:
            self.report["summary"]["files_up_to_date"] += 1
            self.report["files"].append({
                "path": file_path,
                "status": "up_to_date",
                "reason": "Content matches template"
            })
            return True
    
    def _generate_requirements_txt(self) -> str:
        """
        Generate the requirements.txt file by analyzing project dependencies.
        
        Returns:
            The content of the requirements.txt file
        """
        self.log("Generating requirements.txt content...")
        
        # Start with a basic set of dependencies
        dependencies = [
            "networkx>=2.5",
            "rdflib>=6.0.0",
            "pyyaml>=6.0",
            "fastapi>=0.68.0",
            "uvicorn>=0.15.0",
            "pydantic>=1.8.2",
            "pytest>=6.2.5",
            "black>=21.9b0",
            "isort>=5.9.3",
            "flake8>=3.9.2",
            "mypy>=0.910",
            "pylint>=2.11.1",
            "pre-commit>=2.15.0"
        ]
        
        # Analyze Python files to find import statements
        import_pattern = re.compile(r'^import\s+([a-zA-Z0-9_.]+)|^from\s+([a-zA-Z0-9_.]+)\s+import', re.MULTILINE)
        
        # Comprehensive list of standard library modules
        standard_libs = set([
            # Basic Python modules
            "abc", "aifc", "argparse", "array", "ast", "asyncio", "atexit", "audioop",
            "base64", "bdb", "binascii", "binhex", "bisect", "builtins", "bz2",
            "calendar", "cgi", "cgitb", "chunk", "cmath", "cmd", "code", "codecs",
            "codeop", "collections", "colorsys", "compileall", "concurrent", "configparser",
            "contextlib", "contextvars", "copy", "copyreg", "cProfile", "crypt", "csv",
            "ctypes", "curses", "dataclasses", "datetime", "dbm", "decimal", "difflib",
            "dis", "distutils", "doctest", "dummy_threading", "email", "encodings",
            "ensurepip", "enum", "errno", "faulthandler", "fcntl", "filecmp", "fileinput",
            "fnmatch", "formatter", "fractions", "ftplib", "functools", "gc", "getopt",
            "getpass", "gettext", "glob", "grp", "gzip", "hashlib", "heapq", "hmac",
            "html", "http", "idlelib", "imaplib", "imghdr", "imp", "importlib",
            "inspect", "io", "ipaddress", "itertools", "json", "keyword", "lib2to3",
            "linecache", "locale", "logging", "lzma", "macpath", "mailbox", "mailcap",
            "marshal", "math", "mimetypes", "mmap", "modulefinder", "msilib", "msvcrt",
            "multiprocessing", "netrc", "nis", "nntplib", "numbers", "operator", "optparse",
            "os", "ossaudiodev", "parser", "pathlib", "pdb", "pickle", "pickletools",
            "pipes", "pkgutil", "platform", "plistlib", "poplib", "posix", "pprint",
            "profile", "pstats", "pty", "pwd", "py_compile", "pyclbr", "pydoc", "queue",
            "quopri", "random", "re", "readline", "reprlib", "resource", "rlcompleter",
            "runpy", "sched", "secrets", "select", "selectors", "shelve", "shlex",
            "shutil", "signal", "site", "smtpd", "smtplib", "sndhdr", "socket",
            "socketserver", "spwd", "sqlite3", "ssl", "stat", "statistics", "string",
            "stringprep", "struct", "subprocess", "sunau", "symbol", "symtable", "sys",
            "sysconfig", "syslog", "tabnanny", "tarfile", "telnetlib", "tempfile",
            "termios", "test", "textwrap", "threading", "time", "timeit", "tkinter",
            "token", "tokenize", "trace", "traceback", "tracemalloc", "tty", "turtle",
            "turtledemo", "types", "typing", "unicodedata", "unittest", "urllib",
            "uu", "uuid", "venv", "warnings", "wave", "weakref", "webbrowser",
            "winreg", "winsound", "wsgiref", "xdrlib", "xml", "xmlrpc", "zipapp",
            "zipfile", "zipimport", "zlib",
            
            # Local project modules (to avoid adding them as dependencies)
            "core", "scripts", "tests", "services", "example", "di", "yaml"
        ])
        
        # Known package name mappings (module name -> package name)
        package_mappings = {
            "yaml": "pyyaml",
        }
        
        # Default versions for common packages
        default_versions = {
            "numpy": ">=1.20.0",
            "pandas": ">=1.3.0",
            "matplotlib": ">=3.4.0",
            "requests": ">=2.25.0",
            "hypothesis": ">=6.0.0",
            "dependency_injector": ">=4.40.0"
        }
        
        # Walk through Python files
        for root, _, files in os.walk(self.project_dir):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # Find import statements
                        matches = import_pattern.findall(content)
                        for match in matches:
                            module = match[0] or match[1]
                            # Get the top-level package
                            top_package = module.split('.')[0]
                            
                            # Skip standard library modules
                            if top_package in standard_libs:
                                continue
                            
                            # Skip relative imports
                            if not top_package:
                                continue
                            
                            # Apply package name mapping if available
                            if top_package in package_mappings:
                                top_package = package_mappings[top_package]
                            
                            # Add to dependencies if not already present
                            if not any(dep.startswith(f"{top_package}>=") or dep == top_package for dep in dependencies):
                                # Use default version if available
                                if top_package in default_versions:
                                    dependencies.append(f"{top_package}{default_versions[top_package]}")
                                else:
                                    dependencies.append(f"{top_package}>=0.0.0")
                    
                    except (IOError, OSError) as e:
                        logger.error(f"Error reading file {file_path}: {e}")
        
        # Sort dependencies
        dependencies.sort()
        
        # Generate requirements.txt content
        content = "# Generated by update_essential_files.py\n"
        content += "# Date: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n"
        content += "\n".join(dependencies)
        content += "\n"
        
        return content
    
    def _update_requirements_txt(self) -> bool:
        """
        Update the requirements.txt file by analyzing project dependencies.
        
        Returns:
            True if the update was successful, False otherwise
        """
        self.log("Updating requirements.txt...")
        
        file_path = "requirements.txt"
        content = self._generate_requirements_txt()
        
        # Check if the file needs to be updated
        if self._file_needs_update(file_path, content):
            # Backup the file if it exists
            if os.path.exists(os.path.join(self.project_dir, file_path)):
                if not self._backup_file(file_path):
                    return False
                
                # Write the file
                if self._write_file(file_path, content):
                    self.report["summary"]["files_updated"] += 1
                    self.report["files"].append({
                        "path": file_path,
                        "status": "updated",
                        "reason": "Content did not match generated dependencies"
                    })
                    return True
                else:
                    return False
            else:
                # Create the file
                if self._write_file(file_path, content):
                    self.report["summary"]["files_created"] += 1
                    self.report["files"].append({
                        "path": file_path,
                        "status": "created",
                        "reason": "File did not exist"
                    })
                    return True
                else:
                    return False
        else:
            self.report["summary"]["files_up_to_date"] += 1
            self.report["files"].append({
                "path": file_path,
                "status": "up_to_date",
                "reason": "Content matches generated dependencies"
            })
            return True
    
    def _update_knowledge_graph(self) -> bool:
        """
        Update the knowledge graph with file metadata.
        
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
                
                # Create QualityCheckResult objects for the changes
                results = []
                
                # Add results for updated files
                for file_info in self.report["files"]:
                    if file_info["status"] in ["updated", "created"]:
                        result = QualityCheckResult(
                            check_id="essential_files",
                            severity=QualityCheckSeverity.INFO,
                            message=f"File {file_info['status']}: {file_info['path']}",
                            file_path=file_info["path"],
                            source="EssentialFilesUpdater"
                        )
                        results.append(result)
                
                # Update the knowledge graph
                if results:
                    self.quality_enforcer.update_knowledge_graph(results)
                    self.log(f"Updated knowledge graph with {len(results)} changes")
                
                return True
            else:
                # Try to run the update_knowledge_graph.py script
                update_script = os.path.join(self.project_dir, "core/kg/scripts/update_knowledge_graph.py")
                if os.path.exists(update_script):
                    self.log("Updating knowledge graph via update_knowledge_graph.py...")
                    import subprocess
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
    
    def _rollback(self) -> bool:
        """
        Rollback changes by restoring files from backups.
        
        Returns:
            True if the rollback was successful, False otherwise
        """
        self.log("Rolling back changes...")
        
        success = True
        
        for backup_info in self.report["rollback_info"]["files_backed_up"]:
            original_path = backup_info["original_path"]
            backup_path = backup_info["backup_path"]
            
            abs_original_path = os.path.join(self.project_dir, original_path)
            abs_backup_path = os.path.join(self.project_dir, backup_path)
            
            try:
                # Create directory structure if needed
                os.makedirs(os.path.dirname(abs_original_path), exist_ok=True)
                
                # Copy the file back
                shutil.copy2(abs_backup_path, abs_original_path)
                
                self.log(f"Restored file: {original_path} from {backup_path}")
            
            except (IOError, OSError) as e:
                logger.error(f"Error restoring file {original_path}: {e}")
                success = False
        
        return success
    
    def update_essential_files(self) -> bool:
        """
        Update essential files according to the specification manifest.
        
        Returns:
            True if the update was successful, False otherwise
        """
        self.log("Starting essential files update...")
        
        success = True
        
        # Update README.md
        self.report["summary"]["files_checked"] += 1
        if not self._update_readme():
            success = False
        
        # Update .gitignore
        self.report["summary"]["files_checked"] += 1
        if not self._update_gitignore():
            success = False
        
        # Update requirements.txt
        self.report["summary"]["files_checked"] += 1
        if not self._update_requirements_txt():
            success = False
        
        # Update knowledge graph
        if success and not self.dry_run:
            if not self._update_knowledge_graph():
                logger.warning("Failed to update knowledge graph, but file updates were successful")
        
        return success
    
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


def load_manifest(manifest_path: str) -> Dict[str, Any]:
    """
    Load the specification manifest from a file.
    
    Args:
        manifest_path: Path to the manifest file
        
    Returns:
        The loaded manifest data
    """
    try:
        with open(manifest_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading manifest from {manifest_path}: {e}")
        sys.exit(1)


def main():
    """Main entry point for the script."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Update essential files according to the specification manifest.")
    parser.add_argument("--project-dir", default=".", help="Path to the project directory")
    parser.add_argument("--manifest", default="config/specifications/specification-manifest.json", help="Path to the specification manifest")
    parser.add_argument("--output", default="data/reports/essential-files-report.json", help="Path to the output report file")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode (don't actually modify files)")
    parser.add_argument("--backup-dir", help="Directory to store backups of files before modification")
    
    args = parser.parse_args()
    
    # Load manifest
    manifest = load_manifest(args.manifest)
    
    # Create essential files updater
    updater = EssentialFilesUpdater(
        project_dir=args.project_dir,
        manifest=manifest,
        verbose=args.verbose,
        dry_run=args.dry_run,
        backup_dir=args.backup_dir
    )
    
    # Update essential files
    success = updater.update_essential_files()
    
    # Save report
    updater.save_report(args.output)
    
    # Print summary
    print("\nSummary:")
    print(f"  Files checked: {updater.report['summary']['files_checked']}")
    print(f"  Files up-to-date: {updater.report['summary']['files_up_to_date']}")
    print(f"  Files updated: {updater.report['summary']['files_updated']}")
    print(f"  Files created: {updater.report['summary']['files_created']}")
    print(f"  Files backed up: {updater.report['summary']['files_backed_up']}")
    print(f"  Errors: {updater.report['summary']['errors']}")
    
    if args.dry_run:
        print("\nDry run mode: No files were modified.")
        print(f"Check the report at {args.output} for details.")
    else:
        if success:
            print("\nEssential files update completed successfully.")
        else:
            print("\nEssential files update completed with errors. Check the log for details.")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())