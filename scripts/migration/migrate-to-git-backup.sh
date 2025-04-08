#!/bin/bash

# ============================================================================
# Backup System Migration Script
# ============================================================================
# This script orchestrates the migration from the local backup system to the
# git branch-based backup system, removing all traces of the former backup
# routine and ensuring the git-based backup system works correctly.
# ============================================================================

set -e

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print section headers
print_header() {
    echo -e "\n${YELLOW}========================================"
    echo -e "  $1"
    echo -e "========================================${NC}\n"
}

# Function to check if a command succeeded
check_success() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $1 completed successfully${NC}"
    else
        echo -e "${RED}✗ $1 failed${NC}"
        exit 1
    fi
}

# Make scripts executable
chmod +x scripts/utils/cleanup/remove-local-backup-system.sh
chmod +x data_sources/knowledge_graph/scripts/remove_backup_references.py
chmod +x scripts/utils/validation/verify-backup-system.sh
chmod +x scripts/utils/backup/create-backup-branch.sh
chmod +x scripts/utils/backup/restore-from-backup.sh

# Step 1: Create a git backup of the current state
print_header "Step 1: Creating a git backup of the current state"
./scripts/utils/backup/create-backup-branch.sh
check_success "Git backup creation"

# Step 2: Remove local backup system
print_header "Step 2: Removing local backup system"
./scripts/utils/cleanup/remove-local-backup-system.sh
check_success "Local backup system removal"

# Step 3: Update documentation
print_header "Step 3: Documentation has been updated"
echo -e "${BLUE}The backup-functionality.md file has been updated to remove references to the local backup system.${NC}"

# Step 4: Update Knowledge Graph
print_header "Step 4: Updating Knowledge Graph"
python3 data_sources/knowledge_graph/scripts/remove_backup_references.py
check_success "Knowledge Graph update"

# Step 5: Verify the changes
print_header "Step 5: Verifying the changes"
./scripts/utils/validation/verify-backup-system.sh
check_success "Verification"

print_header "Migration Complete"
echo -e "${GREEN}The migration to the git branch-based backup system is complete.${NC}"
echo -e "${GREEN}All traces of the former backup routine have been removed.${NC}"
echo -e "${GREEN}The git-based backup system is working correctly.${NC}"

echo -e "\n${BLUE}To create a backup:${NC}"
echo -e "  ./scripts/utils/backup/create-backup-branch.sh"

echo -e "\n${BLUE}To restore from a backup:${NC}"
echo -e "  ./scripts/utils/backup/restore-from-backup.sh [backup-branch-name] [file1 file2 ...]"

exit 0