"""
Configuration module for the MCP-BASE-STACK project.

This module provides a unified configuration system for the project,
supporting YAML-based configuration files, environment variable overrides,
and different environments (dev, test, prod).

The configuration system is designed to be flexible, maintainable, and
provide sensible defaults with validation.
"""

from core.config.settings import (
    get_config,
    get_logging_config,
    get_quality_config,
    get_documentation_config
)

from core.config.loader import (
    load_config,
    load_config_from_file,
    load_config_from_env
)

__all__ = [
    'get_config',
    'get_logging_config',
    'get_quality_config',
    'get_documentation_config',
    'load_config',
    'load_config_from_file',
    'load_config_from_env'
]