"""
Quality Hooks Module

This module provides backward compatibility with the existing hooks system.
It re-exports the hook functions from the QualityEnforcer facade to maintain
the same public API while leveraging the new modular architecture.
"""

from core.quality.enforcer import enforcer

# Re-export hook functions from the QualityEnforcer facade
check_code_quality = enforcer.check_code_quality
check_documentation_quality = enforcer.check_documentation_quality
validate_file_structure = enforcer.validate_file_structure
suggest_improvements = enforcer.suggest_improvements
update_knowledge_graph = enforcer.update_knowledge_graph

__all__ = [
    'check_code_quality',
    'check_documentation_quality',
    'validate_file_structure',
    'suggest_improvements',
    'update_knowledge_graph'
]