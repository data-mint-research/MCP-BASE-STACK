"""
Providers for the dependency injection container.

This module defines the service providers that will be used by the dependency injection container.
Each provider is responsible for creating and configuring a specific service.
"""

import logging
import os
import uuid
from typing import Dict, Any, Optional

import requests
from dependency_injector.providers import Factory, Singleton, Configuration


class ConfigProvider:
    """Provider for configuration settings."""
    
    @staticmethod
    def get_config() -> Dict[str, Any]:
        """
        Get configuration settings from environment variables.
        
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        return {
            'llm_server': {
                'host': os.environ.get('LLM_SERVER_HOST', 'localhost'),
                'port': os.environ.get('LLM_SERVER_PORT', '11434'),
                'model': os.environ.get('LLM_MODEL', 'deepseek-coder:6.7b'),
                'timeout': int(os.environ.get('LLM_TIMEOUT', '120')),
            },
            'logging': {
                'level': os.environ.get('LOG_LEVEL', 'INFO'),
                'file': os.environ.get('LOG_FILE', 'mcp_debug.log'),
            },
            'server': {
                'host': os.environ.get('SERVER_HOST', '0.0.0.0'),
                'port': int(os.environ.get('SERVER_PORT', '8000')),
            },
            'mcp': {
                'server_id': os.environ.get('MCP_SERVER_ID', 'default'),
                'host_enabled': os.environ.get('MCP_HOST_ENABLED', 'true').lower() == 'true',
                'client_enabled': os.environ.get('MCP_CLIENT_ENABLED', 'true').lower() == 'true',
                'server_enabled': os.environ.get('MCP_SERVER_ENABLED', 'true').lower() == 'true',
            }
        }


class LoggingProvider:
    """Provider for logging services."""
    
    @staticmethod
    def get_logger(name: str, config: Dict[str, Any]) -> logging.Logger:
        """
        Configure and return a logger.
        
        Args:
            name: Logger name
            config: Logging configuration
            
        Returns:
            logging.Logger: Configured logger
        """
        log_level = getattr(logging, config['logging']['level'])
        log_file = config['logging']['file']
        
        logger = logging.getLogger(name)
        logger.setLevel(log_level)
        
        # Clear existing handlers to avoid duplicates
        if logger.handlers:
            logger.handlers.clear()
            
        # Add handlers
        file_handler = logging.FileHandler(log_file)
        console_handler = logging.StreamHandler()
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger


class LLMClientProvider:
    """Provider for LLM client services."""
    
    @staticmethod
    def get_client(config: Dict[str, Any], logger: logging.Logger):
        """
        Create and return an LLM client.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
            
        Returns:
            LLMClient: Client for interacting with the LLM server
        """
        return LLMClient(
            host=config['llm_server']['host'],
            port=config['llm_server']['port'],
            model=config['llm_server']['model'],
            timeout=config['llm_server']['timeout'],
            logger=logger
        )


class LLMClient:
    """Client for interacting with the LLM server."""
    
    def __init__(
        self,
        host: str,
        port: str,
        model: str,
        timeout: int,
        logger: logging.Logger
    ):
        """
        Initialize the LLM client.
        
        Args:
            host: LLM server host
            port: LLM server port
            model: Model name to use
            timeout: Request timeout in seconds
            logger: Logger instance
        """
        self.host = host
        self.port = port
        self.model = model
        self.timeout = timeout
        self.logger = logger
        self.base_url = f"http://{host}:{port}"
        
    def generate(self, prompt: str) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: Input prompt
            
        Returns:
            str: Generated response
            
        Raises:
            Exception: If the request fails
        """
        self.logger.info(f"Querying {self.model} with prompt length: {len(prompt)}")
        
        payload = {"model": self.model, "prompt": prompt}
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            answer_text = response.text.strip()
            self.logger.info(f"Got response from LLM, length: {len(answer_text)}")
            return answer_text
        except Exception as e:
            self.logger.error(f"LLM inference error: {str(e)}")
            raise
            
    def check_connection(self) -> Dict[str, Any]:
        """
        Check connection to the LLM server.
        
        Returns:
            Dict[str, Any]: Connection status information
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            models = response.json().get("models", [])
            return {
                "status": "connected",
                "api_status": response.status_code,
                "models_available": models
            }
        except Exception as e:
            self.logger.error(f"LLM Server connection check failed: {str(e)}")
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "error_details": str(e)
            }


class ResourceProvider:
    """Provider for resource services."""
    
    @staticmethod
    def get_file_resource_provider(config: Dict[str, Any], logger: logging.Logger):
        """
        Create and return a file resource provider.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
            
        Returns:
            FileResourceProvider: Provider for file resources
        """
        from src.server.resources import FileResourceProvider
        
        # Get base path from config or use default
        base_path = config.get('resources', {}).get('file_base_path', None)
        
        return FileResourceProvider(base_path=base_path)


class ToolProvider:
    """Provider for tool services."""
    
    @staticmethod
    def get_shell_command_tool():
        """
        Get the shell command tool function.
        
        Returns:
            Callable: Function decorated with @tool() to execute shell commands
        """
        from src.server.tools import execute_shell_command
        return execute_shell_command


class MCPComponentProvider:
    """Provider for MCP components."""
    
    @staticmethod
    def get_host(config: Dict[str, Any], logger: logging.Logger):
        """
        Create and return an MCP Host component using SDK factory methods.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
            
        Returns:
            MCPHost: Host component for MCP
        """
        from src.host.host import MCPHost
        from temp.mcp import Host, Consent, Context, Authentication
        import uuid
        
        # Ensure the config has the necessary MCP settings
        if "mcp" not in config:
            config["mcp"] = {}
            
        # Set default host ID if not provided
        if "host_id" not in config.get("mcp", {}):
            config["mcp"]["host_id"] = f"host-{uuid.uuid4()}"
            
        # Set default consent level if not provided
        if "default_consent_level" not in config.get("mcp", {}):
            config["mcp"]["default_consent_level"] = "BASIC"
            
        # Initialize authentication configuration if not present
        if "auth" not in config:
            config["auth"] = {
                "provider": "basic",
                "session_timeout": 3600  # 1 hour
            }
            
        # Initialize context management configuration if not present
        if "context" not in config:
            config["context"] = {
                "storage": "memory",
                "cleanup_interval": 3600  # 1 hour
            }
            
        # Use SDK factory methods to create components
        host_id = config["mcp"]["host_id"]
        mcp_host = Host.create(host_id)
        auth_provider = Authentication.create_provider(config.get("auth", {}))
        context_manager = Context.create_manager(config.get("context", {}))
        consent_manager = Consent.create_manager(config.get("consent", {}))
        
        # Create the host with SDK components
        return MCPHost(
            logger=logger,
            config=config,
            mcp_host=mcp_host,
            auth_provider=auth_provider,
            context_manager=context_manager,
            consent_manager=consent_manager
        )
    
    @staticmethod
    def get_client(config: Dict[str, Any], logger: logging.Logger, host=None):
        """
        Create and return an MCP Client component using SDK factory methods.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
            host: Optional MCPHost instance to connect to
            
        Returns:
            MCPClient: Client component for MCP
        """
        from src.client.client import MCPClient
        from mcp import Client
        import uuid
        
        # Ensure client has an ID
        if "mcp" not in config:
            config["mcp"] = {}
            
        if "client_id" not in config.get("mcp", {}):
            config["mcp"]["client_id"] = f"client-{uuid.uuid4()}"
            
        client_id = config["mcp"]["client_id"]
        
        # Use SDK factory method to create client
        mcp_client = Client.create(client_id, config.get("client", {}))
        
        # Create the client with SDK component
        client = MCPClient(logger=logger, config=config, mcp_client=mcp_client)
        
        # Connect to host if provided
        if host is not None:
            client.connect_to_host(host)
            
            # Register client with host
            client_info = {
                "capabilities": {
                    "tools": True,
                    "resources": True,
                    "subscriptions": True
                },
                "client_id": client_id,
                "name": config.get("mcp", {}).get("client_name", f"Client-{client_id}")
            }
            host.register_client(client_id, client_info, client)
            logger.info(f"Registered client {client_id} with host")
            
        return client
    
    @staticmethod
    def get_server(server_id: str, config: Dict[str, Any], logger: logging.Logger, host=None):
        """
        Create and return an MCP Server component using SDK factory methods.
        
        Args:
            server_id: Unique identifier for the server
            config: Configuration dictionary
            logger: Logger instance
            host: Optional MCPHost instance to register with
            
        Returns:
            MCPServer: Server component for MCP
        """
        from src.server.server import MCPServer
        from src.server.tools import execute_shell_command
        from src.server.resources import FileResourceProvider
        from mcp import Server
        
        # Use SDK factory method to create server
        server_config = config.get("server", {})
        mcp_server = Server.create(server_id, server_config)
        
        # Create the server with SDK component
        server = MCPServer(
            server_id=server_id,
            logger=logger,
            config=config,
            mcp_server=mcp_server
        )
        
        # Register tools
        server.register_tool(execute_shell_command)
        
        # Register resource providers
        file_provider = ResourceProvider.get_file_resource_provider(config, logger)
        server.register_resource_provider("file", file_provider)
        
        # Register with host if provided
        if host is not None:
            server_info = {
                "capabilities": server.capabilities,
                "server_id": server_id,
                "description": config.get("mcp", {}).get("server_description", f"MCP Server {server_id}"),
                "version": config.get("mcp", {}).get("server_version", "1.0.0"),
                "primitives": {
                    "tools": True,
                    "resources": True,
                    "prompts": False
                }
            }
            host.register_server(server_id, server_info, server)
            
            # Set up default consent for this server if configured
            if config.get("mcp", {}).get("auto_consent", True):
                from src.host.host import ConsentLevel
                for client_id in host.get_registered_clients():
                    host.register_consent(
                        client_id=client_id,
                        server_id=server_id,
                        operation_pattern="*",
                        consent_level=ConsentLevel.BASIC
                    )
                    
            logger.info(f"Registered server {server_id} with host")
        
        return server