#!/usr/bin/env python3
"""
Script to identify duplicate files in a project.

This script scans a directory recursively, calculates MD5 hashes of files,
and identifies files with identical content (duplicates).

Usage:
    python3 find_duplicate_files.py [--project-dir DIR] [--output FILE] [--verbose]
"""

import argparse
import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Find duplicate files in a project")
    parser.add_argument(
        "--project-dir", 
        default=".", 
        help="Path to the project directory (default: current directory)"
    )
    parser.add_argument(
        "--output", 
        default="duplicate_files_report.json", 
        help="Path to the output report file (default: duplicate_files_report.json)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose output"
    )
    return parser.parse_args()

def get_file_hash(file_path: str) -> str:
    """
    Calculate MD5 hash of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        MD5 hash of the file content
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def find_duplicate_files(project_dir: str, verbose: bool = False) -> Dict[str, List[str]]:
    """
    Find duplicate files in a directory.
    
    Args:
        project_dir: Path to the project directory
        verbose: Whether to print verbose output
        
    Returns:
        Dictionary mapping file hashes to lists of file paths
    """
    if verbose:
        print(f"Scanning directory: {project_dir}")
    
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
        r'backup_\d{8}_\d{6}/'  # Ignore backup directories
    ]
    
    # Compile the patterns
    ignore_regexes = [re.compile(pattern) for pattern in ignore_patterns]
    
    # Dictionary to store file hashes and paths
    file_hashes = defaultdict(list)
    
    # Count of files scanned
    files_scanned = 0
    
    # Walk through the project directory
    for root, dirs, files in os.walk(project_dir):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if not any(regex.search(os.path.join(root, d, '')) for regex in ignore_regexes)]
        
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, project_dir)
            
            # Skip ignored files
            if any(regex.search(rel_path) for regex in ignore_regexes):
                continue
            
            # Skip large files (> 10 MB) to avoid performance issues
            try:
                file_size = os.path.getsize(file_path)
                if file_size > 10 * 1024 * 1024:
                    if verbose:
                        print(f"Skipping large file: {rel_path} ({file_size / (1024 * 1024):.2f} MB)")
                    continue
                
                # Calculate file hash
                file_hash = get_file_hash(file_path)
                file_hashes[file_hash].append(rel_path)
                files_scanned += 1
                
                if verbose and files_scanned % 100 == 0:
                    print(f"Scanned {files_scanned} files...")
            
            except (IOError, OSError) as e:
                print(f"Error processing file {rel_path}: {e}", file=sys.stderr)
    
    if verbose:
        print(f"Scanned {files_scanned} files in total")
    
    # Filter out unique files (hashes with only one file)
    duplicate_hashes = {h: paths for h, paths in file_hashes.items() if len(paths) > 1}
    
    if verbose:
        print(f"Found {len(duplicate_hashes)} sets of duplicate files")
    
    return duplicate_hashes

def generate_report(duplicate_hashes: Dict[str, List[str]], project_dir: str) -> Dict:
    """
    Generate a report of duplicate files.
    
    Args:
        duplicate_hashes: Dictionary mapping file hashes to lists of file paths
        project_dir: Path to the project directory
        
    Returns:
        Report dictionary
    """
    report = {
        "project_dir": os.path.abspath(project_dir),
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_duplicate_sets": len(duplicate_hashes),
            "total_duplicate_files": sum(len(paths) - 1 for paths in duplicate_hashes.values()),
            "total_wasted_space": 0
        },
        "duplicate_sets": []
    }
    
    # Process each set of duplicate files
    for file_hash, file_paths in duplicate_hashes.items():
        # Sort by modification time (newest first)
        sorted_paths = sorted(
            file_paths,
            key=lambda p: os.path.getmtime(os.path.join(project_dir, p)),
            reverse=True
        )
        
        # Get file info for the first file (they're all the same size)
        first_path = os.path.join(project_dir, sorted_paths[0])
        file_size = os.path.getsize(first_path)
        wasted_space = file_size * (len(sorted_paths) - 1)
        report["summary"]["total_wasted_space"] += wasted_space
        
        # Add to report
        duplicate_set = {
            "hash": file_hash,
            "file_size": file_size,
            "wasted_space": wasted_space,
            "files": []
        }
        
        for path in sorted_paths:
            abs_path = os.path.join(project_dir, path)
            mtime = os.path.getmtime(abs_path)
            mtime_str = datetime.fromtimestamp(mtime).isoformat()
            
            duplicate_set["files"].append({
                "path": path,
                "last_modified": mtime_str
            })
        
        report["duplicate_sets"].append(duplicate_set)
    
    # Sort duplicate sets by wasted space (largest first)
    report["duplicate_sets"].sort(key=lambda x: x["wasted_space"], reverse=True)
    
    return report

def format_size(size_bytes: int) -> str:
    """
    Format a size in bytes as a human-readable string.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Human-readable size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def generate_markdown_report(report: Dict, output_path: str) -> None:
    """
    Generate a Markdown report of duplicate files.
    
    Args:
        report: Report dictionary
        output_path: Path to the output Markdown file
    """
    with open(output_path, "w") as f:
        f.write("# Duplicate Files Report\n\n")
        
        # Write summary
        f.write("## Summary\n\n")
        f.write(f"- **Project Directory**: {report['project_dir']}\n")
        f.write(f"- **Report Generated**: {report['timestamp']}\n")
        f.write(f"- **Total Duplicate Sets**: {report['summary']['total_duplicate_sets']}\n")
        f.write(f"- **Total Duplicate Files**: {report['summary']['total_duplicate_files']}\n")
        f.write(f"- **Total Wasted Space**: {format_size(report['summary']['total_wasted_space'])}\n\n")
        
        # Write recommendations
        f.write("## Recommendations\n\n")
        f.write("1. **Review and Consolidate**: Review each set of duplicate files and determine which ones to keep.\n")
        f.write("2. **Update References**: Update any references to the removed files to point to the kept files.\n")
        f.write("3. **Implement File Deduplication**: Consider implementing a file deduplication strategy to prevent future duplicates.\n")
        f.write("4. **Document File Locations**: Ensure that file locations are well-documented to prevent accidental duplication.\n\n")
        
        # Write duplicate sets
        f.write("## Duplicate Sets\n\n")
        
        for i, duplicate_set in enumerate(report["duplicate_sets"], 1):
            f.write(f"### Set {i}: {format_size(duplicate_set['file_size'])} each, {format_size(duplicate_set['wasted_space'])} wasted\n\n")
            
            # Write file table
            f.write("| File Path | Last Modified |\n")
            f.write("|-----------|---------------|\n")
            
            for file_info in duplicate_set["files"]:
                f.write(f"| `{file_info['path']}` | {file_info['last_modified']} |\n")
            
            f.write("\n")

def main():
    """Main function."""
    args = parse_args()
    
    # Find duplicate files
    duplicate_hashes = find_duplicate_files(args.project_dir, args.verbose)
    
    # Generate report
    report = generate_report(duplicate_hashes, args.project_dir)
    
    # Write JSON report
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)
    
    # Write Markdown report
    markdown_output = os.path.splitext(args.output)[0] + ".md"
    generate_markdown_report(report, markdown_output)
    
    # Print summary
    print(f"Found {report['summary']['total_duplicate_sets']} sets of duplicate files")
    print(f"Total duplicate files: {report['summary']['total_duplicate_files']}")
    print(f"Total wasted space: {format_size(report['summary']['total_wasted_space'])}")
    print(f"Report written to {args.output} and {markdown_output}")

if __name__ == "__main__":
    main()