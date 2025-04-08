#!/bin/bash
# MCP Migration Orchestration Script
# This script executes the MCP migration workflow

set -e  # Exit on error

# Script constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STRUCTURE_FILE="${SCRIPT_DIR}/structure.yaml"
PROMPT_CHAIN_FILE="${SCRIPT_DIR}/prompt-chain.yaml"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
LOG_DIR="${PROJECT_ROOT}/logs/migration"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${LOG_DIR}/mcp_migration_${TIMESTAMP}.log"
OUTPUT_DIR="${PROJECT_ROOT}/data/migration/mcp"

# Color codes for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create necessary directories
mkdir -p "${LOG_DIR}"
mkdir -p "${OUTPUT_DIR}"

# Initialize log file
echo "MCP Migration Log - ${TIMESTAMP}" > "${LOG_FILE}"
echo "===================================" >> "${LOG_FILE}"

# Function to log messages
log() {
    local level=$1
    local message=$2
    local color=$NC
    
    case $level in
        "INFO") color=$BLUE ;;
        "SUCCESS") color=$GREEN ;;
        "WARNING") color=$YELLOW ;;
        "ERROR") color=$RED ;;
    esac
    
    echo -e "${color}[$(date +"%Y-%m-%d %H:%M:%S")] [${level}] ${message}${NC}"
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] [${level}] ${message}" >> "${LOG_FILE}"
}

# Function to check if a file exists
check_file() {
    local file=$1
    if [ ! -f "$file" ]; then
        log "ERROR" "File not found: $file"
        exit 1
    fi
}

# Function to get user approval
get_approval() {
    local message=$1
    echo -e "${YELLOW}"
    echo "========================================================"
    echo "$message"
    echo "========================================================"
    echo -e "${NC}"
    read -p "Do you want to proceed? (y/n): " choice
    case "$choice" in
        y|Y ) return 0 ;;
        * ) return 1 ;;
    esac
}

# Function to run a prompt in the workflow
run_prompt() {
    local prompt_id=$1
    local input_file=$2
    local output_file="${OUTPUT_DIR}/${prompt_id}_output.json"
    
    log "INFO" "Running prompt: ${prompt_id}"
    
    # Extract prompt details from prompt-chain.yaml
    local prompt_name=$(grep -A 1 "id: \"${prompt_id}\"" "${PROMPT_CHAIN_FILE}" | grep "name:" | sed 's/.*name: "\(.*\)".*/\1/')
    local prompt_description=$(grep -A 2 "id: \"${prompt_id}\"" "${PROMPT_CHAIN_FILE}" | grep "description:" | sed 's/.*description: "\(.*\)".*/\1/')
    
    log "INFO" "Prompt: ${prompt_name} - ${prompt_description}"
    
    # Display prompt information and get user approval
    if ! get_approval "About to run prompt: ${prompt_name}\n\nDescription: ${prompt_description}\n\nThis will process the input data and generate output for the next step."; then
        log "WARNING" "User aborted prompt: ${prompt_id}"
        exit 0
    fi
    
    # Here we would normally call an LLM or other processing system
    # For now, we'll just simulate the process
    log "INFO" "Processing prompt ${prompt_id}..."
    sleep 2  # Simulate processing time
    
    # Create a placeholder output file
    echo "{\"status\": \"success\", \"prompt_id\": \"${prompt_id}\", \"timestamp\": \"$(date +"%Y-%m-%d %H:%M:%S")\"}" > "${output_file}"
    
    log "SUCCESS" "Prompt ${prompt_id} completed successfully"
    log "INFO" "Output saved to: ${output_file}"
    
    # Return the output file path
    echo "${output_file}"
}

# Function to display help
show_help() {
    echo "MCP Migration Script"
    echo "Usage: $0 [options] [prompt_id]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -a, --all      Run all prompts in sequence"
    echo "  -c, --check    Check prerequisites only"
    echo "  -v, --verbose  Enable verbose logging"
    echo ""
    echo "Prompt IDs:"
    echo "  analyze_current_structure   Analyze the current codebase structure"
    echo "  design_mcp_architecture     Design the MCP architecture"
    echo "  create_migration_plan       Create a detailed migration plan"
    echo "  implement_host_component    Implement the MCP Host component"
    echo "  implement_client_component  Implement the MCP Client component"
    echo "  implement_server_component  Implement the MCP Server component"
    echo ""
    echo "Example:"
    echo "  $0 --all                    # Run all prompts in sequence"
    echo "  $0 analyze_current_structure # Run only the analyze_current_structure prompt"
}

# Check prerequisites
check_prerequisites() {
    log "INFO" "Checking prerequisites..."
    
    # Check if required files exist
    check_file "${STRUCTURE_FILE}"
    check_file "${PROMPT_CHAIN_FILE}"
    
    # Check if we have write access to output directory
    if [ ! -w "${OUTPUT_DIR}" ]; then
        mkdir -p "${OUTPUT_DIR}"
        if [ ! -w "${OUTPUT_DIR}" ]; then
            log "ERROR" "No write access to output directory: ${OUTPUT_DIR}"
            exit 1
        fi
    fi
    
    # Check for required tools
    for cmd in grep sed python3; do
        if ! command -v $cmd &> /dev/null; then
            log "ERROR" "Required command not found: $cmd"
            exit 1
        fi
    done
    
    log "SUCCESS" "All prerequisites satisfied"
}

# Run the full workflow
run_full_workflow() {
    log "INFO" "Starting full MCP migration workflow"
    
    # Step 1: Analyze current structure
    local analyze_output=$(run_prompt "analyze_current_structure" "")
    
    # Step 2: Design MCP architecture
    local design_output=$(run_prompt "design_mcp_architecture" "${analyze_output}")
    
    # Step 3: Create migration plan
    local plan_output=$(run_prompt "create_migration_plan" "${design_output}")
    
    # Step 4: Implement Host component
    local host_output=$(run_prompt "implement_host_component" "${plan_output}")
    
    # Step 5: Implement Client component
    local client_output=$(run_prompt "implement_client_component" "${host_output}")
    
    # Step 6: Implement Server component
    local server_output=$(run_prompt "implement_server_component" "${client_output}")
    
    log "SUCCESS" "MCP migration workflow completed successfully"
    log "INFO" "Final output: ${server_output}"
    
    # Display summary
    echo -e "${GREEN}"
    echo "========================================================"
    echo "MCP Migration Workflow Summary"
    echo "========================================================"
    echo "Workflow started at: $(head -n 1 "${LOG_FILE}" | cut -d '-' -f 2-)"
    echo "Workflow completed at: $(date +"%Y-%m-%d %H:%M:%S")"
    echo "Log file: ${LOG_FILE}"
    echo "Output directory: ${OUTPUT_DIR}"
    echo -e "${NC}"
}

# Run a single prompt
run_single_prompt() {
    local prompt_id=$1
    
    # Validate prompt ID
    if ! grep -q "id: \"${prompt_id}\"" "${PROMPT_CHAIN_FILE}"; then
        log "ERROR" "Invalid prompt ID: ${prompt_id}"
        echo "Valid prompt IDs:"
        grep -o 'id: "[^"]*"' "${PROMPT_CHAIN_FILE}" | sed 's/id: "\(.*\)"/  \1/'
        exit 1
    fi
    
    # Determine input file based on dependencies
    local input_file=""
    case "${prompt_id}" in
        "analyze_current_structure")
            # No input needed for first prompt
            ;;
        "design_mcp_architecture")
            # Check if analyze_current_structure output exists
            if [ -f "${OUTPUT_DIR}/analyze_current_structure_output.json" ]; then
                input_file="${OUTPUT_DIR}/analyze_current_structure_output.json"
            else
                log "WARNING" "Missing input from previous step. Running analyze_current_structure first."
                input_file=$(run_prompt "analyze_current_structure" "")
            fi
            ;;
        "create_migration_plan")
            # Check if design_mcp_architecture output exists
            if [ -f "${OUTPUT_DIR}/design_mcp_architecture_output.json" ]; then
                input_file="${OUTPUT_DIR}/design_mcp_architecture_output.json"
            else
                log "WARNING" "Missing input from previous step. Running design_mcp_architecture first."
                if [ -f "${OUTPUT_DIR}/analyze_current_structure_output.json" ]; then
                    input_file=$(run_prompt "design_mcp_architecture" "${OUTPUT_DIR}/analyze_current_structure_output.json")
                else
                    log "WARNING" "Missing input from analyze_current_structure. Running it first."
                    local analyze_output=$(run_prompt "analyze_current_structure" "")
                    input_file=$(run_prompt "design_mcp_architecture" "${analyze_output}")
                fi
            fi
            ;;
        # Add similar logic for other prompts
        *)
            log "WARNING" "Dependency resolution not implemented for ${prompt_id}. Running without input."
            ;;
    esac
    
    # Run the prompt
    run_prompt "${prompt_id}" "${input_file}"
    
    log "SUCCESS" "Completed running prompt: ${prompt_id}"
}

# Main script execution
main() {
    # Parse command line arguments
    local run_all=false
    local check_only=false
    local verbose=false
    local prompt_id=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -a|--all)
                run_all=true
                shift
                ;;
            -c|--check)
                check_only=true
                shift
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            *)
                prompt_id=$1
                shift
                ;;
        esac
    done
    
    # Check prerequisites
    check_prerequisites
    
    if [ "$check_only" = true ]; then
        log "INFO" "Prerequisite check completed. Exiting as requested."
        exit 0
    fi
    
    # Run the workflow
    if [ "$run_all" = true ]; then
        run_full_workflow
    elif [ -n "$prompt_id" ]; then
        run_single_prompt "$prompt_id"
    else
        log "INFO" "No action specified. Use --all to run the full workflow or specify a prompt ID."
        show_help
        exit 0
    fi
}

# Execute main function
main "$@"