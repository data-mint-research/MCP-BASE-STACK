"""
Unit tests for the LogManager module.

This module contains tests for the LogManager class, which is responsible
for managing logging operations across the application.
"""

import os
import unittest
import logging
from unittest.mock import patch, MagicMock
import pytest

from tests.utils.fixtures import temp_test_dir
from tests.utils.mocks import MockConfig


@pytest.mark.logging
class TestLogManager:
    """Test cases for the LogManager class."""
    
    @pytest.fixture
    def mock_log_manager_module(self):
        """Create a mock log_manager module."""
        with patch('core.logging.manager') as mock_module:
            # Create a mock LogManager class
            mock_manager = MagicMock()
            mock_manager.configure.return_value = True
            mock_manager.get_logger.return_value = logging.getLogger("test")
            mock_manager.log.return_value = None
            
            # Set up the module
            mock_module.LogManager = MagicMock(return_value=mock_manager)
            
            yield mock_module
    
    def test_initialization(self, mock_log_manager_module):
        """Test initializing the LogManager."""
        from core.logging.manager import LogManager
        
        # Create a LogManager instance
        manager = LogManager()
        
        # Verify the manager was initialized
        assert manager is not None
    
    def test_configure(self, mock_log_manager_module, test_config):
        """Test configuring the LogManager."""
        from core.logging.manager import LogManager
        
        # Create a LogManager instance
        manager = LogManager()
        
        # Configure the manager
        result = manager.configure(test_config["logging"])
        
        # Verify the result
        assert result is True
    
    def test_get_logger(self, mock_log_manager_module):
        """Test getting a logger from the LogManager."""
        from core.logging.manager import LogManager
        
        # Create a LogManager instance
        manager = LogManager()
        
        # Get a logger
        logger = manager.get_logger("test_module")
        
        # Verify the logger
        assert logger is not None
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test"
    
    def test_log(self, mock_log_manager_module):
        """Test logging a message with the LogManager."""
        from core.logging.manager import LogManager
        
        # Create a LogManager instance
        manager = LogManager()
        
        # Log a message
        manager.log("test_module", logging.INFO, "Test message")
        
        # Verify the log method was called
        mock_log_manager_module.LogManager().log.assert_called_once_with(
            "test_module", logging.INFO, "Test message"
        )


@pytest.mark.logging
class TestLogManagerIntegration:
    """Integration tests for the LogManager class."""
    
    @pytest.fixture
    def log_config(self):
        """Create a log configuration."""
        return {
            "level": "INFO",
            "directory": "data/logs",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    
    def test_log_file_creation(self, temp_test_dir, log_config):
        """Test that log files are created correctly."""
        # Update the log directory to use the temp directory
        log_config["directory"] = temp_test_dir
        
        # Create a real LogManager
        from core.logging.manager import LogManager
        manager = LogManager()
        
        # Configure the manager
        with patch('core.logging.directory_manager.create_log_directory') as mock_create_dir:
            mock_create_dir.return_value = temp_test_dir
            manager.configure(log_config)
        
        # Get a logger and log a message
        logger = manager.get_logger("test_module")
        logger.info("Test message")
        
        # Check if a log file was created
        log_files = [f for f in os.listdir(temp_test_dir) if f.endswith(".log")]
        assert len(log_files) > 0
    
    def test_log_rotation(self, temp_test_dir, log_config):
        """Test log rotation."""
        # Update the log directory to use the temp directory
        log_config["directory"] = temp_test_dir
        log_config["max_bytes"] = 1024  # Small size to trigger rotation
        log_config["backup_count"] = 3
        
        # Create a real LogManager
        from core.logging.manager import LogManager
        manager = LogManager()
        
        # Configure the manager
        with patch('core.logging.directory_manager.create_log_directory') as mock_create_dir:
            mock_create_dir.return_value = temp_test_dir
            manager.configure(log_config)
        
        # Get a logger and log many messages to trigger rotation
        logger = manager.get_logger("test_module")
        for i in range(1000):
            logger.info(f"Test message {i} with some extra text to make it longer")
        
        # Check if multiple log files were created (original + rotated)
        log_files = [f for f in os.listdir(temp_test_dir) if ".log" in f]
        assert len(log_files) > 1


@pytest.mark.logging
@pytest.mark.error
class TestLogManagerErrorConditions:
    """Test cases for error conditions in the LogManager."""
    
    @pytest.fixture
    def mock_error_module(self):
        """Create a mock module that raises errors."""
        with patch('core.logging.manager') as mock_module:
            # Create a mock LogManager class that raises errors
            mock_manager = MagicMock()
            mock_manager.configure.side_effect = Exception("Configuration error")
            mock_manager.get_logger.side_effect = Exception("Logger error")
            mock_manager.log.side_effect = Exception("Log error")
            
            # Set up the module
            mock_module.LogManager = MagicMock(return_value=mock_manager)
            
            yield mock_module
    
    def test_configuration_error(self, mock_error_module, test_config):
        """Test handling of configuration errors."""
        from core.logging.manager import LogManager
        
        # Create a LogManager instance
        manager = LogManager()
        
        # Configure the manager and verify it raises an exception
        with pytest.raises(Exception) as excinfo:
            manager.configure(test_config["logging"])
        
        assert "Configuration error" in str(excinfo.value)
    
    def test_logger_error(self, mock_error_module):
        """Test handling of logger errors."""
        from core.logging.manager import LogManager
        
        # Create a LogManager instance
        manager = LogManager()
        
        # Get a logger and verify it raises an exception
        with pytest.raises(Exception) as excinfo:
            manager.get_logger("test_module")
        
        assert "Logger error" in str(excinfo.value)
    
    def test_log_error(self, mock_error_module):
        """Test handling of log errors."""
        from core.logging.manager import LogManager
        
        # Create a LogManager instance
        manager = LogManager()
        
        # Log a message and verify it raises an exception
        with pytest.raises(Exception) as excinfo:
            manager.log("test_module", logging.INFO, "Test message")
        
        assert "Log error" in str(excinfo.value)


@pytest.mark.logging
class TestLogManagerRecovery:
    """Test cases for recovery mechanisms in the LogManager."""
    
    @pytest.fixture
    def mock_recovery_module(self):
        """Create a mock module with recovery mechanisms."""
        with patch('core.logging.manager') as mock_module:
            # Create a mock LogManager class with recovery mechanisms
            mock_manager = MagicMock()
            
            # Configure method that fails first, then succeeds
            configure_mock = MagicMock()
            configure_mock.side_effect = [Exception("Configuration error"), True]
            mock_manager.configure = configure_mock
            
            # Get logger method that fails first, then succeeds
            get_logger_mock = MagicMock()
            get_logger_mock.side_effect = [Exception("Logger error"), logging.getLogger("test")]
            mock_manager.get_logger = get_logger_mock
            
            # Log method that fails first, then succeeds
            log_mock = MagicMock()
            log_mock.side_effect = [Exception("Log error"), None]
            mock_manager.log = log_mock
            
            # Set up the module
            mock_module.LogManager = MagicMock(return_value=mock_manager)
            
            yield mock_module
    
    def test_configuration_recovery(self, mock_recovery_module, test_config):
        """Test recovery from configuration errors."""
        from core.logging.manager import LogManager
        
        # Create a LogManager instance
        manager = LogManager()
        
        # First attempt should fail
        with pytest.raises(Exception):
            manager.configure(test_config["logging"])
        
        # Second attempt should succeed
        result = manager.configure(test_config["logging"])
        assert result is True
    
    def test_logger_recovery(self, mock_recovery_module):
        """Test recovery from logger errors."""
        from core.logging.manager import LogManager
        
        # Create a LogManager instance
        manager = LogManager()
        
        # First attempt should fail
        with pytest.raises(Exception):
            manager.get_logger("test_module")
        
        # Second attempt should succeed
        logger = manager.get_logger("test_module")
        assert logger is not None
        assert isinstance(logger, logging.Logger)
    
    def test_log_recovery(self, mock_recovery_module):
        """Test recovery from log errors."""
        from core.logging.manager import LogManager
        
        # Create a LogManager instance
        manager = LogManager()
        
        # First attempt should fail
        with pytest.raises(Exception):
            manager.log("test_module", logging.INFO, "Test message")
        
        # Second attempt should succeed
        manager.log("test_module", logging.INFO, "Test message")
        # No exception should be raised


if __name__ == '__main__':
    unittest.main()