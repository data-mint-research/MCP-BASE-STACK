#!/bin/bash

# ============================================================================
# Backup Directory Cleanup Script
# ============================================================================
# This script removes the unwanted directory-based backups created by the
# previous backup functionality. It's a one-time cleanup script.
# ============================================================================

echo "Cleaning up unwanted backup directories..."

# List of backup directories to remove
BACKUP_DIRS=$(find . -maxdepth 1 -type d -name "backup_*")

if [ -z "$BACKUP_DIRS" ]; then
    echo "No backup directories found."
    exit 0
fi

echo "The following backup directories will be removed:"
for dir in $BACKUP_DIRS; do
    echo "  - $dir"
done

# Ask for confirmation
read -p "Do you want to proceed with removal? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

# Remove the backup directories
for dir in $BACKUP_DIRS; do
    echo "Removing $dir..."
    rm -rf "$dir"
done

echo "Backup directories have been removed."
echo "The git-based backup functionality (create-backup-branch.sh) is now the only backup method."
echo "Use ./restore-from-backup.sh to restore from git-based backups."

exit 0