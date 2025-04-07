#!/bin/bash

# ============================================================================
# Pre-commit Hooks Installation Script
# ============================================================================
# This script installs pre-commit hooks for code quality checks.
# It performs the following tasks:
#
# 1. Installs pre-commit if not already installed
# 2. Installs the pre-commit hooks defined in .pre-commit-config.yaml
# 3. Updates the existing Git hooks to include code quality checks
# ============================================================================

set -e

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print section headers
print_header() {
    echo -e "\n${YELLOW}========================================"
    echo -e "  $1"
    echo -e "========================================${NC}\n"
}

# Check if we're in the project root
if [ ! -f ".pre-commit-config.yaml" ]; then
    echo -e "${RED}Error: .pre-commit-config.yaml not found. This script must be run from the project root directory.${NC}"
    exit 1
fi

print_header "Installing Pre-commit Hooks"

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo -e "${RED}Error: pip is not installed. Please install Python and pip first.${NC}"
    exit 1
fi

# Install pre-commit if not already installed
if ! command -v pre-commit &> /dev/null; then
    echo -e "Installing pre-commit..."
    pip install pre-commit
else
    echo -e "pre-commit is already installed."
fi

# Install the pre-commit hooks
echo -e "Installing pre-commit hooks defined in .pre-commit-config.yaml..."
pre-commit install

# Install the Git hooks
print_header "Installing Git Hooks"

# Check if the .git-hooks directory exists
if [ ! -d ".git-hooks" ]; then
    echo -e "${RED}Error: .git-hooks directory not found.${NC}"
    exit 1
fi

# Check if the .git directory exists
if [ ! -d ".git" ]; then
    echo -e "${RED}Error: .git directory not found. Please run this script from a Git repository.${NC}"
    exit 1
fi

# Create hooks directory if it doesn't exist
mkdir -p .git/hooks

# Copy the pre-commit hook
cp .git-hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

echo -e "${GREEN}Pre-commit hook installed successfully.${NC}"

# Create a Git configuration to use our hooks directory
git config core.hooksPath .git-hooks

print_header "Installation Complete"
echo -e "${GREEN}Pre-commit hooks have been successfully installed.${NC}"
echo -e "The hooks will run automatically before each commit to ensure code quality."
echo -e "You can also run them manually with: ${YELLOW}pre-commit run --all-files${NC}"
echo -e "To fix code quality issues automatically, run: ${YELLOW}./fix_code_quality.sh${NC}"

exit 0