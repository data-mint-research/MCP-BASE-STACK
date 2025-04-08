# Knowledge Graph Quality Metrics Schema

This document describes the quality metrics schema integrated into the knowledge graph. The schema enables tracking, monitoring, and analysis of code quality metrics across the codebase.

## Overview

The quality metrics schema extends the knowledge graph with:

1. Quality metrics nodes that represent quality measurements
2. Component-quality relationships that link quality metrics to components
3. Automated updates from quality check results

## Schema Structure

### Node Types

- **Quality Metrics Node**: Central node that organizes all quality metrics
  - Type: `component`
  - Component Type: `metrics`
  - Status: `active`

- **Component Quality Metric Nodes**: Nodes that store quality metrics for specific components
  - Type: `quality_metric`
  - Contains metrics like complexity, coverage, and issue counts

### Relationships

- **TRACKS**: Connects the central Quality Metrics node to component-specific quality metric nodes
- **MEASURES**: Connects component quality metric nodes to their respective component nodes

### Attributes

Quality metric nodes include the following attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| complexity_cyclomatic | long | Cyclomatic complexity measurement |
| complexity_cognitive | long | Cognitive complexity measurement |
| type_hint_coverage | double | Percentage of functions with type hints |
| documentation_coverage | double | Percentage of documented functions/classes |
| test_coverage | double | Percentage of code covered by tests |
| issues_count | long | Total number of quality issues |
| info_count | long | Number of info-level issues |
| warning_count | long | Number of warning-level issues |
| error_count | long | Number of error-level issues |
| critical_count | long | Number of critical-level issues |
| last_modified | double | Timestamp of last update |

## Automated Updates

The quality metrics in the knowledge graph are automatically updated through:

1. The `QualityEnforcer.update_knowledge_graph()` method, which:
   - Exports quality check results to a JSON file
   - Triggers the knowledge graph update script

2. The `update_knowledge_graph.py` script, which:
   - Reads the latest quality report
   - Updates quality metric nodes in the graph
   - Updates component-quality relationships

## Usage Examples

### Querying Quality Metrics

To query quality metrics for a specific component:

```python
import networkx as nx

# Load the knowledge graph
graph = nx.read_graphml("core/kg/data/knowledge_graph.graphml")

# Get quality metrics for the core component
core_quality = graph.nodes["core_quality"]
print(f"Core documentation coverage: {core_quality.get('documentation_coverage', 0.0) * 100}%")
print(f"Core type hint coverage: {core_quality.get('type_hint_coverage', 0.0) * 100}%")
print(f"Core issues: {core_quality.get('issues_count', 0)}")
```

### Visualizing Quality Trends

Quality metrics can be tracked over time by storing historical data in the knowledge graph. This enables visualization of quality trends and identification of areas for improvement.

## Integration with Quality Enforcement

The quality metrics schema is integrated with the quality enforcement system:

1. Quality checks are run by the `QualityEnforcer`
2. Results are exported to JSON reports
3. The knowledge graph is updated with the latest metrics
4. Components with quality issues can be identified through the graph

This integration ensures that the knowledge graph serves as the single source of truth for code quality across the project.