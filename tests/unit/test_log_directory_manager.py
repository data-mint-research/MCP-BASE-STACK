"""
Unit tests for the LogDirectoryManager module.

This module contains tests to verify the functionality of the LogDirectoryManager
module, including directory creation, path generation, and error handling.
"""

import os
import unittest
import shutil
from unittest import mock
from datetime import datetime
from pathlib import Path

from core.config import get_logging_config
from core.logging.directory_manager import (
    LogDirectoryManager,
    create_log_directory,
    get_log_file_path,
    verify_log_directory_structure
)


class TestLogDirectoryManager(unittest.TestCase):
    """Test cases for the LogDirectoryManager module."""

    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary test directory
        self.test_module = "test_module"
        
        # Get log directory from configuration
        config = get_logging_config()
        self.log_base_dir = config.get("directory", os.path.join("data", "logs"))
        self.test_log_dir = os.path.join(self.log_base_dir, self.test_module)
        
        # Ensure the test directory doesn't exist before tests
        if os.path.exists(self.test_log_dir):
            shutil.rmtree(self.test_log_dir)

    def tearDown(self):
        """Clean up test environment after each test."""
        # Remove the test directory after tests
        if os.path.exists(self.test_log_dir):
            shutil.rmtree(self.test_log_dir)

    def test_create_log_directory(self):
        """Test creating a log directory for a module."""
        # Call the function
        result = LogDirectoryManager.create_log_directory(self.test_module)
        
        # Verify the directory was created
        self.assertTrue(os.path.exists(result))
        self.assertTrue(os.path.isdir(result))
        self.assertEqual(result, self.test_log_dir)

    def test_get_log_file_path(self):
        """Test getting a log file path for a module."""
        # Mock the _format_date method to return a fixed date
        with mock.patch.object(
            LogDirectoryManager, '_format_date', return_value='2025-04-07'
        ):
            # Call the function
            result = LogDirectoryManager.get_log_file_path(self.test_module)
            
            # Verify the path is correct
            expected_path = os.path.join(
                self.test_log_dir, 
                f"2025-04-07_{self.test_module}-log"
            )
            self.assertEqual(result, expected_path)

    def test_verify_log_directory_structure_valid(self):
        """Test verifying a valid log directory structure."""
        # Get log directory from configuration
        config = get_logging_config()
        log_base_dir = config.get("directory", os.path.join("data", "logs"))
        
        # Create the base log directory
        os.makedirs(log_base_dir, exist_ok=True)
        
        # Call the function
        result = LogDirectoryManager.verify_log_directory_structure()
        
        # Verify the result
        self.assertTrue(result)

    def test_verify_log_directory_structure_missing(self):
        """Test verifying when log directory is missing."""
        # Get log directory from configuration
        config = get_logging_config()
        log_base_dir = config.get("directory", os.path.join("data", "logs"))
        
        # Ensure the base log directory doesn't exist
        if os.path.exists(log_base_dir):
            shutil.rmtree(log_base_dir)
        
        # Call the function
        result = LogDirectoryManager.verify_log_directory_structure()
        
        # Verify the result
        self.assertFalse(result)

    def test_format_date(self):
        """Test the date formatting function."""
        # Mock datetime.now() to return a fixed date
        fixed_date = datetime(2025, 4, 7)
        with mock.patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_date
            
            # Call the function
            result = LogDirectoryManager._format_date()
            
            # Verify the result
            self.assertEqual(result, "2025-04-07")

    @mock.patch('os.makedirs')
    def test_permission_error_handling(self, mock_makedirs):
        """Test handling of permission errors."""
        # Mock os.makedirs to raise a PermissionError
        mock_makedirs.side_effect = PermissionError("Permission denied")
        
        # Call the function and verify it raises a PermissionError
        with self.assertRaises(PermissionError):
            LogDirectoryManager.create_log_directory(self.test_module)

    def test_convenience_functions(self):
        """Test the convenience functions."""
        # Mock the class methods
        with mock.patch.object(
            LogDirectoryManager, 'create_log_directory'
        ) as mock_create, mock.patch.object(
            LogDirectoryManager, 'get_log_file_path'
        ) as mock_get_path, mock.patch.object(
            LogDirectoryManager, 'verify_log_directory_structure'
        ) as mock_verify:
            # Set return values
            mock_create.return_value = "mocked_dir"
            mock_get_path.return_value = "mocked_path"
            mock_verify.return_value = True
            
            # Call the convenience functions
            create_result = create_log_directory(self.test_module)
            path_result = get_log_file_path(self.test_module)
            verify_result = verify_log_directory_structure()
            
            # Verify the results
            self.assertEqual(create_result, "mocked_dir")
            self.assertEqual(path_result, "mocked_path")
            self.assertTrue(verify_result)
            
            # Verify the class methods were called
            mock_create.assert_called_once_with(self.test_module)
            mock_get_path.assert_called_once_with(self.test_module)
            mock_verify.assert_called_once()


if __name__ == '__main__':
    unittest.main()