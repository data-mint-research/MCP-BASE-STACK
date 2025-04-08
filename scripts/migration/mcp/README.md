# MCP Migration Scripts

This directory contains scripts for planning and executing the migration to the Model Context Protocol (MCP) architecture.

## Overview

The migration process consists of several steps:

1. **Analyze Current Structure**: Analyze the current system structure to identify components that need to be migrated.
2. **Design MCP Architecture**: Design the target MCP architecture based on the analysis.
3. **Create Migration Plan**: Create a detailed migration plan with phases, tasks, dependencies, and timeline.
4. **Execute Migration**: Execute the migration plan and track progress.

## Scripts

### 1. Analyze Current Structure

```bash
python analyze_current_structure.py [--output PATH]
```

This script analyzes the current system structure and identifies components that need to be migrated to MCP. It outputs a JSON report with the analysis results.

**Arguments:**
- `--output PATH`: Path to output the analysis report (default: data/migration/mcp/analysis_report.json)
- `--verbose`: Enable verbose logging

### 2. Design MCP Architecture

```bash
python design_mcp_architecture.py [--analysis-report PATH] [--output PATH]
```

This script designs the target MCP architecture based on the analysis report. It outputs a JSON file with the architecture design.

**Arguments:**
- `--analysis-report PATH`: Path to the analysis report JSON file (default: data/migration/mcp/analysis_report.json)
- `--output PATH`: Path to output the architecture design (default: data/migration/mcp/architecture_design.json)
- `--verbose`: Enable verbose logging

### 3. Create Migration Plan

```bash
python create_migration_plan.py [--architecture-design PATH] [--analysis-report PATH] [--output PATH]
```

This script creates a detailed migration plan with phases, tasks, dependencies, and timeline. It outputs a JSON file with the migration plan.

**Arguments:**
- `--architecture-design PATH`: Path to the architecture design JSON file (default: data/migration/mcp/architecture_design.json)
- `--analysis-report PATH`: Path to the analysis report JSON file (default: data/migration/mcp/analysis_report.json)
- `--output PATH`: Path to output the migration plan (default: data/migration/mcp/migration_plan.json)
- `--verbose`: Enable verbose logging

## Migration Plan Structure

The migration plan is a JSON file with the following structure:

```json
{
  "phases": [
    {
      "id": "phase_id",
      "name": "Phase Name",
      "description": "Phase Description",
      "order": 1,
      "tasks": ["task_id1", "task_id2"],
      "dependencies": ["dependency_phase_id1"],
      "start_date": "2025-01-01",
      "end_date": "2025-02-01"
    }
  ],
  "tasks": [
    {
      "id": "task_id1",
      "name": "Task Name",
      "description": "Task Description",
      "phase_id": "phase_id",
      "component_name": "Component Name",
      "estimated_effort_days": 5.0,
      "dependencies": ["dependency_task_id1"],
      "subtasks": ["subtask_id1"],
      "status": "not_started",
      "assignee": "",
      "risk_assessment": {
        "level": "medium",
        "description": "Risk Description",
        "mitigation_strategy": "Mitigation Strategy",
        "impact": "Impact Description"
      },
      "start_date": "2025-01-01",
      "end_date": "2025-01-06"
    }
  ],
  "dependencies": [
    {
      "source_task_id": "dependency_task_id1",
      "target_task_id": "task_id1",
      "type": "finish-to-start",
      "description": "Dependency Description"
    }
  ],
  "timeline": {
    "start_date": "2025-01-01",
    "end_date": "2025-12-31",
    "phases": {
      "phase_id": {
        "start_date": "2025-01-01",
        "end_date": "2025-02-01"
      }
    },
    "tasks": {
      "task_id1": {
        "start_date": "2025-01-01",
        "end_date": "2025-01-06"
      }
    }
  },
  "architecture_design_path": "data/migration/mcp/architecture_design.json",
  "analysis_report_path": "data/migration/mcp/analysis_report.json",
  "timestamp": "2025-01-01T00:00:00.000000"
}
```

## Running Tests

To run the unit tests for the migration scripts:

```bash
cd scripts/migration/mcp
python -m unittest discover tests
```

## Directory Structure

```
scripts/migration/mcp/
├── README.md                       # This file
├── analyze_current_structure.py    # Script to analyze current structure
├── design_mcp_architecture.py      # Script to design MCP architecture
├── create_migration_plan.py        # Script to create migration plan
└── tests/                          # Unit tests
    ├── test_analyze_current_structure.py
    ├── test_design_mcp_architecture.py
    └── test_create_migration_plan.py
```

## Data Directory

The scripts output their results to the `data/migration/mcp/` directory by default. Make sure this directory exists or specify alternative output paths.