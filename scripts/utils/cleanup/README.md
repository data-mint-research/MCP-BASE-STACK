# Cleanup Utilities

## Overview

This directory contains utility scripts for cleaning up unwanted files, directories, and backup artifacts in the MCP-BASE-STACK project. These utilities help maintain a clean and organized codebase by removing unnecessary files and ensuring files are in their correct locations.

## Current Status

The project has achieved 100% file structure compliance:
- 249 total files properly organized
- 100% naming convention compliance
- 100% directory structure compliance

The cleanup utilities work in conjunction with the file structure standardization system to maintain this high level of organization.

## Scripts

### cleanup_files.py

A comprehensive file cleanup script that identifies and safely removes orphaned or outdated files, and ensures files are in their ideal locations according to the specification manifest.

Features:
- Loads the specification manifest to determine ideal file locations
- Identifies orphaned files (not referenced by any other file or not in the knowledge graph)
- Identifies outdated files (old migration files, duplicate files, outdated versions)
- Identifies files in incorrect locations based on the specification manifest
- Generates detailed reports of files to be cleaned up or moved
- Safely removes, archives, or moves files based on user confirmation
- Updates the knowledge graph with changes made
- Special handling for `__init__.py` files and `README.md` files

Usage:
```bash
python cleanup_files.py --project-dir /path/to/project --manifest /path/to/manifest.json --output /path/to/report.json
python cleanup_files.py --project-dir /path/to/project --verbose
python cleanup_files.py --project-dir /path/to/project --dry-run
python cleanup_files.py --project-dir /path/to/project --interactive
python cleanup_files.py --project-dir /path/to/project --batch
python cleanup_files.py --project-dir /path/to/project --move-only  # Only move files to correct locations
```

### cleanup_backup_dirs.sh

A one-time cleanup script that removes unwanted directory-based backups created by the previous backup functionality.

Features:
- Finds all backup directories matching the pattern "backup_*"
- Displays the directories to be removed
- Asks for confirmation before removal
- Removes the backup directories

Usage:
```bash
./cleanup_backup_dirs.sh
```

### remove_local_backup_system.sh

Removes the local backup system components that have been replaced by the git-based backup system.

Features:
- Removes local backup configuration files
- Removes local backup scripts
- Removes local backup directories
- Updates references to use the git-based backup system

Usage:
```bash
./remove_local_backup_system.sh
```

## Safety Measures

All cleanup scripts implement the following safety measures:

1. **Confirmation**: Never delete or move files without explicit confirmation
2. **Backup**: Create backups of files before deletion or movement
3. **Logging**: Log all actions taken
4. **Rollback**: Provide a rollback mechanism for all operations
5. **Knowledge Graph**: Update the knowledge graph to reflect changes
6. **Special File Handling**: Preserve `__init__.py` files and keep `README.md` files in their directories

## Integration with Knowledge Graph

The cleanup utilities update the knowledge graph to reflect the changes made to the file system. This ensures that the knowledge graph remains the single source of truth for the project's structure.

## Integration with File Structure Standardization

The cleanup utilities work in conjunction with the file structure standardization system:

1. The file structure standardization system ensures files follow naming conventions and are in ideal directories
2. The cleanup utilities identify and remove orphaned or outdated files that are no longer needed

Together, these tools maintain a clean, well-organized codebase that follows best practices and standards.

## Best Practices

When using these cleanup utilities:

1. Always run with `--dry-run` first to see what would be changed
2. Use `--verbose` to get detailed information about the cleanup process
3. Consider using `--interactive` mode for fine-grained control over which files are affected
4. Always review the generated reports before applying changes
5. Ensure the knowledge graph is updated after cleanup operations
6. Run the file structure standardization script after cleanup to ensure complete compliance