#!/usr/bin/env python3
"""
Script to identify potentially orphaned files in the project.

This script scans all files in the project directory, analyzes references between files,
and identifies files that are not referenced by any other file.

Usage:
    python3 identify_orphaned_files.py
"""

import os
import re
import json
import datetime
from pathlib import Path
from typing import Dict, List, Set, Any

# Define patterns for files to ignore
IGNORE_PATTERNS = [
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
IGNORE_REGEXES = [re.compile(pattern) for pattern in IGNORE_PATTERNS]

# Define patterns for file references in different file types
REFERENCE_PATTERNS = {
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

def is_text_file(file_path: str) -> bool:
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

def scan_files(project_dir: str) -> Dict[str, Any]:
    """
    Scan all files in the project directory.
    
    Args:
        project_dir: Path to the project directory
        
    Returns:
        Dictionary with all_files and file_info
    """
    all_files = set()
    file_info = {}
    
    # Walk through the project directory
    for root, dirs, files in os.walk(project_dir):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if not any(regex.search(os.path.join(root, d, '')) for regex in IGNORE_REGEXES)]
        
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, project_dir)
            
            # Skip ignored files
            if any(regex.search(rel_path) for regex in IGNORE_REGEXES):
                continue
            
            all_files.add(rel_path)
            
            # Get file info
            try:
                file_size = os.path.getsize(file_path)
                file_mtime = os.path.getmtime(file_path)
                file_mtime_str = datetime.datetime.fromtimestamp(file_mtime).isoformat()
                
                file_info[rel_path] = {
                    "size": file_size,
                    "last_modified": file_mtime_str
                }
            except (IOError, OSError) as e:
                print(f"Error getting info for file {rel_path}: {e}")
    
    return {"all_files": all_files, "file_info": file_info}

def scan_file_references(project_dir: str, all_files: Set[str]) -> Set[str]:
    """
    Scan files for references to other files.
    
    Args:
        project_dir: Path to the project directory
        all_files: Set of all files in the project
        
    Returns:
        Set of referenced files
    """
    referenced_files = set()
    
    # Scan each file for references
    for file_path in all_files:
        abs_path = os.path.join(project_dir, file_path)
        
        # Skip binary files and large files
        if not is_text_file(abs_path) or os.path.getsize(abs_path) > 10 * 1024 * 1024:
            continue
        
        try:
            with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Check for references based on file extension
            for pattern_key, patterns in REFERENCE_PATTERNS.items():
                if re.search(pattern_key, file_path):
                    for pattern in patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            # Convert module references to file paths
                            if re.search(r'\.py$', file_path) and '.' in match and '/' not in match and '\\' not in match:
                                # Convert Python module to file path
                                module_path = match.replace('.', '/') + '.py'
                                referenced_files.add(module_path)
                            else:
                                # Normalize the path
                                norm_path = os.path.normpath(match)
                                if not os.path.isabs(norm_path):
                                    # Resolve relative path
                                    dir_path = os.path.dirname(file_path)
                                    resolved_path = os.path.normpath(os.path.join(dir_path, norm_path))
                                    referenced_files.add(resolved_path)
                                else:
                                    # Convert absolute path to relative if it's within the project
                                    try:
                                        rel_path = os.path.relpath(norm_path, project_dir)
                                        referenced_files.add(rel_path)
                                    except ValueError:
                                        # Path is outside the project directory
                                        pass
        
        except (IOError, OSError) as e:
            print(f"Error scanning file {file_path} for references: {e}")
    
    return referenced_files

def identify_orphaned_files(all_files: Set[str], referenced_files: Set[str], file_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Identify orphaned files.
    
    Args:
        all_files: Set of all files in the project
        referenced_files: Set of referenced files
        file_info: Dictionary with file information
        
    Returns:
        List of orphaned files with information
    """
    # Files that are not referenced by any other file
    orphaned_files = all_files - referenced_files
    
    # Create a list of orphaned files with information
    orphaned_files_info = []
    for file_path in sorted(orphaned_files):
        if file_path in file_info:
            orphaned_files_info.append({
                "path": file_path,
                "size": file_info[file_path]["size"],
                "last_modified": file_info[file_path]["last_modified"],
                "reason": "Not referenced by any other file"
            })
    
    return orphaned_files_info

def generate_report(project_dir: str, orphaned_files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a report of orphaned files.
    
    Args:
        project_dir: Path to the project directory
        orphaned_files: List of orphaned files with information
        
    Returns:
        Report dictionary
    """
    # Calculate total size of orphaned files
    total_size = sum(file["size"] for file in orphaned_files)
    
    # Create the report
    report = {
        "project_dir": project_dir,
        "timestamp": datetime.datetime.now().isoformat(),
        "summary": {
            "total_orphaned_files": len(orphaned_files),
            "total_size": total_size
        },
        "orphaned_files": orphaned_files
    }
    
    return report

def main():
    """
    Main function.
    """
    project_dir = os.path.abspath(".")
    print(f"Scanning files in directory: {project_dir}")
    
    # Scan files
    scan_result = scan_files(project_dir)
    all_files = scan_result["all_files"]
    file_info = scan_result["file_info"]
    print(f"Found {len(all_files)} files")
    
    # Scan file references
    referenced_files = scan_file_references(project_dir, all_files)
    print(f"Found {len(referenced_files)} file references")
    
    # Identify orphaned files
    orphaned_files = identify_orphaned_files(all_files, referenced_files, file_info)
    print(f"Identified {len(orphaned_files)} orphaned files")
    
    # Generate report
    report = generate_report(project_dir, orphaned_files)
    
    # Write report to file
    report_path = "orphaned_files_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Report written to {report_path}")
    
    # Print summary
    print("\nSummary:")
    print(f"Total orphaned files: {report['summary']['total_orphaned_files']}")
    print(f"Total size: {report['summary']['total_size']} bytes")
    
    # Print top 10 orphaned files by size
    if orphaned_files:
        print("\nTop 10 orphaned files by size:")
        for file in sorted(orphaned_files, key=lambda x: x["size"], reverse=True)[:10]:
            print(f"{file['path']} ({file['size']} bytes)")

if __name__ == "__main__":
    main()