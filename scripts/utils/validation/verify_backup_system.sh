#!/bin/bash

# ============================================================================
# Backup System Verification Script
# ============================================================================
# This script verifies that the git branch-based backup system is working
# correctly and that all traces of the local backup system have been removed.
# ============================================================================

set -e

echo "Starting backup system verification..."

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a directory exists
check_directory_exists() {
    if [ -d "$1" ]; then
        echo -e "${RED}✗ Directory still exists: $1${NC}"
        return 1
    else
        echo -e "${GREEN}✓ Directory removed: $1${NC}"
        return 0
    fi
}

# Function to check if a file exists
check_file_exists() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓ File exists: $1${NC}"
        return 0
    else
        echo -e "${RED}✗ File missing: $1${NC}"
        return 1
    fi
}

# Function to check if a string is in a file
check_string_in_file() {
    if grep -q "$2" "$1"; then
        echo -e "${RED}✗ String '$2' found in file: $1${NC}"
        return 1
    else
        echo -e "${GREEN}✓ String '$2' not found in file: $1${NC}"
        return 0
    fi
}

# Function to test git-based backup
test_git_backup() {
    echo -e "\n${BLUE}Testing git-based backup system...${NC}"
    
    # Create a test file
    echo "Test file for backup verification" > test_backup_file.txt
    
    # Create a backup
    if ./scripts/utils/backup/create_backup_branch.sh; then
        echo -e "${GREEN}✓ Successfully created backup branch${NC}"
        
        # Get the backup branch name
        BACKUP_BRANCH=$(cat data/backup/.last_backup_branch)
        echo -e "${BLUE}Backup branch: ${BACKUP_BRANCH}${NC}"
        
        # Modify the test file
        echo "Modified content" > test_backup_file.txt
        
        # Restore from backup
        if ./scripts/utils/backup/restore_from_backup.sh "$BACKUP_BRANCH" test_backup_file.txt; then
            # Check if the file was restored correctly
            if grep -q "Test file for backup verification" test_backup_file.txt; then
                echo -e "${GREEN}✓ Successfully restored file from backup${NC}"
                rm test_backup_file.txt
                return 0
            else
                echo -e "${RED}✗ File content was not restored correctly${NC}"
                rm test_backup_file.txt
                return 1
            fi
        else
            echo -e "${RED}✗ Failed to restore from backup${NC}"
            rm test_backup_file.txt
            return 1
        fi
    else
        echo -e "${RED}✗ Failed to create backup branch${NC}"
        rm test_backup_file.txt
        return 1
    fi
}

echo -e "\n${BLUE}Checking for local backup directories...${NC}"
# Check root-level backup directories
ROOT_BACKUP_DIRS=$(find . -maxdepth 1 -type d -name "backup_*")
if [ -n "$ROOT_BACKUP_DIRS" ]; then
    echo -e "${RED}✗ Root-level backup directories still exist:${NC}"
    for dir in $ROOT_BACKUP_DIRS; do
        echo "  - $dir"
    done
    VERIFICATION_FAILED=true
else
    echo -e "${GREEN}✓ No root-level backup directories found${NC}"
fi

# Check data/backup/essential_files_* directories
DATA_BACKUP_DIRS=$(find data/backup -maxdepth 1 -type d -name "essential_files_*" 2>/dev/null || true)
if [ -n "$DATA_BACKUP_DIRS" ]; then
    echo -e "${RED}✗ Data backup directories still exist:${NC}"
    for dir in $DATA_BACKUP_DIRS; do
        echo "  - $dir"
    done
    VERIFICATION_FAILED=true
else
    echo -e "${GREEN}✓ No data backup directories found${NC}"
fi

echo -e "\n${BLUE}Checking for required git backup files...${NC}"
# Check that required files exist
check_file_exists "scripts/utils/backup/create_backup_branch.sh" || VERIFICATION_FAILED=true
check_file_exists "scripts/utils/backup/restore_from_backup.sh" || VERIFICATION_FAILED=true
check_file_exists "data/backup/.last_backup_branch" || VERIFICATION_FAILED=true

echo -e "\n${BLUE}Checking documentation for local backup references...${NC}"
# Check documentation for references to local backup
if [ -f "docs/backup-functionality.md" ]; then
    check_string_in_file "docs/backup-functionality.md" "directory-based backup" || VERIFICATION_FAILED=true
    check_string_in_file "docs/backup-functionality.md" "local backup" || VERIFICATION_FAILED=true
    check_string_in_file "docs/backup-functionality.md" "cleanup_backup_dirs.sh" || VERIFICATION_FAILED=true
else
    echo -e "${RED}✗ docs/backup-functionality.md file not found${NC}"
    VERIFICATION_FAILED=true
fi

echo -e "\n${BLUE}Testing git-based backup system...${NC}"
# Test git-based backup
test_git_backup || VERIFICATION_FAILED=true

# Final verification result
echo -e "\n${BLUE}Verification complete.${NC}"
if [ "$VERIFICATION_FAILED" = true ]; then
    echo -e "${RED}✗ Verification failed. Some issues were found.${NC}"
    echo -e "${YELLOW}Please run the removal script again to fix these issues.${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Verification successful. The git-based backup system is working correctly.${NC}"
    echo -e "${GREEN}✓ All traces of the local backup system have been removed.${NC}"
    exit 0
fi