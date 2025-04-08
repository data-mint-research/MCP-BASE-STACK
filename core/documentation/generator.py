"""
Documentation Generator Module

This module provides the DocumentationGenerator class for generating documentation
from source code and other project artifacts.
"""

import os
import logging
import inspect
import importlib
import pkgutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from core.config.settings import get_config

logger = logging.getLogger(__name__)


class DocumentationGenerator:
    """Documentation generator class."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the DocumentationGenerator.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from settings."""
        if not self.config:
            settings = get_config()
            self.config = settings.get("documentation", {})
        
        # Set default values
        self.output_format = self.config.get("output_format", "markdown")
        self.template_dir = self.config.get("template_dir", "core/documentation/templates")
        self.include_private = self.config.get("include_private", False)
        self.include_source = self.config.get("include_source", True)
    
    def generate_documentation(self, source_dir: str, output_dir: str) -> List[str]:
        """
        Generate documentation for the specified source directory.
        
        Args:
            source_dir: Source directory to generate documentation for
            output_dir: Output directory for the generated documentation
            
        Returns:
            List of generated documentation file paths
        """
        logger.info(f"Generating documentation for {source_dir} to {output_dir}")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Collect modules and packages
        modules = self._collect_modules(source_dir)
        
        # Generate documentation for each module
        output_files = []
        for module_name, module_path in modules:
            output_file = self._generate_module_documentation(module_name, module_path, output_dir)
            if output_file:
                output_files.append(output_file)
        
        # Generate index file
        index_file = self._generate_index(modules, output_dir)
        if index_file:
            output_files.append(index_file)
        
        logger.info(f"Generated {len(output_files)} documentation files")
        return output_files
    
    def _collect_modules(self, source_dir: str) -> List[Tuple[str, str]]:
        """
        Collect Python modules and packages from the source directory.
        
        Args:
            source_dir: Source directory to collect modules from
            
        Returns:
            List of tuples (module_name, module_path)
        """
        modules = []
        source_path = Path(source_dir)
        
        # Add the source directory to sys.path temporarily
        import sys
        sys.path.insert(0, str(source_path.parent))
        
        try:
            # Walk through the directory and collect modules
            for root, dirs, files in os.walk(source_dir):
                # Skip __pycache__ directories
                if "__pycache__" in dirs:
                    dirs.remove("__pycache__")
                
                # Process Python files
                for file in files:
                    if file.endswith(".py") and file != "__init__.py":
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, source_dir)
                        module_name = os.path.splitext(rel_path)[0].replace(os.path.sep, ".")
                        modules.append((module_name, file_path))
                
                # Process packages
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    init_path = os.path.join(dir_path, "__init__.py")
                    if os.path.exists(init_path):
                        rel_path = os.path.relpath(dir_path, source_dir)
                        module_name = rel_path.replace(os.path.sep, ".")
                        modules.append((module_name, dir_path))
        finally:
            # Remove the source directory from sys.path
            sys.path.remove(str(source_path.parent))
        
        return modules
    
    def _generate_module_documentation(self, module_name: str, module_path: str, output_dir: str) -> Optional[str]:
        """
        Generate documentation for a module.
        
        Args:
            module_name: Name of the module
            module_path: Path to the module
            output_dir: Output directory for the generated documentation
            
        Returns:
            Path to the generated documentation file, or None if generation failed
        """
        logger.info(f"Generating documentation for module {module_name}")
        
        try:
            # Import the module
            module = importlib.import_module(module_name)
            
            # Generate documentation content
            content = self._generate_module_content(module_name, module)
            
            # Write to file
            output_file = os.path.join(output_dir, f"{module_name}.md")
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, "w") as f:
                f.write(content)
            
            return output_file
        except Exception as e:
            logger.error(f"Error generating documentation for module {module_name}: {e}")
            return None
    
    def _generate_module_content(self, module_name: str, module: Any) -> str:
        """
        Generate documentation content for a module.
        
        Args:
            module_name: Name of the module
            module: Module object
            
        Returns:
            Documentation content
        """
        content = f"# {module_name}\n\n"
        
        # Add module docstring
        if module.__doc__:
            content += f"{module.__doc__.strip()}\n\n"
        
        # Add classes
        classes = inspect.getmembers(module, inspect.isclass)
        if classes:
            content += "## Classes\n\n"
            for name, cls in classes:
                # Skip imported classes
                if cls.__module__ != module.__name__:
                    continue
                
                # Skip private classes if not included
                if name.startswith("_") and not self.include_private:
                    continue
                
                content += f"### {name}\n\n"
                
                # Add class docstring
                if cls.__doc__:
                    content += f"{cls.__doc__.strip()}\n\n"
                
                # Add methods
                methods = inspect.getmembers(cls, inspect.isfunction)
                if methods:
                    content += "#### Methods\n\n"
                    for method_name, method in methods:
                        # Skip private methods if not included
                        if method_name.startswith("_") and not self.include_private:
                            continue
                        
                        content += f"##### `{method_name}`\n\n"
                        
                        # Add method docstring
                        if method.__doc__:
                            content += f"{method.__doc__.strip()}\n\n"
                        
                        # Add method signature
                        signature = inspect.signature(method)
                        content += f"```python\n{method_name}{signature}\n```\n\n"
        
        # Add functions
        functions = inspect.getmembers(module, inspect.isfunction)
        if functions:
            content += "## Functions\n\n"
            for name, func in functions:
                # Skip imported functions
                if func.__module__ != module.__name__:
                    continue
                
                # Skip private functions if not included
                if name.startswith("_") and not self.include_private:
                    continue
                
                content += f"### `{name}`\n\n"
                
                # Add function docstring
                if func.__doc__:
                    content += f"{func.__doc__.strip()}\n\n"
                
                # Add function signature
                signature = inspect.signature(func)
                content += f"```python\n{name}{signature}\n```\n\n"
        
        return content
    
    def _generate_index(self, modules: List[Tuple[str, str]], output_dir: str) -> Optional[str]:
        """
        Generate an index file for the documentation.
        
        Args:
            modules: List of tuples (module_name, module_path)
            output_dir: Output directory for the generated documentation
            
        Returns:
            Path to the generated index file, or None if generation failed
        """
        logger.info("Generating documentation index")
        
        try:
            # Generate index content
            content = "# API Documentation\n\n"
            content += "## Modules\n\n"
            
            # Group modules by package
            packages = {}
            for module_name, _ in modules:
                parts = module_name.split(".")
                if len(parts) > 1:
                    package = parts[0]
                    if package not in packages:
                        packages[package] = []
                    packages[package].append(module_name)
                else:
                    if "root" not in packages:
                        packages["root"] = []
                    packages["root"].append(module_name)
            
            # Add links to modules
            for package, package_modules in sorted(packages.items()):
                if package != "root":
                    content += f"### {package}\n\n"
                else:
                    content += "### Root Modules\n\n"
                
                for module_name in sorted(package_modules):
                    content += f"- [{module_name}]({module_name}.md)\n"
                
                content += "\n"
            
            # Write to file
            output_file = os.path.join(output_dir, "index.md")
            with open(output_file, "w") as f:
                f.write(content)
            
            return output_file
        except Exception as e:
            logger.error(f"Error generating documentation index: {e}")
            return None