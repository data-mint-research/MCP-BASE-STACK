"""
Auto-fix Capabilities for Quality Components

This package provides auto-fix capabilities for quality components, including:
- Code style fixes
- Documentation fixes
- Structure fixes
- Static analysis fixes

These modules implement safe, automated fixes for common quality issues.
"""

from core.quality.components.fixes.code_style import CodeStyleFixes
from core.quality.components.fixes.documentation import DocumentationFixes
from core.quality.components.fixes.static_analysis import StaticAnalysisFixes
from core.quality.components.fixes.structure import StructureFixes

__all__ = [
    "CodeStyleFixes",
    "DocumentationFixes",
    "StaticAnalysisFixes",
    "StructureFixes"
]