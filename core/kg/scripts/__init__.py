"""
Knowledge Graph Scripts

This package contains scripts for managing the knowledge graph.
"""

from core.kg.scripts.update_knowledge_graph import (
    update_component_status,
    update_file_structure_metrics,
    update_quality_metrics,
)
from core.kg.scripts.setup_knowledge_graph import setup_knowledge_graph

__all__ = [
    'update_component_status',
    'update_file_structure_metrics',
    'update_quality_metrics',
    'setup_knowledge_graph',
]