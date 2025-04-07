# MCP-BASE-STACK Coding Conventions

This document outlines the specific coding practices and patterns to be followed in the MCP-BASE-STACK project. While the [Style Guide](./style-guide.md) covers formatting and naming conventions, this document focuses on implementation patterns and best practices.

## Table of Contents

1. [Python Coding Conventions](#python-coding-conventions)
2. [Shell Script Conventions](#shell-script-conventions)
3. [Knowledge Graph Integration](#knowledge-graph-integration)
4. [Error Handling Patterns](#error-handling-patterns)
5. [Configuration Management](#configuration-management)
6. [Logging Practices](#logging-practices)
7. [Security Practices](#security-practices)
8. [Performance Considerations](#performance-considerations)

## Python Coding Conventions

### Function and Method Design

- **Single Responsibility**: Each function or method should do exactly one thing and do it well.
  ```python
  # Good
  def validate_config(config):
      """Validate configuration."""
      # ...
  
  def load_config(path):
      """Load configuration from path."""
      # ...
  
  # Bad
  def load_and_validate_config(path):
      """Load and validate configuration."""
      # Load config
      # ...
      # Validate config
      # ...
  ```

- **Function Length**: Keep functions short and focused (preferably under 30 lines).

- **Parameter Count**: Limit the number of parameters (preferably 5 or fewer).
  ```python
  # Good
  def process_data(config, data):
      """Process data using configuration."""
      # ...
  
  # Better (for many parameters)
  def process_data(config):
      """Process data using configuration object."""
      # ...
  ```

- **Return Values**: Be consistent with return values. Prefer returning objects over tuples.
  ```python
  # Good
  def get_user_info(user_id):
      """Get user information."""
      return UserInfo(name="John", age=30)
  
  # Avoid
  def get_user_info(user_id):
      """Get user information."""
      return "John", 30
  ```

### Class Design

- **Inheritance**: Use inheritance sparingly. Prefer composition over inheritance.
  ```python
  # Good (composition)
  class ConfigManager:
      def __init__(self, validator):
          self.validator = validator
      
      def validate(self, config):
          return self.validator.validate(config)
  
  # Avoid (inheritance) when composition is clearer
  class ConfigManager(ConfigValidator):
      pass
  ```

- **Abstract Base Classes**: Use ABC for defining interfaces.
  ```python
  from abc import ABC, abstractmethod
  
  class Validator(ABC):
      @abstractmethod
      def validate(self, data):
          """Validate data."""
          pass
  ```

- **Properties**: Use properties instead of getter/setter methods.
  ```python
  # Good
  class User:
      def __init__(self, name):
          self._name = name
      
      @property
      def name(self):
          return self._name
      
      @name.setter
      def name(self, value):
          if not value:
              raise ValueError("Name cannot be empty")
          self._name = value
  
  # Avoid
  class User:
      def __init__(self, name):
          self._name = name
      
      def get_name(self):
          return self._name
      
      def set_name(self, value):
          if not value:
              raise ValueError("Name cannot be empty")
          self._name = value
  ```

### Module Organization

- **Initialization**: Use `__init__.py` files to expose a clean API.
  ```python
  # mcp_base_stack/core/__init__.py
  from .config import ConfigManager, load_config
  from .error import MCPBaseStackError, ErrorCode
  
  __all__ = ['ConfigManager', 'load_config', 'MCPBaseStackError', 'ErrorCode']
  ```

- **Private Functions**: Use underscore prefix for private functions.
  ```python
  def _internal_helper():
      """Internal helper function."""
      pass
  
  def public_function():
      """Public function."""
      _internal_helper()
  ```

### Type Hints

- **Use Type Hints**: Always use type hints for function parameters and return values.
  ```python
  def process_data(data: List[Dict[str, Any]]) -> Dict[str, int]:
      """Process data and return results."""
      # ...
  ```

- **Type Aliases**: Use type aliases for complex types.
  ```python
  from typing import Dict, List, TypeVar, Union
  
  ConfigType = Dict[str, Union[str, int, bool, List[str]]]
  
  def load_config(path: str) -> ConfigType:
      """Load configuration from path."""
      # ...
  ```

- **Optional Types**: Use Optional for parameters that can be None.
  ```python
  def get_config(key: str, default: Optional[str] = None) -> Optional[str]:
      """Get configuration value."""
      # ...
  ```

### Context Managers

- **Resource Management**: Use context managers for resource management.
  ```python
  # Good
  with open("file.txt", "r") as f:
      content = f.read()
  
  # Avoid
  f = open("file.txt", "r")
  content = f.read()
  f.close()
  ```

- **Custom Context Managers**: Implement context managers for custom resources.
  ```python
  class DatabaseConnection:
      def __enter__(self):
          self.connect()
          return self
      
      def __exit__(self, exc_type, exc_val, exc_tb):
          self.disconnect()
  ```

## Shell Script Conventions

### Script Structure

- **Shebang Line**: Always include a shebang line.
  ```bash
  #!/bin/bash
  ```

- **Script Description**: Include a description at the top of the script.
  ```bash
  #!/bin/bash
  #
  # Description: This script performs a health check on the MCP-BASE-STACK.
  ```

- **Exit on Error**: Use `set -e` to exit on error.
  ```bash
  #!/bin/bash
  
  # Exit on error
  set -e
  ```

- **Function Definitions**: Define functions at the top of the script.
  ```bash
  #!/bin/bash
  
  # Function to check if a file exists
  check_file() {
    local file="$1"
    if [ ! -f "$file" ]; then
      echo "Error: File $file not found"
      return 1
    fi
    return 0
  }
  
  # Main script logic
  main() {
    # ...
  }
  
  # Call main function
  main "$@"
  ```

### Variable Usage

- **Quote Variables**: Always quote variables.
  ```bash
  # Good
  file_name="example.txt"
  if [ -f "$file_name" ]; then
    # ...
  fi
  
  # Bad
  file_name=example.txt
  if [ -f $file_name ]; then
    # ...
  fi
  ```

- **Local Variables**: Use `local` for function-local variables.
  ```bash
  function process_file() {
    local file_name="$1"
    # ...
  }
  ```

- **Default Values**: Use `${var:-default}` for default values.
  ```bash
  config_file="${CONFIG_FILE:-config.yaml}"
  ```

### Command Substitution

- **Use $()**: Use `$()` for command substitution, not backticks.
  ```bash
  # Good
  current_date=$(date +"%Y-%m-%d")
  
  # Bad
  current_date=`date +"%Y-%m-%d"`
  ```

### Error Handling

- **Check Return Codes**: Always check return codes for critical operations.
  ```bash
  if ! command_that_might_fail; then
    echo "Error: Command failed"
    exit 1
  fi
  ```

- **Error Function**: Define an error function for consistent error handling.
  ```bash
  error() {
    local message="$1"
    local exit_code="${2:-1}"
    echo "Error: $message" >&2
    exit "$exit_code"
  }
  
  # Usage
  if [ ! -f "$config_file" ]; then
    error "Config file not found" 2
  fi
  ```

- **Trap Errors**: Use trap to handle errors.
  ```bash
  # Function to handle errors
  handle_error() {
    local exit_code=$1
    local line_number=$2
    echo "Error on line $line_number, exit code $exit_code"
    exit $exit_code
  }
  
  # Set up error trap
  trap 'handle_error $? $LINENO' ERR
  ```

## Knowledge Graph Integration

### Node Creation

- **Node Types**: Use consistent node types.
  ```python
  # Component node
  kg.add_node(
      "component_id",
      type="component",
      name="Component Name",
      status="implemented"
  )
  
  # File node
  kg.add_node(
      "file_id",
      type="file",
      path="path/to/file.py",
      language="python"
  )
  ```

- **Node IDs**: Use consistent naming for node IDs.
  ```python
  # Component IDs: lowercase with underscores
  component_id = "knowledge_graph"
  
  # File IDs: derived from path, lowercase with underscores
  file_id = "kg_module_py"
  ```

### Relationship Creation

- **Relationship Types**: Use consistent relationship types.
  ```python
  # Component contains file
  kg.add_edge(
      "component_id",
      "file_id",
      relation="contains"
  )
  
  # Component implements feature
  kg.add_edge(
      "component_id",
      "feature_id",
      relation="implements"
  )
  ```

- **Relationship Validation**: Validate relationships before adding them.
  ```python
  if kg.has_node(source_id) and kg.has_node(target_id):
      kg.add_edge(source_id, target_id, relation=relation_type)
  else:
      logging.error(f"Cannot create relationship: nodes not found")
  ```

### Knowledge Graph Updates

- **Atomic Updates**: Make knowledge graph updates atomic.
  ```python
  def update_knowledge_graph():
      """Update the knowledge graph."""
      # Create a transaction or use a temporary graph
      temp_graph = kg.copy()
      
      try:
          # Make changes to temp_graph
          # ...
          
          # Commit changes
          kg.update(temp_graph)
      except Exception as e:
          logging.error(f"Failed to update knowledge graph: {e}")
          # Rollback or handle error
  ```

- **Update Verification**: Verify updates after making them.
  ```python
  def verify_update(node_id, expected_attributes):
      """Verify that a node was updated correctly."""
      node = kg.get_node(node_id)
      for key, value in expected_attributes.items():
          if node.get(key) != value:
              return False
      return True
  ```

## Error Handling Patterns

### Exception Hierarchy

- **Base Exception**: Use a base exception for all project-specific exceptions.
  ```python
  class MCPBaseStackError(Exception):
      """Base exception for all MCP-BASE-STACK exceptions."""
      pass
  ```

- **Specific Exceptions**: Create specific exceptions for different error categories.
  ```python
  class ConfigError(MCPBaseStackError):
      """Exception for configuration errors."""
      pass
  
  class DockerError(MCPBaseStackError):
      """Exception for Docker-related errors."""
      pass
  ```

### Try-Except Blocks

- **Specific Exceptions**: Catch specific exceptions, not `Exception`.
  ```python
  # Good
  try:
      config.load()
  except ConfigError as e:
      logging.error(f"Configuration error: {e}")
  except IOError as e:
      logging.error(f"I/O error: {e}")
  
  # Avoid
  try:
      config.load()
  except Exception as e:
      logging.error(f"Error: {e}")
  ```

- **Exception Chaining**: Use exception chaining to preserve context.
  ```python
  try:
      config.load()
  except IOError as e:
      raise ConfigError("Failed to load configuration") from e
  ```

- **Finally Block**: Use finally for cleanup.
  ```python
  connection = None
  try:
      connection = database.connect()
      # ...
  except DatabaseError as e:
      logging.error(f"Database error: {e}")
  finally:
      if connection:
          connection.close()
  ```

### Error Logging

- **Log Context**: Include context in error logs.
  ```python
  try:
      process_file(file_path)
  except IOError as e:
      logging.error(f"Failed to process file {file_path}: {e}")
  ```

- **Log Levels**: Use appropriate log levels.
  ```python
  # Critical error
  logging.critical("Database connection failed, system cannot function")
  
  # Error that prevents a specific operation
  logging.error(f"Failed to process file {file_path}")
  
  # Warning about potential issues
  logging.warning(f"File {file_path} is larger than recommended size")
  
  # Informational message
  logging.info(f"Processing file {file_path}")
  
  # Debug information
  logging.debug(f"File {file_path} has {line_count} lines")
  ```

## Configuration Management

### Configuration Sources

- **Environment Variables**: Use environment variables for deployment-specific configuration.
  ```python
  import os
  
  database_url = os.environ.get("DATABASE_URL", "localhost:5432")
  ```

- **Configuration Files**: Use configuration files for complex configuration.
  ```python
  import yaml
  
  with open("config.yaml", "r") as f:
      config = yaml.safe_load(f)
  ```

- **Default Configuration**: Define default configuration in code.
  ```python
  DEFAULT_CONFIG = {
      "database": {
          "host": "localhost",
          "port": 5432,
          "username": "user",
          "password": "password",
          "database": "db"
      },
      "logging": {
          "level": "INFO",
          "file": "app.log"
      }
  }
  ```

### Configuration Validation

- **Schema Validation**: Validate configuration against a schema.
  ```python
  from pydantic import BaseModel, Field
  
  class DatabaseConfig(BaseModel):
      host: str = Field(default="localhost")
      port: int = Field(default=5432)
      username: str
      password: str
      database: str
  
  class Config(BaseModel):
      database: DatabaseConfig
      logging: LoggingConfig
  
  # Validate configuration
  try:
      config = Config(**raw_config)
  except ValidationError as e:
      logging.error(f"Invalid configuration: {e}")
  ```

- **Configuration Access**: Use a centralized configuration manager.
  ```python
  class ConfigManager:
      def __init__(self, config_path):
          self.config = self._load_config(config_path)
      
      def _load_config(self, config_path):
          # Load and validate configuration
          # ...
      
      def get(self, key, default=None):
          """Get a configuration value."""
          # ...
      
      def get_section(self, section):
          """Get a configuration section."""
          # ...
  ```

## Logging Practices

### Logger Configuration

- **Logger Setup**: Configure loggers at application startup.
  ```python
  import logging
  
  def configure_logging(config):
      """Configure logging based on configuration."""
      logging.basicConfig(
          level=getattr(logging, config.get("level", "INFO")),
          format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
          datefmt="%Y-%m-%d %H:%M:%S",
          filename=config.get("file"),
          filemode="a"
      )
  ```

- **Module Loggers**: Use module-level loggers.
  ```python
  import logging
  
  # Create a module-level logger
  logger = logging.getLogger(__name__)
  
  def process_data(data):
      """Process data."""
      logger.info(f"Processing {len(data)} items")
      # ...
  ```

### Log Messages

- **Structured Logging**: Use structured logging for machine-readable logs.
  ```python
  import json
  
  def log_structured(level, message, **kwargs):
      """Log a structured message."""
      log_data = {
          "message": message,
          **kwargs
      }
      logger.log(level, json.dumps(log_data))
  
  # Usage
  log_structured(
      logging.INFO,
      "User logged in",
      user_id=123,
      ip_address="192.168.1.1"
  )
  ```

- **Log Context**: Include relevant context in log messages.
  ```python
  logger.info(f"Processing file {file_path} ({file_size} bytes)")
  ```

## Security Practices

### Input Validation

- **Validate All Input**: Validate all input from external sources.
  ```python
  def process_user_input(user_input):
      """Process user input."""
      # Validate input
      if not isinstance(user_input, str):
          raise ValueError("User input must be a string")
      
      if len(user_input) > 1000:
          raise ValueError("User input too long")
      
      # Process input
      # ...
  ```

- **Parameterized Queries**: Use parameterized queries for database operations.
  ```python
  # Good
  cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
  
  # Bad
  cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
  ```

### Secrets Management

- **Environment Variables**: Store secrets in environment variables.
  ```python
  import os
  
  database_password = os.environ.get("DATABASE_PASSWORD")
  ```

- **Secret Files**: Store secrets in separate files with restricted permissions.
  ```python
  def load_secret(secret_path):
      """Load a secret from a file."""
      try:
          with open(secret_path, "r") as f:
              return f.read().strip()
      except IOError as e:
          logging.error(f"Failed to load secret from {secret_path}: {e}")
          return None
  ```

- **No Hardcoded Secrets**: Never hardcode secrets in source code.
  ```python
  # Bad
  API_KEY = "1234567890abcdef"
  
  # Good
  API_KEY = os.environ.get("API_KEY")
  ```

## Performance Considerations

### Resource Management

- **Close Resources**: Always close resources when done.
  ```python
  # Good
  with open("file.txt", "r") as f:
      content = f.read()
  
  # Bad
  f = open("file.txt", "r")
  content = f.read()
  # Resource leak if an exception occurs before f.close()
  ```

- **Connection Pooling**: Use connection pooling for database connections.
  ```python
  from sqlalchemy import create_engine
  
  engine = create_engine("postgresql://user:password@localhost/db", pool_size=5, max_overflow=10)
  ```

### Efficient Data Processing

- **Generators**: Use generators for processing large datasets.
  ```python
  def process_large_file(file_path):
      """Process a large file line by line."""
      with open(file_path, "r") as f:
          for line in f:
              yield process_line(line)
  
  # Usage
  for result in process_large_file("large_file.txt"):
      print(result)
  ```

- **Batch Processing**: Process data in batches.
  ```python
  def process_items(items, batch_size=100):
      """Process items in batches."""
      for i in range(0, len(items), batch_size):
          batch = items[i:i+batch_size]
          process_batch(batch)
  ```

### Caching

- **Memoization**: Use memoization for expensive function calls.
  ```python
  from functools import lru_cache
  
  @lru_cache(maxsize=100)
  def expensive_calculation(x):
      """Perform an expensive calculation."""
      # ...
      return result
  ```

- **Cache Invalidation**: Implement proper cache invalidation.
  ```python
  class Cache:
      def __init__(self):
          self.data = {}
          self.timestamps = {}
      
      def get(self, key, max_age=None):
          """Get a value from the cache."""
          if key not in self.data:
              return None
          
          if max_age is not None:
              timestamp = self.timestamps.get(key, 0)
              if time.time() - timestamp > max_age:
                  # Cache entry is too old
                  del self.data[key]
                  del self.timestamps[key]
                  return None
          
          return self.data[key]
      
      def set(self, key, value):
          """Set a value in the cache."""
          self.data[key] = value
          self.timestamps[key] = time.time()
  ```

## Conclusion

Following these coding conventions ensures that the MCP-BASE-STACK codebase is consistent, maintainable, and robust. These conventions should be used in conjunction with the [Style Guide](./style-guide.md) to ensure a high-quality codebase.

If you have any questions or suggestions for improving these conventions, please open an issue or pull request.