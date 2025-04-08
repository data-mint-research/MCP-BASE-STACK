"""
Quality Components Package

This package contains modular components for quality enforcement, including:
- Base classes and interfaces for quality components
- Code style checking components
- Static analysis components
- Documentation validation components
- Project structure validation components

Each component follows a consistent interface and can be used independently
or as part of the QualityEnforcer facade.
"""

from core.quality.components.base import (
    QualityComponent,
    QualityCheck,
    QualityCheckResult,
    QualityCheckSeverity,
    QualityCheckRegistry
)

__all__ = [
    'QualityComponent',
    'QualityCheck',
    'QualityCheckResult',
    'QualityCheckSeverity',
    'QualityCheckRegistry'
]