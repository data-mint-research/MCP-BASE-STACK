# Auto-fix Capabilities

This document describes the auto-fix capabilities of the quality enforcement system, which allow for automatic resolution of common quality issues.

## Overview

The auto-fix capabilities provide a way to automatically fix common quality issues identified by the quality checks. These capabilities are designed to be:

- **Safe**: Fixes are designed to be non-destructive and maintain the original functionality of the code.
- **Interactive**: Users can review and approve fixes before they are applied.
- **Previewable**: Users can see what changes will be made before applying them.
- **Verifiable**: Fixes are verified to ensure they don't introduce new issues.

## Components

The auto-fix capabilities are organized into several components:

### Fix Modules

These modules provide specific fixes for different types of quality issues:

- **Code Style Fixes** (`core/quality/components/fixes/code_style.py`): Fixes for code style issues, including:
  - Black formatting
  - Import sorting with isort
  - Line ending normalization
  - Whitespace cleanup

- **Documentation Fixes** (`core/quality/components/fixes/documentation.py`): Fixes for documentation issues, including:
  - Docstring generation and formatting
  - README file creation and updates
  - Documentation coverage improvements
  - Comment formatting and standardization

- **Structure Fixes** (`core/quality/components/fixes/structure.py`): Fixes for structure-related issues, including:
  - Directory structure corrections
  - File naming convention enforcement
  - Import organization
  - Circular dependency resolution

- **Static Analysis Fixes** (`core/quality/components/fixes/static_analysis.py`): Fixes for static analysis issues, including:
  - Linting errors (flake8, pylint)
  - Type annotation issues (mypy)
  - Security vulnerabilities
  - Performance optimizations

### Interactive Mode

The interactive mode (`core/quality/components/interactive.py`) provides a way for users to interactively review and approve fixes. It includes:

- User confirmation of fixes
- Selection of which fixes to apply
- Customization of fix options
- Integration with the command-line interface

Example usage:

```python
from core.quality.enforcer import enforcer

# Run checks and get results
results = enforcer.run_all_checks()

# Fix issues interactively
unfixed = enforcer.fix_issues(results, interactive=True)
```

### Fix Preview

The fix preview functionality (`core/quality/components/preview.py`) allows users to see what changes will be made before applying them. It includes:

- Generating fix previews (diffs)
- Visualizing changes
- Comparing multiple fix options
- Integration with the interactive mode

Example usage:

```python
from core.quality.enforcer import enforcer

# Run checks and get results
results = enforcer.run_all_checks()

# Preview fixes
previews = enforcer.preview_fixes(results)
for file_path, diff in previews.items():
    print(f"Preview of fixes for {file_path}:")
    print(diff)
```

### Fix Verification

The fix verification functionality (`core/quality/components/verification.py`) ensures that fixes don't introduce new issues. It includes:

- Verifying fixes don't introduce new issues
- Validating fix results
- Rolling back if verification fails
- Integration with the fix workflow

Example usage:

```python
from core.quality.enforcer import enforcer

# Run checks and get results
results = enforcer.run_all_checks()

# Fix issues with verification
unfixed = enforcer.fix_issues(results, verify=True)
```

## Usage Examples

### Basic Auto-fix

To automatically fix all issues in a project:

```python
from core.quality.enforcer import enforcer

# Auto-fix all issues
fixed_count, unfixed_count = enforcer.auto_fix_issues()
print(f"Fixed {fixed_count} issues, {unfixed_count} issues remain unfixed")
```

### Interactive Auto-fix

To interactively fix issues:

```python
from core.quality.enforcer import enforcer

# Auto-fix issues interactively
fixed_count, unfixed_count = enforcer.auto_fix_issues(interactive=True)
print(f"Fixed {fixed_count} issues, {unfixed_count} issues remain unfixed")
```

### Preview Before Fixing

To preview fixes before applying them:

```python
from core.quality.enforcer import enforcer

# Preview fixes before applying them
fixed_count, unfixed_count = enforcer.auto_fix_issues(preview=True)
print(f"Fixed {fixed_count} issues, {unfixed_count} issues remain unfixed")
```

### Fix Specific Files

To fix issues in specific files:

```python
from core.quality.enforcer import enforcer

# Fix issues in specific files
file_paths = ["path/to/file1.py", "path/to/file2.py"]
fixed_count, unfixed_count = enforcer.auto_fix_issues(file_paths)
print(f"Fixed {fixed_count} issues, {unfixed_count} issues remain unfixed")
```

## Command-line Interface

The auto-fix capabilities are also available through the command-line interface:

```bash
# Auto-fix all issues
python -m core.quality.cli fix

# Auto-fix issues interactively
python -m core.quality.cli fix --interactive

# Preview fixes before applying them
python -m core.quality.cli fix --preview

# Fix issues in specific files
python -m core.quality.cli fix path/to/file1.py path/to/file2.py
```

## Customizing Fix Options

Fix options can be customized through the interactive mode or by modifying the configuration:

```yaml
# config/environments/dev.yaml
quality:
  fixes:
    code_style:
      black:
        line_length: 88
      isort:
        profile: black
    static_analysis:
      flake8:
        ignore: ["E203", "W503"]
```

## Fix Types

### Code Style Fixes

| Issue Type | Fix Description | Example |
|------------|----------------|---------|
| Black formatting | Formats Python code according to Black's style guide | Fixes spacing, line breaks, and other formatting issues |
| Import sorting | Sorts imports according to isort's rules | Organizes imports by standard library, third-party, and local |
| Line endings | Normalizes line endings to LF or CRLF | Ensures consistent line endings across files |
| Trailing whitespace | Removes trailing whitespace | Cleans up whitespace at the end of lines |

### Documentation Fixes

| Issue Type | Fix Description | Example |
|------------|----------------|---------|
| Missing module docstring | Adds a module docstring | Adds a basic docstring with module name and description |
| Missing function docstring | Adds a function docstring | Adds a docstring with parameters and return value |
| Missing README | Creates a README.md template | Creates a basic README with sections for overview, features, etc. |
| Documentation coverage | Improves documentation coverage | Adds missing documentation for parameters, return values, etc. |

### Structure Fixes

| Issue Type | Fix Description | Example |
|------------|----------------|---------|
| File naming | Renames files to follow naming conventions | Renames `badName.py` to `good_name.py` |
| Import organization | Organizes imports | Sorts imports and removes unused imports |
| Circular dependencies | Resolves circular dependencies | Adds lazy imports to break circular dependencies |
| Directory structure | Creates missing directories | Creates directories according to project structure |

### Static Analysis Fixes

| Issue Type | Fix Description | Example |
|------------|----------------|---------|
| Flake8 issues | Fixes common linting issues | Removes unused variables, adds missing whitespace, etc. |
| Pylint issues | Fixes common linting issues | Fixes docstring formatting, variable naming, etc. |
| Type annotation issues | Adds missing type annotations | Adds type hints to function parameters and return values |
| Security issues | Fixes security vulnerabilities | Replaces hardcoded passwords with environment variables |

## Integration with Knowledge Graph

The auto-fix capabilities are integrated with the knowledge graph to track quality improvements over time. Each fix is recorded in the knowledge graph, allowing for analysis of quality trends and identification of recurring issues.

## Conclusion

The auto-fix capabilities provide a powerful way to automatically resolve common quality issues, improving code quality and reducing the time spent on manual fixes. By combining safe auto-fix options with interactive mode, preview functionality, and verification, the system ensures that fixes are applied correctly and don't introduce new issues.