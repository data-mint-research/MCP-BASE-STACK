"""
Unit tests for the LoggingConfig module.

This module contains tests to verify the functionality of the LoggingConfig
module, including logger configuration, handler creation, and error handling.
"""

import os
import unittest
import logging
import shutil
from unittest import mock
from pathlib import Path

from core.logging.config import (
    configure_logger,
    get_file_handler,
    get_console_handler,
    _get_formatter,
    LOG_LEVELS,
    DEFAULT_LOG_FORMAT,
    DEFAULT_DATE_FORMAT
)
from core.logging.directory_manager import LOG_BASE_DIR


class TestLoggingConfig(unittest.TestCase):
    """Test cases for the LoggingConfig module."""

    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary test directory
        self.test_module = "test_logging_module"
        self.test_log_dir = os.path.join(LOG_BASE_DIR, self.test_module)
        
        # Ensure the test directory exists
        os.makedirs(self.test_log_dir, exist_ok=True)

    def tearDown(self):
        """Clean up test environment after each test."""
        # Remove the test directory after tests
        if os.path.exists(self.test_log_dir):
            shutil.rmtree(self.test_log_dir)
        
        # Reset the root logger to avoid affecting other tests
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

    def test_get_formatter(self):
        """Test the formatter creation function."""
        formatter = _get_formatter()
        
        self.assertIsInstance(formatter, logging.Formatter)
        self.assertEqual(formatter._fmt, DEFAULT_LOG_FORMAT)
        self.assertEqual(formatter.datefmt, DEFAULT_DATE_FORMAT)

    def test_get_console_handler(self):
        """Test creating a console handler."""
        handler = get_console_handler()
        
        self.assertIsInstance(handler, logging.StreamHandler)
        self.assertIsInstance(handler.formatter, logging.Formatter)

    @mock.patch('core.logging.directory_manager.LogDirectoryManager.get_log_file_path')
    def test_get_file_handler(self, mock_get_path):
        """Test creating a file handler."""
        # Mock the get_log_file_path to return a test path
        test_log_path = os.path.join(self.test_log_dir, "test_log_file")
        mock_get_path.return_value = test_log_path
        
        # Create a file handler
        with mock.patch('logging.FileHandler') as mock_file_handler:
            mock_instance = mock.MagicMock()
            mock_file_handler.return_value = mock_instance
            
            handler = get_file_handler(self.test_module)
            
            # Verify the handler was created with the correct path
            mock_file_handler.assert_called_once_with(test_log_path)
            # Verify the formatter was set
            mock_instance.setFormatter.assert_called_once()

    @mock.patch('core.logging.directory_manager.LogDirectoryManager.get_log_file_path')
    def test_get_file_handler_error(self, mock_get_path):
        """Test error handling when creating a file handler."""
        # Mock the get_log_file_path to raise an error
        mock_get_path.side_effect = PermissionError("Permission denied")
        
        # Verify the error is propagated
        with self.assertRaises(PermissionError):
            get_file_handler(self.test_module)

    @mock.patch('core.logging.config.get_file_handler')
    @mock.patch('core.logging.config.get_console_handler')
    def test_configure_logger(self, mock_console_handler, mock_file_handler):
        """Test configuring a logger."""
        # Mock the handlers
        mock_console = mock.MagicMock()
        mock_file = mock.MagicMock()
        mock_console_handler.return_value = mock_console
        mock_file_handler.return_value = mock_file
        
        # Configure a logger
        logger = configure_logger(self.test_module, "INFO")
        
        # Verify the logger was configured correctly
        self.assertEqual(logger.level, logging.INFO)
        self.assertEqual(len(logger.handlers), 2)
        self.assertFalse(logger.propagate)
        
        # Verify the handlers were added
        mock_file_handler.assert_called_once_with(self.test_module)
        mock_console_handler.assert_called_once()

    def test_configure_logger_invalid_level(self):
        """Test configuring a logger with an invalid level."""
        # Verify an error is raised for an invalid level
        with self.assertRaises(ValueError):
            configure_logger(self.test_module, "INVALID_LEVEL")

    def test_configure_logger_different_levels(self):
        """Test configuring loggers with different levels."""
        # Test each valid log level
        for level_name, level_value in LOG_LEVELS.items():
            with mock.patch('core.logging.config.get_file_handler'), \
                 mock.patch('core.logging.config.get_console_handler'):
                logger = configure_logger(self.test_module, level_name)
                self.assertEqual(logger.level, level_value)

    def test_configure_logger_clears_existing_handlers(self):
        """Test that configure_logger clears existing handlers."""
        # Configure a logger twice
        with mock.patch('core.logging.config.get_file_handler'), \
             mock.patch('core.logging.config.get_console_handler'):
            logger = configure_logger(self.test_module)
            # Add a mock handler directly
            mock_handler = mock.MagicMock()
            logger.addHandler(mock_handler)
            # Reconfigure the logger
            logger = configure_logger(self.test_module)
            # Verify the handlers were cleared and only the new ones exist
            self.assertEqual(len(logger.handlers), 2)
            # Verify the mock handler is not in the handlers
            self.assertNotIn(mock_handler, logger.handlers)


if __name__ == '__main__':
    unittest.main()