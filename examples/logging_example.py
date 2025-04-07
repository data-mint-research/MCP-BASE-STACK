#!/usr/bin/env python3
"""
Example script demonstrating the usage of the LoggingConfig module.

This script shows how to configure and use loggers with the standardized
logging configuration system.
"""

import os
import sys
import time
from pathlib import Path

# Add the project root to the Python path to allow importing from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logging.config import configure_logger
from core.logging.directory_manager import get_log_file_path, verify_log_directory_structure


def main():
    """
    Main function demonstrating the usage of the LoggingConfig module.
    """
    # Verify the log directory structure
    if not verify_log_directory_structure():
        print("Log directory structure is not valid. Creating it...")
    
    # Example 1: Basic logger configuration with default level (INFO)
    basic_logger = configure_logger("basic_example")
    print(f"Basic logger configured. Log file: {get_log_file_path('basic_example')}")
    
    # Log messages at different levels
    basic_logger.debug("This is a DEBUG message (won't be shown with default INFO level)")
    basic_logger.info("This is an INFO message")
    basic_logger.warning("This is a WARNING message")
    basic_logger.error("This is an ERROR message")
    basic_logger.critical("This is a CRITICAL message")
    
    # Example 2: Configure a logger with DEBUG level
    debug_logger = configure_logger("debug_example", "DEBUG")
    print(f"Debug logger configured. Log file: {get_log_file_path('debug_example')}")
    
    # Log messages at different levels (all will be shown)
    debug_logger.debug("This is a DEBUG message (will be shown with DEBUG level)")
    debug_logger.info("This is an INFO message")
    debug_logger.warning("This is a WARNING message")
    debug_logger.error("This is an ERROR message")
    debug_logger.critical("This is a CRITICAL message")
    
    # Example 3: Configure loggers for different modules
    module1_logger = configure_logger("module1")
    module2_logger = configure_logger("module2")
    
    print(f"Module1 logger configured. Log file: {get_log_file_path('module1')}")
    print(f"Module2 logger configured. Log file: {get_log_file_path('module2')}")
    
    # Simulate logs from different modules
    module1_logger.info("Module1: Initializing...")
    module2_logger.info("Module2: Initializing...")
    
    time.sleep(1)  # Simulate some processing time
    
    module1_logger.warning("Module1: Resource usage high")
    module2_logger.error("Module2: Failed to connect to database")
    
    time.sleep(1)  # Simulate some processing time
    
    module1_logger.info("Module1: Processing completed")
    module2_logger.info("Module2: Retrying connection...")
    
    # Example 4: Error handling demonstration
    try:
        # Attempt to perform an operation that might fail
        result = 10 / 0
    except Exception as e:
        # Log the error
        basic_logger.error(f"An error occurred: {str(e)}", exc_info=True)
        print("An error occurred and was logged with traceback.")
    
    print("\nLogging demonstration completed.")
    print("Check the log files in the following locations:")
    for module in ["basic_example", "debug_example", "module1", "module2"]:
        print(f"- {get_log_file_path(module)}")


if __name__ == "__main__":
    main()