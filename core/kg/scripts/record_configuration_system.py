"""
Script to record the configuration system in the knowledge graph.

This script adds information about the configuration system to the knowledge graph,
including its components, relationships, and functionality.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from core.kg.scripts.update_knowledge_graph import (
    add_node,
    add_relationship,
    add_property,
    save_graph
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def record_configuration_system():
    """
    Record the configuration system in the knowledge graph.
    
    This function adds nodes, relationships, and properties to the knowledge graph
    to represent the configuration system and its components.
    """
    logger.info("Recording configuration system in knowledge graph...")
    
    # Add configuration system node
    config_system_id = add_node(
        "ConfigurationSystem",
        "Configuration System",
        "A unified configuration system for the MCP-BASE-STACK project"
    )
    
    # Add properties to the configuration system node
    add_property(config_system_id, "version", "1.0")
    add_property(config_system_id, "description", "Provides a unified approach to managing configuration settings across the project")
    add_property(config_system_id, "features", [
        "YAML-based configuration files",
        "Environment variable overrides",
        "Different environments (dev, test, prod)",
        "Configuration validation",
        "Sensible defaults"
    ])
    
    # Add component nodes
    loader_id = add_node(
        "ConfigLoader",
        "Configuration Loader",
        "Loads configuration from files and environment variables"
    )
    
    settings_id = add_node(
        "ConfigSettings",
        "Configuration Settings",
        "Provides access to configuration settings with validation"
    )
    
    validator_id = add_node(
        "ConfigValidator",
        "Configuration Validator",
        "Validates configuration against schemas"
    )
    
    # Add relationships between components
    add_relationship(config_system_id, "CONTAINS", loader_id)
    add_relationship(config_system_id, "CONTAINS", settings_id)
    add_relationship(settings_id, "USES", validator_id)
    add_relationship(settings_id, "USES", loader_id)
    
    # Add configuration file nodes
    dev_config_id = add_node(
        "DevConfig",
        "Development Configuration",
        "Configuration for the development environment"
    )
    
    test_config_id = add_node(
        "TestConfig",
        "Test Configuration",
        "Configuration for the test environment"
    )
    
    prod_config_id = add_node(
        "ProdConfig",
        "Production Configuration",
        "Configuration for the production environment"
    )
    
    # Add relationships between configuration system and files
    add_relationship(config_system_id, "USES", dev_config_id)
    add_relationship(config_system_id, "USES", test_config_id)
    add_relationship(config_system_id, "USES", prod_config_id)
    
    # Add module nodes
    logging_module_id = add_node(
        "LoggingModule",
        "Logging Module",
        "Provides logging functionality for the project"
    )
    
    quality_module_id = add_node(
        "QualityModule",
        "Quality Module",
        "Provides quality enforcement functionality for the project"
    )
    
    documentation_module_id = add_node(
        "DocumentationModule",
        "Documentation Module",
        "Provides documentation generation functionality for the project"
    )
    
    # Add relationships between modules and configuration system
    add_relationship(logging_module_id, "USES", config_system_id)
    add_relationship(quality_module_id, "USES", config_system_id)
    add_relationship(documentation_module_id, "USES", config_system_id)
    
    # Add configuration section nodes
    logging_config_id = add_node(
        "LoggingConfig",
        "Logging Configuration",
        "Configuration for the logging module"
    )
    
    quality_config_id = add_node(
        "QualityConfig",
        "Quality Configuration",
        "Configuration for the quality module"
    )
    
    documentation_config_id = add_node(
        "DocumentationConfig",
        "Documentation Configuration",
        "Configuration for the documentation module"
    )
    
    # Add relationships between configuration system and sections
    add_relationship(config_system_id, "CONTAINS", logging_config_id)
    add_relationship(config_system_id, "CONTAINS", quality_config_id)
    add_relationship(config_system_id, "CONTAINS", documentation_config_id)
    
    # Add relationships between modules and configuration sections
    add_relationship(logging_module_id, "USES", logging_config_id)
    add_relationship(quality_module_id, "USES", quality_config_id)
    add_relationship(documentation_module_id, "USES", documentation_config_id)
    
    # Add documentation node
    docs_id = add_node(
        "ConfigurationDocs",
        "Configuration System Documentation",
        "Documentation for the configuration system"
    )
    
    # Add relationship between configuration system and documentation
    add_relationship(config_system_id, "DOCUMENTED_BY", docs_id)
    
    # Add test node
    tests_id = add_node(
        "ConfigurationTests",
        "Configuration System Tests",
        "Unit tests for the configuration system"
    )
    
    # Add relationship between configuration system and tests
    add_relationship(config_system_id, "TESTED_BY", tests_id)
    
    # Save the updated knowledge graph
    save_graph()
    
    logger.info("Configuration system recorded in knowledge graph.")


if __name__ == "__main__":
    record_configuration_system()