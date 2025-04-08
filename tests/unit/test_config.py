"""
Unit tests for the configuration module.

This module contains tests to verify the functionality of the configuration
module, including loading from files, environment variables, and validation.
"""

import os
import unittest
import tempfile
import yaml
from unittest import mock
from pathlib import Path

from core.config.loader import (
    load_config,
    load_config_from_file,
    load_config_from_env,
    _convert_value,
    _get_default_config
)

from core.config.settings import (
    get_config,
    get_logging_config,
    get_quality_config,
    get_documentation_config,
    ConfigValidator,
    ConfigValidationError,
    clear_config_cache
)


class TestConfigLoader(unittest.TestCase):
    """Test cases for the configuration loader module."""

    def setUp(self):
        """Set up test environment before each test."""
        # Clear the configuration cache
        clear_config_cache()
        
        # Save original environment variables
        self.original_env = os.environ.copy()
        
        # Create a temporary directory for test configuration files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_dir = os.path.join(self.temp_dir.name, "config", "environments")
        os.makedirs(self.config_dir, exist_ok=True)

    def tearDown(self):
        """Clean up test environment after each test."""
        # Restore original environment variables
        os.environ.clear()
        os.environ.update(self.original_env)
        
        # Clean up temporary directory
        self.temp_dir.cleanup()

    def test_convert_value(self):
        """Test converting string values to appropriate types."""
        # Test boolean conversion
        self.assertTrue(_convert_value("true"))
        self.assertTrue(_convert_value("True"))
        self.assertTrue(_convert_value("yes"))
        self.assertTrue(_convert_value("1"))
        self.assertFalse(_convert_value("false"))
        self.assertFalse(_convert_value("False"))
        self.assertFalse(_convert_value("no"))
        self.assertFalse(_convert_value("0"))
        
        # Test integer conversion
        self.assertEqual(_convert_value("42"), 42)
        self.assertEqual(_convert_value("-42"), -42)
        
        # Test float conversion
        self.assertEqual(_convert_value("3.14"), 3.14)
        self.assertEqual(_convert_value("-3.14"), -3.14)
        
        # Test string (no conversion)
        self.assertEqual(_convert_value("hello"), "hello")
        self.assertEqual(_convert_value("3.14.15"), "3.14.15")  # Not a valid float

    def test_get_default_config(self):
        """Test getting the default configuration."""
        config = _get_default_config()
        
        # Verify the default configuration structure
        self.assertIn("logging", config)
        self.assertIn("quality", config)
        self.assertIn("documentation", config)
        
        # Verify logging configuration
        self.assertEqual(config["logging"]["level"], "INFO")
        self.assertIn("format", config["logging"])
        self.assertIn("date_format", config["logging"])
        self.assertIn("directory", config["logging"])
        
        # Verify quality configuration
        self.assertTrue(config["quality"]["enforcer"]["enabled"])
        self.assertIn("hooks_directory", config["quality"]["enforcer"])
        self.assertIn("report_directory", config["quality"]["enforcer"])
        
        # Verify documentation configuration
        self.assertIn("output_directory", config["documentation"])
        self.assertIn("templates_directory", config["documentation"])
        self.assertTrue(config["documentation"]["auto_generate"])

    def test_load_config_from_file(self):
        """Test loading configuration from a file."""
        # Create a test configuration file
        test_config = {
            "logging": {
                "level": "DEBUG",
                "format": "test-format",
                "date_format": "test-date-format",
                "directory": "test-directory"
            }
        }
        
        # Write the configuration to a file
        config_file = os.path.join(self.config_dir, "test.yaml")
        with open(config_file, "w") as f:
            yaml.dump(test_config, f)
        
        # Load the configuration
        config = load_config_from_file("test")
        
        # Verify the configuration was loaded correctly
        self.assertEqual(config["logging"]["level"], "DEBUG")
        self.assertEqual(config["logging"]["format"], "test-format")
        self.assertEqual(config["logging"]["date_format"], "test-date-format")
        self.assertEqual(config["logging"]["directory"], "test-directory")

    def test_load_config_from_file_not_found(self):
        """Test loading configuration when the file is not found."""
        # Load a non-existent configuration file
        config = load_config_from_file("nonexistent")
        
        # Verify the default configuration was returned
        self.assertEqual(config["logging"]["level"], "INFO")

    def test_load_config_from_env(self):
        """Test applying environment variable overrides to configuration."""
        # Set up environment variables
        os.environ["MCP_LOGGING_LEVEL"] = "DEBUG"
        os.environ["MCP_QUALITY_ENFORCER_ENABLED"] = "false"
        
        # Create a base configuration
        base_config = _get_default_config()
        
        # Apply environment variable overrides
        config = load_config_from_env(base_config)
        
        # Verify the overrides were applied
        self.assertEqual(config["logging"]["level"], "DEBUG")
        self.assertFalse(config["quality"]["enforcer"]["enabled"])
        
        # Verify other values were not changed
        self.assertEqual(config["logging"]["format"], base_config["logging"]["format"])

    def test_load_config(self):
        """Test loading configuration with environment detection."""
        # Create a test configuration file
        test_config = {
            "logging": {
                "level": "DEBUG",
                "format": "test-format",
                "date_format": "test-date-format",
                "directory": "test-directory"
            }
        }
        
        # Write the configuration to a file
        config_file = os.path.join(self.config_dir, "test.yaml")
        with open(config_file, "w") as f:
            yaml.dump(test_config, f)
        
        # Set up environment variables
        os.environ["MCP_ENV"] = "test"
        os.environ["MCP_LOGGING_LEVEL"] = "ERROR"
        
        # Mock the DEFAULT_CONFIG_DIR to use our temporary directory
        with mock.patch("core.config.loader.DEFAULT_CONFIG_DIR", self.config_dir):
            # Load the configuration
            config = load_config()
            
            # Verify the configuration was loaded correctly
            self.assertEqual(config["logging"]["level"], "ERROR")  # From env var
            self.assertEqual(config["logging"]["format"], "test-format")  # From file
            self.assertEqual(config["logging"]["date_format"], "test-date-format")  # From file
            self.assertEqual(config["logging"]["directory"], "test-directory")  # From file


class TestConfigSettings(unittest.TestCase):
    """Test cases for the configuration settings module."""

    def setUp(self):
        """Set up test environment before each test."""
        # Clear the configuration cache
        clear_config_cache()
        
        # Save original environment variables
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Clean up test environment after each test."""
        # Restore original environment variables
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_config_validator(self):
        """Test the configuration validator."""
        # Create a test schema
        schema = {
            "string_value": {
                "type": str,
                "required": True
            },
            "int_value": {
                "type": int,
                "min": 0,
                "max": 100
            },
            "enum_value": {
                "type": str,
                "enum": ["option1", "option2", "option3"]
            },
            "nested": {
                "nested_value": {
                    "type": str,
                    "required": True
                }
            }
        }
        
        # Create a valid configuration
        valid_config = {
            "string_value": "test",
            "int_value": 42,
            "enum_value": "option2",
            "nested": {
                "nested_value": "test"
            }
        }
        
        # Validate the configuration
        errors = ConfigValidator.validate(valid_config, schema)
        
        # Verify no errors were found
        self.assertEqual(len(errors), 0)
        
        # Create an invalid configuration
        invalid_config = {
            "string_value": 42,  # Wrong type
            "int_value": 200,  # Out of range
            "enum_value": "invalid",  # Not in enum
            "nested": {
                # Missing required nested_value
            }
        }
        
        # Validate the configuration
        errors = ConfigValidator.validate(invalid_config, schema)
        
        # Verify errors were found
        self.assertGreater(len(errors), 0)
        
        # Check for specific errors
        error_paths = [error.path for error in errors]
        self.assertIn("string_value", error_paths)
        self.assertIn("int_value", error_paths)
        self.assertIn("enum_value", error_paths)
        self.assertIn("nested.nested_value", error_paths)

    @mock.patch("core.config.settings.load_config")
    def test_get_config(self, mock_load_config):
        """Test getting the configuration."""
        # Mock the load_config function
        mock_load_config.return_value = _get_default_config()
        
        # Get the configuration
        config = get_config()
        
        # Verify the configuration was loaded
        self.assertIn("logging", config)
        self.assertIn("quality", config)
        self.assertIn("documentation", config)
        
        # Verify the function was called with the correct arguments
        mock_load_config.assert_called_once_with(None)
        
        # Get the configuration again (should use cache)
        config = get_config()
        
        # Verify the function was not called again
        mock_load_config.assert_called_once()

    @mock.patch("core.config.settings.get_config")
    def test_get_logging_config(self, mock_get_config):
        """Test getting the logging configuration."""
        # Mock the get_config function
        mock_get_config.return_value = {
            "logging": {
                "level": "DEBUG",
                "format": "test-format",
                "date_format": "test-date-format",
                "directory": "test-directory"
            }
        }
        
        # Get the logging configuration
        config = get_logging_config()
        
        # Verify the configuration was loaded
        self.assertEqual(config["level"], "DEBUG")
        self.assertEqual(config["format"], "test-format")
        self.assertEqual(config["date_format"], "test-date-format")
        self.assertEqual(config["directory"], "test-directory")
        
        # Verify the function was called with the correct arguments
        mock_get_config.assert_called_once_with(None)

    @mock.patch("core.config.settings.get_config")
    def test_get_quality_config(self, mock_get_config):
        """Test getting the quality configuration."""
        # Mock the get_config function
        mock_get_config.return_value = {
            "quality": {
                "enforcer": {
                    "enabled": True,
                    "hooks_directory": "test-hooks-directory",
                    "report_directory": "test-report-directory"
                }
            }
        }
        
        # Get the quality configuration
        config = get_quality_config()
        
        # Verify the configuration was loaded
        self.assertTrue(config["enforcer"]["enabled"])
        self.assertEqual(config["enforcer"]["hooks_directory"], "test-hooks-directory")
        self.assertEqual(config["enforcer"]["report_directory"], "test-report-directory")
        
        # Verify the function was called with the correct arguments
        mock_get_config.assert_called_once_with(None)

    @mock.patch("core.config.settings.get_config")
    def test_get_documentation_config(self, mock_get_config):
        """Test getting the documentation configuration."""
        # Mock the get_config function
        mock_get_config.return_value = {
            "documentation": {
                "output_directory": "test-output-directory",
                "templates_directory": "test-templates-directory",
                "auto_generate": True
            }
        }
        
        # Get the documentation configuration
        config = get_documentation_config()
        
        # Verify the configuration was loaded
        self.assertEqual(config["output_directory"], "test-output-directory")
        self.assertEqual(config["templates_directory"], "test-templates-directory")
        self.assertTrue(config["auto_generate"])
        
        # Verify the function was called with the correct arguments
        mock_get_config.assert_called_once_with(None)


if __name__ == "__main__":
    unittest.main()