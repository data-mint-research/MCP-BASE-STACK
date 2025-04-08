#!/bin/bash

# ============================================================================
# Enhanced Automatic Code Quality Fix Script
# ============================================================================
# This script automatically fixes code quality issues using:
# - Black (Python formatter)
# - isort (Python import sorter)
# - autopep8 (Python code fixer for flake8 issues)
# - shfmt (Shell script formatter)
# - prettier (JavaScript/TypeScript/JSON/CSS/YAML/Markdown formatter)
# ============================================================================

set -e

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Define paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SPEC_MANIFEST="$PROJECT_ROOT/config/specifications/specification-manifest.json"
REPORT_DIR="$PROJECT_ROOT/data/reports"
REPORT_FILE="$REPORT_DIR/code_quality_fixes_report.json"
KG_PATH="$PROJECT_ROOT/core/kg/data/knowledge_graph.graphml"

# Ensure report directory exists
mkdir -p "$REPORT_DIR"

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
    local category="$3"
    local file_pattern="$4"
    
    print_header "Running $name"
    echo -e "Command: ${YELLOW}$cmd${NC}\n"
    
    # Create a temporary file to store the output
    local output_file=$(mktemp)
    
    if eval "$cmd" > "$output_file" 2>&1; then
        echo -e "\n${GREEN}✓ $name completed${NC}"
        # Add to report as success
        add_to_report "$name" "$category" "success" "$(cat "$output_file")" "$file_pattern"
        rm "$output_file"
        return 0
    else
        echo -e "\n${RED}✗ $name failed${NC}"
        # Display the output
        cat "$output_file"
        # Add to report as failure
        add_to_report "$name" "$category" "failure" "$(cat "$output_file")" "$file_pattern"
        echo "$name" >> "$FAILURES"
        rm "$output_file"
        return 1
    fi
}

# Function to add a result to the JSON report
add_to_report() {
    local tool="$1"
    local category="$2"
    local status="$3"
    local output="$4"
    local file_pattern="$5"
    
    # Escape special characters for JSON
    output=$(echo "$output" | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')
    
    # Add to the report array
    REPORT_DATA+="{\"tool\":\"$tool\",\"category\":\"$category\",\"status\":\"$status\",\"output\":\"$output\",\"file_pattern\":\"$file_pattern\"},"
}

# Function to load standards from specification manifest
load_standards() {
    if [ ! -f "$SPEC_MANIFEST" ]; then
        echo -e "${RED}Error: Specification manifest not found at $SPEC_MANIFEST${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}Loading standards from specification manifest...${NC}"
    
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        echo -e "${YELLOW}Warning: jq is not installed. Using default standards.${NC}"
        echo -e "${YELLOW}Install jq with: sudo apt-get install jq${NC}"
        
        # Set default values
        PYTHON_NAMING="snake_case.py"
        SHELL_NAMING="kebab-case.sh"
        MARKDOWN_NAMING="kebab-case.md"
        YAML_NAMING="kebab-case.yaml or kebab-case.yml"
        
        echo -e "Using default naming conventions:"
        echo -e "Python modules naming convention: ${BLUE}$PYTHON_NAMING${NC}"
        echo -e "Shell scripts naming convention: ${BLUE}$SHELL_NAMING${NC}"
        echo -e "Markdown files naming convention: ${BLUE}$MARKDOWN_NAMING${NC}"
        echo -e "YAML files naming convention: ${BLUE}$YAML_NAMING${NC}"
        
        echo -e "\nUsing default code patterns for applying fixes."
        return
    fi
    
    # Extract naming conventions for different file types
    PYTHON_NAMING=$(jq -r '.specification_manifest.naming_conventions.python.modules.pattern' "$SPEC_MANIFEST")
    SHELL_NAMING=$(jq -r '.specification_manifest.naming_conventions.shell.scripts.pattern' "$SPEC_MANIFEST")
    MARKDOWN_NAMING=$(jq -r '.specification_manifest.naming_conventions.documentation.markdown_files.pattern' "$SPEC_MANIFEST")
    YAML_NAMING=$(jq -r '.specification_manifest.naming_conventions.configuration.yaml_files.pattern' "$SPEC_MANIFEST")
    
    echo -e "Python modules naming convention: ${BLUE}$PYTHON_NAMING${NC}"
    echo -e "Shell scripts naming convention: ${BLUE}$SHELL_NAMING${NC}"
    echo -e "Markdown files naming convention: ${BLUE}$MARKDOWN_NAMING${NC}"
    echo -e "YAML files naming convention: ${BLUE}$YAML_NAMING${NC}"
    
    # Extract code patterns
    PYTHON_MODULE_HEADER=$(jq -r '.specification_manifest.code_patterns.python.module_header.template' "$SPEC_MANIFEST")
    SHELL_SCRIPT_HEADER=$(jq -r '.specification_manifest.code_patterns.shell.script_header.template' "$SPEC_MANIFEST")
    
    echo -e "\nLoaded code patterns for applying fixes."
}

# Function to initialize the JSON report
init_report() {
    mkdir -p "$REPORT_DIR"
    
    # Start the JSON report
    echo "{" > "$REPORT_FILE"
    echo "  \"timestamp\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"," >> "$REPORT_FILE"
    echo "  \"results\": [" >> "$REPORT_FILE"
    
    # Initialize the report data array
    REPORT_DATA=""
}

# Function to finalize the JSON report
finalize_report() {
    # Remove the trailing comma if there are results
    if [ -n "$REPORT_DATA" ]; then
        REPORT_DATA=${REPORT_DATA%,}
    fi
    
    # Add the report data to the file
    echo "$REPORT_DATA" >> "$REPORT_FILE"
    
    # Close the JSON structure
    echo "  ]," >> "$REPORT_FILE"
    
    # Add summary information
    echo "  \"summary\": {" >> "$REPORT_FILE"
    echo "    \"total_fixes\": $TOTAL_FIXES," >> "$REPORT_FILE"
    echo "    \"successful\": $((TOTAL_FIXES - $(wc -l < "$FAILURES")))," >> "$REPORT_FILE"
    echo "    \"failed\": $(wc -l < "$FAILURES")," >> "$REPORT_FILE"
    echo "    \"categories\": {" >> "$REPORT_FILE"
    
    # Add category counts
    for category in "${!CATEGORY_COUNTS[@]}"; do
        echo "      \"$category\": ${CATEGORY_COUNTS[$category]}," >> "$REPORT_FILE"
    done
    
    # Remove the trailing comma from the last category
    sed -i '$ s/,$//' "$REPORT_FILE"
    
    echo "    }" >> "$REPORT_FILE"
    echo "  }" >> "$REPORT_FILE"
    echo "}" >> "$REPORT_FILE"
    
    echo -e "\n${GREEN}Fix report generated at $REPORT_FILE${NC}"
}

# Function to update the knowledge graph
update_knowledge_graph() {
    if [ ! -f "$KG_PATH" ]; then
        echo -e "${YELLOW}Warning: Knowledge graph not found at $KG_PATH. Skipping update.${NC}"
        return
    fi
    
    echo -e "\n${BLUE}Updating knowledge graph with code quality fixes...${NC}"
    
    # Run the Python script to update the knowledge graph
    python3 "$SCRIPT_DIR/check_code_quality_nodes.py" --report "$REPORT_FILE" --fixes
    
    echo -e "${GREEN}Knowledge graph updated successfully.${NC}"
}

# Check if we're in the project root
if [ ! -f "config/pyproject.toml" ] || [ ! -f "config/linting/.flake8" ]; then
    echo -e "${RED}Error: This script must be run from the project root directory${NC}"
    exit 1
fi

# Load standards from specification manifest
load_standards

# Initialize the report
init_report

# Create a temporary file to store failures
FAILURES=$(mktemp)

# Initialize category counts
declare -A CATEGORY_COUNTS
CATEGORY_COUNTS["python"]=0
CATEGORY_COUNTS["shell"]=0
CATEGORY_COUNTS["markdown"]=0
CATEGORY_COUNTS["yaml"]=0
CATEGORY_COUNTS["json"]=0
CATEGORY_COUNTS["general"]=0

# Initialize total fixes counter
TOTAL_FIXES=0

# Find files by type
PYTHON_FILES=$(find . -type f -name "*.py" -not -path "*/\.*" -not -path "*/venv/*" -not -path "*/node_modules/*")
SHELL_FILES=$(find . -type f -name "*.sh" -not -path "*/\.*" -not -path "*/venv/*" -not -path "*/node_modules/*")
MARKDOWN_FILES=$(find . -type f -name "*.md" -not -path "*/\.*" -not -path "*/venv/*" -not -path "*/node_modules/*")
YAML_FILES=$(find . -type f -name "*.yml" -o -name "*.yaml" -not -path "*/\.*" -not -path "*/venv/*" -not -path "*/node_modules/*")
JSON_FILES=$(find . -type f -name "*.json" -not -path "*/\.*" -not -path "*/venv/*" -not -path "*/node_modules/*")
JS_TS_FILES=$(find . -type f \( -name "*.js" -o -name "*.ts" -o -name "*.jsx" -o -name "*.tsx" \) -not -path "*/\.*" -not -path "*/venv/*" -not -path "*/node_modules/*")
CSS_FILES=$(find . -type f \( -name "*.css" -o -name "*.scss" -o -name "*.sass" \) -not -path "*/\.*" -not -path "*/venv/*" -not -path "*/node_modules/*")

# Python fixes
if [ -n "$PYTHON_FILES" ]; then
    # Run isort (Python import sorter)
    if command -v isort &> /dev/null; then
        run_fix "isort $PYTHON_FILES" "isort (Python import sorter)" "python" "*.py"
        ((TOTAL_FIXES++))
        ((CATEGORY_COUNTS["python"]++))
    else
        echo -e "${YELLOW}Warning: isort is not installed. Install with: pip install isort${NC}"
        add_to_report "isort (Python import sorter)" "python" "skipped" "Not installed" "*.py"
    fi

    # Run Black (Python formatter)
    if command -v black &> /dev/null; then
        run_fix "black $PYTHON_FILES" "Black (Python formatter)" "python" "*.py"
        ((TOTAL_FIXES++))
        ((CATEGORY_COUNTS["python"]++))
    else
        echo -e "${YELLOW}Warning: Black is not installed. Install with: pip install black${NC}"
        add_to_report "Black (Python formatter)" "python" "skipped" "Not installed" "*.py"
    fi

    # Run autopep8 (Python code fixer for flake8 issues)
    if command -v autopep8 &> /dev/null; then
        run_fix "autopep8 --in-place --aggressive --aggressive $PYTHON_FILES" "autopep8 (Python code fixer)" "python" "*.py"
        ((TOTAL_FIXES++))
        ((CATEGORY_COUNTS["python"]++))
    else
        echo -e "${YELLOW}Warning: autopep8 is not installed. Install with: pip install autopep8${NC}"
        add_to_report "autopep8 (Python code fixer)" "python" "skipped" "Not installed" "*.py"
    fi
    
    # Run autoflake (Remove unused imports and variables)
    if command -v autoflake &> /dev/null; then
        run_fix "autoflake --in-place --remove-all-unused-imports --remove-unused-variables $PYTHON_FILES" "autoflake (Python unused code remover)" "python" "*.py"
        ((TOTAL_FIXES++))
        ((CATEGORY_COUNTS["python"]++))
    else
        echo -e "${YELLOW}Warning: autoflake is not installed. Install with: pip install autoflake${NC}"
        add_to_report "autoflake (Python unused code remover)" "python" "skipped" "Not installed" "*.py"
    fi
fi

# Shell script fixes
if [ -n "$SHELL_FILES" ]; then
    # Run shfmt (Shell script formatter)
    if command -v shfmt &> /dev/null; then
        run_fix "shfmt -w $SHELL_FILES" "shfmt (Shell script formatter)" "shell" "*.sh"
        ((TOTAL_FIXES++))
        ((CATEGORY_COUNTS["shell"]++))
    else
        echo -e "${YELLOW}Warning: shfmt is not installed. Install with: go install mvdan.cc/sh/v3/cmd/shfmt@latest${NC}"
        add_to_report "shfmt (Shell script formatter)" "shell" "skipped" "Not installed" "*.sh"
    fi
fi

# Prettier fixes for various file types
if command -v prettier &> /dev/null; then
    # JavaScript/TypeScript
    if [ -n "$JS_TS_FILES" ]; then
        run_fix "prettier --write $JS_TS_FILES" "prettier (JS/TS formatter)" "javascript" "*.js,*.ts,*.jsx,*.tsx"
        ((TOTAL_FIXES++))
        ((CATEGORY_COUNTS["javascript"]++))
    fi
    
    # JSON
    if [ -n "$JSON_FILES" ]; then
        run_fix "prettier --write $JSON_FILES" "prettier (JSON formatter)" "json" "*.json"
        ((TOTAL_FIXES++))
        ((CATEGORY_COUNTS["json"]++))
    fi
    
    # CSS
    if [ -n "$CSS_FILES" ]; then
        run_fix "prettier --write $CSS_FILES" "prettier (CSS formatter)" "css" "*.css,*.scss,*.sass"
        ((TOTAL_FIXES++))
        ((CATEGORY_COUNTS["css"]++))
    fi
    
    # YAML
    if [ -n "$YAML_FILES" ]; then
        run_fix "prettier --write $YAML_FILES" "prettier (YAML formatter)" "yaml" "*.yml,*.yaml"
        ((TOTAL_FIXES++))
        ((CATEGORY_COUNTS["yaml"]++))
    fi
    
    # Markdown
    if [ -n "$MARKDOWN_FILES" ]; then
        run_fix "prettier --write $MARKDOWN_FILES" "prettier (Markdown formatter)" "markdown" "*.md"
        ((TOTAL_FIXES++))
        ((CATEGORY_COUNTS["markdown"]++))
    fi
else
    echo -e "${YELLOW}Warning: prettier is not installed. Install with: npm install -g prettier${NC}"
    add_to_report "prettier" "general" "skipped" "Not installed" "multiple"
fi

# Finalize the report
finalize_report

# Update the knowledge graph
update_knowledge_graph

print_header "Fix Complete"
echo -e "${GREEN}Automatic fixes have been applied.${NC}"
echo -e "Run ${YELLOW}./scripts/utils/quality/check_code_quality.sh${NC} to verify all issues are fixed."
echo -e "For more granular control, run:"
echo -e "${YELLOW}  python3 ./scripts/utils/quality/enforce_code_standards.py --check${NC}"
echo -e "Some issues may require manual fixes, especially for mypy, pylint, and shellcheck."
echo -e "A detailed report of applied fixes is available at: ${BLUE}$REPORT_FILE${NC}"

exit 0