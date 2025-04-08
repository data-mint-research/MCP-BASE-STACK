# Code Quality Tools Guide

This guide provides a comprehensive overview of the code quality tools implemented in the MCP-BASE-STACK project. It is designed to help new developers understand how to use these tools effectively to maintain high code quality standards.

## Table of Contents

- [Code Quality Tools Guide](#code-quality-tools-guide)
  - [Table of Contents](#table-of-contents)
  - [Quick-Start Guide](#quick-start-guide)
    - [Installing Pre-commit Hooks](#installing-pre-commit-hooks)
    - [Running Code Quality Checks Manually](#running-code-quality-checks-manually)
    - [Automatically Fixing Code Quality Issues](#automatically-fixing-code-quality-issues)
  - [Common Code Quality Issues and Solutions](#common-code-quality-issues-and-solutions)
    - [Formatting Issues (Black/isort)](#formatting-issues-blackisort)
      - [Issue: Code formatting doesn't match Black's style](#issue-code-formatting-doesnt-match-blacks-style)
      - [Issue: Imports are not properly sorted](#issue-imports-are-not-properly-sorted)
    - [Linting Issues (flake8/pylint)](#linting-issues-flake8pylint)
      - [Issue: Unused imports (F401)](#issue-unused-imports-f401)
      - [Issue: Line too long (E501)](#issue-line-too-long-e501)
      - [Issue: Missing docstring (D100, D101, D102)](#issue-missing-docstring-d100-d101-d102)
      - [Issue: Too many branches/statements (R0912, R0915)](#issue-too-many-branchesstatements-r0912-r0915)
    - [Type Checking Issues (mypy)](#type-checking-issues-mypy)
      - [Issue: Missing type annotations](#issue-missing-type-annotations)
      - [Issue: Incompatible types](#issue-incompatible-types)
      - [Issue: Untyped function definitions](#issue-untyped-function-definitions)
    - [Shell Script Issues (shellcheck)](#shell-script-issues-shellcheck)
      - [Issue: Double quote to prevent globbing and word splitting (SC2086)](#issue-double-quote-to-prevent-globbing-and-word-splitting-sc2086)
      - [Issue: Use `$()` instead of backticks (SC2006)](#issue-use--instead-of-backticks-sc2006)
      - [Issue: Not handling error cases (SC2181)](#issue-not-handling-error-cases-sc2181)
  - [Troubleshooting Guide](#troubleshooting-guide)
    - [Pre-commit Hooks Not Running](#pre-commit-hooks-not-running)
    - [Black and isort Conflicts](#black-and-isort-conflicts)
    - [mypy Cannot Find Imports](#mypy-cannot-find-imports)
    - [flake8 and Black Line Length Conflicts](#flake8-and-black-line-length-conflicts)
  - [Best Practices for Maintaining Code Quality](#best-practices-for-maintaining-code-quality)

## Quick-Start Guide

### Installing Pre-commit Hooks

Pre-commit hooks automatically run code quality checks before each commit, preventing you from committing code that doesn't meet our quality standards.

To install the pre-commit hooks:

```bash
# Run from the project root directory
./scripts/utils/installation/install-pre-commit-hooks.sh
```

This script will:
1. Install pre-commit if it's not already installed
2. Install the hooks defined in `.pre-commit-config.yaml`
3. Set up Git to use these hooks

After installation, the hooks will run automatically before each commit. If any checks fail, the commit will be blocked until you fix the issues.

### Running Code Quality Checks Manually

You can run all code quality checks manually using the provided script:

```bash
# Run from the project root directory
./scripts/utils/quality/check-code-quality.sh
```

This script will run:
- Black (Python formatter)
- isort (Python import sorter)
- flake8 (Python linter)
- mypy (Python type checker)
- pylint (Python linter)
- shellcheck (Shell script linter)

You can also run individual tools manually:

```bash
# Format Python code with Black
black path/to/file.py

# Sort imports with isort
isort path/to/file.py

# Lint Python code with flake8
flake8 path/to/file.py

# Type check Python code with mypy
mypy path/to/file.py

# Lint Python code with pylint
pylint path/to/file.py

# Lint shell scripts with shellcheck
shellcheck path/to/file.sh
```

### Automatically Fixing Code Quality Issues

Some code quality issues can be fixed automatically using the provided script:

```bash
# Run from the project root directory
./scripts/utils/quality/fix-code-quality.sh
```

This script will:
- Run isort to sort imports
- Run Black to format code
- Run autopep8 to fix some flake8 issues

Note that not all issues can be fixed automatically. You may need to manually fix some issues, especially for mypy, pylint, and shellcheck.

## Common Code Quality Issues and Solutions

### Formatting Issues (Black/isort)

#### Issue: Code formatting doesn't match Black's style

**Example:**
```python
def function(arg1,arg2,
    arg3):
    return arg1+arg2+arg3
```

**Solution:**
Run Black to automatically format the code:
```bash
black path/to/file.py
```

**Result:**
```python
def function(arg1, arg2, arg3):
    return arg1 + arg2 + arg3
```

#### Issue: Imports are not properly sorted

**Example:**
```python
import sys
from typing import List
import os
from mcp_base_stack.core import logging
import yaml
```

**Solution:**
Run isort to automatically sort imports:
```bash
isort path/to/file.py
```

**Result:**
```python
import os
import sys
from typing import List

import yaml

from mcp_base_stack.core import logging
```

### Linting Issues (flake8/pylint)

#### Issue: Unused imports (F401)

**Example:**
```python
import os
import sys  # Unused import
from typing import List, Dict  # Dict is unused

def function():
    return os.path.join('a', 'b')
```

**Solution:**
Remove unused imports:
```python
import os
from typing import List

def function():
    return os.path.join('a', 'b')
```

#### Issue: Line too long (E501)

**Example:**
```python
def function():
    return "This is a very long string that exceeds the maximum line length of 88 characters and will cause a linting error."
```

**Solution:**
Break long strings into multiple lines:
```python
def function():
    return (
        "This is a very long string that exceeds the maximum line length "
        "of 88 characters and will cause a linting error."
    )
```

#### Issue: Missing docstring (D100, D101, D102)

**Example:**
```python
def calculate_total(items):
    total = 0
    for item in items:
        total += item
    return total
```

**Solution:**
Add appropriate docstrings:
```python
def calculate_total(items):
    """
    Calculate the sum of all items in the list.
    
    Args:
        items: A list of numbers to sum
        
    Returns:
        The sum of all items
    """
    total = 0
    for item in items:
        total += item
    return total
```

#### Issue: Too many branches/statements (R0912, R0915)

**Solution:**
Refactor complex functions into smaller, more focused functions:

```python
# Before: Complex function with too many branches
def process_data(data):
    # ... many lines of code with multiple if/else branches ...
    
# After: Refactored into smaller functions
def validate_data(data):
    # ... validation logic ...
    
def transform_data(data):
    # ... transformation logic ...
    
def process_data(data):
    """Process the input data."""
    if not validate_data(data):
        return None
    return transform_data(data)
```

### Type Checking Issues (mypy)

#### Issue: Missing type annotations

**Example:**
```python
def get_config(key, default=None):
    config = load_config()
    return config.get(key, default)
```

**Solution:**
Add type annotations:
```python
from typing import Any, Dict, Optional

def get_config(key: str, default: Optional[Any] = None) -> Any:
    config: Dict[str, Any] = load_config()
    return config.get(key, default)
```

#### Issue: Incompatible types

**Example:**
```python
def get_user_id() -> int:
    user_id = get_user_data().get('id')
    return user_id  # Error: user_id might be None
```

**Solution:**
Handle potential None values:
```python
def get_user_id() -> int:
    user_id = get_user_data().get('id')
    if user_id is None:
        raise ValueError("User ID not found")
    return user_id
```

#### Issue: Untyped function definitions

**Example:**
```python
# Error with disallow_untyped_defs=True
def process_data(data):
    return data
```

**Solution:**
Add type annotations to function parameters and return value:
```python
from typing import Dict, Any

def process_data(data: Dict[str, Any]) -> Dict[str, Any]:
    return data
```

### Shell Script Issues (shellcheck)

#### Issue: Double quote to prevent globbing and word splitting (SC2086)

**Example:**
```bash
FILES=*.txt
cp $FILES /destination
```

**Solution:**
Use double quotes around variables:
```bash
FILES="*.txt"
cp "$FILES" /destination
```

#### Issue: Use `$()` instead of backticks (SC2006)

**Example:**
```bash
DATE=`date +%Y-%m-%d`
```

**Solution:**
Use `$()` for command substitution:
```bash
DATE=$(date +%Y-%m-%d)
```

#### Issue: Not handling error cases (SC2181)

**Example:**
```bash
command
if [ $? -ne 0 ]; then
    echo "Command failed"
fi
```

**Solution:**
Use direct if statement with the command:
```bash
if ! command; then
    echo "Command failed"
fi
```

## Troubleshooting Guide

### Pre-commit Hooks Not Running

**Issue:** Pre-commit hooks are not running before commits.

**Solution:**
1. Ensure pre-commit is installed:
   ```bash
   pip install pre-commit
   ```

2. Reinstall the hooks:
   ```bash
   pre-commit install
   ```

3. Check if Git is using the correct hooks path:
   ```bash
   git config core.hooksPath
   ```
   
   If it's not set to `.git-hooks`, run:
   ```bash
   git config core.hooksPath .git-hooks
   ```

### Black and isort Conflicts

**Issue:** Black and isort formatting conflicts.

**Solution:**
Ensure isort is configured to be compatible with Black. In our project, this is already set up in `config/pyproject.toml`:

```toml
[tool.isort]
profile = "black"
```

If you're still having issues, run isort first, then Black:

```bash
isort path/to/file.py
black path/to/file.py
```

### mypy Cannot Find Imports

**Issue:** mypy reports "Cannot find module" or "Cannot find implementation or library stub" errors.

**Solution:**
1. Install type stubs for third-party libraries:
   ```bash
   pip install types-requests types-PyYAML
   ```
2. Add missing libraries to mypy configuration in `config/linting/mypy.ini`:
   ```ini
   [mypy.plugins.third_party_library.*]
   ignore_missing_imports = True
   ```

### flake8 and Black Line Length Conflicts

**Issue:** flake8 reports line length errors on lines that Black has formatted.

**Solution:**
Our configuration already aligns flake8 and Black line length (88 characters) and ignores E203 (whitespace before ':') which Black handles differently. If you're still having issues, check `config/linting/.flake8` configuration:

```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
```

## Best Practices for Maintaining Code Quality

1. **Run Checks Before Committing**
   - Let pre-commit hooks run automatically before each commit
   - Alternatively, run `./scripts/utils/quality/check-code-quality.sh` manually before committing

2. **Fix Issues Immediately**
   - Don't ignore code quality warnings
   - Use `./scripts/utils/quality/fix-code-quality.sh` to fix issues automatically when possible
   - Fix remaining issues manually

3. **Write Tests**
   - Ensure all new code has appropriate test coverage
   - Run tests before and after making changes

4. **Follow the Style Guide**
   - Refer to the [MCP-BASE-STACK Style Guide](../conventions/style-guide.md) for detailed coding standards
   - Consistency is key to maintainable code

5. **Use Type Annotations**
   - Add type annotations to all new functions and classes
   - Update existing code with type annotations when modifying it

6. **Write Meaningful Docstrings**
   - Document all modules, classes, and functions
   - Follow the Google docstring style as specified in the style guide

7. **Keep Dependencies Updated**
   - Regularly update code quality tools to benefit from improvements
   - Update type stubs for third-party libraries

8. **Refactor Regularly**
   - Don't let technical debt accumulate
   - Refactor complex functions into smaller, more focused functions
   - Remove dead code and unused imports

9. **Review Code Quality in Pull Requests**
   - Include code quality checks in code reviews
   - Ensure all code quality issues are addressed before merging

10. **Continuous Integration**
    - Set up CI pipelines to run code quality checks automatically
    - Block merges if code quality checks fail

By following these guidelines and using the provided tools, you'll help maintain high code quality standards across the MCP-BASE-STACK project.