#!/usr/bin/env python3
"""
File cleanup script that identifies and safely removes orphaned or outdated files.

This script provides functionality to:
1. Load the specification manifest
2. Use results from traverse_project.py and analyze_code.py to identify files that need cleanup
3. Identify orphaned files (files not referenced by any other file or not in the knowledge graph)
4. Identify outdated files (old migration files, duplicate files, outdated versions)
5. Generate a detailed report of files to be cleaned up
6. Safely remove or archive these files based on user confirmation

The script implements safety measures:
- Never delete files without explicit confirmation
- Create backups of files before deletion
- Log all actions taken
- Provide a rollback mechanism

Usage:
    python cleanup_files.py --project-dir /path/to/project --manifest /path/to/manifest.json --output /path/to/report.json
    python cleanup_files.py --project-dir /path/to/project --verbose
    python cleanup_files.py --project-dir /path/to/project --dry-run
    python cleanup_files.py --project-dir /path/to/project --interactive
    python cleanup_files.py --project-dir /path/to/project --batch
"""

import argparse
import datetime
import json
import logging
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set, Union

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('cleanup_files.log')
    ]
)
logger = logging.getLogger(__name__)


class FileCleanup:
    """
    Class to identify and safely remove orphaned or outdated files.
    
    This class provides methods to identify files that need cleanup,
    generate a detailed report, and safely remove or archive these files
    based on user confirmation.
    
    Attributes:
        project_dir: Path to the project directory
        manifest: The specification manifest
        verbose: Whether to enable verbose logging
        dry_run: Whether to run in dry-run mode (only report issues without making changes)
        interactive: Whether to run in interactive mode (confirm each deletion)
        batch: Whether to run in batch mode (apply all changes at once with a single confirmation)
        backup_dir: Directory to store backups of files before deletion
    """
    
    def __init__(
        self, 
        project_dir: str, 
        manifest: Dict[str, Any], 
        verbose: bool = False, 
        dry_run: bool = False,
        interactive: bool = False,
        batch: bool = False,
        backup_dir: str = None
    ):
        """
        Initialize the FileCleanup.
        
        Args:
            project_dir: Path to the project directory
            manifest: The specification manifest
            verbose: Whether to enable verbose logging
            dry_run: Whether to run in dry-run mode (only report issues without making changes)
            interactive: Whether to run in interactive mode (confirm each deletion)
            batch: Whether to run in batch mode (apply all changes at once with a single confirmation)
            backup_dir: Directory to store backups of files before deletion
        """
        self.project_dir = os.path.abspath(project_dir)
        self.manifest = manifest
        self.verbose = verbose
        self.dry_run = dry_run
        self.interactive = interactive
        self.batch = batch
        
        # Set up backup directory
        if backup_dir:
            self.backup_dir = os.path.abspath(backup_dir)
        else:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.backup_dir = os.path.join(self.project_dir, f"backup_{timestamp}")
        
        # Create backup directory if it doesn't exist
        if not os.path.exists(self.backup_dir) and not self.dry_run:
            os.makedirs(self.backup_dir)
            self.log(f"Created backup directory: {self.backup_dir}")
        
        # Extract relevant sections from the manifest
        self.dir_structure = manifest["specification_manifest"]["directory_structure"]
        self.file_templates = manifest["specification_manifest"]["file_templates"]
        
        # Initialize report data structure
        self.report = {
            "project_dir": self.project_dir,
            "timestamp": datetime.datetime.now().isoformat(),
            "summary": {
                "total_files_scanned": 0,
                "orphaned_files": 0,
                "outdated_files": 0,
                "duplicate_files": 0,
                "total_files_to_cleanup": 0,
                "total_size_to_cleanup": 0,
                "files_backed_up": 0,
                "files_removed": 0,
                "files_archived": 0
            },
            "orphaned_files": [],
            "outdated_files": [],
            "duplicate_files": [],
            "actions_taken": [],
            "rollback_info": {
                "backup_dir": self.backup_dir,
                "files_backed_up": []
            }
        }
        
        # Initialize file tracking
        self.all_files = set()
        self.referenced_files = set()
        self.knowledge_graph_files = set()
        self.expected_files = set()
        self.file_hashes = {}  # For duplicate detection
        
        # Load project structure and code analysis reports if available
        self.project_structure_report = self._load_report("project-structure-report.json")
        self.code_analysis_report = self._load_report("code-analysis-report.json")
    
    def log(self, message: str) -> None:
        """
        Log a message if verbose mode is enabled.
        
        Args:
            message: The message to log
        """
        if self.verbose:
            logger.info(message)
    
    def _load_report(self, report_path: str) -> Optional[Dict[str, Any]]:
        """
        Load a report file if it exists.
        
        Args:
            report_path: Path to the report file
            
        Returns:
            The loaded report data, or None if the file doesn't exist
        """
        try:
            with open(os.path.join(self.project_dir, report_path), 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.log(f"Warning: Could not load {report_path}: {e}")
            return None
    
    def _scan_files(self) -> None:
        """
        Scan all files in the project directory.
        
        This method walks through the project directory, collecting information
        about all files and calculating their hashes for duplicate detection.
        """
        self.log(f"Scanning files in directory: {self.project_dir}")
        
        # Define patterns for files to ignore
        ignore_patterns = [
            r'\.git/',
            r'\.vscode/',
            r'__pycache__/',
            r'\.pyc$',
            r'\.pyo$',
            r'\.pyd$',
            r'\.so$',
            r'\.dll$',
            r'\.exe$',
            r'\.bin$',
            r'\.obj$',
            r'\.o$',
            r'\.a$',
            r'\.lib$',
            r'\.out$',
            r'\.log$',
            r'\.swp$',
            r'\.swo$',
            r'\.DS_Store$',
            r'Thumbs\.db$',
            r'\.bak$',
            r'\.tmp$',
            r'\.temp$',
            r'\.backup$',
            r'backup_\d{8}_\d{6}/'  # Ignore backup directories created by this script
        ]
        
        # Compile the patterns
        ignore_regexes = [re.compile(pattern) for pattern in ignore_patterns]
        
        # Walk through the project directory
        for root, dirs, files in os.walk(self.project_dir):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if not any(regex.search(os.path.join(root, d, '')) for regex in ignore_regexes)]
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.project_dir)
                
                # Skip ignored files
                if any(regex.search(rel_path) for regex in ignore_regexes):
                    continue
                
                self.all_files.add(rel_path)
                
                # Calculate file hash for duplicate detection
                try:
                    file_size = os.path.getsize(file_path)
                    
                    # Only calculate hash for files under a certain size to avoid performance issues
                    if file_size < 10 * 1024 * 1024:  # 10 MB
                        import hashlib
                        with open(file_path, 'rb') as f:
                            file_hash = hashlib.md5(f.read()).hexdigest()
                        
                        if file_hash in self.file_hashes:
                            self.file_hashes[file_hash].append(rel_path)
                        else:
                            self.file_hashes[file_hash] = [rel_path]
                except (IOError, OSError) as e:
                    logger.error(f"Error calculating hash for {rel_path}: {e}")
        
        self.report["summary"]["total_files_scanned"] = len(self.all_files)
        self.log(f"Scanned {len(self.all_files)} files")
    
    def _load_knowledge_graph(self) -> None:
        """
        Load the knowledge graph to identify files that are referenced.
        
        This method attempts to load the knowledge graph files and extract
        file references from them.
        """
        self.log("Loading knowledge graph...")
        
        # Try to load the knowledge graph files
        kg_paths = [
            os.path.join(self.project_dir, "core/kg/data/knowledge_graph.graphml"),
            os.path.join(self.project_dir, "core/kg/data/knowledge_graph.ttl")
        ]
        
        for kg_path in kg_paths:
            if os.path.isfile(kg_path):
                self.log(f"Found knowledge graph file: {kg_path}")
                
                try:
                    with open(kg_path, 'r') as f:
                        content = f.read()
                    
                    # Extract file paths from the knowledge graph
                    # This is a simple approach that looks for file paths in the content
                    # A more sophisticated approach would parse the knowledge graph format
                    file_paths = re.findall(r'(?:file|path)="([^"]+)"', content)
                    file_paths.extend(re.findall(r'(?:file|path)>([^<]+)<', content))
                    
                    for path in file_paths:
                        # Normalize the path
                        norm_path = os.path.normpath(path)
                        if os.path.isabs(norm_path):
                            # Convert absolute path to relative
                            try:
                                rel_path = os.path.relpath(norm_path, self.project_dir)
                                self.knowledge_graph_files.add(rel_path)
                            except ValueError:
                                # Path is outside the project directory
                                pass
                        else:
                            # Already a relative path
                            self.knowledge_graph_files.add(norm_path)
                    
                    self.log(f"Extracted {len(self.knowledge_graph_files)} file references from knowledge graph")
                
                except Exception as e:
                    logger.error(f"Error loading knowledge graph file {kg_path}: {e}")
    
    def _collect_expected_files(self) -> None:
        """
        Collect the list of files that are expected to exist based on the manifest.
        
        This method extracts the list of required and optional files from the
        specification manifest.
        """
        self.log("Collecting expected files from manifest...")
        
        for dir_path, dir_info in self.file_templates.items():
            if dir_path == "root":
                base_path = ""
            else:
                base_path = dir_path
            
            # Add required files
            if "required_files" in dir_info:
                for file_name in dir_info["required_files"]:
                    file_path = os.path.join(base_path, file_name)
                    self.expected_files.add(file_path)
            
            # Add optional files
            if "optional_files" in dir_info:
                for file_name in dir_info["optional_files"]:
                    file_path = os.path.join(base_path, file_name)
                    self.expected_files.add(file_path)
        
        self.log(f"Collected {len(self.expected_files)} expected files from manifest")
    
    def _scan_file_references(self) -> None:
        """
        Scan files for references to other files.
        
        This method scans source code files for import statements, require statements,
        and other references to files.
        """
        self.log("Scanning files for references...")
        
        # Define patterns for file references in different file types
        reference_patterns = {
            r'\.py$': [
                r'(?:from|import)\s+([a-zA-Z0-9_.]+)',  # Python imports
                r'(?:open|with open)\s*\(\s*[\'"]([^\'"]+)[\'"]'  # File open operations
            ],
            r'\.js$|\.ts$|\.jsx$|\.tsx$': [
                r'(?:import|require)\s*\(\s*[\'"]([^\'"]+)[\'"]',  # JS/TS imports
                r'import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]',
                r'import\s+[\'"]([^\'"]+)[\'"]'
            ],
            r'\.sh$': [
                r'source\s+[\'"]?([^\s\'"]+)[\'"]?',  # Shell source
                r'\.\s+[\'"]?([^\s\'"]+)[\'"]?'  # Shell dot command
            ],
            r'\.md$|\.rst$': [
                r'\[.*\]\(([^)]+)\)',  # Markdown links
                r'include\s+[\'"]([^\'"]+)[\'"]'  # RST includes
            ],
            r'\.html$|\.xml$': [
                r'href=[\'"]([^\'"]+)[\'"]',  # HTML/XML links
                r'src=[\'"]([^\'"]+)[\'"]'  # HTML/XML sources
            ],
            r'\.json$|\.yaml$|\.yml$': [
                r'[\'"](?:file|path|source|destination)[\'"]:\s*[\'"]([^\'"]+)[\'"]'  # Config file references
            ]
        }
        
        # Scan each file for references
        for file_path in self.all_files:
            abs_path = os.path.join(self.project_dir, file_path)
            
            # Skip binary files and large files
            if not self._is_text_file(abs_path) or os.path.getsize(abs_path) > 10 * 1024 * 1024:
                continue
            
            try:
                with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Check for references based on file extension
                for pattern_key, patterns in reference_patterns.items():
                    if re.search(pattern_key, file_path):
                        for pattern in patterns:
                            matches = re.findall(pattern, content)
                            for match in matches:
                                # Convert module references to file paths
                                if re.search(r'\.py$', file_path) and '.' in match and '/' not in match and '\\' not in match:
                                    # Convert Python module to file path
                                    module_path = match.replace('.', '/') + '.py'
                                    self.referenced_files.add(module_path)
                                else:
                                    # Normalize the path
                                    norm_path = os.path.normpath(match)
                                    if not os.path.isabs(norm_path):
                                        # Resolve relative path
                                        dir_path = os.path.dirname(file_path)
                                        resolved_path = os.path.normpath(os.path.join(dir_path, norm_path))
                                        self.referenced_files.add(resolved_path)
                                    else:
                                        # Convert absolute path to relative if it's within the project
                                        try:
                                            rel_path = os.path.relpath(norm_path, self.project_dir)
                                            self.referenced_files.add(rel_path)
                                        except ValueError:
                                            # Path is outside the project directory
                                            pass
            
            except (IOError, OSError) as e:
                logger.error(f"Error scanning file {file_path} for references: {e}")
        
        self.log(f"Found {len(self.referenced_files)} file references")
    
    def _is_text_file(self, file_path: str) -> bool:
        """
        Check if a file is a text file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file is a text file, False otherwise
        """
        # Check file extension first
        text_extensions = {
            '.txt', '.md', '.rst', '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.xml',
            '.css', '.scss', '.less', '.json', '.yaml', '.yml', '.sh', '.bash', '.c',
            '.cpp', '.h', '.hpp', '.java', '.go', '.rb', '.php', '.pl', '.pm', '.conf',
            '.cfg', '.ini', '.properties', '.toml', '.csv', '.tsv'
        }
        
        _, ext = os.path.splitext(file_path)
        if ext.lower() in text_extensions:
            return True
        
        # If extension check is inconclusive, try to read the file
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\0' not in chunk  # Binary files typically contain null bytes
        except (IOError, OSError):
            return False
    
    def _identify_orphaned_files(self) -> None:
        """
        Identify orphaned files.
        
        Orphaned files are files that are not referenced by any other file,
        not in the knowledge graph, and not expected based on the manifest.
        """
        self.log("Identifying orphaned files...")
        
        # Files that are not referenced, not in the knowledge graph, and not expected
        orphaned_files = self.all_files - self.referenced_files - self.knowledge_graph_files - self.expected_files
        
        # Add to report
        for file_path in sorted(orphaned_files):
            abs_path = os.path.join(self.project_dir, file_path)
            
            # Skip directories
            if os.path.isdir(abs_path):
                continue
            
            # Get file info
            try:
                file_size = os.path.getsize(abs_path)
                file_mtime = os.path.getmtime(abs_path)
                file_mtime_str = datetime.datetime.fromtimestamp(file_mtime).isoformat()
                
                self.report["orphaned_files"].append({
                    "path": file_path,
                    "size": file_size,
                    "last_modified": file_mtime_str,
                    "reason": "Not referenced by any other file, not in the knowledge graph, and not expected based on the manifest"
                })
                
                self.report["summary"]["orphaned_files"] += 1
                self.report["summary"]["total_files_to_cleanup"] += 1
                self.report["summary"]["total_size_to_cleanup"] += file_size
            
            except (IOError, OSError) as e:
                logger.error(f"Error getting info for orphaned file {file_path}: {e}")
        
        self.log(f"Identified {self.report['summary']['orphaned_files']} orphaned files")
    
    def _identify_outdated_files(self) -> None:
        """
        Identify outdated files.
        
        Outdated files include old migration files, backup files, and files
        with outdated naming conventions.
        """
        self.log("Identifying outdated files...")
        
        # Patterns for outdated files
        outdated_patterns = [
            (r'\.bak$', "Backup file"),
            (r'\.old$', "Old version"),
            (r'\.backup$', "Backup file"),
            (r'\.orig$', "Original version"),
            (r'\.tmp$', "Temporary file"),
            (r'\.temp$', "Temporary file"),
            (r'~$', "Temporary file"),
            (r'_old\.[^.]+$', "Old version"),
            (r'_backup\.[^.]+$', "Backup file"),
            (r'_bak\.[^.]+$', "Backup file"),
            (r'_\d{8}\.[^.]+$', "Dated backup"),
            (r'_\d{6}\.[^.]+$', "Dated backup"),
            (r'_v\d+\.[^.]+$', "Versioned file"),
            (r'\.swp$', "Vim swap file"),
            (r'\.swo$', "Vim swap file"),
            (r'\.swn$', "Vim swap file"),
            (r'\.DS_Store$', "macOS system file"),
            (r'Thumbs\.db$', "Windows system file"),
            (r'desktop\.ini$', "Windows system file"),
            (r'\.pyc$', "Python compiled file"),
            (r'\.pyo$', "Python optimized file"),
            (r'\.pyd$', "Python dynamic module"),
            (r'__pycache__/', "Python cache directory")
        ]
        
        # Check each file against the patterns
        for file_path in self.all_files:
            abs_path = os.path.join(self.project_dir, file_path)
            
            # Skip directories
            if os.path.isdir(abs_path):
                continue
            
            # Check against outdated patterns
            for pattern, reason in outdated_patterns:
                if re.search(pattern, file_path):
                    try:
                        file_size = os.path.getsize(abs_path)
                        file_mtime = os.path.getmtime(abs_path)
                        file_mtime_str = datetime.datetime.fromtimestamp(file_mtime).isoformat()
                        
                        self.report["outdated_files"].append({
                            "path": file_path,
                            "size": file_size,
                            "last_modified": file_mtime_str,
                            "reason": reason
                        })
                        
                        self.report["summary"]["outdated_files"] += 1
                        self.report["summary"]["total_files_to_cleanup"] += 1
                        self.report["summary"]["total_size_to_cleanup"] += file_size
                        break  # Stop after first match
                    
                    except (IOError, OSError) as e:
                        logger.error(f"Error getting info for outdated file {file_path}: {e}")
        
        self.log(f"Identified {self.report['summary']['outdated_files']} outdated files")
    
    def _identify_duplicate_files(self) -> None:
        """
        Identify duplicate files.
        
        Duplicate files are files with identical content but different paths.
        """
        self.log("Identifying duplicate files...")
        
        # Find files with the same hash
        for file_hash, file_paths in self.file_hashes.items():
            if len(file_paths) > 1:
                # Sort by modification time (oldest first)
                sorted_paths = sorted(
                    file_paths,
                    key=lambda p: os.path.getmtime(os.path.join(self.project_dir, p))
                )
                
                # Keep the newest file, mark others as duplicates
                newest_path = sorted_paths[-1]
                for path in sorted_paths[:-1]:
                    abs_path = os.path.join(self.project_dir, path)
                    
                    try:
                        file_size = os.path.getsize(abs_path)
                        file_mtime = os.path.getmtime(abs_path)
                        file_mtime_str = datetime.datetime.fromtimestamp(file_mtime).isoformat()
                        
                        self.report["duplicate_files"].append({
                            "path": path,
                            "size": file_size,
                            "last_modified": file_mtime_str,
                            "duplicate_of": newest_path,
                            "reason": f"Duplicate of {newest_path}"
                        })
                        
                        self.report["summary"]["duplicate_files"] += 1
                        self.report["summary"]["total_files_to_cleanup"] += 1
                        self.report["summary"]["total_size_to_cleanup"] += file_size
                    
                    except (IOError, OSError) as e:
                        logger.error(f"Error getting info for duplicate file {path}: {e}")
        
        self.log(f"Identified {self.report['summary']['duplicate_files']} duplicate files")
    
    def _backup_file(self, file_path: str) -> bool:
        """
        Create a backup of a file before deletion.
        
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
            return False
    
    def _remove_file(self, file_path: str) -> bool:
        """
        Remove a file.
        
        Args:
            file_path: Path to the file to remove
            
        Returns:
            True if the removal was successful, False otherwise
        """
        if self.dry_run:
            self.log(f"[DRY RUN] Would remove file: {file_path}")
            return True
        
        abs_path = os.path.join(self.project_dir, file_path)
        
        try:
            # Remove the file
            os.remove(abs_path)
            
            # Add to report
            self.report["actions_taken"].append({
                "action": "remove",
                "path": file_path,
                "timestamp": datetime.datetime.now().isoformat()
            })
            
            self.report["summary"]["files_removed"] += 1
            self.log(f"Removed file: {file_path}")
            return True
        
        except (IOError, OSError) as e:
            logger.error(f"Error removing file {file_path}: {e}")
            return False
    
    def _archive_file(self, file_path: str) -> bool:
        """
        Archive a file by moving it to the archive directory.
        
        Args:
            file_path: Path to the file to archive
            
        Returns:
            True if the archiving was successful, False otherwise
        """
        if self.dry_run:
            self.log(f"[DRY RUN] Would archive file: {file_path}")
            return True
        
        abs_path = os.path.join(self.project_dir, file_path)
        archive_dir = os.path.join(self.project_dir, "archive")
        archive_path = os.path.join(archive_dir, file_path)
        
        try:
            # Create archive directory if it doesn't exist
            os.makedirs(os.path.dirname(archive_path), exist_ok=True)
            
            # Move the file
            shutil.move(abs_path, archive_path)
            
            # Add to report
            self.report["actions_taken"].append({
                "action": "archive",
                "path": file_path,
                "archive_path": os.path.relpath(archive_path, self.project_dir),
                "timestamp": datetime.datetime.now().isoformat()
            })
            
            self.report["summary"]["files_archived"] += 1
            self.log(f"Archived file: {file_path} to {archive_path}")
            return True
        
        except (IOError, OSError) as e:
            logger.error(f"Error archiving file {file_path}: {e}")
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
    
    def cleanup(self) -> bool:
        """
        Clean up files based on the analysis.
        
        This method removes or archives files that have been identified for cleanup
        based on the user's confirmation.
        
        Returns:
            True if the cleanup was successful, False otherwise
        """
        self.log("Starting cleanup...")
        
        # Check if there are files to clean up
        if self.report["summary"]["total_files_to_cleanup"] == 0:
            logger.info("No files to clean up.")
            return True
        
        # Get files to clean up
        files_to_cleanup = []
        files_to_cleanup.extend([file_info["path"] for file_info in self.report["orphaned_files"]])
