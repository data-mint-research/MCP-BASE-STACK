#!/bin/bash

# ============================================================================
# Unified Code Quality Check Script
# ============================================================================
# This script runs all code quality tools on the project:
# - Black (Python formatter)
# - isort (Python import sorter)
# - flake8 (Python linter)
# - mypy (Python type checker)
# - pylint (Python linter)
# - shellcheck (Shell script linter)
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
run_check() {
    local cmd="$1"
    local name="$2"
    
    print_header "Running $name"
    echo -e "Command: ${YELLOW}$cmd${NC}\n"
    
    if eval "$cmd"; then
        echo -e "\n${GREEN}✓ $name passed${NC}"
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

# Create a temporary file to store failures
FAILURES=$(mktemp)

# Find Python files
PYTHON_FILES=$(find . -type f -name "*.py" -not -path "*/\.*" -not -path "*/venv/*" -not -path "*/node_modules/*")
SHELL_FILES=$(find . -type f -name "*.sh" -not -path "*/\.*" -not -path "*/venv/*" -not -path "*/node_modules/*")

# Run Black (Python formatter)
if command -v black &> /dev/null; then
    run_check "black --check $PYTHON_FILES" "Black (Python formatter)" || echo "black" >> "$FAILURES"
else
    echo -e "${YELLOW}Warning: Black is not installed. Install with: pip install black${NC}"
    echo "black" >> "$FAILURES"
fi

# Run isort (Python import sorter)
if command -v isort &> /dev/null; then
    run_check "isort --check $PYTHON_FILES" "isort (Python import sorter)" || echo "isort" >> "$FAILURES"
else
    echo -e "${YELLOW}Warning: isort is not installed. Install with: pip install isort${NC}"
    echo "isort" >> "$FAILURES"
fi

# Run flake8 (Python linter)
if command -v flake8 &> /dev/null; then
    run_check "flake8 $PYTHON_FILES" "flake8 (Python linter)" || echo "flake8" >> "$FAILURES"
else
    echo -e "${YELLOW}Warning: flake8 is not installed. Install with: pip install flake8${NC}"
    echo "flake8" >> "$FAILURES"
fi

# Run mypy (Python type checker)
if command -v mypy &> /dev/null; then
    run_check "mypy $PYTHON_FILES" "mypy (Python type checker)" || echo "mypy" >> "$FAILURES"
else
    echo -e "${YELLOW}Warning: mypy is not installed. Install with: pip install mypy${NC}"
    echo "mypy" >> "$FAILURES"
fi

# Run pylint (Python linter)
if command -v pylint &> /dev/null; then
    run_check "pylint $PYTHON_FILES" "pylint (Python linter)" || echo "pylint" >> "$FAILURES"
else
    echo -e "${YELLOW}Warning: pylint is not installed. Install with: pip install pylint${NC}"
    echo "pylint" >> "$FAILURES"
fi

# Run shellcheck (Shell script linter)
if command -v shellcheck &> /dev/null; then
    run_check "shellcheck $SHELL_FILES" "shellcheck (Shell script linter)" || echo "shellcheck" >> "$FAILURES"
else
    echo -e "${YELLOW}Warning: shellcheck is not installed. Install with: sudo apt-get install shellcheck${NC}"
    echo "shellcheck" >> "$FAILURES"
fi

# Check if there were any failures
if [ -s "$FAILURES" ]; then
    print_header "Summary of Failures"
    echo -e "${RED}The following checks failed:${NC}"
    cat "$FAILURES" | while read -r line; do
        echo -e "  - $line"
    done
    
    print_header "How to Fix"
    echo -e "To automatically fix issues, run:"
    echo -e "${YELLOW}  ./scripts/utils/quality/fix_code_quality.sh${NC}"
    
    rm "$FAILURES"
    exit 1
else
    print_header "All Checks Passed"
    echo -e "${GREEN}All code quality checks passed successfully!${NC}"
    rm "$FAILURES"
    exit 0
fi