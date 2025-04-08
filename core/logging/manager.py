"""
Logging Manager Module

This module provides the LogManager class.
"""

import os
import logging
from typing import Optional, Dict, Any


class LogManager:
    """Logging manager class."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the LogManager.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.loggers = {}
        
        # Set up default logging configuration
        self.log_level = self.config.get("log_level", logging.INFO)
        self.log_format = self.config.get("log_format", 
                                         "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self.log_dir = self.config.get("log_dir", "logs")
        
        # Create the log directory if it doesn't exist
        os.makedirs(self.log_dir, exist_ok=True)
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger with the specified name.
        
        Args:
            name: Logger name
            
        Returns:
            logging.Logger: Logger instance
        """
        if name in self.loggers:
            return self.loggers[name]
        
        # Create a new logger
        logger = logging.getLogger(name)
        logger.setLevel(self.log_level)
        
        # Create a file handler
        log_file = os.path.join(self.log_dir, f"{name}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(self.log_level)
        
        # Create a formatter
        formatter = logging.Formatter(self.log_format)
        file_handler.setFormatter(formatter)
        
        # Add the handler to the logger
        logger.addHandler(file_handler)
        
        # Store the logger
        self.loggers[name] = logger
        
        return logger