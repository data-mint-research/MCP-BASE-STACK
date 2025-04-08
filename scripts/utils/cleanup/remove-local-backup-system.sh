#!/bin/bash

# ============================================================================
# Local Backup System Removal Script
# ============================================================================
# This script completely removes all traces of the former local backup system,
# ensuring that only the git branch-based backup system remains.
# ============================================================================

set -e

echo "Starting removal of local backup system..."

# 1. Remove root-level backup directories
echo "Removing root-level backup directories..."
ROOT_BACKUP_DIRS=$(find . -maxdepth 1 -type d -name "backup_*")
if [ -n "$ROOT_BACKUP_DIRS" ]; then
    for dir in $ROOT_BACKUP_DIRS; do
        echo "  - Removing $dir"
        rm -rf "$dir"
    done
    echo "Root-level backup directories removed."
else
    echo "No root-level backup directories found."
fi

# 2. Remove data/backup/essential_files_* directories
echo "Removing data/backup/essential_files_* directories..."
DATA_BACKUP_DIRS=$(find data/backup -maxdepth 1 -type d -name "essential_files_*")
if [ -n "$DATA_BACKUP_DIRS" ]; then
    for dir in $DATA_BACKUP_DIRS; do
        echo "  - Removing $dir"
        rm -rf "$dir"
    done
    echo "Data backup directories removed."
else
    echo "No data backup directories found."
fi

# 3. Keep only .last_backup_branch in data/backup
echo "Ensuring only .last_backup_branch remains in data/backup..."
find data/backup -type f -not -name ".last_backup_branch" -exec rm -f {} \;
find data/backup -type d -not -path "data/backup" -exec rm -rf {} \;

# 4. Update documentation to remove references to local backup
echo "Updating backup-functionality.md to remove references to local backup..."
# This will be done separately with the write_to_file tool

echo "Local backup system removal completed."
echo "The git-based backup functionality is now the only backup method."
echo "Use scripts/utils/backup/create-backup-branch.sh to create backups."
echo "Use scripts/utils/backup/restore-from-backup.sh to restore from backups."

exit 0