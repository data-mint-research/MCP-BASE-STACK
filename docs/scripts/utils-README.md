# Utility Scripts

This directory contains various utility scripts organized by their function. Each subdirectory contains scripts related to a specific category of functionality.

## Directory Structure

- **backup/**: Scripts related to creating and restoring backups
  - `create-backup-branch.sh`: Creates a backup branch in git
  - `restore-from-backup.sh`: Restores code from a backup branch

- **cleanup/**: Scripts for cleaning up files and directories
  - `cleanup-backup-dirs.sh`: Cleans up backup directories
  - `cleanup_files.py`: Python script for cleaning up files

- **quality/**: Scripts for checking and fixing code quality
  - `check-code-quality.sh`: Checks code quality against defined standards
  - `fix-code-quality.sh`: Automatically fixes code quality issues
  - `check_code_quality_nodes.py`: Checks code quality nodes in the knowledge graph

- **analysis/**: Scripts for analyzing code and project structure
  - `analyze_code.py`: Analyzes code structure and patterns
  - `check_kg_nodes.py`: Checks knowledge graph nodes
  - `traverse_project.py`: Traverses the project structure

- **installation/**: Scripts for installing hooks and other components
  - `install-pre-commit-hooks.sh`: Installs pre-commit hooks
  - `install-file-update-hooks.sh`: Installs file update hooks

- **validation/**: Scripts for validating project components
  - `validate-manifest.py`: Validates the project manifest
  - `verify-stack-health.sh`: Verifies the health of the stack

## Usage

Each script can be run from its respective directory. For example:

```bash
# Run a backup script
./scripts/utils/backup/create-backup-branch.sh

# Run a cleanup script
python ./scripts/utils/cleanup/cleanup_files.py

# Run a quality script
./scripts/utils/quality/check-code-quality.sh
```

## Adding New Scripts

When adding new utility scripts, please place them in the appropriate subdirectory based on their function. If a new category is needed, create a new subdirectory with a descriptive name.