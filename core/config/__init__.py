"""
Configuration Module

This module provides configuration management functionality for the MCP-BASE-STACK project.
"""

from core.config.loader import load_config_from_file
from core.config.settings import get_config, get_logging_config

__all__ = [
    'get_config',
    'load_config_from_file',
    'get_logging_config',
]