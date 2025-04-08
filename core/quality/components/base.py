"""
Base Classes and Interfaces for Quality Components

This module defines the core abstractions for the quality enforcement system:
- QualityComponent: Base class for all quality components
- QualityCheck: Interface for individual quality checks
- QualityCheckResult: Class representing the result of a quality check
- QualityCheckSeverity: Enum for severity levels
- QualityCheckRegistry: Registry for quality check plugins
"""

import abc
import enum
import importlib
import inspect
import logging
import os
import pkgutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type, Union

from core.config.settings import get_config

logger = logging.getLogger(__name__)


class QualityCheckSeverity(enum.Enum):
    """Severity levels for quality check results."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class QualityCheckResult:
    """Result of a quality check."""
    check_id: str
    severity: QualityCheckSeverity
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    column: Optional[int] = None
    source: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    fix_available: bool = False
    fix_command: Optional[str] = None
    
    def __str__(self) -> str:
        """String representation of the result."""
        location = ""
        if self.file_path:
            location = f"{self.file_path}"
            if self.line_number:
                location += f":{self.line_number}"
                if self.column:
                    location += f":{self.column}"
        
        return f"[{self.severity.value.upper()}] {self.check_id}: {self.message} {location}"


class QualityCheck(abc.ABC):
    """Interface for individual quality checks."""
    
    @property
    @abc.abstractmethod
    def id(self) -> str:
        """Unique identifier for the check."""
        pass
    
    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Human-readable name for the check."""
        pass
    
    @property
    @abc.abstractmethod
    def description(self) -> str:
        """Description of what the check does."""
        pass
    
    @property
    def enabled(self) -> bool:
        """Whether the check is enabled."""
        config = get_config()
        quality_config = config.get("quality", {})
        checks_config = quality_config.get("checks", {})
        check_config = checks_config.get(self.id, {})
        return check_config.get("enabled", True)
    
    @property
    def severity(self) -> QualityCheckSeverity:
        """Default severity for issues found by this check."""
        config = get_config()
        quality_config = config.get("quality", {})
        checks_config = quality_config.get("checks", {})
        check_config = checks_config.get(self.id, {})
        severity_str = check_config.get(
            "severity",
            QualityCheckSeverity.WARNING.value
        )
        return QualityCheckSeverity(severity_str)
    
    @abc.abstractmethod
    def run(self, file_paths: Optional[List[str]] = None, **kwargs) -> List[QualityCheckResult]:
        """
        Run the quality check.
        
        Args:
            file_paths: Optional list of file paths to check. If None, check all relevant files.
            **kwargs: Additional arguments for the check.
            
        Returns:
            List of QualityCheckResult objects.
        """
        pass
    
    def can_fix(self) -> bool:
        """Whether this check can automatically fix issues."""
        return False
    
    def fix(self, results: List[QualityCheckResult]) -> List[QualityCheckResult]:
        """
        Fix issues identified by this check.
        
        Args:
            results: List of QualityCheckResult objects to fix.
            
        Returns:
            List of QualityCheckResult objects that couldn't be fixed.
        """
        if not self.can_fix():
            return results
        return results


class QualityComponent(abc.ABC):
    """Base class for quality components."""
    
    def __init__(self, name: str = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the component.
        
        Args:
            name: Optional name for the component
            config: Optional configuration for the component
        """
        self._name = name
        self._config = config or {}
        self._checks: List[QualityCheck] = []
        self._initialize_checks()
    
    @property
    def name(self) -> str:
        """Name of the component."""
        if self._name:
            return self._name
        return self.__class__.__name__.lower()
    
    @property
    def description(self) -> str:
        """Description of the component."""
        return f"Quality component for {self.name}"
    
    def _initialize_checks(self) -> None:
        """Initialize the checks for this component."""
        # This is a base implementation that does nothing
        # Subclasses should override this method to add checks
        pass
    
    @property
    def checks(self) -> List[QualityCheck]:
        """Get all checks for this component."""
        return self._checks
    
    def get_enabled_checks(self) -> List[QualityCheck]:
        """Get all enabled checks for this component."""
        return [check for check in self._checks if check.enabled]
    
    def run_checks(self, file_paths: Optional[List[str]] = None, **kwargs) -> List[QualityCheckResult]:
        """
        Run all enabled checks for this component.
        
        Args:
            file_paths: Optional list of file paths to check. If None, check all relevant files.
            **kwargs: Additional arguments for the checks.
            
        Returns:
            List of QualityCheckResult objects.
        """
        results = []
        for check in self.get_enabled_checks():
            try:
                check_results = check.run(file_paths, **kwargs)
                results.extend(check_results)
            except Exception as e:
                logger.exception(f"Error running check {check.id}: {e}")
                results.append(QualityCheckResult(
                    check_id=check.id,
                    severity=QualityCheckSeverity.ERROR,
                    message=f"Error running check: {str(e)}",
                    source=self.name
                ))
        return results
    
    def fix_issues(self, results: List[QualityCheckResult]) -> List[QualityCheckResult]:
        """
        Fix issues identified by this component's checks.
        
        Args:
            results: List of QualityCheckResult objects to fix.
            
        Returns:
            List of QualityCheckResult objects that couldn't be fixed.
        """
        remaining_results = []
        check_map = {check.id: check for check in self._checks}
        
        # Group results by check_id
        results_by_check: Dict[str, List[QualityCheckResult]] = {}
        for result in results:
            if result.check_id not in results_by_check:
                results_by_check[result.check_id] = []
            results_by_check[result.check_id].append(result)
        
        # Fix issues for each check
        for check_id, check_results in results_by_check.items():
            if check_id in check_map and check_map[check_id].can_fix():
                unfixed = check_map[check_id].fix(check_results)
                remaining_results.extend(unfixed)
            else:
                remaining_results.extend(check_results)
        
        return remaining_results


class QualityCheckRegistry:
    """Registry for quality check plugins."""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super(QualityCheckRegistry, cls).__new__(cls)
            cls._instance._checks = {}
            cls._instance._components = {}
            cls._instance._initialized = False
        return cls._instance
    
    def register_check(self, check_class: Type[QualityCheck]) -> None:
        """
        Register a quality check.
        
        Args:
            check_class: The QualityCheck class to register.
        """
        try:
            check = check_class()
            self._checks[check.id] = check_class
            logger.debug(f"Registered quality check: {check.id}")
        except Exception as e:
            logger.error(f"Failed to register quality check {check_class.__name__}: {e}")
    
    def register_component(self, component_class: Type[QualityComponent]) -> None:
        """
        Register a quality component.
        
        Args:
            component_class: The QualityComponent class to register.
        """
        try:
            component = component_class()
            self._components[component.name] = component_class
            logger.debug(f"Registered quality component: {component.name}")
        except Exception as e:
            logger.error(f"Failed to register quality component {component_class.__name__}: {e}")
    
    def get_check(self, check_id: str) -> Optional[QualityCheck]:
        """
        Get a quality check by ID.
        
        Args:
            check_id: The ID of the check to get.
            
        Returns:
            The QualityCheck instance, or None if not found.
        """
        check_class = self._checks.get(check_id)
        if check_class:
            return check_class()
        return None
    
    def get_component(self, component_name: str) -> Optional[QualityComponent]:
        """
        Get a quality component by name.
        
        Args:
            component_name: The name of the component to get.
            
        Returns:
            The QualityComponent instance, or None if not found.
        """
        component_class = self._components.get(component_name)
        if component_class:
            return component_class()
        return None
    
    def get_all_checks(self) -> Dict[str, Type[QualityCheck]]:
        """
        Get all registered quality checks.
        
        Returns:
            Dictionary mapping check IDs to QualityCheck classes.
        """
        return self._checks.copy()
    
    def get_all_components(self) -> Dict[str, Type[QualityComponent]]:
        """
        Get all registered quality components.
        
        Returns:
            Dictionary mapping component names to QualityComponent classes.
        """
        return self._components.copy()
    
    def discover_plugins(self, plugin_dirs: Optional[List[str]] = None) -> None:
        """
        Discover and register plugins from specified directories.
        
        Args:
            plugin_dirs: List of directories to search for plugins.
                If None, use the default plugin directories from settings.
        """
        if plugin_dirs is None:
            config = get_config()
            quality_config = config.get("quality", {})
            plugin_dirs = quality_config.get("plugin_dirs", [])
        
        for plugin_dir in plugin_dirs:
            self._discover_plugins_in_dir(plugin_dir)
    
    def _discover_plugins_in_dir(self, plugin_dir: str) -> None:
        """
        Discover and register plugins in a directory.
        
        Args:
            plugin_dir: Directory to search for plugins.
        """
        plugin_dir_path = Path(plugin_dir)
        if not plugin_dir_path.exists() or not plugin_dir_path.is_dir():
            logger.warning(f"Plugin directory does not exist: {plugin_dir}")
            return
        
        # Add the plugin directory to sys.path temporarily
        sys.path.insert(0, str(plugin_dir_path.parent))
        
        try:
            # Import all modules in the plugin directory
            for _, name, is_pkg in pkgutil.iter_modules([str(plugin_dir_path)]):
                try:
                    module = importlib.import_module(f"{plugin_dir_path.name}.{name}")
                    
                    # Register all QualityCheck and QualityComponent classes in the module
                    for _, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, QualityCheck) and obj != QualityCheck:
                            self.register_check(obj)
                        elif issubclass(obj, QualityComponent) and obj != QualityComponent:
                            self.register_component(obj)
                except Exception as e:
                    logger.error(f"Error loading plugin module {name}: {e}")
        finally:
            # Remove the plugin directory from sys.path
            sys.path.remove(str(plugin_dir_path.parent))
    
    def initialize(self) -> None:
        """Initialize the registry by discovering plugins."""
        if not self._initialized:
            self.discover_plugins()
            self._initialized = True


# Initialize the registry
registry = QualityCheckRegistry()