"""
Providers for the dependency injection container.

This module defines the service providers that will be used by the dependency injection container.
Each provider is responsible for creating and configuring a specific service.
"""

import logging
import os
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


class ToolProvider:
    """Provider for tool services."""
    
    @staticmethod
    def get_shell_command_executor(logger: logging.Logger):
        """
        Create and return a shell command executor.
        
        Args:
            logger: Logger instance
            
        Returns:
            Callable: Function to execute shell commands
        """
        from tools.shell.command import execute_shell_command
        
        # Return a wrapper that uses the provided logger
        def execute_command(command: str, timeout: int = 60):
            return execute_shell_command(command, timeout)
            
        return execute_command