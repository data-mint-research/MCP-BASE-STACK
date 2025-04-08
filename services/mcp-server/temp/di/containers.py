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
    ToolProvider,
    ResourceProvider,
    MCPComponentProvider
)
from src.services.prompt_processor import PromptProcessor
from src.services.example_service import ExampleService
from temp.host.host import MCPHost
from temp.mcp import Host, Client, Server, Consent, Context, Authentication, JsonRpc
from src.client.client import MCPClient
from src.server.server import MCPServer


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
    shell_command_tool = providers.Singleton(
        ToolProvider.get_shell_command_tool
    )
    
    # Resources
    file_resource_provider = providers.Singleton(
        ResourceProvider.get_file_resource_provider,
        config=config,
        logger=logger
    )
    
    # LLM Client
    llm_client = providers.Singleton(
        LLMClientProvider.get_client,
        config=config,
        logger=logger
    )
    
    # MCP Components
    mcp_host = providers.Singleton(
        MCPComponentProvider.get_host,
        logger=logger,
        config=config
    )
    
    mcp_client = providers.Singleton(
        MCPComponentProvider.get_client,
        logger=logger,
        config=config,
        host=mcp_host
    )
    
    mcp_server = providers.Singleton(
        MCPComponentProvider.get_server,
        server_id=config.provided.mcp.server_id,
        config=config,
        logger=logger,
        host=mcp_host
    )
    
    # Services
    prompt_processor = providers.Singleton(
        PromptProcessor,
        logger=logger,
        shell_command_executor=shell_command_tool
    )
    
    # Example service
    example_service = providers.Singleton(
        ExampleService,
        logger=logger,
        config=config
    )