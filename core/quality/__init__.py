"""
Quality Module

This module provides tools for enforcing code quality standards across the project.
It includes a modular architecture for quality checks, with components for:
- Code style (formatting, consistency)
- Static analysis (linting, type checking)
- Documentation (docstrings, README files)
- Project structure (directory organization, file naming)

The main entry point is the QualityEnforcer class, which provides a facade over
the component system while maintaining backward compatibility with existing hooks.
"""

from core.quality.enforcer import QualityEnforcer, enforcer
from core.quality.components.base import (
    QualityCheck,
    QualityCheckResult,
    QualityCheckSeverity,
    QualityCheckRegistry,
    QualityComponent
)

__all__ = [
    'QualityEnforcer',
    'enforcer',
    'QualityCheck',
    'QualityCheckResult',
    'QualityCheckSeverity',
    'QualityCheckRegistry',
    'QualityComponent'
]