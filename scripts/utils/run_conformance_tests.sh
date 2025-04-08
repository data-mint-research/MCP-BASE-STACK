#!/bin/bash
# =============================================================================
# MCP Conformance Testing Script
# =============================================================================
# This script runs the MCP conformance tests and reports the results.
# It is designed to be used in CI/CD pipelines to verify MCP compliance.
#
# Usage:
#   ./run_conformance_tests.sh [--verbose] [--report-path=<path>] [--fail-fast]
#
# Options:
#   --verbose       Show detailed test output
#   --report-path   Path to save the test report (default: ./conformance-report.json)
#   --fail-fast     Stop on first test failure
#
# Exit codes:
#   0 - All tests passed
#   1 - Some tests failed
#   2 - Script error
# =============================================================================

set -e

# Default values
VERBOSE=false
REPORT_PATH="./conformance-report.json"
FAIL_FAST=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MCP_SERVER_DIR="$PROJECT_ROOT/services/mcp-server"

# Parse command line arguments
for arg in "$@"; do
  case $arg in
    --verbose)
      VERBOSE=true
      shift
      ;;
    --report-path=*)
      REPORT_PATH="${arg#*=}"
      shift
      ;;
    --fail-fast)
      FAIL_FAST=true
      shift
      ;;
    *)
      echo "Unknown option: $arg"
      exit 2
      ;;
  esac
done

# Ensure the MCP server directory exists
if [ ! -d "$MCP_SERVER_DIR" ]; then
  echo "Error: MCP server directory not found at $MCP_SERVER_DIR"
  exit 2
fi

# Create a temporary directory for test artifacts
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

echo "=== MCP Conformance Testing ==="
echo "Running tests from: $MCP_SERVER_DIR"
echo "Report will be saved to: $REPORT_PATH"
echo "================================"

# Function to run the tests
run_tests() {
  cd "$MCP_SERVER_DIR"
  
  # Prepare test command
  TEST_CMD="python -m unittest src/tests/test_conformance.py"
  
  if [ "$VERBOSE" = true ]; then
    TEST_CMD="$TEST_CMD -v"
  fi
  
  if [ "$FAIL_FAST" = true ]; then
    TEST_CMD="$TEST_CMD -f"
  fi
  
  # Run the tests
  if [ "$VERBOSE" = true ]; then
    echo "Running command: $TEST_CMD"
    eval "$TEST_CMD" | tee "$TEMP_DIR/test_output.txt"
  else
    echo "Running tests..."
    eval "$TEST_CMD" > "$TEMP_DIR/test_output.txt" 2>&1
  fi
  
  # Capture the exit code
  TEST_EXIT_CODE=${PIPESTATUS[0]}
  
  return $TEST_EXIT_CODE
}

# Function to generate a JSON report
generate_report() {
  local exit_code=$1
  local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  local status="PASSED"
  
  if [ $exit_code -ne 0 ]; then
    status="FAILED"
  fi
  
  # Extract test results
  local total_tests=$(grep -o "Ran [0-9]* test" "$TEMP_DIR/test_output.txt" | awk '{print $2}')
  local failed_tests=$(grep -c "FAIL:" "$TEMP_DIR/test_output.txt" || echo "0")
  local error_tests=$(grep -c "ERROR:" "$TEMP_DIR/test_output.txt" || echo "0")
  local passed_tests=$((total_tests - failed_tests - error_tests))
  
  # Create the report JSON
  cat > "$REPORT_PATH" << EOF
{
  "timestamp": "$timestamp",
  "status": "$status",
  "summary": {
    "total": $total_tests,
    "passed": $passed_tests,
    "failed": $failed_tests,
    "errors": $error_tests
  },
  "details": {
    "output": $(python -c "import json; print(json.dumps(open('$TEMP_DIR/test_output.txt').read()))")
  },
  "metadata": {
    "version": "1.0.0",
    "test_suite": "MCP Conformance Tests",
    "environment": "$(uname -a)"
  }
}
EOF
  
  echo "Report generated at: $REPORT_PATH"
}

# Main execution
echo "Starting conformance tests..."
run_tests
TEST_RESULT=$?

# Generate the report
generate_report $TEST_RESULT

# Print summary
if [ $TEST_RESULT -eq 0 ]; then
  echo "✅ All conformance tests passed!"
else
  echo "❌ Some conformance tests failed. See report for details."
fi

# Return the test result as the exit code
exit $TEST_RESULT