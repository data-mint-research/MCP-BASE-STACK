# Backup Functionality

## Overview

This document describes the backup functionality used in the MCP-BASE-STACK project. The system uses a git branch-based backup approach to create snapshots before making changes to the codebase.

## Git Branch-Based Backup

The git branch-based backup functionality creates a new git branch with a timestamp-based name and commits the current state to this branch as a backup before making changes. This approach has several advantages:

- **Version Control Integration**: Backups are integrated with the git version control system
- **Space Efficiency**: Only stores the differences between versions
- **Selective Restoration**: Can restore specific files or the entire project
- **History Preservation**: Maintains a history of backups as git branches

## Scripts

### create-backup-branch.sh

This script creates a new git branch with a timestamp-based name (e.g., `backup-20250408-024358`) and commits the current state to this branch as a backup before making changes.

Usage:
```bash
./scripts/utils/backup/create-backup-branch.sh
```

The script:
1. Creates a new git branch with a timestamp-based name
2. Commits the current state to this branch
3. Returns to the original branch
4. Saves the backup branch name to `data/backup/.last_backup_branch` for reference

### restore-from-backup.sh

This script restores files from a backup branch created by `create-backup-branch.sh`. It can either restore specific files or perform a complete restore of all files.

Usage:
```bash
# Restore from the most recent backup (using data/backup/.last_backup_branch)
./scripts/utils/backup/restore-from-backup.sh

# Restore from a specific backup branch
./scripts/utils/backup/restore-from-backup.sh backup-20250408-024358

# Restore specific files from a backup branch
./scripts/utils/backup/restore-from-backup.sh backup-20250408-024358 file1.py file2.sh
```

The script:
1. Checks if a backup branch exists
2. For specific file restoration: Creates a temporary branch, restores the specified files, then returns to the original branch
3. For full restoration: Creates a new branch from the backup branch

## Integration with Quality Tools

The backup functionality is integrated with the quality tools:

- `scripts/utils/quality/fix-code-quality.sh` creates a git branch-based backup before applying fixes
- `scripts/utils/quality/check-code-quality.sh` excludes backup directories from analysis