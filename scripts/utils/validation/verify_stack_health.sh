#!/bin/bash
# ============================================================================
# MCP-BASE-STACK Health Check Script
# ============================================================================
# Description:
#   This script performs a comprehensive health check of the MCP-BASE-STACK
#   by verifying the availability of all required services, checking
#   connectivity between components, and monitoring resource usage.
#
# Usage:
#   ./verify_stack_health.sh [--output filename]
#
# Options:
#   --output filename    Specify an alternative output file
#                        (default: stack-health-report.txt)
#
# Output:
#   - Displays health check results to stdout
#   - Writes detailed report to stack-health-report.txt
#
# Requirements:
#   - curl: For API availability checks
#   - docker: For container interaction
#   - nvidia-smi: For GPU resource monitoring (if GPU is available)
#
# Exit Codes:
#   0 - All checks passed
#   1 - One or more checks failed
# ============================================================================

# ----------------------------------------------------------------------------
# Function: check_service_availability
# Description: Checks if a service is available at the specified URL
# Arguments:
#   $1 - Service name
#   $2 - URL to check
#   $3 - Success pattern (optional)
# Returns:
#   0 if service is available, 1 otherwise
# ----------------------------------------------------------------------------
check_service_availability() {
  local service_name="$1"
  local url="$2"
  local pattern="$3"
  
  echo "=== $service_name Availability ===" | tee -a stack-health-report.txt
  
  if [[ -n "$pattern" ]]; then
    # Check with pattern matching
    if curl -s "$url" 2>/dev/null | grep -q "$pattern"; then
      echo "$service_name is responding" | tee -a stack-health-report.txt
      return 0
    else
      echo "$service_name not available" | tee -a stack-health-report.txt
      return 1
    fi
  else
    # Simple HTTP status check
    curl -I "$url" 2>/dev/null | head -n 1 | tee -a stack-health-report.txt
    if [[ ${PIPESTATUS[0]} -eq 0 ]]; then
      return 0
    else
      return 1
    fi
  fi
  
  echo "" | tee -a stack-health-report.txt
}

# ----------------------------------------------------------------------------
# Function: check_system_resources
# Description: Checks system resource usage (memory, GPU)
# Arguments:
#   None
# Returns:
#   0 if resources are available, 1 if critically low
# ----------------------------------------------------------------------------
check_system_resources() {
  echo "=== System Resource Usage ===" | tee -a stack-health-report.txt
  
  # Check memory
  echo "Memory:" | tee -a stack-health-report.txt
  free -h | tee -a stack-health-report.txt
  
  # Check GPU if available
  echo "GPU:" | tee -a stack-health-report.txt
  if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv | tee -a stack-health-report.txt
  else
    echo "NVIDIA GPU not detected or nvidia-smi not available" | tee -a stack-health-report.txt
  fi
  
  echo "" | tee -a stack-health-report.txt
  return 0
}

# ----------------------------------------------------------------------------
# Function: check_llm_models
# Description: Checks available LLM models
# Arguments:
#   None
# Returns:
#   0 if models are available, 1 otherwise
# ----------------------------------------------------------------------------
check_llm_models() {
  echo "=== LLM Server Models Available ===" | tee -a stack-health-report.txt
  
  if docker exec llm-server ollama list 2>/dev/null | tee -a stack-health-report.txt; then
    echo "" | tee -a stack-health-report.txt
    return 0
  else
    echo "Failed to list LLM models" | tee -a stack-health-report.txt
    echo "" | tee -a stack-health-report.txt
    return 1
  fi
}

# ============================================================================
# Main Script
# ============================================================================

# Initialize variables
REPORT_FILE="stack-health-report.txt"
EXIT_CODE=0

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --output)
      REPORT_FILE="$2"
      shift
      ;;
    *)
      echo "Unknown parameter: $1"
      exit 1
      ;;
  esac
  shift
done

# Start health check
echo "=== MCP-BASE-STACK HEALTH CHECK ==="
echo "$(date)" | tee $REPORT_FILE
echo "" | tee -a $REPORT_FILE

# Check LibreChat API
check_service_availability "LibreChat API" "http://localhost:3080/"
if [[ $? -ne 0 ]]; then
  EXIT_CODE=1
fi

# Check LLM Server API
check_service_availability "LLM Server API" "http://localhost:11434/api/tags" "models"
if [[ $? -ne 0 ]]; then
  EXIT_CODE=1
fi

# Check MCP Server
check_service_availability "MCP Server" "http://localhost:8000/debug/health"
if [[ $? -ne 0 ]]; then
  EXIT_CODE=1
fi

# Check LLM models
check_llm_models
if [[ $? -ne 0 ]]; then
  EXIT_CODE=1
fi

# Check system resources
check_system_resources

# Finish health check
if [[ $EXIT_CODE -eq 0 ]]; then
  echo "Health check completed successfully - see $REPORT_FILE for details"
else
  echo "Health check completed with issues - see $REPORT_FILE for details"
fi

exit $EXIT_CODE