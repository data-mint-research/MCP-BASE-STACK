#!/bin/bash
# Pre-commit hook to check for vulnerable dependencies
# This script runs the dependency audit script and fails if vulnerable dependencies are found

set -e

echo "Running dependency vulnerability check..."

# Get the project root directory
PROJECT_ROOT=$(git rev-parse --show-toplevel)

# Check if any dependency files were modified
DEPENDENCY_FILES=$(git diff --cached --name-only | grep -E '(requirements\.txt|package\.json|docker-compose\.yml|pom\.xml|build\.gradle)')

if [ -z "$DEPENDENCY_FILES" ]; then
    echo "No dependency files modified, skipping vulnerability check."
    exit 0
fi

echo "Dependency files modified, checking for vulnerabilities..."

# Run the dependency audit script
cd "$PROJECT_ROOT"
python scripts/utils/maintenance/audit_dependencies.py --verbose

# Check if there are any vulnerable dependencies
VULNERABLE_COUNT=$(jq '.summary.vulnerable_dependencies' data/reports/dependency-audit-report.json)

if [ "$VULNERABLE_COUNT" -gt 0 ]; then
    echo "ERROR: $VULNERABLE_COUNT vulnerable dependencies found!"
    echo "See data/reports/dependency-audit-report.json for details."
    echo "Fix the vulnerabilities before committing or use --no-verify to bypass this check."
    exit 1
fi

echo "No vulnerable dependencies found."
exit 0