# File Cleanup Implementation Plan

## Overview

This document outlines the plan for implementing file cleanup in the MCP-BASE-STACK project based on the previous identification tasks. The cleanup will be performed using the `cleanup_files.py` script in interactive mode, which will allow for careful review of each file before taking action.

## Prerequisites

1. ✅ Created the `config/specifications` directory
2. ✅ Created the `specification-manifest.json` file
3. ✅ Created the `specification-manifest-schema.json` file

## Cleanup Categories

Based on the previous identification tasks, the following categories of files need to be cleaned up:

### 1. Zone.Identifier Files

These are Windows-specific metadata files that are not needed and can be safely removed:

- `docs/MCP/README.md:Zone.Identifier`
- `docs/MCP/architecture.md:Zone.Identifier`
- `docs/MCP/compliance-checklist.md:Zone.Identifier`
- `docs/MCP/docs_MCP.zip:Zone.Identifier`
- `docs/MCP/init-mcpgeek.sh:Zone.Identifier`
- `docs/MCP/protocol.md:Zone.Identifier`
- `docs/MCP/quickstart.md:Zone.Identifier`
- `docs/MCP/resources.md:Zone.Identifier`
- `docs/MCP/roo-mode.json:Zone.Identifier`
- `docs/MCP/sdk-usage.md:Zone.Identifier`
- `docs/MCP/tools.md:Zone.Identifier`

### 2. Empty Files

Empty files that may indicate incomplete or abandoned work:

- `create_new_file.py` (0 bytes)
- Empty log files in the `data/logs` directory

### 3. Duplicate Files

Files with identical content in different locations:

#### Docker Compose Files
- Keep files in `config/services/` directory, remove duplicates in `services/` directory:
  - `services/librechat/docker-compose.yml` (duplicate of `config/services/librechat/docker-compose.yml`)
  - `services/librechat/docker-compose.temp.yml` (duplicate of `config/services/librechat/docker-compose.temp.yml`)
  - `services/mcp-server/docker-compose.yml` (duplicate of `config/services/mcp-server/docker-compose.yml`)
  - `services/llm-server/docker-compose.yml` (duplicate of `config/services/llm-server/docker-compose.yml`)

#### README Files
- Keep original README files in source directories, remove duplicates in docs directory:
  - `docs/scripts/utils-quality-README.md` (duplicate of `scripts/utils/quality/README.md`)
  - `docs/scripts/maintenance-README.md` (duplicate of `scripts/maintenance/README.md`)
  - `docs/tests/README.md` (duplicate of `tests/README.md`)
  - `docs/services/mcp-server-di-README.md` (duplicate of `services/mcp-server/src/di/README.md`)
  - `docs/kg/scripts-README.md` (duplicate of `core/kg/scripts/README.md`)

#### Other Duplicates
- `standardize_file_structure.py` and `standardize_file_structure_fixed.py` (determine which is the correct version)

### 4. Configuration Files in Multiple Locations

- Keep the root version for tool compatibility, implement symlinks or a build process to ensure they stay in sync:
  - `.pre-commit-config.yaml` and `config/lint/pre-commit-config.yaml`
  - `.markdownlint.yaml` and `config/lint/markdownlint.yaml`
  - `.yamllint.yaml` and `config/lint/yamllint.yaml`
  - `pytest.ini` and `config/pytest.ini`

## Implementation Steps

1. Run the cleanup_files.py script in interactive mode
2. Review and clean up each file category
3. Document all cleanup actions taken
4. Verify no functionality is broken after cleanup
5. Update the knowledge graph with the cleanup results

## Execution Plan

### Step 1: Run cleanup_files.py in Interactive Mode

```bash
python scripts/utils/cleanup/cleanup_files.py --project-dir . --manifest config/specifications/specification-manifest.json --interactive
```

### Step 2: Document Cleanup Actions

For each file that is cleaned up, document:
- File path
- Reason for cleanup
- Action taken (removed, archived, moved)
- Date and time of action

### Step 3: Verify Functionality

After cleanup, verify that no functionality is broken by:
- Running tests
- Checking that the application still builds and runs
- Verifying that documentation is still accessible

### Step 4: Update Knowledge Graph

Update the knowledge graph with the cleanup results to ensure it remains the single source of truth.

## Expected Outcomes

1. Removal of unnecessary files (Zone.Identifier files, empty files)
2. Consolidation of duplicate files
3. Improved organization of configuration files
4. Updated knowledge graph reflecting the changes
5. Reduced technical debt and improved maintainability

## Rollback Plan

If any issues are encountered during or after cleanup:
1. Use the backup files created by the cleanup_files.py script to restore the original files
2. Document the issues encountered
3. Update the cleanup plan to address the issues