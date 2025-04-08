"""
Configuration settings module for the MCP-BASE-STACK project.

This module provides access to configuration settings with validation,
ensuring that required values are present and have the correct types.
"""

import os
import logging
from typing import Dict, Any, Optional, List, Union, Type, Callable
from dataclasses import dataclass, field

from core.config.loader import load_config

# Configure logging for the module itself
logger = logging.getLogger(__name__)


@dataclass
class ConfigValidationError:
    """Class representing a configuration validation error."""
    path: str
    message: str
    
    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


class ConfigValidator:
    """
    Validates configuration against a schema.
    
    This class provides methods to validate configuration values against
    a schema, ensuring that required values are present and have the correct types.
    """
    
    @staticmethod
    def validate(config: Dict[str, Any], schema: Dict[str, Any], path: str = "") -> List[ConfigValidationError]:
        """
        Validate configuration against a schema.
        
        Args:
            config: The configuration to validate.
            schema: The schema to validate against.
            path: The current path in the configuration (for nested validation).
            
        Returns:
            A list of validation errors, or an empty list if validation passed.
        """
        errors = []
        
        for key, schema_value in schema.items():
            current_path = f"{path}.{key}" if path else key
            
            # Check if the key exists in the configuration
            if key not in config:
                if isinstance(schema_value, dict) and schema_value.get("required", True):
                    errors.append(ConfigValidationError(current_path, "Required key is missing"))
                continue
            
            config_value = config[key]
            
            # If the schema value is a dictionary, it's either a nested schema or a schema definition
            if isinstance(schema_value, dict):
                # Check if it's a schema definition
                if "type" in schema_value:
                    # Validate the value against the schema definition
                    errors.extend(ConfigValidator._validate_value(config_value, schema_value, current_path))
                else:
                    # It's a nested schema, validate recursively
                    if not isinstance(config_value, dict):
                        errors.append(ConfigValidationError(current_path, f"Expected a dictionary, got {type(config_value).__name__}"))
                    else:
                        errors.extend(ConfigValidator.validate(config_value, schema_value, current_path))
            
            # If the schema value is a type, validate the type
            elif isinstance(schema_value, type):
                if not isinstance(config_value, schema_value):
                    errors.append(ConfigValidationError(
                        current_path,
                        f"Expected type {schema_value.__name__}, got {type(config_value).__name__}"
                    ))
        
        return errors
    
    @staticmethod
    def _validate_value(value: Any, schema: Dict[str, Any], path: str) -> List[ConfigValidationError]:
        """
        Validate a single value against a schema definition.
        
        Args:
            value: The value to validate.
            schema: The schema definition to validate against.
            path: The current path in the configuration.
            
        Returns:
            A list of validation errors, or an empty list if validation passed.
        """
        errors = []
        
        # Get the expected type
        expected_type = schema.get("type")
        if expected_type is None:
            return errors
        
        # Convert string type names to actual types
        if isinstance(expected_type, str):
            type_map = {
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict
            }
            expected_type = type_map.get(expected_type.lower(), str)
        
        # Validate the type
        if not isinstance(value, expected_type):
            errors.append(ConfigValidationError(
                path,
                f"Expected type {expected_type.__name__}, got {type(value).__name__}"
            ))
            return errors
        
        # Validate enum values
        if "enum" in schema and value not in schema["enum"]:
            errors.append(ConfigValidationError(
                path,
                f"Value must be one of {schema['enum']}, got {value}"
            ))
        
        # Validate minimum value
        if "min" in schema and value < schema["min"]:
            errors.append(ConfigValidationError(
                path,
                f"Value must be at least {schema['min']}, got {value}"
            ))
        
        # Validate maximum value
        if "max" in schema and value > schema["max"]:
            errors.append(ConfigValidationError(
                path,
                f"Value must be at most {schema['max']}, got {value}"
            ))
        
        # Validate minimum length
        if "min_length" in schema and len(value) < schema["min_length"]:
            errors.append(ConfigValidationError(
                path,
                f"Length must be at least {schema['min_length']}, got {len(value)}"
            ))
        
        # Validate maximum length
        if "max_length" in schema and len(value) > schema["max_length"]:
            errors.append(ConfigValidationError(
                path,
                f"Length must be at most {schema['max_length']}, got {len(value)}"
            ))
        
        # Validate pattern
        if "pattern" in schema and hasattr(value, "match") and not value.match(schema["pattern"]):
            errors.append(ConfigValidationError(
                path,
                f"Value must match pattern {schema['pattern']}"
            ))
        
        # Validate custom validator
        if "validator" in schema and callable(schema["validator"]):
            try:
                if not schema["validator"](value):
                    errors.append(ConfigValidationError(
                        path,
                        f"Value failed custom validation"
                    ))
            except Exception as e:
                errors.append(ConfigValidationError(
                    path,
                    f"Custom validation error: {str(e)}"
                ))
        
        return errors


# Define schemas for different configuration sections

LOGGING_SCHEMA = {
    "level": {
        "type": str,
        "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        "required": True
    },
    "format": {
        "type": str,
        "required": True
    },
    "date_format": {
        "type": str,
        "required": True
    },
    "directory": {
        "type": str,
        "required": True
    }
}

QUALITY_SCHEMA = {
    "enforcer": {
        "enabled": {
            "type": bool,
            "required": True
        },
        "hooks_directory": {
            "type": str,
            "required": True
        },
        "report_directory": {
            "type": str,
            "required": True
        }
    }
}

DOCUMENTATION_SCHEMA = {
    "output_directory": {
        "type": str,
        "required": True
    },
    "templates_directory": {
        "type": str,
        "required": True
    },
    "auto_generate": {
        "type": bool,
        "required": True
    }
}

# Cache for loaded configuration
_config_cache = {}


def get_config(environment: str = None, validate: bool = True) -> Dict[str, Any]:
    """
    Get the configuration for the specified environment.
    
    Args:
        environment: The environment to get configuration for (dev, test, prod).
            If None, it will try to determine from the MCP_ENV environment variable,
            defaulting to 'dev' if not set.
        validate: Whether to validate the configuration against schemas.
            
    Returns:
        A dictionary containing the configuration.
        
    Raises:
        ValueError: If validation is enabled and the configuration is invalid.
    """
    # Determine the environment
    if environment is None:
        environment = os.environ.get("MCP_ENV", "dev")
    
    # Check if the configuration is already cached
    cache_key = f"{environment}_{validate}"
    if cache_key in _config_cache:
        return _config_cache[cache_key]
    
    # Load the configuration
    config = load_config(environment)
    
    # Validate the configuration if requested
    if validate:
        errors = []
        
        # Validate logging configuration
        if "logging" in config:
            errors.extend(ConfigValidator.validate(config["logging"], LOGGING_SCHEMA, "logging"))
        
        # Validate quality configuration
        if "quality" in config:
            errors.extend(ConfigValidator.validate(config["quality"], QUALITY_SCHEMA, "quality"))
        
        # Validate documentation configuration
        if "documentation" in config:
            errors.extend(ConfigValidator.validate(config["documentation"], DOCUMENTATION_SCHEMA, "documentation"))
        
        # Raise an error if there are validation errors
        if errors:
            error_messages = "\n".join(str(error) for error in errors)
            raise ValueError(f"Configuration validation failed:\n{error_messages}")
    
    # Cache the configuration
    _config_cache[cache_key] = config
    
    return config


def get_logging_config(environment: str = None) -> Dict[str, Any]:
    """
    Get the logging configuration for the specified environment.
    
    Args:
        environment: The environment to get configuration for (dev, test, prod).
            If None, it will try to determine from the MCP_ENV environment variable,
            defaulting to 'dev' if not set.
            
    Returns:
        A dictionary containing the logging configuration.
        
    Raises:
        ValueError: If the configuration is invalid.
        KeyError: If the logging configuration section is missing.
    """
    config = get_config(environment)
    
    if "logging" not in config:
        raise KeyError("Logging configuration section is missing")
    
    return config["logging"]


def get_quality_config(environment: str = None) -> Dict[str, Any]:
    """
    Get the quality configuration for the specified environment.
    
    Args:
        environment: The environment to get configuration for (dev, test, prod).
            If None, it will try to determine from the MCP_ENV environment variable,
            defaulting to 'dev' if not set.
            
    Returns:
        A dictionary containing the quality configuration.
        
    Raises:
        ValueError: If the configuration is invalid.
        KeyError: If the quality configuration section is missing.
    """
    config = get_config(environment)
    
    if "quality" not in config:
        raise KeyError("Quality configuration section is missing")
    
    return config["quality"]


def get_documentation_config(environment: str = None) -> Dict[str, Any]:
    """
    Get the documentation configuration for the specified environment.
    
    Args:
        environment: The environment to get configuration for (dev, test, prod).
            If None, it will try to determine from the MCP_ENV environment variable,
            defaulting to 'dev' if not set.
            
    Returns:
        A dictionary containing the documentation configuration.
        
    Raises:
        ValueError: If the configuration is invalid.
        KeyError: If the documentation configuration section is missing.
    """
    config = get_config(environment)
    
    if "documentation" not in config:
        raise KeyError("Documentation configuration section is missing")
    
    return config["documentation"]


def clear_config_cache():
    """Clear the configuration cache."""
    global _config_cache
    _config_cache = {}