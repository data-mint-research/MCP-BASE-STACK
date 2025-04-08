#!/usr/bin/env python3
"""
Script to rename files according to naming conventions and update references.

This script:
1. Renames files according to the project's naming conventions
2. Updates references to the renamed files in other files
3. Verifies that all references are updated correctly
"""

import os
import re
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

# Define the files to rename and their new names
FILES_TO_RENAME = {
    # Shell scripts (kebab-case)
    "scripts/deployment/update-ollama-references.sh": "scripts/deployment/update-ollama-references.sh",
    "scripts/deployment/restart-stack.sh": "scripts/deployment/restart-stack.sh",
    "scripts/deployment/start-mcp-server.sh": "scripts/deployment/start-mcp-server.sh",
    "scripts/deployment/register-new-features.sh": "scripts/deployment/register-new-features.sh",
    "scripts/utils/run-conformance-tests.sh": "scripts/utils/run-conformance-tests.sh",
    "scripts/utils/run-mcp-client-test.sh": "scripts/utils/run-mcp-client-test.sh",
    "scripts/utils/run-mcp-host.sh": "scripts/utils/run-mcp-host.sh",
    "scripts/utils/test-shellcheck.sh": "scripts/utils/test-shellcheck.sh",
    "scripts/utils/backup/create-backup-branch.sh": "scripts/utils/backup/create-backup-branch.sh",
    "scripts/utils/backup/restore-from-backup.sh": "scripts/utils/backup/restore-from-backup.sh",
    "scripts/utils/cleanup/cleanup-backup-dirs.sh": "scripts/utils/cleanup/cleanup-backup-dirs.sh",
    "scripts/utils/cleanup/remove-local-backup-system.sh": "scripts/utils/cleanup/remove-local-backup-system.sh",
    "scripts/utils/installation/install-pre-commit-hooks.sh": "scripts/utils/installation/install-pre-commit-hooks.sh",
    "scripts/utils/installation/install-quality-tools.sh": "scripts/utils/installation/install-quality-tools.sh",
    "scripts/utils/quality/check-code-quality.sh": "scripts/utils/quality/check-code-quality.sh",
    "scripts/utils/quality/fix-code-quality.sh": "scripts/utils/quality/fix-code-quality.sh",
    "scripts/utils/validation/verify-backup-system.sh": "scripts/utils/validation/verify-backup-system.sh",
    "scripts/utils/validation/verify-stack-health.sh": "scripts/utils/validation/verify-stack-health.sh",
    "scripts/migration/migrate-to-git-backup.sh": "scripts/migration/migrate-to-git-backup.sh",
}

def find_references(old_filename: str) -> List[Tuple[str, List[int]]]:
    """
    Find all references to the old filename in the codebase.
    
    Args:
        old_filename: The old filename to search for
        
    Returns:
        List of tuples containing (file_path, line_numbers)
    """
    # Extract the basename without path
    old_basename = os.path.basename(old_filename)
    
    # Use grep to find references to both the full path and just the filename
    try:
        # Search for the full path
        full_path_cmd = ["grep", "-r", "--include=*.*", "-l", old_filename, "."]
        full_path_result = subprocess.run(full_path_cmd, capture_output=True, text=True)
        full_path_files = full_path_result.stdout.strip().split('\n') if full_path_result.stdout else []
        
        # Search for just the filename
        basename_cmd = ["grep", "-r", "--include=*.*", "-l", old_basename, "."]
        basename_result = subprocess.run(basename_cmd, capture_output=True, text=True)
        basename_files = basename_result.stdout.strip().split('\n') if basename_result.stdout else []
        
        # Combine and deduplicate results
        all_files = list(set(full_path_files + basename_files))
        
        # Filter out empty strings and the file itself
        all_files = [f for f in all_files if f and f != old_filename]
        
        # For each file, find the line numbers containing the reference
        references = []
        for file_path in all_files:
            if not os.path.isfile(file_path):
                continue
                
            line_numbers = []
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f, 1):
                    if old_filename in line or old_basename in line:
                        line_numbers.append(i)
            
            if line_numbers:
                references.append((file_path, line_numbers))
        
        return references
    
    except subprocess.CalledProcessError:
        print(f"Error searching for references to {old_filename}")
        return []

def update_references(old_filename: str, new_filename: str, references: List[Tuple[str, List[int]]]) -> None:
    """
    Update references to the old filename in other files.
    
    Args:
        old_filename: The old filename
        new_filename: The new filename
        references: List of tuples containing (file_path, line_numbers)
    """
    old_basename = os.path.basename(old_filename)
    new_basename = os.path.basename(new_filename)
    
    for file_path, _ in references:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Replace full paths
            updated_content = content.replace(old_filename, new_filename)
            
            # Replace basenames, but be careful not to replace substrings of other words
            updated_content = re.sub(r'\b' + re.escape(old_basename) + r'\b', new_basename, updated_content)
            
            if content != updated_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                print(f"Updated references in {file_path}")
        
        except Exception as e:
            print(f"Error updating references in {file_path}: {e}")

def rename_file(old_filename: str, new_filename: str) -> bool:
    """
    Rename a file and update references to it.
    
    Args:
        old_filename: The old filename
        new_filename: The new filename
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if the old file exists
        if not os.path.exists(old_filename):
            print(f"File not found: {old_filename}")
            return False
        
        # Check if the new file already exists
        if os.path.exists(new_filename):
            print(f"Target file already exists: {new_filename}")
            return False
        
        # Find references to the old filename
        print(f"Finding references to {old_filename}...")
        references = find_references(old_filename)
        print(f"Found {len(references)} files with references to {old_filename}")
        
        # Create the directory for the new file if it doesn't exist
        os.makedirs(os.path.dirname(new_filename), exist_ok=True)
        
        # Rename the file
        os.rename(old_filename, new_filename)
        print(f"Renamed {old_filename} to {new_filename}")
        
        # Update references
        print(f"Updating references...")
        update_references(old_filename, new_filename, references)
        
        return True
    
    except Exception as e:
        print(f"Error renaming {old_filename} to {new_filename}: {e}")
        return False

def main() -> None:
    """Main function to rename files and update references."""
    # Count successful and failed renames
    success_count = 0
    failure_count = 0
    
    # Process each file
    for old_filename, new_filename in FILES_TO_RENAME.items():
        print(f"\nProcessing: {old_filename} -> {new_filename}")
        
        if rename_file(old_filename, new_filename):
            success_count += 1
        else:
            failure_count += 1
    
    # Print summary
    print(f"\nRenaming complete. {success_count} files renamed successfully, {failure_count} failed.")
    
    # Update file structure metrics
    print("\nUpdating file structure metrics...")
    try:
        subprocess.run(["python3", "standardize_file_structure.py", "--validate"], check=True)
        print("File structure metrics updated successfully.")
    except subprocess.CalledProcessError:
        print("Error updating file structure metrics.")

if __name__ == "__main__":
    main()