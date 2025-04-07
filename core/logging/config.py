"""
LoggingConfig module for configuring loggers with standardized settings.

This module provides functionality to configure loggers that redirect logs
to standardized locations using the LogDirectoryManager.
"""

import logging
import os
from typing import Dict, Optional

from core.logging.directory_manager import LogDirectoryManager

# Default log format
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# Default date format for log messages
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Mapping of string log levels to logging module constants
LOG_LEVELS: Dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}


def configure_logger(module_name: str, level: str = "INFO") -> logging.Logger:
    """
    Configures and returns a logger for a specific module.
    
    Args:
        module_name: The name of the module to configure a logger for.
        level: The logging level as a string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            Defaults to "INFO".
            
    Returns:
        A configured logger instance.
        
    Raises:
        ValueError: If an invalid logging level is provided.
    """
    # Validate the logging level
    if level not in LOG_LEVELS:
        valid_levels = ", ".join(LOG_LEVELS.keys())
        raise ValueError(f"Invalid logging level: {level}. Valid levels are: {valid_levels}")
    
    # Get or create a logger for the module
    logger = logging.getLogger(module_name)
    
    # Clear any existing handlers to avoid duplicate logs
    if logger.handlers:
        logger.handlers.clear()
    
    # Set the logging level
    logger.setLevel(LOG_LEVELS[level])
    
    # Add handlers
    logger.addHandler(get_file_handler(module_name))
    logger.addHandler(get_console_handler())
    
    # Prevent propagation to the root logger to avoid duplicate logs
    logger.propagate = False
    
    return logger


def get_file_handler(module_name: str) -> logging.FileHandler:
    """
    Creates and returns a file handler for a specific module.
    
    Args:
        module_name: The name of the module to create a file handler for.
        
    Returns:
        A configured FileHandler instance.
        
    Raises:
        PermissionError: If there are permission issues creating the log file.
        OSError: If there are other OS-related errors.
    """
    try:
        # Get the log file path using LogDirectoryManager
        log_file_path = LogDirectoryManager.get_log_file_path(module_name)
        
        # Create a file handler
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setFormatter(_get_formatter())
        
        return file_handler
        
    except (PermissionError, OSError) as e:
        # Log the error and re-raise
        logging.error(f"Error creating file handler for module {module_name}: {str(e)}")
        raise


def get_console_handler() -> logging.StreamHandler:
    """
    Creates and returns a console handler.
    
    Returns:
        A configured StreamHandler instance.
    """
    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(_get_formatter())
    
    return console_handler


def _get_formatter() -> logging.Formatter:
    """
    Helper function to create a standardized log formatter.
    
    Returns:
        A configured Formatter instance.
    """
    return logging.Formatter(DEFAULT_LOG_FORMAT, DEFAULT_DATE_FORMAT)