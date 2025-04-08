# Dependency Management

This document outlines the dependency management system implemented in the MCP-BASE-STACK project.

## Overview

The dependency management system ensures that:

1. All dependency versions are standardized and consistent across the project
2. Dependencies are regularly checked for known vulnerabilities
3. Dependencies are kept up-to-date through an automated workflow

## Components

### 1. Standardized Dependency Versions

All dependencies in the project use pinned versions (e.g., `package==1.0.0` instead of `package>=1.0.0`) to ensure consistency and reproducibility. This prevents "works on my machine" issues and ensures that all environments use the same dependency versions.

### 2. Vulnerability Checking

The system automatically checks for known vulnerabilities in dependencies using:

- **Pre-commit hook**: Runs before each commit to catch vulnerable dependencies early
- **CI/CD pipeline**: Checks for vulnerabilities during the quality checks workflow
- **Weekly audit**: Performs a comprehensive audit of all dependencies

Vulnerability data is sourced from:
- Python: pip-audit and safety
- Node.js: npm audit
- Java: OWASP Dependency Check (when applicable)

### 3. Dependency Update Workflow

A weekly automated workflow checks for:
- Outdated dependencies
- Security vulnerabilities
- Inconsistent dependency versions

When issues are found, the workflow automatically creates pull requests to:
- Update outdated dependencies to their latest versions
- Fix vulnerable dependencies with security patches
- Standardize inconsistent dependency versions

## Tools

### Dependency Auditor

The `scripts/utils/maintenance/audit_dependencies.py` script is the core tool for dependency management. It:

- Scans the project for dependency declarations (requirements.txt, package.json, etc.)
- Checks if dependencies are up-to-date
- Identifies known vulnerabilities
- Detects inconsistent versions across the project
- Generates a comprehensive report
- Updates the knowledge graph with dependency information

### Usage

#### Manual Audit

Run a manual dependency audit:

```bash
python scripts/utils/maintenance/audit_dependencies.py --verbose
```

#### Pre-commit Hook

The pre-commit hook automatically runs the dependency audit when files like `requirements.txt` or `package.json` are modified.

#### CI/CD Integration

The dependency audit is integrated into the CI/CD pipeline as part of the quality checks workflow.

## Best Practices

1. **Always use pinned versions** for dependencies (e.g., `package==1.0.0`)
2. **Regularly review** dependency update pull requests
3. **Test thoroughly** after dependency updates
4. **Document** any dependency-specific requirements or constraints
5. **Monitor** the dependency audit reports for security issues

## Knowledge Graph Integration

The dependency management system integrates with the knowledge graph by:

1. Recording dependency information
2. Tracking dependency update history
3. Documenting known vulnerabilities
4. Maintaining dependency relationships

This integration ensures that the knowledge graph remains the single source of truth for all dependency-related information.