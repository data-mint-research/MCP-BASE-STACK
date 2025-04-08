# Quality Utilities

This directory contains utilities for enforcing and checking code quality standards.

## Documentation Coverage Checker

The documentation coverage checker (`check_documentation_coverage.py`) is a tool that analyzes Python files to determine documentation coverage at multiple levels:

- Module level (module docstrings)
- Class level (class docstrings)
- Method/function level (function docstrings)
- Parameter level (parameter documentation in docstrings)
- Return value documentation

### Features

- **Detailed Analysis**: Provides detailed feedback on missing documentation at various levels
- **Component-Level Metrics**: Generates metrics for each component in the project
- **Dashboard Integration**: Exports metrics that are displayed in the quality dashboard
- **Pre-commit Integration**: Can be used as a pre-commit hook to enforce documentation standards

### Usage

#### Command Line

```bash
# Check specific files
python scripts/utils/quality/check_documentation_coverage.py path/to/file1.py path/to/file2.py

# Check all Python files in the project
python scripts/utils/quality/check_documentation_coverage.py
```

#### Pre-commit Hook

The documentation coverage checker is integrated as a pre-commit hook in `.pre-commit-config.yaml`:

```yaml
-   id: documentation-coverage
    name: Documentation Coverage Check
    description: Check documentation coverage for Python files
    entry: python scripts/utils/quality/check_documentation_coverage.py
    language: python
    types: [python]
    pass_filenames: true
    stages: [commit]
```

This hook will run automatically when you commit changes to Python files.

### Configuration

The documentation coverage checker has the following configurable thresholds:

- `MIN_MODULE_COVERAGE`: Minimum required module docstring coverage (default: 0.9 or 90%)
- `MIN_CLASS_COVERAGE`: Minimum required class docstring coverage (default: 0.9 or 90%)
- `MIN_FUNCTION_COVERAGE`: Minimum required function docstring coverage (default: 0.8 or 80%)
- `MIN_PARAM_COVERAGE`: Minimum required parameter docstring coverage (default: 0.7 or 70%)
- `MIN_RETURN_COVERAGE`: Minimum required return value docstring coverage (default: 0.7 or 70%)

You can modify these thresholds in the `check_documentation_coverage.py` script.

### Output

The documentation coverage checker generates a JSON report at `data/reports/documentation_coverage_metrics.json` with detailed metrics, including:

- Overall documentation coverage
- Module-level coverage
- Class-level coverage
- Function-level coverage
- Parameter-level coverage
- Return value coverage
- Component-specific metrics

These metrics are displayed in the quality dashboard for easy visualization.

## Other Quality Utilities

- **ShellCheck**: `test-shellcheck.sh` - Checks shell scripts for common issues
- **Dependency Audit**: `maintenance/audit_dependencies.py` - Checks dependencies for known vulnerabilities