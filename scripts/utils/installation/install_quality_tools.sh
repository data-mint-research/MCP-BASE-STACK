#!/bin/bash

# ============================================================================
# Quality Tools Installation Script
# ============================================================================
# This script installs additional quality tools that are not included in
# the requirements.txt file. It performs the following tasks:
#
# 1. Installs shellcheck for shell script linting
# 2. Installs shfmt for shell script formatting
# 3. Installs markdownlint for Markdown linting
# 4. Installs yamllint for YAML linting
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

# Function to check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

print_header "Installing Quality Tools"

# Install shellcheck
if ! command_exists shellcheck; then
    echo -e "Installing shellcheck..."
    
    if command_exists apt-get; then
        sudo apt-get update
        sudo apt-get install -y shellcheck
    elif command_exists brew; then
        brew install shellcheck
    elif command_exists dnf; then
        sudo dnf install -y shellcheck
    elif command_exists yum; then
        sudo yum install -y shellcheck
    else
        echo -e "${RED}Error: Could not install shellcheck. Please install it manually.${NC}"
        echo -e "Visit: https://github.com/koalaman/shellcheck#installing"
    fi
else
    echo -e "shellcheck is already installed."
fi

# Install shfmt
if ! command_exists shfmt; then
    echo -e "Installing shfmt..."
    
    if command_exists go; then
        go install mvdan.cc/sh/v3/cmd/shfmt@latest
    elif command_exists brew; then
        brew install shfmt
    else
        echo -e "${YELLOW}Warning: Could not install shfmt automatically.${NC}"
        echo -e "Installing via webinstall..."
        curl -sS https://webinstall.dev/shfmt | bash
    fi
else
    echo -e "shfmt is already installed."
fi

# Install markdownlint
if ! command_exists markdownlint; then
    echo -e "Installing markdownlint..."
    
    if command_exists npm; then
        npm install -g markdownlint-cli
    else
        echo -e "${RED}Error: npm is not installed. Please install Node.js and npm first.${NC}"
        echo -e "Visit: https://nodejs.org/en/download/"
    fi
else
    echo -e "markdownlint is already installed."
fi

# Install yamllint
if ! command_exists yamllint; then
    echo -e "Installing yamllint..."
    
    if command_exists pip; then
        pip install yamllint
    else
        echo -e "${RED}Error: pip is not installed. Please install Python and pip first.${NC}"
    fi
else
    echo -e "yamllint is already installed."
fi

print_header "Installation Complete"
echo -e "${GREEN}Quality tools have been successfully installed.${NC}"
echo -e "You can now run pre-commit hooks and quality checks."

exit 0