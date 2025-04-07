"""
Dependency Injection Container for MCP Server.

This module defines the main dependency injection container that wires up
all the application dependencies and makes them available throughout the application.
"""

from dependency_injector import containers, providers

from .providers import (
    ConfigProvider,
    LoggingProvider,
    LLMClientProvider,
    ToolProvider
)
from services.prompt_processor import PromptProcessor
from services.example_service import ExampleService


class Container(containers.DeclarativeContainer):
    """
    Dependency Injection Container for MCP Server.
    
    This container manages all application dependencies and provides
    a clean way to access services throughout the application.
    """
    
    # Configuration
    config = providers.Singleton(
        ConfigProvider.get_config
    )
    
    # Logging
    logger = providers.Singleton(
        LoggingProvider.get_logger,
        name="mcp_server",
        config=config
    )
    
    # Tools
    shell_command_executor = providers.Singleton(
        ToolProvider.get_shell_command_executor,
        logger=logger
    )
    
    # LLM Client
    llm_client = providers.Singleton(
        LLMClientProvider.get_client,
        config=config,
        logger=logger
    )
    
    # Services
    prompt_processor = providers.Singleton(
        PromptProcessor,
        logger=logger,
        shell_command_executor=shell_command_executor
    )
    
    # Example service
    example_service = providers.Singleton(
        ExampleService,
        logger=logger,
        config=config
    )