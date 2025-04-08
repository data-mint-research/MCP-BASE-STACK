#!/bin/bash

# ============================================================================
# Automatic Code Quality Fix Script
# ============================================================================
# This script automatically fixes code quality issues using:
# - Black (Python formatter)
# - isort (Python import sorter)
# - autopep8 (Python code fixer for flake8 issues)
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

# Function to run a command and check its exit status
run_fix() {
    local cmd="$1"
    local name="$2"
    
    print_header "Running $name"
    echo -e "Command: ${YELLOW}$cmd${NC}\n"
    
    if eval "$cmd"; then
        echo -e "\n${GREEN}✓ $name completed${NC}"
        return 0
    else
        echo -e "\n${RED}✗ $name failed${NC}"
        return 1
    fi
}

# Check if we're in the project root
if [ ! -f "config/pyproject.toml" ] || [ ! -f "config/linting/.flake8" ]; then
    echo -e "${RED}Error: This script must be run from the project root directory${NC}"
    exit 1
fi

# Find Python files
PYTHON_FILES=$(find . -type f -name "*.py" -not -path "*/\.*" -not -path "*/venv/*" -not -path "*/node_modules/*")
SHELL_FILES=$(find . -type f -name "*.sh" -not -path "*/\.*" -not -path "*/venv/*" -not -path "*/node_modules/*")

# Run isort (Python import sorter)
if command -v isort &> /dev/null; then
    run_fix "isort $PYTHON_FILES" "isort (Python import sorter)"
else
    echo -e "${YELLOW}Warning: isort is not installed. Install with: pip install isort${NC}"
fi

# Run Black (Python formatter)
if command -v black &> /dev/null; then
    run_fix "black $PYTHON_FILES" "Black (Python formatter)"
else
    echo -e "${YELLOW}Warning: Black is not installed. Install with: pip install black${NC}"
fi

# Run autopep8 (Python code fixer for flake8 issues)
if command -v autopep8 &> /dev/null; then
    run_fix "autopep8 --in-place --aggressive --aggressive $PYTHON_FILES" "autopep8 (Python code fixer)"
else
    echo -e "${YELLOW}Warning: autopep8 is not installed. Install with: pip install autopep8${NC}"
fi

print_header "Fix Complete"
echo -e "${GREEN}Automatic fixes have been applied.${NC}"
echo -e "Run ${YELLOW}./scripts/utils/quality/check_code_quality.sh${NC} to verify all issues are fixed."
echo -e "Some issues may require manual fixes, especially for mypy, pylint, and shellcheck."

exit 0