# Validation Utilities

## Overview

This directory contains utility scripts for validating various aspects of the MCP-BASE-STACK project. These utilities ensure that the project adheres to its specifications, that components are functioning correctly, and that the system as a whole is healthy.

## Scripts

### validate_manifest.py

Validates the specification manifest against its schema and validates a project against the manifest.

Features:
- Validates the specification manifest against its JSON Schema
- Validates a project directory against the specification manifest
- Checks directory structure compliance
- Verifies required file presence
- Validates naming conventions

Usage:
```bash
# Validate the manifest against its schema
python validate_manifest.py validate-schema
python validate_manifest.py validate-schema --manifest path/to/manifest.json --schema path/to/schema.json

# Validate a project against the manifest
python validate_manifest.py validate-project [directory]
python validate_manifest.py validate-project [directory] --manifest path/to/manifest.json
```

### verify-backup-system.sh

Verifies that the backup system is functioning correctly by:
- Checking that backup scripts are present and executable
- Verifying that backup directories exist and have the correct permissions
- Testing the backup creation process
- Validating the integrity of existing backups
- Checking that the restore functionality works correctly

Usage:
```bash
./verify-backup-system.sh
```

### verify-stack-health.sh

Performs a comprehensive health check of the MCP-BASE-STACK by:
- Verifying that all required services are running
- Checking connectivity between components
- Validating configuration files
- Monitoring resource usage
- Testing critical functionality

This script is useful for ensuring that the system is in a healthy state before deploying changes or after system updates.

Usage:
```bash
./verify-stack-health.sh
```

## Integration with CI/CD

These validation utilities are designed to be integrated into CI/CD pipelines to ensure that:

1. All changes adhere to the project's specifications
2. The system remains in a healthy state after changes
3. Backups are functioning correctly to enable recovery if needed

Example integration in a GitHub Actions workflow:

```yaml
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Validate manifest
        run: python scripts/utils/validation/validate_manifest.py validate-project
      - name: Verify stack health
        run: ./scripts/utils/validation/verify-stack-health.sh
```

## Integration with Knowledge Graph

The validation utilities update the knowledge graph with their findings, ensuring that the project's state is accurately reflected. This integration allows for tracking compliance and health metrics over time.

## Best Practices

When using these validation utilities:

1. Run them regularly, not just when making changes
2. Integrate them into your CI/CD pipeline
3. Address validation failures immediately
4. Use the detailed output to understand and fix issues
5. Ensure the knowledge graph is updated after validation