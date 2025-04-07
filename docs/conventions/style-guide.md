# MCP-BASE-STACK Style Guide

This document outlines the coding standards and conventions to be followed in the MCP-BASE-STACK project. Adhering to these guidelines ensures consistency, maintainability, and readability across the codebase.

## Table of Contents

1. [Naming Conventions](#naming-conventions)
2. [Documentation Standards](#documentation-standards)
3. [Code Formatting](#code-formatting)
4. [Error Handling](#error-handling)
5. [Testing Conventions](#testing-conventions)
6. [Import Organization](#import-organization)
7. [File Organization](#file-organization)
8. [Design Patterns](#design-patterns)
9. [Code Quality Tools](#code-quality-tools)

## Naming Conventions

### Python Module Naming

- **Package Names**: Lowercase with underscores (snake_case)
  ```python
  # Good
  knowledge_graph
  core
  
  # Bad
  KnowledgeGraph
  Core
  ```

- **Module Names**: Lowercase with underscores (snake_case)
  ```python
  # Good
  config.py
  error.py
  
  # Bad
  Config.py
  Error.py
  ```

- **Class Names**: CamelCase
  ```python
  # Good
  class ConfigManager:
      pass
  
  # Bad
  class config_manager:
      pass
  ```

- **Function Names**: Lowercase with underscores (snake_case)
  ```python
  # Good
  def validate_config():
      pass
  
  # Bad
  def ValidateConfig():
      pass
  ```

- **Constant Names**: UPPERCASE with underscores
  ```python
  # Good
  DEFAULT_CONFIG_DIR = "config"
  
  # Bad
  defaultConfigDir = "config"
  ```

- **Variable Names**: Lowercase with underscores (snake_case)
  ```python
  # Good
  config_manager = ConfigManager()
  
  # Bad
  ConfigManager = ConfigManager()
  ```

- **Private Attributes**: Prefix with a single underscore
  ```python
  # Good
  self._initialized = False
  
  # Bad
  self.initialized = False  # For private attributes
  ```

### Shell Script Naming

- **Script Names**: Lowercase with hyphens (kebab-case)
  ```bash
  # Good
  create-backup.sh
  install-hooks.sh
  
  # Bad
  CreateBackup.sh
  install_hooks.sh
  ```

- **Function Names**: Lowercase with underscores (snake_case)
  ```bash
  # Good
  function check_config() {
      # ...
  }
  
  # Bad
  function CheckConfig() {
      # ...
  }
  ```

- **Variable Names**: Lowercase for local variables, UPPERCASE for environment variables
  ```bash
  # Good
  local config_file="config.yaml"
  export CONFIG_PATH="/etc/config"
  
  # Bad
  local CONFIG_FILE="config.yaml"
  export configPath="/etc/config"
  ```

### Configuration Files

- **Environment Files**: `.env` for environment variables
- **Docker Compose Files**: `docker-compose.yml` or `<component>.yml`
- **Configuration Templates**: `<name>-template.<extension>`

### Documentation Files

- **Markdown Files**: `<name>.md`
- **Diagram Files**: `<name>.mmd` for Mermaid diagrams
- **API Documentation**: Generated from docstrings

### Test Files

- **Test Files**: `test_<module_name>.py`
- **Fixture Files**: Placed in `fixtures/` directory
- **Mock Data**: Placed in `fixtures/` directory

## Documentation Standards

### Docstrings

All modules, classes, and functions should have docstrings following the Google style:

```python
"""
Short description of the module/class/function.

Longer description that explains the purpose and functionality
in more detail if needed.

Attributes (for modules/classes):
    attribute_name: Description of the attribute.

Args (for functions):
    param_name: Description of the parameter.

Returns:
    Description of the return value.

Raises:
    ExceptionType: Description of when this exception is raised.

Examples:
    Examples of how to use the function/class.
"""
```

#### Module Docstrings

```python
"""
Configuration management for the MCP-BASE-STACK.

This module provides functions for loading, validating, and managing the configuration.
"""
```

#### Class Docstrings

```python
class ConfigManager:
    """Configuration manager for the MCP-BASE-STACK.
    
    This class provides methods for loading, validating, and managing
    the configuration for the MCP-BASE-STACK.
    
    Attributes:
        config_dir: Directory containing configuration files.
        env_file: Path to the environment file.
    """
```

#### Function Docstrings

```python
def validate_config(config_file: str) -> bool:
    """
    Validate a configuration file.
    
    Args:
        config_file: Path to the configuration file.
        
    Returns:
        bool: True if the configuration is valid, False otherwise.
        
    Raises:
        ConfigError: If the configuration file is invalid.
    """
```

### Type Hints

All functions should have type hints for parameters and return values:

```python
from typing import Dict, List, Optional, Union

def get_config(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get a configuration value."""
    pass

def get_config_section(section: str) -> Dict[str, Union[str, int, bool]]:
    """Get a configuration section."""
    pass
```

### Comments

- Comments should explain why, not what
- Comments should be used sparingly
- Comments should be kept up-to-date
- All comments should be in English

```python
# Good
# Retry the operation to handle transient network errors
retry_count = 3

# Bad
# Set retry_count to 3
retry_count = 3
```

## Code Formatting

### Python Formatting (PEP 8)

All Python code should follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide:

- Use 4 spaces for indentation (no tabs)
- Maximum line length of 88 characters (Black default)
- Surround top-level functions and classes with two blank lines
- Surround method definitions inside classes with one blank line
- Use blank lines to separate logical sections

### Shell Script Formatting (Google Shell Style Guide)

All shell scripts should follow the [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html):

- Use 2 spaces for indentation (no tabs)
- Maximum line length of 80 characters
- Use blank lines to separate logical sections
- Always use `#!/bin/bash` as the shebang line
- Always use double quotes for strings containing variables
- Always use `$()` for command substitution (not backticks)

### Formatting Tools

- **Black**: Use Black for automatic Python code formatting
  ```bash
  black path/to/file.py
  ```

- **isort**: Use isort for sorting Python imports
  ```bash
  isort path/to/file.py
  ```

- **shellcheck**: Use shellcheck for shell script linting
  ```bash
  shellcheck path/to/file.sh
  ```

### String Formatting

- Use f-strings for string formatting when possible
  ```python
  # Good
  name = "World"
  greeting = f"Hello, {name}!"
  
  # Acceptable for older Python versions
  greeting = "Hello, {}!".format(name)
  
  # Bad
  greeting = "Hello, " + name + "!"
  ```

- Use triple quotes for multi-line strings and docstrings
  ```python
  message = """
  This is a multi-line
  string.
  """
  ```

### Whitespace

- No trailing whitespace
- Always surround binary operators with a single space
- No space around the equals sign in keyword arguments or default parameter values
  ```python
  # Good
  def func(default=None):
      x = y + z
      
  # Bad
  def func(default = None):
      x=y+z
  ```

## Error Handling

### Exception Hierarchy

All exceptions should inherit from the base `MCPBaseStackError` class:

```python
class MCPBaseStackError(Exception):
    """Base class for all MCP-BASE-STACK exceptions."""
    
    def __init__(self, message: str, code: ErrorCode = ErrorCode.GENERAL_ERROR):
        """
        Initialize a new MCP-BASE-STACK exception.
        
        Args:
            message: Error message
            code: Error code
        """
        self.message = message
        self.code = code
        super().__init__(f"[{code.name}] {message}")
```

Specific exception types should be created for different error categories:

```python
class ConfigError(MCPBaseStackError):
    """Exception for configuration errors."""
    
    def __init__(self, message: str):
        """
        Initialize a new configuration error exception.
        
        Args:
            message: Error message
        """
        super().__init__(message, ErrorCode.CONFIG_ERROR)
```

### Error Codes

Use the `ErrorCode` enum for consistent error codes:

```python
class ErrorCode(Enum):
    """Error codes for the MCP-BASE-STACK."""
    
    SUCCESS = 0
    GENERAL_ERROR = 1
    CONFIG_ERROR = 2
    DOCKER_ERROR = 3
    NETWORK_ERROR = 4
    VALIDATION_ERROR = 5
    API_ERROR = 6
    KNOWLEDGE_GRAPH_ERROR = 7
    # ...
```

### Shell Script Error Handling

Shell scripts should use proper error handling:

```bash
#!/bin/bash

# Exit on error
set -e

# Function to handle errors
handle_error() {
  local exit_code=$1
  local line_number=$2
  echo "Error on line $line_number, exit code $exit_code"
  exit $exit_code
}

# Set up error trap
trap 'handle_error $? $LINENO' ERR

# Rest of the script
```

### Exception Handling

- Catch exceptions at the appropriate level
- Use specific exception types when possible
- Log exceptions with context
- Convert exceptions to user-friendly messages

```python
try:
    config.load_config()
except ConfigError as e:
    logging.error(f"Failed to load configuration: {str(e)}")
    sys.exit(1)
```

## Testing Conventions

### Test Organization

- Tests should be organized by module
- Tests should be in a `tests/unit` or `tests/integration` directory
- Tests should follow the same structure as the code

### Test Naming

- Test files should be named `test_<module_name>.py`
- Test classes should be named `Test<ClassName>`
- Test functions should be named `test_<function_name>`

```python
# File: tests/unit/core/test_config.py

class TestConfig:
    """Test cases for the config module."""
    
    def test_load_config(self):
        """Test the load_config function."""
        pass
```

### Test Coverage

- Tests should cover all public functions
- Tests should cover edge cases
- Tests should cover error cases

### Test Fixtures

Use pytest fixtures for test setup and teardown:

```python
@pytest.fixture
def config_file():
    """Create a temporary configuration file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml") as f:
        f.write("key: value\n")
        f.flush()
        yield f.name
```

### Mocks

Use unittest.mock for mocking external dependencies:

```python
@patch("mcp_base_stack.core.docker.client")
def test_docker_compose_up(mock_client):
    """Test docker_compose_up function."""
    mock_client.containers.run.return_value = {"Id": "container_id"}
    result = docker.compose_up("project", "compose_file", "service")
    assert result is True
    mock_client.containers.run.assert_called_once()
```

### Assertions

Use pytest assertions for clear test results:

```python
def test_get_config():
    """Test the get_config function."""
    # Setup
    config_manager = ConfigManager()
    config_manager.config_values = {"TEST_KEY": "test_value"}
    
    # Execute
    result = config_manager.get_config("TEST_KEY", "default")
    
    # Assert
    assert result == "test_value"
```

## Import Organization

### Import Order

Imports should be organized in the following order:

1. Standard library imports
2. Related third-party imports
3. Local application/library specific imports

Each group should be separated by a blank line:

```python
# Standard library imports
import os
import sys
from typing import Dict, List, Optional

# Third-party imports
import yaml
from pydantic import BaseModel

# Local imports
from mcp_base_stack.core import logging
from mcp_base_stack.core.error import ConfigError
```

### Import Style

- Use absolute imports for clarity
- Avoid wildcard imports (`from module import *`)
- Use aliases for long or conflicting module names

```python
# Good
from mcp_base_stack.core import logging
import numpy as np

# Bad
from mcp_base_stack.core.logging import *
```

### Circular Imports

Avoid circular imports by:
- Importing modules at function or method level when necessary
- Using forward references in type hints
- Restructuring code to avoid circular dependencies

```python
# Avoid circular imports with function-level imports
def get_module():
    from mcp_base_stack.modules.knowledge_graph.module import KnowledgeGraphModule
    return KnowledgeGraphModule()
```

## File Organization

### Directory Structure

Follow the standardized directory structure:

```
MCP-BASE-STACK/
├── docs/                  # Project documentation
├── config/                # Configuration files
├── core/                  # Core functionality
│   ├── kg/                # Knowledge graph functionality
│   └── ...                # Other core modules
├── services/              # Service implementations
│   ├── librechat/         # LibreChat service
│   ├── llm-server/        # LLM server service
│   └── mcp-server/        # MCP server service
├── scripts/               # Utility scripts
│   ├── deployment/        # Deployment scripts
│   ├── maintenance/       # Maintenance scripts
│   └── setup/             # Setup scripts
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── data/              # Test data
└── README.md              # Project overview
```

### Module Structure

Each module should follow this structure:

```
module_name/
├── __init__.py            # Package initialization
├── module.py              # Main module implementation
├── commands.py            # CLI commands (if applicable)
├── models.py              # Data models (if applicable)
└── README.md              # Module documentation
```

### File Content Organization

Within each file, organize content in the following order:

1. Module docstring
2. Imports
3. Constants
4. Exception classes
5. Classes
6. Functions
7. Main execution code (if applicable)

```python
"""
Module docstring.
"""

# Imports
import os
from typing import Dict

# Constants
DEFAULT_VALUE = 42

# Exception classes
class ModuleError(Exception):
    pass

# Classes
class ModuleClass:
    pass

# Functions
def module_function():
    pass

# Main execution
if __name__ == "__main__":
    module_function()
```

## Design Patterns

### Singleton Pattern

Use the singleton pattern for module instances:

```python
class Module:
    """Example module with singleton pattern."""
    
    # Singleton instance
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Implement thread-safe singleton pattern."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Module, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        """Initialize the module with default values."""
        # Only initialize once
        if getattr(self, '_initialized', False):
            return
            
        # Initialization code here
        self._initialized = True

# Module-level getter function
def get_module():
    """Get the module instance."""
    return Module()
```

### Factory Pattern

Use the factory pattern for creating objects:

```python
def create_logger(name):
    """Create a logger."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger
```

### Strategy Pattern

Use the strategy pattern for interchangeable algorithms:

```python
class ValidationStrategy:
    """Interface for validation strategies."""
    
    def validate(self, value):
        """Validate a value."""
        pass

class RequiredValidator(ValidationStrategy):
    """Validator that checks if a value is not None."""
    
    def validate(self, value):
        """Validate that a value is not None."""
        return value is not None

class TypeValidator(ValidationStrategy):
    """Validator that checks if a value is of a specific type."""
    
    def __init__(self, expected_type):
        """Initialize the validator with an expected type."""
        self.expected_type = expected_type
    
    def validate(self, value):
        """Validate that a value is of the expected type."""
        return isinstance(value, self.expected_type)
```

### Dependency Injection

Use dependency injection to reduce coupling:

```python
class Module:
    """Example module with dependency injection."""
    
    def __init__(self, logger=None, config=None):
        """Initialize the module with dependencies."""
        self.logger = logger or logging.get_logger()
        self.config = config or config.get_config()
```

## Code Quality Tools

The project uses several code quality tools to maintain high standards:

### Black

Black is an uncompromising Python code formatter:

```bash
black path/to/file.py
```

Configuration in pyproject.toml:
```toml
[tool.black]
line-length = 88
target-version = ['py38']
include = '\.pyi?$'
```

### isort

isort sorts imports alphabetically and automatically separates them into sections:

```bash
isort path/to/file.py
```

Configuration in pyproject.toml:
```toml
[tool.isort]
profile = "black"
line_length = 88
```

### flake8

flake8 is a Python linter:

```bash
flake8 path/to/file.py
```

Configuration in .flake8:
```ini
[flake8]
max-line-length = 88
extend-ignore = E203
```

### mypy

mypy is a static type checker:

```bash
mypy path/to/file.py
```

Configuration in pyproject.toml:
```toml
[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
```

### shellcheck

shellcheck is a shell script static analysis tool:

```bash
shellcheck path/to/file.sh
```

### Pre-commit Hooks

The project uses pre-commit hooks to enforce code quality standards:

```yaml
# .pre-commit-config.yaml
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files

-   repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
    -   id: black

-   repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
    -   id: isort

-   repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
    -   id: flake8

-   repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
    -   id: mypy
        additional_dependencies: [types-requests, types-PyYAML]

-   repo: https://github.com/koalaman/shellcheck-precommit
    rev: v0.9.0
    hooks:
    -   id: shellcheck
```

## Conclusion

Following these style guidelines ensures consistency across the codebase and makes it easier for developers to understand, maintain, and extend the code. If you have any questions or suggestions for improving these guidelines, please open an issue or pull request.