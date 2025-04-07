#!/bin/bash

# ============================================================================
# Git Branch-Based Restore Script
# ============================================================================
# This script restores files from a backup branch created by
# create_backup_branch.sh. It can either restore specific files or
# perform a complete restore of all files.
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

# Check for backup branch argument
if [ -z "$1" ]; then
    # Try to read from .last_backup_branch file
    if [ -f ".last_backup_branch" ]; then
        BACKUP_BRANCH=$(cat .last_backup_branch)
        echo "Using backup branch from .last_backup_branch: ${BACKUP_BRANCH}"
    else
        echo "Error: No backup branch specified"
        echo "Usage: $0 <backup-branch-name> [file1 file2 ...]"
        echo "Example: $0 backup-20250407-153842"
        echo "Example: $0 backup-20250407-153842 file1.txt file2.js"
        exit 1
    fi
else
    BACKUP_BRANCH="$1"
fi

# Check if backup branch exists
if ! git show-ref --verify --quiet "refs/heads/${BACKUP_BRANCH}"; then
    echo "Error: Backup branch '${BACKUP_BRANCH}' does not exist"
    echo "Available branches:"
    git branch | grep "backup-"
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "Warning: You have uncommitted changes"
    echo "Automatically continuing with restore (for testing purposes)"
    # For production, uncomment the following lines to ask for confirmation
    # read -p "Do you want to continue and overwrite these changes? (y/n) " -n 1 -r
    # echo
    # if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    #     echo "Restore cancelled"
    #     exit 0
    # fi
fi

# Determine if specific files should be restored
if [ $# -gt 1 ]; then
    # Restore specific files
    echo "Restoring specific files from ${BACKUP_BRANCH}..."
    
    # Create a temporary branch for the restore operation
    TEMP_BRANCH="temp-restore-${RANDOM}"
    git checkout -b "${TEMP_BRANCH}"
    
    # Checkout files from backup branch
    shift # Remove the first argument (backup branch name)
    for file in "$@"; do
        if git checkout "${BACKUP_BRANCH}" -- "${file}"; then
            echo "Restored: ${file}"
        else
            echo "Failed to restore: ${file}"
        fi
    done
    
    # Return to original branch
    git checkout "${CURRENT_BRANCH}"
    git branch -D "${TEMP_BRANCH}"
else
    # Full restore
    echo "Performing full restore from ${BACKUP_BRANCH}..."
    
    # Create a new branch for the restored state
    RESTORE_BRANCH="restored-from-${BACKUP_BRANCH}"
    
    # Check if restore branch already exists
    if git show-ref --verify --quiet "refs/heads/${RESTORE_BRANCH}"; then
        echo "Warning: Restore branch '${RESTORE_BRANCH}' already exists"
        echo "Automatically overwriting existing branch (for testing purposes)"
        # For production, uncomment the following lines to ask for confirmation
        # read -p "Do you want to overwrite it? (y/n) " -n 1 -r
        # echo
        # if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        #     echo "Restore cancelled"
        #     exit 0
        # fi
        git branch -D "${RESTORE_BRANCH}"
    fi
    
    # Create restore branch from backup
    if git checkout -b "${RESTORE_BRANCH}" "${BACKUP_BRANCH}"; then
        echo "Successfully restored to branch: ${RESTORE_BRANCH}"
        echo "You are now on branch: ${RESTORE_BRANCH}"
        echo "To return to your original branch, run: git checkout ${CURRENT_BRANCH}"
    else
        echo "Error: Failed to restore from backup branch"
        exit 1
    fi
fi

exit 0