"""
Mock objects for testing.

This module provides mock objects for external dependencies used in tests,
such as file systems, knowledge graph connections, and configuration objects.
"""

import os
from typing import Dict, List, Optional, Any, Union
from unittest.mock import MagicMock


class MockFileSystem:
    """
    Mock file system for testing file operations.
    
    This class provides a mock file system that can be used to test
    file operations without actually modifying the file system.
    """
    
    def __init__(self, structure: Optional[Dict[str, Any]] = None):
        """
        Initialize the mock file system.
        
        Args:
            structure: Optional dictionary representing the file structure.
                If None, an empty structure is created.
        """
        self.structure = structure or {}
        self.files = {}
        self._build_files()
    
    def _build_files(self, prefix: str = "", structure: Optional[Dict[str, Any]] = None) -> None:
        """
        Build the flat files dictionary from the nested structure.
        
        Args:
            prefix: Prefix for the current directory.
            structure: Current structure to process.
        """
        if structure is None:
            structure = self.structure
        
        for name, content in structure.items():
            path = os.path.join(prefix, name)
            if isinstance(content, dict):
                self._build_files(path, content)
            else:
                self.files[path] = content
    
    def exists(self, path: str) -> bool:
        """
        Check if a file or directory exists.
        
        Args:
            path: Path to check.
            
        Returns:
            True if the path exists, False otherwise.
        """
        # Check if it's a file
        if path in self.files:
            return True
        
        # Check if it's a directory (prefix of any file)
        for file_path in self.files:
            if file_path.startswith(path + os.sep):
                return True
        
        return False
    
    def is_file(self, path: str) -> bool:
        """
        Check if a path is a file.
        
        Args:
            path: Path to check.
            
        Returns:
            True if the path is a file, False otherwise.
        """
        return path in self.files
    
    def is_dir(self, path: str) -> bool:
        """
        Check if a path is a directory.
        
        Args:
            path: Path to check.
            
        Returns:
            True if the path is a directory, False otherwise.
        """
        if path == "":
            return True
        
        for file_path in self.files:
            if file_path.startswith(path + os.sep):
                return True
        
        return False
    
    def read_file(self, path: str) -> str:
        """
        Read a file's contents.
        
        Args:
            path: Path to the file.
            
        Returns:
            The file's contents.
            
        Raises:
            FileNotFoundError: If the file doesn't exist.
        """
        if path not in self.files:
            raise FileNotFoundError(f"File not found: {path}")
        
        return self.files[path]
    
    def write_file(self, path: str, content: str) -> None:
        """
        Write content to a file.
        
        Args:
            path: Path to the file.
            content: Content to write.
        """
        self.files[path] = content
    
    def list_dir(self, path: str) -> List[str]:
        """
        List the contents of a directory.
        
        Args:
            path: Path to the directory.
            
        Returns:
            List of file and directory names in the directory.
            
        Raises:
            NotADirectoryError: If the path is not a directory.
        """
        if not self.is_dir(path):
            raise NotADirectoryError(f"Not a directory: {path}")
        
        contents = set()
        path_prefix = path + os.sep if path else ""
        
        for file_path in self.files:
            if file_path.startswith(path_prefix):
                # Get the next component of the path
                remaining = file_path[len(path_prefix):]
                next_component = remaining.split(os.sep, 1)[0]
                contents.add(next_component)
        
        return sorted(list(contents))


class MockKnowledgeGraph:
    """
    Mock knowledge graph for testing knowledge graph operations.
    
    This class provides a mock knowledge graph that can be used to test
    knowledge graph operations without actually modifying the knowledge graph.
    """
    
    def __init__(self, schema: Optional[Dict[str, Any]] = None):
        """
        Initialize the mock knowledge graph.
        
        Args:
            schema: Optional dictionary representing the knowledge graph schema.
                If None, an empty schema is created.
        """
        self.schema = schema or {"nodes": {}, "relationships": {}}
        self.nodes = {}
        self.relationships = []
    
    def add_node(self, label: str, properties: Dict[str, Any]) -> str:
        """
        Add a node to the knowledge graph.
        
        Args:
            label: The node label.
            properties: The node properties.
            
        Returns:
            The node ID.
        """
        node_id = f"{label}_{len(self.nodes)}"
        self.nodes[node_id] = {
            "label": label,
            "properties": properties
        }
        return node_id
    
    def add_relationship(self, source_id: str, target_id: str, type_name: str, properties: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a relationship to the knowledge graph.
        
        Args:
            source_id: The source node ID.
            target_id: The target node ID.
            type_name: The relationship type.
            properties: Optional relationship properties.
        """
        self.relationships.append({
            "source": source_id,
            "target": target_id,
            "type": type_name,
            "properties": properties or {}
        })
    
    def query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a query on the knowledge graph.
        
        Args:
            query: The query string.
            params: Optional query parameters.
            
        Returns:
            The query results.
        """
        # This is a very simplified mock that just returns empty results
        # In a real implementation, this would parse the query and return appropriate results
        return []


class MockConfig:
    """
    Mock configuration for testing.
    
    This class provides a mock configuration that can be used to test
    code that depends on configuration values.
    """
    
    def __init__(self, values: Optional[Dict[str, Any]] = None):
        """
        Initialize the mock configuration.
        
        Args:
            values: Optional dictionary of configuration values.
                If None, default values are used.
        """
        self.values = values or {
            "quality": {
                "enabled": True,
                "components": ["code_style", "static_analysis", "documentation", "structure"],
                "severity_threshold": "WARNING",
                "auto_fix": True
            },
            "logging": {
                "level": "INFO",
                "directory": "data/logs",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "documentation": {
                "required": True,
                "coverage_threshold": 80.0,
                "output_directory": "docs/generated"
            },
            "knowledge_graph": {
                "enabled": True,
                "update_on_quality_check": True,
                "metrics_schema_path": "core/kg/quality_metrics_schema.py",
                "metrics_query_path": "core/kg/quality_metrics_query.py"
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: The configuration key.
            default: The default value to return if the key is not found.
            
        Returns:
            The configuration value.
        """
        parts = key.split(".")
        current = self.values
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        
        return current
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: The configuration key.
            value: The configuration value.
        """
        parts = key.split(".")
        current = self.values
        
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value


def create_mock_quality_component() -> MagicMock:
    """
    Create a mock quality component.
    
    Returns:
        A mock quality component.
    """
    mock_component = MagicMock()
    mock_component.name = "Mock Component"
    mock_component.run_checks.return_value = []
    mock_component.fix_issues.return_value = []
    return mock_component


def create_mock_quality_check() -> MagicMock:
    """
    Create a mock quality check.
    
    Returns:
        A mock quality check.
    """
    mock_check = MagicMock()
    mock_check.id = "mock_check"
    mock_check.name = "Mock Check"
    mock_check.description = "A mock quality check"
    mock_check.run.return_value = []
    mock_check.fix.return_value = []
    return mock_check