#!/bin/bash

# ============================================================================
# Git Branch-Based Backup Script
# ============================================================================
# This script creates a new Git branch with a timestamp-based name and
# commits the current state to this branch as a backup before making changes.
# ============================================================================

# Check if we're in a Git repository
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo "Error: Not in a Git repository"
    exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "Error: Unable to determine current branch"
    exit 1
fi

# Create timestamp for branch name
TIMESTAMP=$(date '+%Y%m%d-%H%M%S')
BACKUP_BRANCH="backup-${TIMESTAMP}"

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "Warning: You have uncommitted changes"
    echo "These changes will be included in the backup branch"
fi

# Create backup branch
echo "Creating backup branch: ${BACKUP_BRANCH}"
if git checkout -b "${BACKUP_BRANCH}"; then
    # Stage all changes
    git add -A
    
    # Commit changes to backup branch
    if git commit -m "Backup commit before changes (${TIMESTAMP})"; then
        echo "Backup created successfully on branch: ${BACKUP_BRANCH}"
    else
        echo "Warning: No changes to commit or commit failed"
    fi
    
    # Return to original branch
    git checkout "${CURRENT_BRANCH}"
    echo "Returned to branch: ${CURRENT_BRANCH}"
    echo "You can now make your changes safely"
    echo "To restore from this backup later, run: ./restore-from-backup.sh ${BACKUP_BRANCH}"
else
    echo "Error: Failed to create backup branch"
    exit 1
fi

# Output the backup branch name for reference
echo "${BACKUP_BRANCH}" > data/backup/.last_backup_branch
echo "Backup branch name saved to data/backup/.last_backup_branch"

exit 0