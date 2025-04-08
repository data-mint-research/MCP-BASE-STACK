# Logging System Documentation

## Overview

The MCP-BASE-STACK logging system provides a standardized approach to logging across the entire project. It ensures that logs are consistently formatted, properly organized, and easily accessible for debugging and monitoring purposes.

The logging system consists of two main components:

1. **LogDirectoryManager** - Manages the creation and organization of log directories and files
2. **LoggingConfig** - Configures loggers with standardized settings and handlers

These components work together to provide a robust logging infrastructure that follows best practices and maintains a consistent structure across all modules.

### Key Benefits

- **Standardized Structure**: All logs follow the same directory structure and naming conventions
- **Module Isolation**: Each module's logs are stored in separate directories for easy identification
- **Automatic Directory Creation**: Log directories are created automatically when needed
- **Consistent Formatting**: All log messages follow the same format for easier parsing and analysis
- **Multiple Output Targets**: Logs are sent to both console and files by default
- **Flexible Log Levels**: Support for different logging levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Directory Structure

The logging system uses a hierarchical directory structure to organize logs by module:

```
docs/
└── logs/
    ├── module1/
    │   ├── YYYY-MM-DD_module1-log
    │   └── ...
    ├── module2/
    │   ├── YYYY-MM-DD_module2-log
    │   └── ...
    └── ...
```

### Base Directory

The base directory for all logs is `docs/logs/`. This is defined as `LOG_BASE_DIR` in the `LogDirectoryManager` module.

### Module-Specific Directories

Each module has its own subdirectory under the base directory. This helps to:

- Isolate logs from different modules
- Make it easier to find logs for a specific module
- Prevent log files from becoming too large

### Directory Creation

Directories are created automatically by the `LogDirectoryManager` when needed:

- The base log directory is created if it doesn't exist
- Module-specific directories are created when a logger is configured for that module
- Appropriate error handling is in place for permission issues

## Naming Conventions

### Log File Naming

Log files follow a standardized naming convention:

```
YYYY-MM-DD_module-name-log
```

Where:
- `YYYY-MM-DD` is the date when the log file was created
- `module-name` is the name of the module that the log file belongs to

This naming convention provides several benefits:
- Files are automatically sorted chronologically
- The module name is clearly visible in the filename
- The purpose of the file (log) is indicated in the filename

### Module Naming Recommendations

When choosing module names for logging:

- Use lowercase names for consistency
- Use underscores instead of spaces
- Keep names short but descriptive
- Use the same module name across the codebase for consistency

For example, use `database_connector` instead of `Database Connector Module`.

## Usage Examples

### Basic Logger Configuration

To configure a basic logger with the default INFO level:

```python
from core.logging.config import configure_logger

# Configure a logger for your module
logger = configure_logger("my_module")

# Use the logger
logger.info("Application started")
logger.warning("Resource usage is high")
logger.error("Failed to connect to database")
```

### Setting Different Log Levels

You can configure loggers with different log levels:

```python
from core.logging.config import configure_logger

# Configure a logger with DEBUG level
debug_logger = configure_logger("debug_module", "DEBUG")

# Configure a logger with WARNING level
warning_logger = configure_logger("warning_module", "WARNING")

# The DEBUG level logger will show all messages
debug_logger.debug("This debug message will be shown")
debug_logger.info("This info message will be shown")

# The WARNING level logger will only show WARNING and above
warning_logger.debug("This debug message will NOT be shown")
warning_logger.info("This info message will NOT be shown")
warning_logger.warning("This warning message will be shown")
```

### Module-Specific Logging

You can create separate loggers for different modules:

```python
from core.logging.config import configure_logger

# Configure loggers for different modules
auth_logger = configure_logger("authentication")
db_logger = configure_logger("database")
api_logger = configure_logger("api")

# Use module-specific loggers
auth_logger.info("User logged in: user123")
db_logger.error("Database connection failed")
api_logger.warning("API rate limit approaching")
```

### Error Handling with Logging

Use logging to capture exceptions with tracebacks:

```python
import logging
from core.logging.config import configure_logger

# Configure a logger
logger = configure_logger("error_handler")

try:
    # Some code that might raise an exception
    result = 10 / 0
except Exception as e:
    # Log the error with traceback
    logger.error(f"An error occurred: {str(e)}", exc_info=True)
    
    # Or alternatively:
    logger.exception("An error occurred during calculation")
```

### Checking Log File Paths

You can get the path to a module's log file:

```python
from core.logging.directory_manager import get_log_file_path

# Get the log file path for a module
log_path = get_log_file_path("my_module")
print(f"Logs are being written to: {log_path}")
```

### Verifying Log Directory Structure

You can verify that the log directory structure is valid:

```python
from core.logging.directory_manager import verify_log_directory_structure

# Verify the log directory structure
if not verify_log_directory_structure():
    print("Log directory structure is not valid. Creating it...")
    # Take appropriate action
```

## Troubleshooting

### Common Issues and Solutions

#### Permission Errors

**Issue**: Permission errors when creating log directories or files.

**Solution**:
- Ensure your user has write permissions to the `docs/logs` directory
- Check if the directory is owned by a different user
- Try running the application with elevated privileges if appropriate

**Example Error**:
```
PermissionError: [Errno 13] Permission denied: 'docs/logs/my_module'
```

#### Missing Log Files

**Issue**: Log files are not being created.

**Solution**:
- Verify that the log directory structure is valid using `verify_log_directory_structure()`
- Check if the base log directory exists
- Ensure there are no permission issues
- Make sure the logger is properly configured

#### Duplicate Log Entries

**Issue**: The same log entries appear multiple times.

**Solution**:
- This can happen if you configure the same logger multiple times
- Make sure you're not creating multiple logger instances for the same module
- The `configure_logger` function clears existing handlers to prevent this

#### Incorrect Log Levels

**Issue**: Some log messages are not appearing.

**Solution**:
- Check the log level of your logger
- Remember that loggers filter messages based on their level:
  - DEBUG shows all messages
  - INFO shows INFO, WARNING, ERROR, and CRITICAL
  - WARNING shows WARNING, ERROR, and CRITICAL
  - ERROR shows ERROR and CRITICAL
  - CRITICAL shows only CRITICAL

#### Invalid Log Level Error

**Issue**: ValueError when configuring a logger.

**Solution**:
- Make sure you're using a valid log level
- Valid levels are: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
- Log levels are case-sensitive

**Example Error**:
```
ValueError: Invalid logging level: DEBUG_LEVEL. Valid levels are: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Debugging Tips

1. **Enable DEBUG Level**: Configure your logger with the "DEBUG" level during development to see all log messages.

2. **Check Log File Contents**: Examine the log files directly to ensure messages are being written correctly.

3. **Verify Directory Structure**: Use `verify_log_directory_structure()` to check if the log directory structure is valid.

4. **Use Console Output**: Remember that logs are sent to both files and the console by default, so check your console output.

5. **Inspect Logger Configuration**: Print the logger's level and handlers to verify it's configured correctly:
   ```python
   logger = configure_logger("my_module")
   print(f"Logger level: {logger.level}")
   print(f"Logger handlers: {logger.handlers}")
   ```

## Advanced Usage

### Custom Formatters

The default log format is:
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

If you need a custom format, you can modify the `DEFAULT_LOG_FORMAT` constant in `core/logging/config.py`.

### Log Rotation

The current implementation does not include log rotation. For production environments, consider implementing log rotation to prevent log files from growing too large.

### Integration with External Logging Systems

To integrate with external logging systems (like ELK, Splunk, etc.), you can add custom handlers to your loggers after configuration:

```python
import logging
from core.logging.config import configure_logger

# Configure a logger
logger = configure_logger("my_module")

# Add a custom handler (example)
custom_handler = logging.Handler()  # Replace with your custom handler
custom_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
logger.addHandler(custom_handler)