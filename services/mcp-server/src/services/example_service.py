"""
Example Service.

This is a simple example service that demonstrates how to use the dependency injection framework.
It shows how to inject dependencies and use them in a service class.
"""

import logging
from typing import Dict, Any


class ExampleService:
    """
    Example service that demonstrates dependency injection.
    
    This service shows how to:
    1. Inject dependencies through the constructor
    2. Use those dependencies in service methods
    3. Structure a service class for testability
    """
    
    def __init__(
        self,
        logger: logging.Logger,
        config: Dict[str, Any]
    ):
        """
        Initialize the example service with injected dependencies.
        
        Args:
            logger: Logger instance
            config: Configuration dictionary
        """
        self.logger = logger
        self.config = config
        self.logger.info("ExampleService initialized with dependency injection")
        
    def get_service_info(self) -> Dict[str, Any]:
        """
        Get information about this service.
        
        Returns:
            Dict[str, Any]: Service information
        """
        self.logger.info("ExampleService.get_service_info called")
        
        return {
            "name": "ExampleService",
            "description": "A simple example service that demonstrates dependency injection",
            "config_keys": list(self.config.keys()),
            "server_config": self.config.get("server", {})
        }
        
    def process_data(self, data: str) -> str:
        """
        Process some data using the service.
        
        Args:
            data: Input data to process
            
        Returns:
            str: Processed data
        """
        self.logger.info(f"Processing data: {data[:20]}...")
        
        # Simple processing - just uppercase the data
        result = data.upper()
        
        self.logger.info(f"Data processing complete, result length: {len(result)}")
        return result