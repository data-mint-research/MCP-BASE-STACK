# Maintenance Scripts

## Overview

This directory contains scripts for maintaining the MCP-BASE-STACK project. These scripts handle automated code reviews, quality reporting, testing, and system verification to ensure the project remains in a healthy state.

## Scripts

### automated_code_review.py

Analyzes code changes in a pull request or between git references, providing detailed feedback on:
- Code quality
- Potential bugs
- Security vulnerabilities
- Performance concerns
- Documentation completeness
- Test coverage

Usage:
```bash
python automated_code_review.py [options]
```

Options:
- `--pr PR_NUMBER`: Pull request number to analyze
- `--base COMMIT`: Base git reference for comparison
- `--head COMMIT`: Head git reference for comparison
- `--config PATH`: Path to configuration file
- `--output PATH`: Output file path
- `--detail {high,medium,low}`: Level of detail in the report
- `--update-kg`: Update the knowledge graph with the review results

### generate_quality_report.py

Generates a comprehensive quality report for the project, including:
- Code quality metrics
- Documentation coverage
- Test coverage
- Dependency analysis
- Compliance with project standards

The report is saved in JSON format and can be used to update the knowledge graph.

### test-mcp-agent.sh

Tests the MCP server's functionality by simulating client requests and validating responses. This script ensures that the MCP server is working correctly and can handle various types of requests.

### verify_kg_migration.py

Verifies that the knowledge graph migration was successful by checking for data integrity, completeness, and consistency. This script is used after making changes to the knowledge graph structure or content.

### verify_librechat_integration.sh

Verifies the integration between LibreChat and the MCP server by testing the communication between the two components. This script ensures that LibreChat can successfully connect to and interact with the MCP server.

### verify-stack-health.sh

Performs a comprehensive health check of the entire MCP-BASE-STACK, including:
- Service availability
- Resource usage
- Configuration validity
- Component connectivity

## Usage

Most scripts in this directory are designed to be run as part of CI/CD pipelines or scheduled maintenance tasks. They can also be run manually when needed.

Example:
```bash
# Generate a quality report
python generate_quality_report.py --output data/reports/quality-report.json

# Verify the stack health
./verify-stack-health.sh

# Run an automated code review
python automated_code_review.py --base main --head feature-branch --output code-review.md
```

## Integration with Knowledge Graph

These maintenance scripts update the knowledge graph with their findings, ensuring that the project's state is accurately reflected in the knowledge graph. This integration allows for tracking quality metrics and system health over time.