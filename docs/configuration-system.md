# Configuration System

This document describes the configuration system for the MCP-BASE-STACK project.

## Overview

The configuration system provides a unified approach to managing configuration settings across the project. It supports:

- YAML-based configuration files
- Environment variable overrides
- Different environments (dev, test, prod)
- Configuration validation
- Sensible defaults

## Directory Structure

The configuration system uses the following directory structure:

```
config/
  environments/
    dev.yaml    # Development environment configuration
    test.yaml   # Test environment configuration
    prod.yaml   # Production environment configuration
core/
  config/
    __init__.py  # Package initialization
    loader.py    # Configuration loading functionality
    settings.py  # Configuration access and validation
```

## Configuration Files

Configuration files are YAML files located in the `config/environments/` directory. Each environment (dev, test, prod) has its own configuration file.

Example configuration file (`config/environments/dev.yaml`):

```yaml
# Development Environment Configuration

logging:
  level: DEBUG
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  date_format: "%Y-%m-%d %H:%M:%S"
  directory: "data/logs"

quality:
  enforcer:
    enabled: true
    hooks_directory: "core/quality/hooks"
    report_directory: "data/reports"

documentation:
  output_directory: "docs"
  templates_directory: "core/documentation/templates"
  auto_generate: true
```

## Environment Variables

Configuration values can be overridden using environment variables. The system looks for environment variables with the prefix `MCP_` and applies them as overrides to the configuration.

For example:
- `MCP_LOGGING_LEVEL=DEBUG` overrides the `logging.level` configuration value
- `MCP_QUALITY_ENFORCER_ENABLED=false` overrides the `quality.enforcer.enabled` configuration value

The environment variable `MCP_ENV` can be used to specify which environment configuration to load (dev, test, prod). If not set, it defaults to `dev`.

## Using the Configuration System

### Getting Configuration Values

The configuration system provides several functions to access configuration values:

```python
from core.config import get_config, get_logging_config, get_quality_config, get_documentation_config

# Get the entire configuration
config = get_config()

# Get specific configuration sections
logging_config = get_logging_config()
quality_config = get_quality_config()
documentation_config = get_documentation_config()

# Access configuration values
log_level = logging_config["level"]
log_directory = logging_config["directory"]
```

### Loading Configuration

The configuration system automatically loads the appropriate configuration based on the environment. You can also explicitly load configuration for a specific environment:

```python
from core.config import get_config

# Load configuration for the test environment
test_config = get_config(environment="test")
```

### Configuration Validation

The configuration system validates configuration values against schemas to ensure they have the correct types and values. If validation fails, a `ValueError` is raised with details about the validation errors.

## Default Configuration

If a configuration file is not found or a configuration value is not specified, the system provides sensible defaults:

```python
# Default configuration
{
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "date_format": "%Y-%m-%d %H:%M:%S",
        "directory": "data/logs"
    },
    "quality": {
        "enforcer": {
            "enabled": True,
            "hooks_directory": "core/quality/hooks",
            "report_directory": "data/reports"
        }
    },
    "documentation": {
        "output_directory": "docs",
        "templates_directory": "core/documentation/templates",
        "auto_generate": True
    }
}
```

## Environment-Specific Configuration

The configuration system provides different default settings for each environment:

- **Development (dev)**:
  - Logging level: `DEBUG`
  - Auto-generate documentation: `true`

- **Test (test)**:
  - Logging level: `INFO`
  - Auto-generate documentation: `false`

- **Production (prod)**:
  - Logging level: `WARNING`
  - Auto-generate documentation: `false`

## Extending the Configuration System

To add new configuration sections or values:

1. Update the default configuration in `core.config.loader._get_default_config()`
2. Add a schema for validation in `core.config.settings`
3. Update the environment-specific configuration files in `config/environments/`
4. Add getter functions in `core.config.settings` if needed

## Best Practices

- Always use the configuration system instead of hardcoding values
- Use environment variables for sensitive information (e.g., API keys, passwords)
- Use environment variables for deployment-specific settings
- Keep configuration files in version control, but exclude sensitive information
- Use validation to catch configuration errors early