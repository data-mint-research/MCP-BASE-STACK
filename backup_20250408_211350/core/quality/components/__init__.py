"""
Quality Components

This package contains various quality components for checking and enforcing code quality standards.
"""

from typing import Dict, Any, Optional

from core.quality.components.base import (
    QualityCheck,
    QualityCheckRegistry,
    QualityCheckResult,
    QualityCheckSeverity,
    QualityComponent,
)

def create_component(name: str, config: Optional[Dict[str, Any]] = None) -> QualityComponent:
    """
    Create a quality component by name.
    
    Args:
        name: The name of the component to create
        config: Optional configuration for the component
        
    Returns:
        QualityComponent: The created component
        
    Raises:
        ValueError: If the component name is not recognized
    """
    config = config or {}
    
    # Map of component names to their classes
    component_map = {
        "code_style": QualityComponent,  # Replace with actual component classes when implemented
        "static_analysis": QualityComponent,
        "documentation": QualityComponent,
        "structure": QualityComponent,
    }
    
    if name not in component_map:
        raise ValueError(f"Unknown quality component: {name}")
    
    # Create and return the component
    return component_map[name](name=name, config=config)

__all__ = [
    'QualityCheck',
    'QualityCheckRegistry',
    'QualityCheckResult',
    'QualityCheckSeverity',
    'QualityComponent',
    'create_component',
]