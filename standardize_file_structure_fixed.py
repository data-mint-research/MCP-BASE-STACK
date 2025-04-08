#!/usr/bin/env python3
"""
File Structure Standardization Script

This script implements file structure standardization improvements by:
1. Fixing naming convention issues in files
2. Relocating files to ideal directories
3. Implementing automated validation for file structure

Usage:
    python standardize_file_structure.py [--dry-run] [--fix-naming] [--relocate] [--validate]

Options:
    --dry-run       Show what would be done without making changes
    --fix-naming    Only fix naming convention issues
    --relocate      Only relocate files to ideal directories
    --validate      Only validate file structure
    
If no options are provided, all actions will be performed.

The script will automatically update the knowledge graph after making changes.
"""

import os
import re
import sys
import shutil
import argparse
import json
import logging
import datetime
import collections
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Counter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"data/logs/file_structure_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

# File naming conventions
NAMING_CONVENTIONS = {
    ".py": r'^[a-z][a-z0-9_]*\.py$',  # snake_case for Python files
    ".js": r'^[a-z][a-zA-Z0-9]*\.js$',  # camelCase for JavaScript files
    ".ts": r'^[a-z][a-zA-Z0-9]*\.ts$',  # camelCase for TypeScript files
    ".jsx": r'^[A-Z][a-zA-Z0-9]*\.jsx$',  # PascalCase for React JSX files
    ".tsx": r'^[A-Z][a-zA-Z0-9]*\.tsx$',  # PascalCase for React TSX files
    ".md": r'^[A-Z][a-zA-Z0-9-]*\.md$',  # PascalCase or hyphenated for Markdown
    ".sh": r'^[a-z][a-z0-9_-]*\.sh$',  # lowercase with hyphens or underscores for shell scripts
    ".json": r'^[a-zA-Z0-9][a-zA-Z0-9_.-]*\.json$',  # any case for JSON files
    ".yml": r'^[a-z][a-z0-9_.-]*\.yml$',  # lowercase for YAML files
    ".yaml": r'^[a-z][a-z0-9_.-]*\.yaml$',  # lowercase for YAML files
    ".css": r'^[a-z][a-zA-Z0-9_.-]*\.css$',  # camelCase or kebab-case for CSS files
    ".html": r'^[a-z][a-zA-Z0-9_.-]*\.html$',  # lowercase for HTML files
    ".txt": r'^[a-zA-Z0-9][a-zA-Z0-9_.-]*\.txt$'  # any case for text files
}

# Directory structure mapping
DIRECTORY_MAPPING = {
    # Core application code
    r'.*_config\.py$': 'core/config/',
    r'.*_settings\.py$': 'core/config/',
    r'.*_logging\.py$': 'core/logging/',
    r'.*_kg\.py$': 'core/kg/scripts/',
    r'.*_quality\.py$': 'core/quality/',
    
    # Documentation
    r'.*_guide\.md$': 'docs/tutorials/',
    r'.*_standard(s)?\.md$': 'docs/conventions/',
    r'.*_schema\.md$': 'docs/knowledge-graph/',
    r'.*_troubleshooting\.md$': 'docs/troubleshooting/',
    
    # Scripts
    r'.*_backup\.sh$': 'scripts/utils/backup/',
    r'.*_deploy\.sh$': 'scripts/deployment/',
    r'.*_install\.sh$': 'scripts/utils/installation/',
    r'.*_validate\.sh$': 'scripts/utils/validation/',
    r'.*_cleanup\.sh$': 'scripts/utils/cleanup/',
    
    # Tests
    r'test_.*\.py$': 'tests/unit/',
    r'test_.*_integration\.py$': 'tests/integration/',
    r'test_.*_performance\.py$': 'tests/performance/',
    r'test_.*_property\.py$': 'tests/property/',
    r'test_.*_chaos\.py$': 'tests/chaos/'
}

# Excluded directories
EXCLUDED_DIRS = [
    '.git',
    'venv',
    'node_modules',
    '__pycache__',
    '.pytest_cache',
    '.vscode',
    '.idea',
    'dist',
    'build',
    '.env',
    'env',
    'migrations'
]

# Files that should never be renamed or moved
PROTECTED_FILES = [
    "__init__.py",
    "README.md",
    "setup.py",
    "requirements.txt",
    "package.json",
    "tsconfig.json",
    ".gitignore",
    ".env.example",
    "Dockerfile",
    "docker-compose.yml",
    "LICENSE"
]

# Issue severity levels
class IssueSeverity:
    """Severity levels for file structure issues."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

def is_excluded(path: str) -> bool:
    """Check if a path should be excluded from processing."""
    # Check for excluded directories
    for excluded in EXCLUDED_DIRS:
        if f'/{excluded}/' in path or path.startswith(f'./{excluded}/'):
            return True
    
    # Check for hidden files/directories (starting with .)
    path_parts = path.split(os.path.sep)
    for part in path_parts:
        if part.startswith('.') and part not in ['.', '..']:
            return True
    
    # Check for symlinks
    if os.path.islink(path):
        return True
    
    return False

def find_all_files() -> List[str]:
    """Find all files in the project."""
    all_files = []
    for root, _, files in os.walk("."):
        if is_excluded(root):
            continue
        for file in files:
            file_path = os.path.join(root, file)
            all_files.append(file_path)
    return all_files

def check_naming_convention(file_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Check if a file follows the naming convention.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Tuple of (follows_convention, suggested_name, severity)
    """
    file_name = os.path.basename(file_path)
    _, ext = os.path.splitext(file_name)
    
    # Special case for protected files - these should not be renamed
    if file_name in PROTECTED_FILES:
        return True, None, None
    
    # If the extension is not in our conventions, return True (no convention to enforce)
    if ext not in NAMING_CONVENTIONS:
        return True, None, None
    
    pattern = NAMING_CONVENTIONS[ext]
    if not re.match(pattern, file_name):
        # Determine severity based on file type and location
        severity = IssueSeverity.MEDIUM
        
        # Core Python files have higher severity
        if ext == '.py' and ('core/' in file_path or 'services/' in file_path):
            severity = IssueSeverity.HIGH
        # Documentation files have lower severity
        elif ext == '.md':
            severity = IssueSeverity.LOW
        
        # Generate a suggested name
        if ext == '.py':
            # Convert to snake_case
            suggested = re.sub(r'([A-Z])', r'_\1', file_name).lower()
            suggested = re.sub(r'^_', '', suggested)  # Remove leading underscore
            suggested = re.sub(r'[^a-z0-9_.]', '_', suggested)  # Replace invalid chars
            if not suggested.startswith(('_', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z')):
                suggested = 'file_' + suggested
        elif ext in ['.js', '.ts']:
            # Convert to camelCase
            parts = re.split(r'[^a-zA-Z0-9]', file_name.replace(ext, ''))
            suggested = parts[0].lower()
            for part in parts[1:]:
                if part:
                    suggested += part[0].upper() + part[1:].lower()
            suggested += ext
        elif ext in ['.jsx', '.tsx']:
            # Convert to PascalCase
            parts = re.split(r'[^a-zA-Z0-9]', file_name.replace(ext, ''))
            suggested = ''
            for part in parts:
                if part:
                    suggested += part[0].upper() + part[1:].lower()
            suggested += ext
        elif ext == '.md':
            # Convert to PascalCase or hyphenated
            parts = re.split(r'[^a-zA-Z0-9]', file_name.replace(ext, ''))
            suggested = ''
            for part in parts:
                if part:
                    suggested += part[0].upper() + part[1:].lower() + '-'
            suggested = suggested.rstrip('-') + ext
        elif ext == '.sh':
            # Convert to lowercase with hyphens
            suggested = file_name.lower()
            suggested = re.sub(r'[^a-z0-9_.-]', '-', suggested)
            if not suggested.startswith(('_', '-', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z')):
                suggested = 'script-' + suggested
        elif ext in ['.json', '.yml', '.yaml']:
            # Convert to lowercase with hyphens
            suggested = file_name.lower()
            suggested = re.sub(r'[^a-z0-9_.-]', '-', suggested)
        elif ext in ['.css', '.html']:
            # Convert to kebab-case
            suggested = re.sub(r'([A-Z])', r'-\1', file_name).lower()
            suggested = re.sub(r'^-', '', suggested)  # Remove leading hyphen
            suggested = re.sub(r'[^a-z0-9_.-]', '-', suggested)  # Replace invalid chars
        else:
            suggested = file_name  # No suggestion
            
        return False, suggested, severity
    
    return True, None, None

def determine_ideal_directory(file_path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Determine the ideal directory for a file based on its name and content.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Tuple of (ideal_directory, severity)
        The ideal directory path, or None if the current location is appropriate
    """
    file_name = os.path.basename(file_path)
    current_dir = os.path.dirname(file_path)
    
    # Skip if already in a standard location
    if (current_dir.startswith('./core/') or
        current_dir.startswith('./docs/') or
        current_dir.startswith('./scripts/') or
        current_dir.startswith('./tests/')):
        return None, None
    
    # Special case for protected files - these should stay in their directories
    if file_name in PROTECTED_FILES:
        return None, None
    
    # Check if the file matches any of the directory mapping patterns
    for pattern, target_dir in DIRECTORY_MAPPING.items():
        if re.match(pattern, file_name):
            # Determine severity based on file type and location
            severity = IssueSeverity.MEDIUM
            
            # Core Python files have higher severity
            if file_name.endswith('.py') and ('core' in target_dir or 'services' in target_dir):
                severity = IssueSeverity.HIGH
            # Documentation files have lower severity
            elif file_name.endswith('.md'):
                severity = IssueSeverity.LOW
                
            return target_dir, severity
    
    # Special case for test files
    if file_name.startswith('test_') and file_name.endswith('.py'):
        return 'tests/unit/', IssueSeverity.MEDIUM
    
    # Special case for documentation files
    if file_name.endswith('.md'):
        # Only relocate if not already in docs/ directory
        if not current_dir.startswith('./docs/'):
            return 'docs/', IssueSeverity.LOW
        # If already in docs/ directory, it's in the right place
        return None, None
    
    return None, None

def fix_naming_conventions(dry_run: bool = False) -> List[Dict[str, Any]]:
        """
        Fix naming convention issues in files.
        
        Args:
            dry_run: If True, only show what would be done without making changes
            
        Returns:
            List of files that were fixed
        """
        logger.info("Checking for naming convention issues...")
        
        all_files = find_all_files()
        files_with_issues = []
        
        # Track files by their target names to detect conflicts
        target_files = {}
        
        for file_path in all_files:
            follows_convention, suggested_name, severity = check_naming_convention(file_path)
            
            if not follows_convention and suggested_name:
                directory = os.path.dirname(file_path)
                new_path = os.path.join(directory, suggested_name)
                
                # Check for potential conflicts
                if new_path in target_files:
                    # We have a conflict - two files would be renamed to the same name
                    conflict_file = target_files[new_path]
                    logger.warning(f"Naming conflict detected: Both {file_path} and {conflict_file} would be renamed to {new_path}")
                    
                    # Modify the suggested name to avoid conflict
                    name, ext = os.path.splitext(suggested_name)
                    suggested_name = f"{name}_1{ext}"
                    new_path = os.path.join(directory, suggested_name)
                    
                    # Check if the modified name also conflicts
                    if new_path in target_files:
                        logger.error(f"Multiple naming conflicts for {file_path}. Skipping.")
                        continue
                
                # Record this file's target path
                target_files[new_path] = file_path
                
                files_with_issues.append({
                    'file_path': file_path,
                    'issue': 'naming_convention',
                    'suggested_name': suggested_name,
                    'new_path': new_path,
                    'severity': severity
                })
                
                if not dry_run:
                    try:
                        # Check if the target file already exists
                        if os.path.exists(new_path):
                            logger.warning(f"Cannot rename {file_path} to {new_path}: Target file already exists")
                            continue
                        
                        # Create parent directories if they don't exist
                        os.makedirs(os.path.dirname(new_path), exist_ok=True)
                        
                        # Rename the file
                        shutil.move(file_path, new_path)
                        logger.info(f"Renamed {file_path} to {new_path}")
                    except PermissionError:
                        logger.error(f"Permission denied when renaming {file_path}. Check file permissions.")
                    except Exception as e:
                        logger.error(f"Error renaming {file_path}: {e}")
        
        # Group issues by severity for reporting
        severity_counts = collections.Counter([issue.get('severity', 'unknown') for issue in files_with_issues])
        logger.info(f"Found {len(files_with_issues)} files with naming convention issues:")
        for severity, count in severity_counts.items():
            logger.info(f"  - {severity.capitalize()}: {count}")
        
        return files_with_issues
    
    def relocate_files(dry_run: bool = False) -> List[Dict[str, Any]]:
        """
        Relocate files to their ideal directories.
        
        Args:
            dry_run: If True, only show what would be done without making changes
            
        Returns:
            List of files that were relocated
        """
        logger.info("Checking for files not in ideal directories...")
        
        all_files = find_all_files()
        files_to_relocate = []
        
        # Track files by their target paths to detect conflicts
        target_files = {}
        
        for file_path in all_files:
            ideal_dir, severity = determine_ideal_directory(file_path)
            
            if ideal_dir:
                file_name = os.path.basename(file_path)
                new_path = os.path.join(ideal_dir, file_name)
                
                # Check for potential conflicts
                if new_path in target_files:
                    # We have a conflict - two files would be moved to the same path
                    conflict_file = target_files[new_path]
                    logger.warning(f"Relocation conflict detected: Both {file_path} and {conflict_file} would be moved to {new_path}")
                    
                    # Modify the target path to avoid conflict
                    name, ext = os.path.splitext(file_name)
                    modified_name = f"{name}_1{ext}"
                    new_path = os.path.join(ideal_dir, modified_name)
                    
                    # Check if the modified path also conflicts
                    if new_path in target_files:
                        logger.error(f"Multiple relocation conflicts for {file_path}. Skipping.")
                        continue
                
                # Record this file's target path
                target_files[new_path] = file_path
                
                # Generate a reason for the relocation
                reason = get_relocation_reason(file_path, ideal_dir)
                
                files_to_relocate.append({
                    'file_path': file_path,
                    'issue': 'wrong_directory',
                    'ideal_directory': ideal_dir,
                    'new_path': new_path,
                    'severity': severity,
                    'reason': reason
                })
                
                if not dry_run:
                    try:
                        # Create the target directory if it doesn't exist
                        os.makedirs(ideal_dir, exist_ok=True)
                        
                        # Check if the target file already exists
                        if os.path.exists(new_path):
                            logger.warning(f"Cannot move {file_path} to {new_path}: Target file already exists")
                            continue
                        
                        # Move the file
                        shutil.move(file_path, new_path)
                        logger.info(f"Moved {file_path} to {new_path}")
                    except PermissionError:
                        logger.error(f"Permission denied when moving {file_path}. Check file permissions.")
                    except Exception as e:
                        logger.error(f"Error moving {file_path}: {e}")
        
        # Group issues by severity for reporting
        severity_counts = collections.Counter([issue.get('severity', 'unknown') for issue in files_to_relocate])
        logger.info(f"Found {len(files_to_relocate)} files not in ideal directories:")
        for severity, count in severity_counts.items():
            logger.info(f"  - {severity.capitalize()}: {count}")
        
        return files_to_relocate
    
    def get_relocation_reason(file_path: str, ideal_dir: str) -> str:
        """
        Generate a human-readable reason for why a file should be relocated.
        
        Args:
            file_path: Path to the file
            ideal_dir: The ideal directory for the file
            
        Returns:
            A string explaining why the file should be relocated
        """
        file_name = os.path.basename(file_path)
        current_dir = os.path.dirname(file_path)
        
        # Test files
        if file_name.startswith('test_') and 'tests/' in ideal_dir:
            return f"Test files should be located in the appropriate tests directory ({ideal_dir})"
        
        # Documentation files
        if file_name.endswith('.md') and 'docs/' in ideal_dir:
            return "Documentation files should be located in the docs directory for better organization"
        
        # Script files
        if file_name.endswith('.sh') and 'scripts/' in ideal_dir:
            return "Shell scripts should be located in the scripts directory for better organization"
        
        # Configuration files
        if file_name.endswith(('.json', '.yml', '.yaml', '.ini', '.conf', '.config')) and 'config/' in ideal_dir:
            return "Configuration files should be located in the config directory for better organization"
        
        # Core files
        if 'core/' in ideal_dir:
            return f"Core application files should be located in the appropriate core directory ({ideal_dir})"
        
        # Default reason
        return f"File should be relocated to {ideal_dir} based on project structure standards"
    
    def validate_file_structure() -> Dict[str, Any]:
        """
        Validate the file structure and generate a report.
        
        Returns:
            Dictionary with validation results
        """
        logger.info("Validating file structure...")
        
        all_files = find_all_files()
        total_files = len(all_files)
        
        # Check naming conventions
        naming_issues = []
        naming_issues_by_severity = {
            IssueSeverity.HIGH: [],
            IssueSeverity.MEDIUM: [],
            IssueSeverity.LOW: []
        }
        
        for file_path in all_files:
            follows_convention, suggested_name, severity = check_naming_convention(file_path)
            if not follows_convention and suggested_name:
                issue = {
                    'file_path': file_path,
                    'issue': 'naming_convention',
                    'suggested_name': suggested_name,
                    'severity': severity
                }
                naming_issues.append(issue)
                
                # Group by severity
                if severity:
                    naming_issues_by_severity[severity].append(issue)
        
        # Check directory structure
        directory_issues = []
        directory_issues_by_severity = {
            IssueSeverity.HIGH: [],
            IssueSeverity.MEDIUM: [],
            IssueSeverity.LOW: []
        }
        
        for file_path in all_files:
            ideal_dir, severity = determine_ideal_directory(file_path)
            if ideal_dir:
                # Check if the file is already in its ideal directory
                current_dir = os.path.dirname(file_path)
                normalized_ideal_dir = ideal_dir.rstrip('/')
                normalized_current_dir = current_dir.lstrip('./').rstrip('/')
                
                # Only flag as an issue if it's not already in the ideal directory
                if normalized_current_dir != normalized_ideal_dir:
                    reason = get_relocation_reason(file_path, ideal_dir)
                    issue = {
                        'file_path': file_path,
                        'issue': 'wrong_directory',
                        'ideal_directory': ideal_dir,
                        'severity': severity,
                        'reason': reason
                    }
                    directory_issues.append(issue)
                    
                    # Group by severity
                    if severity:
                        directory_issues_by_severity[severity].append(issue)
        
        # Calculate compliance percentages
        naming_compliance = 100 - (len(naming_issues) / total_files * 100) if total_files > 0 else 100
        directory_compliance = 100 - (len(directory_issues) / total_files * 100) if total_files > 0 else 100
        overall_compliance = (naming_compliance + directory_compliance) / 2
        
        # Calculate file type statistics
        file_types = {}
        for file_path in all_files:
            _, ext = os.path.splitext(file_path)
            if ext:
                file_types[ext] = file_types.get(ext, 0) + 1
        
        # Generate suggestions for improvement
        print("About to generate suggestions...")
        suggestions = generate_improvement_suggestions(naming_issues, directory_issues)
        print(f"Generated suggestions: {suggestions}")
        
        # Generate report
        report = {
            'timestamp': datetime.datetime.now().isoformat(),
            'total_files': total_files,
            'file_types': file_types,
            'naming_issues': {
                'count': len(naming_issues),
                'compliance_percentage': naming_compliance,
                'issues': naming_issues,
                'issues_by_severity': {
                    'high': len(naming_issues_by_severity[IssueSeverity.HIGH]),
                    'medium': len(naming_issues_by_severity[IssueSeverity.MEDIUM]),
                    'low': len(naming_issues_by_severity[IssueSeverity.LOW])
                }
            },
            'directory_issues': {
                'count': len(directory_issues),
                'compliance_percentage': directory_compliance,
                'issues': directory_issues,
                'issues_by_severity': {
                    'high': len(directory_issues_by_severity[IssueSeverity.HIGH]),
                    'medium': len(directory_issues_by_severity[IssueSeverity.MEDIUM]),
                    'low': len(directory_issues_by_severity[IssueSeverity.LOW])
                }
            },
            'overall_compliance_percentage': overall_compliance,
            'suggestions': suggestions,
            'debug_info': {
                'suggestions_generated': bool(suggestions),
                'suggestions_count': len(suggestions),
                'suggestions_list': suggestions
            }
        }
        
        # Save report to file
        report_dir = Path("data/reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        # Save current report
        report_path = report_dir / "file-structure-report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Also save a timestamped version for historical tracking
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        historical_report_path = report_dir / f"file-structure-report_{timestamp}.json"
        with open(historical_report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"File structure validation report saved to {report_path}")
        logger.info(f"Overall file structure compliance: {overall_compliance:.2f}%")
        logger.info(f"Files with naming convention issues: {len(naming_issues)}")
        logger.info(f"Files not in ideal directories: {len(directory_issues)}")
        
        # Log suggestions
        if suggestions:
            logger.info("Suggestions for improvement:")
            for suggestion in suggestions:
                logger.info(f"- {suggestion}")
        
        return report
    
    def generate_improvement_suggestions(naming_issues: List[Dict[str, Any]], directory_issues: List[Dict[str, Any]]) -> List[str]:
        print("Generating improvement suggestions...")
        """
        Generate suggestions for improving file structure based on identified issues.
        
        Args:
            naming_issues: List of naming convention issues
            directory_issues: List of directory structure issues
            
        Returns:
            List of suggestions for improvement
        """
        suggestions = []
        
        # Check for patterns in naming issues
        if naming_issues:
            # Group by extension
            issues_by_ext = {}
            for issue in naming_issues:
                file_path = issue['file_path']
                _, ext = os.path.splitext(file_path)
                if ext not in issues_by_ext:
                    issues_by_ext[ext] = []
                issues_by_ext[ext].append(issue)
            
            # Generate suggestions for each extension with issues
            for ext, issues in issues_by_ext.items():
                if len(issues) > 3:  # Only suggest if there are multiple issues of the same type
                    if ext == '.py':
                        suggestions.append(f"Consider running a Python code formatter like 'black' or 'autopep8' to standardize Python file naming")
                    elif ext == '.md':
                        suggestions.append(f"Consider using a script to standardize Markdown file names to PascalCase-with-hyphens format")
                    else:
                        suggestions.append(f"Consider standardizing {ext} file names using the standardize_file_structure.py script")
        
        # Check for patterns in directory issues
        if directory_issues:
            # Group by target directory
            issues_by_dir = {}
            for issue in directory_issues:
                ideal_dir = issue['ideal_directory']
                if ideal_dir not in issues_by_dir:
                    issues_by_dir[ideal_dir] = []
                issues_by_dir[ideal_dir].append(issue)
            
            # Generate suggestions for each target directory with issues
            for dir_path, issues in issues_by_dir.items():
                if len(issues) > 3:  # Only suggest if there are multiple issues of the same type
                    if 'tests/' in dir_path:
                        suggestions.append(f"Consider moving all test files to the appropriate test directories")
                    elif 'docs/' in dir_path:
                        suggestions.append(f"Consider consolidating documentation files in the docs directory for better organization")
                    else:
                        suggestions.append(f"Consider reorganizing files to follow the project's directory structure standards")
        
        # General suggestions
        if naming_issues or directory_issues:
            suggestions.append("Consider adding file structure validation to your CI/CD pipeline to catch issues early")
            suggestions.append("Consider documenting file naming and structure conventions in a style guide")
        
        return suggestions
    
    def update_knowledge_graph():
        """Update the knowledge graph with file structure metrics."""
        logger.info("Updating knowledge graph with file structure metrics...")
        
        try:
            # Run the knowledge graph update script
            import subprocess
            subprocess.run(["python3", "core/kg/scripts/update_knowledge_graph.py"], check=True)
            logger.info("Knowledge graph updated successfully")
        except Exception as e:
            logger.error(f"Failed to update knowledge graph: {e}")
    
    def implement_automated_validation():
        """Implement automated validation for file structure."""
        logger.info("Implementing automated validation for file structure...")
        
        # Create a pre-commit hook for file structure validation
        pre_commit_hook = """#!/bin/bash
    # Pre-commit hook for file structure validation
    echo "Validating file structure..."
    python standardize_file_structure.py --validate
    
    # Check if validation passed
    if [ $? -ne 0 ]; then
        echo "File structure validation failed. Please fix the issues before committing."
        exit 1
    fi
    
    exit 0
    """
        
        # Create the pre-commit hook file
        hook_dir = Path(".git-hooks")
        hook_dir.mkdir(exist_ok=True)
        
        hook_path = hook_dir / "pre-commit-file-structure"
        with open(hook_path, 'w') as f:
            f.write(pre_commit_hook)
        
        # Make the hook executable
        os.chmod(hook_path, 0o755)
        
        # Update the pre-commit config to include the file structure validation
        pre_commit_config = Path("config/lint/pre-commit-config.yaml")
        if pre_commit_config.exists():
            with open(pre_commit_config, 'r') as f:
                config_content = f.read()
            
            # Check if the hook is already in the config
            if "pre-commit-file-structure" not in config_content:
                # Add the hook to the config
                with open(pre_commit_config, 'a') as f:
                    f.write("""
      - id: file-structure-validation
        name: File Structure Validation
        entry: .git-hooks/pre-commit-file-structure
        language: script
        pass_filenames: false
    """)
        
        logger.info("Automated validation for file structure implemented")
        return True
    
    def main():
        """Main function to standardize file structure."""
        parser = argparse.ArgumentParser(description="File Structure Standardization Script")
        parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
        parser.add_argument("--fix-naming", action="store_true", help="Only fix naming convention issues")
        parser.add_argument("--relocate", action="store_true", help="Only relocate files to ideal directories")
        parser.add_argument("--validate", action="store_true", help="Only validate file structure")
        
        args = parser.parse_args()
        
        # Create necessary directories
        os.makedirs("data/logs", exist_ok=True)
        os.makedirs("data/reports", exist_ok=True)
        
        # Determine which actions to perform
        do_all = not (args.fix_naming or args.relocate or args.validate)
        
        # Perform actions
        fixed_files = []
        relocated_files = []
        validation_report = None
        
        if args.fix_naming or do_all:
            fixed_files = fix_naming_conventions(args.dry_run)
        
        if args.relocate or do_all:
            relocated_files = relocate_files(args.dry_run)
        
        if args.validate or do_all:
            validation_report = validate_file_structure()
        
        if do_all and not args.dry_run:
            implement_automated_validation()
        
        # Update knowledge graph if changes were made
        if not args.dry_run and (fixed_files or relocated_files):
            update_knowledge_graph()
        
        # Print summary
        logger.info("File Structure Standardization Summary:")
        logger.info(f"- Files with naming convention issues fixed: {len(fixed_files)}")
        logger.info(f"- Files relocated to ideal directories: {len(relocated_files)}")
        
        if validation_report:
            logger.info(f"- Overall file structure compliance: {validation_report['overall_compliance_percentage']:.2f}%")
        
        return 0
    
    if __name__ == "__main__":
        sys.exit(main())
    
    # Special case for script files
    if file_name.endswith('.sh'):
        # Only relocate if not already in scripts/ directory
        if not current_dir.startswith('./scripts/'):
            return 'scripts/utils/', IssueSeverity.MEDIUM
        # If already in scripts/ directory, it's in the right place
        return None, None
    
    # Special case for configuration files
    if file_name.endswith(('.json', '.yml', '.yaml', '.ini', '.conf', '.config')):
        # Only relocate if not already in config/ directory
        if not current_dir.startswith('./config/'):
            return 'config/', IssueSeverity.MEDIUM
        # If already in config/ directory, it's in the right place
        return None, None
    
    return None, None
