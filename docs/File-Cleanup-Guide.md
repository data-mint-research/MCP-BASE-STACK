# File Cleanup Tool Guide

## Overview

The File Cleanup Tool is a utility for identifying and safely removing orphaned or outdated files in the project. It helps maintain a clean codebase by detecting:

- **Orphaned files**: Files not referenced by other files, not in the knowledge graph, and not expected based on the manifest
- **Outdated files**: Backups, old versions, temporary files, etc.
- **Duplicate files**: Files with identical content in different locations

## Current Status

The file structure has been fully standardized with:
- 100% naming convention compliance
- 100% directory structure compliance
- 249 total files properly organized

The cleanup tool works in conjunction with the file structure standardization system to ensure all files are properly named and located in their ideal directories.

## Usage

The cleanup tool can be run in different modes depending on your needs:

### Dry-run Mode

Preview files that would be cleaned up without making any changes:

```bash
python3 cleanup_files.py --project-dir . --manifest config/specifications/specification-manifest.json --dry-run
```

### Interactive Mode

Review and confirm each file deletion individually:

```bash
python3 cleanup_files.py --project-dir . --manifest config/specifications/specification-manifest.json --interactive
```

### Batch Mode

Clean up all identified files with a single confirmation:

```bash
python3 cleanup_files.py --project-dir . --manifest config/specifications/specification-manifest.json --batch
```

### Move-Only Mode

Only move files to their correct locations without deleting any files:

```bash
python3 cleanup_files.py --project-dir . --manifest config/specifications/specification-manifest.json --move-only
```

## Integration with Git Hooks

The cleanup tool is integrated with the pre-commit hook to automatically check for files that could be cleaned up before each commit. This integration:

1. Runs the cleanup tool in dry-run mode
2. Reports the number of files that could be cleaned up
3. Provides instructions for running the interactive cleanup

## Safety Features

The cleanup tool includes several safety features:

- **Automatic backups**: All files are backed up before deletion
- **Detailed logging**: All actions are logged for reference
- **Rollback capability**: Backups can be used to restore files if needed
- **Special file handling**: `__init__.py` files and `README.md` files are handled with special care

## Command-line Options

```
usage: cleanup_files.py [-h] --project-dir PROJECT_DIR --manifest MANIFEST [--output OUTPUT] [--verbose] [--dry-run] [--interactive] [--batch] [--backup-dir BACKUP_DIR] [--move-only]

Identify and clean up orphaned or outdated files.

options:
  -h, --help            show this help message and exit
  --project-dir PROJECT_DIR
                        Path to the project directory
  --manifest MANIFEST   Path to the specification manifest
  --output OUTPUT       Path to the output report file
  --verbose             Enable verbose logging
  --dry-run             Run in dry-run mode (don't actually delete files)
  --interactive         Run in interactive mode (confirm each deletion)
  --batch               Run in batch mode (apply all changes at once)
  --backup-dir BACKUP_DIR
                        Directory to store backups of files before deletion
  --move-only           Only move files to correct locations without deleting
```

## Integration with File Structure Standardization

The File Cleanup Tool works in conjunction with the file structure standardization system:

1. The file structure standardization system ensures files follow naming conventions and are in ideal directories
2. The File Cleanup Tool identifies and removes orphaned or outdated files that are no longer needed

Together, these tools maintain a clean, well-organized codebase that follows best practices and standards.

## Best Practices

1. **Run in dry-run mode first**: Always preview changes before applying them
2. **Use interactive mode for important files**: Confirm each deletion individually for critical files
3. **Keep the knowledge graph updated**: Ensure the knowledge graph reflects the current state of the file system
4. **Run regularly**: Make file cleanup part of your regular maintenance routine
5. **Combine with structure standardization**: Run both tools to ensure complete file system compliance