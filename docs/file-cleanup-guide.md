# File Cleanup Tool Guide

## Overview

The File Cleanup Tool is a utility for identifying and safely removing orphaned or outdated files in the project. It helps maintain a clean codebase by detecting:

- **Orphaned files**: Files not referenced by other files, not in the knowledge graph, and not expected based on the manifest
- **Outdated files**: Backups, old versions, temporary files, etc.
- **Duplicate files**: Files with identical content in different locations

## Usage

The cleanup tool can be run in different modes depending on your needs:

### Dry-run Mode

Preview files that would be cleaned up without making any changes:

```bash
python3 scripts/utils/cleanup/cleanup_files.py --project-dir . --manifest config/specifications/specification-manifest.json --dry-run
```

### Interactive Mode

Review and confirm each file deletion individually:

```bash
python3 scripts/utils/cleanup/cleanup_files.py --project-dir . --manifest config/specifications/specification-manifest.json --interactive
```

### Batch Mode

Clean up all identified files with a single confirmation:

```bash
python3 scripts/utils/cleanup/cleanup_files.py --project-dir . --manifest config/specifications/specification-manifest.json --batch
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

## Command-line Options

```
usage: scripts/utils/cleanup/cleanup_files.py [-h] --project-dir PROJECT_DIR --manifest MANIFEST [--output OUTPUT] [--verbose] [--dry-run] [--interactive] [--batch] [--backup-dir BACKUP_DIR]

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