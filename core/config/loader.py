"""
Configuration loader module for the MCP-BASE-STACK project.

This module provides functionality to load configuration from YAML files
and environment variables, with support for different environments.
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# Configure logging for the module itself
logger = logging.getLogger(__name__)

# Default configuration directory
DEFAULT_CONFIG_DIR = os.path.join("config", "environments")

# Environment variable prefix for configuration overrides
ENV_PREFIX = "MCP_"


def load_config(environment: str = None) -> Dict[str, Any]:
    """
    Load configuration for the specified environment.
    
    This function loads configuration from a YAML file for the specified
    environment, then applies any environment variable overrides.
    
    Args:
        environment: The environment to load configuration for (dev, test, prod).
            If None, it will try to determine from the MCP_ENV environment variable,
            defaulting to 'dev' if not set.
            
    Returns:
        A dictionary containing the loaded configuration.
        
    Raises:
        FileNotFoundError: If the configuration file for the specified environment
            cannot be found.
        yaml.YAMLError: If there is an error parsing the YAML configuration file.
    """
    # Determine the environment
    if environment is None:
        environment = os.environ.get("MCP_ENV", "dev")
    
    logger.info(f"Loading configuration for environment: {environment}")
    
    # Load configuration from file
    config = load_config_from_file(environment)
    
    # Apply environment variable overrides
    config = load_config_from_env(config)
    
    return config


def load_config_from_file(environment: str) -> Dict[str, Any]:
    """
    Load configuration from a YAML file for the specified environment.
    
    Args:
        environment: The environment to load configuration for (dev, test, prod).
            
    Returns:
        A dictionary containing the loaded configuration.
        
    Raises:
        FileNotFoundError: If the configuration file for the specified environment
            cannot be found.
        yaml.YAMLError: If there is an error parsing the YAML configuration file.
    """
    # Determine the configuration file path
    config_file = os.path.join(DEFAULT_CONFIG_DIR, f"{environment}.yaml")
    
    # Check if the file exists
    if not os.path.exists(config_file):
        # Try with .yml extension
        config_file = os.path.join(DEFAULT_CONFIG_DIR, f"{environment}.yml")
        
        if not os.path.exists(config_file):
            # If still not found, use default configuration
            logger.warning(f"Configuration file for environment '{environment}' not found.")
            return _get_default_config()
    
    try:
        # Load the configuration file
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
            
        logger.info(f"Loaded configuration from file: {config_file}")
        return config
        
    except (yaml.YAMLError, IOError) as e:
        logger.error(f"Error loading configuration from file: {str(e)}")
        # Fall back to default configuration
        logger.warning("Using default configuration.")
        return _get_default_config()


def load_config_from_env(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply environment variable overrides to the configuration.
    
    This function looks for environment variables with the prefix MCP_
    and applies them as overrides to the configuration.
    
    Args:
        config: The configuration dictionary to apply overrides to.
            
    Returns:
        The updated configuration dictionary.
    """
    # Create a copy of the configuration to avoid modifying the original
    config = config.copy()
    
    # Get all environment variables with the prefix
    env_vars = {k: v for k, v in os.environ.items() if k.startswith(ENV_PREFIX)}
    
    # Apply overrides
    for key, value in env_vars.items():
        # Remove the prefix
        config_key = key[len(ENV_PREFIX):].lower()
        
        # Handle nested keys (e.g., MCP_LOGGING_LEVEL -> logging.level)
        if '_' in config_key:
            parts = config_key.split('_')
            current = config
            
            # Navigate to the nested dictionary
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Set the value
            current[parts[-1]] = _convert_value(value)
            
        else:
            # Set the value directly
            config[config_key] = _convert_value(value)
    
    if env_vars:
        logger.info(f"Applied {len(env_vars)} environment variable overrides.")
    
    return config


def _convert_value(value: str) -> Any:
    """
    Convert a string value to the appropriate type.
    
    Args:
        value: The string value to convert.
            
    Returns:
        The converted value.
    """
    # Try to convert to boolean
    if value.lower() in ('true', 'yes', '1'):
        return True
    if value.lower() in ('false', 'no', '0'):
        return False
    
    # Try to convert to integer
    try:
        return int(value)
    except ValueError:
        pass
    
    # Try to convert to float
    try:
        return float(value)
    except ValueError:
        pass
    
    # Return as string
    return value


def _get_default_config() -> Dict[str, Any]:
    """
    Get the default configuration.
    
    Returns:
        A dictionary containing the default configuration.
    """
    return {
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "date_format": "%Y-%m-%d %H:%M:%S",
            "directory": os.path.join("data", "logs")
        },
        "quality": {
            "enforcer": {
                "enabled": True,
                "hooks_directory": os.path.join("core", "quality", "hooks"),
                "report_directory": os.path.join("data", "reports")
            }
        },
        "documentation": {
            "output_directory": os.path.join("docs"),
            "templates_directory": os.path.join("core", "documentation", "templates"),
            "auto_generate": True
        }
    }


def create_default_config_files():
    """
    Create default configuration files for all environments.
    
    This function creates default configuration files for the dev, test, and prod
    environments if they don't already exist.
    """
    # Ensure the configuration directory exists
    os.makedirs(DEFAULT_CONFIG_DIR, exist_ok=True)
    
    # Define environments
    environments = ['dev', 'test', 'prod']
    
    # Create default configuration for each environment
    for env in environments:
        config_file = os.path.join(DEFAULT_CONFIG_DIR, f"{env}.yaml")
        
        # Skip if the file already exists
        if os.path.exists(config_file):
            continue
        
        # Get default configuration
        config = _get_default_config()
        
        # Customize for environment
        if env == 'dev':
            config['logging']['level'] = 'DEBUG'
        elif env == 'test':
            config['documentation']['auto_generate'] = False
        elif env == 'prod':
            config['logging']['level'] = 'WARNING'
        
        # Write the configuration file
        try:
            with open(config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
                
            logger.info(f"Created default configuration file for environment: {env}")
            
        except IOError as e:
            logger.error(f"Error creating default configuration file for environment '{env}': {str(e)}")