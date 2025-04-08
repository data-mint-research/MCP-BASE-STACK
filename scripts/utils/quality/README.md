# Quality Utilities

## Overview

This directory contains utility scripts for enforcing and monitoring code quality in the MCP-BASE-STACK project. These utilities help maintain high standards of code quality, documentation, and testing throughout the codebase.

## Purpose

The quality utilities serve several key purposes:

1. **Quality Enforcement**: Automatically enforce coding standards, documentation requirements, and best practices
2. **Quality Monitoring**: Track quality metrics over time and generate reports
3. **Quality Improvement**: Identify areas for improvement and suggest fixes
4. **Knowledge Graph Integration**: Update the knowledge graph with quality metrics

## Current Status

The project has achieved 100% file structure compliance:
- 249 total files properly organized
- 100% naming convention compliance
- 100% directory structure compliance

## Integration with Quality Enforcement System

These utilities work in conjunction with the core quality enforcement system (`core/quality/enforcer.py`). While the core system provides the framework and APIs for quality enforcement, these utilities provide command-line tools and automation scripts that leverage the core system.

## Scripts

This directory contains the following scripts:

### update_file_structure_metrics.py

Updates the knowledge graph with file structure standardization metrics. This script:
- Runs the file structure validation
- Generates a metrics report with naming and directory compliance percentages
- Saves the metrics to `data/reports/file_structure_metrics.json`
- Updates the knowledge graph with the latest metrics

Usage:
```bash
python scripts/utils/quality/update_file_structure_metrics.py
```

### quality_report_generator.py

Generates comprehensive quality reports for the project, including:
- Code quality metrics
- Documentation coverage
- Test coverage
- Compliance with project standards

The report can be generated in various formats (JSON, Markdown, HTML) and can be used to update the knowledge graph.

### code_style_checker.py

Checks code style across the project using tools like:
- Black for Python code formatting
- ESLint for JavaScript code formatting
- ShellCheck for shell script formatting

This script can be run manually or as part of a pre-commit hook.

### documentation_analyzer.py

Analyzes documentation coverage and quality, including:
- Docstring presence and completeness
- README presence and completeness
- Documentation formatting and style
- Cross-references and links

### test_coverage_reporter.py

Generates test coverage reports and identifies areas with insufficient test coverage.

### dependency_analyzer.py

Analyzes project dependencies for:
- Security vulnerabilities
- Outdated packages
- Unused dependencies
- Licensing issues

### quality_dashboard_generator.py

Generates a quality dashboard that visualizes quality metrics over time.

## Usage

These utilities can be used in various ways:

1. **Manual Execution**: Run scripts directly to check quality or generate reports
2. **CI/CD Integration**: Integrate with CI/CD pipelines to enforce quality standards
3. **Pre-commit Hooks**: Run as pre-commit hooks to prevent low-quality code from being committed
4. **Scheduled Jobs**: Run as scheduled jobs to monitor quality over time

Example usage:

```bash
# Update file structure metrics in the knowledge graph
python scripts/utils/quality/update_file_structure_metrics.py

# Generate a quality report
python quality_report_generator.py --output data/reports/quality-report.json

# Check code style
python code_style_checker.py --fix

# Analyze documentation coverage
python documentation_analyzer.py --update-kg
```

## Integration with Knowledge Graph

The quality utilities update the knowledge graph with quality metrics, ensuring that the knowledge graph accurately reflects the current quality state of the project. This integration allows for tracking quality metrics over time and making data-driven decisions about quality improvements.

## Integration with File Structure Standardization

The quality utilities work in conjunction with the file structure standardization system:

1. The `standardize_file_structure.py` script ensures files follow naming conventions and are in ideal directories
2. The `update_file_structure_metrics.py` script updates the knowledge graph with the latest file structure metrics
3. The quality enforcement system uses these metrics to track compliance over time

## Best Practices

When using these quality utilities:

1. Run them regularly, not just when making changes
2. Integrate them into your CI/CD pipeline
3. Address quality issues immediately
4. Use the detailed output to understand and fix issues
5. Ensure the knowledge graph is updated after quality checks
6. Track quality metrics over time to identify trends
7. Maintain 100% file structure compliance by running standardization scripts regularly

## Extending the Quality System

To add new quality checks:

1. Create a new component in the core quality system
2. Create a new utility script in this directory that leverages the component
3. Update the knowledge graph schema to include the new quality metrics
4. Document the new quality check in the quality standards documentation