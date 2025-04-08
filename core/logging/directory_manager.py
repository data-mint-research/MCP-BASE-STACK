"""
LogDirectoryManager module for handling log directory creation and verification.

This module provides functionality to create, verify, and manage the standardized
log directory structure for the MCP-BASE-STACK project.
"""

import os
import datetime
import logging
from pathlib import Path
from typing import Optional

from core.config import get_logging_config

# Configure logging for the module itself
logger = logging.getLogger(__name__)

# Get log directory from configuration
config = get_logging_config()
LOG_BASE_DIR = config.get("directory", os.path.join("data", "logs"))


class LogDirectoryManager:
    """
    Manages the creation and verification of the log directory structure.
    
    This class provides methods to create log directories for specific modules,
    get log file paths, and verify the log directory structure.
    """
    
    @staticmethod
    def create_log_directory(module_name: str) -> str:
        """
        Creates the log directory for a specific module.
        
        Args:
            module_name: The name of the module to create a log directory for.
            
        Returns:
            The path to the created log directory.
            
        Raises:
            PermissionError: If there are permission issues creating the directory.
            OSError: If there are other OS-related errors.
        """
        try:
            # Ensure the base log directory exists
            # Get log directory from configuration
            config = get_logging_config()
            log_base_dir = config.get("directory", os.path.join("data", "logs"))
            
            # Ensure the base log directory exists
            if not os.path.exists(log_base_dir):
                os.makedirs(log_base_dir, exist_ok=True)
                logger.info(f"Created base log directory: {log_base_dir}")
            
            # Create module-specific log directory
            module_log_dir = os.path.join(log_base_dir, module_name)
            os.makedirs(module_log_dir, exist_ok=True)
            logger.info(f"Created module log directory: {module_log_dir}")
            
            return module_log_dir
            
        except PermissionError as e:
            LogDirectoryManager._handle_permission_error(e, log_base_dir)
            raise
        except OSError as e:
            logger.error(f"Error creating log directory for module {module_name}: {str(e)}")
            raise
    
    @staticmethod
    def get_log_file_path(module_name: str) -> str:
        """
        Returns the path to the log file for a specific module.
        
        Args:
            module_name: The name of the module to get a log file path for.
            
        Returns:
            The path to the log file.
        """
        # Ensure the module log directory exists
        module_log_dir = LogDirectoryManager.create_log_directory(module_name)
        
        # Create log file name with date
        date_str = LogDirectoryManager._format_date()
        log_file_name = f"{date_str}_{module_name}-log"
        
        return os.path.join(module_log_dir, log_file_name)
    
    @staticmethod
    def verify_log_directory_structure() -> bool:
        """
        Verifies the log directory structure.
        
        This method checks if the base log directory exists and is writable.
        
        Returns:
            True if the structure is valid, False otherwise.
        """
        try:
            # Check if base log directory exists
            # Get log directory from configuration
            config = get_logging_config()
            log_base_dir = config.get("directory", os.path.join("data", "logs"))
            
            if not os.path.exists(log_base_dir):
                logger.warning(f"Base log directory does not exist: {log_base_dir}")
                return False
            
            # Check if base log directory is a directory
            if not os.path.isdir(log_base_dir):
                logger.error(f"Base log path exists but is not a directory: {log_base_dir}")
                return False
            
            # Check if base log directory is writable
            test_file_path = os.path.join(log_base_dir, ".write_test")
            try:
                with open(test_file_path, 'w') as f:
                    f.write("test")
                os.remove(test_file_path)
            except (PermissionError, OSError):
                logger.error(f"Base log directory is not writable: {log_base_dir}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying log directory structure: {str(e)}")
            return False
    
    @staticmethod
    def _format_date() -> str:
        """
        Helper function to format the current date as yyyy-mm-dd.
        
        Returns:
            The formatted date string.
        """
        return datetime.datetime.now().strftime("%Y-%m-%d")
    
    @staticmethod
    def _handle_permission_error(error: PermissionError, path: str) -> None:
        """
        Helper function to handle permission errors.
        
        Args:
            error: The PermissionError that occurred.
            path: The path where the permission error occurred.
        """
        logger.error(f"Permission error accessing path: {path}")
        logger.error(f"Error details: {str(error)}")
        
        # Check if the directory exists but is not writable
        if os.path.exists(path):
            logger.error(f"Path exists but you don't have sufficient permissions: {path}")
            logger.info("Please check file system permissions and ensure your user has write access.")
        else:
            logger.error(f"Cannot create directory due to permission restrictions: {path}")
            logger.info("Please check parent directory permissions and ensure your user has write access.")


# Convenience functions to use the LogDirectoryManager class
def create_log_directory(module_name: str) -> str:
    """Convenience function to create a log directory for a module."""
    return LogDirectoryManager.create_log_directory(module_name)


def get_log_file_path(module_name: str) -> str:
    """Convenience function to get a log file path for a module."""
    return LogDirectoryManager.get_log_file_path(module_name)


def verify_log_directory_structure() -> bool:
    """Convenience function to verify the log directory structure."""
    return LogDirectoryManager.verify_log_directory_structure()