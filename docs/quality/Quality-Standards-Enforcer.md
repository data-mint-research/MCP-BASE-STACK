# Quality Standards Enforcer

The Quality Standards Enforcer is a master script that orchestrates the execution of all quality enforcement scripts in an iterative cycle, continuing until no further changes are needed. It then generates a comprehensive final report and updates the knowledge graph with the final state.

## Overview

The Quality Standards Enforcer executes the following quality enforcement scripts in order:

1. **Static Code Analysis** - Verifies code structure and identifies issues
2. **File Cleanup** - Manages file locations and removes orphaned files
3. **Essential Files Update** - Ensures required files exist and are up-to-date
4. **Code Formatting and Linting** - Enforces code style and quality standards
5. **Dependency Audit** - Checks dependencies for issues and updates

The enforcer runs these scripts in an iterative cycle, continuing until no further changes are detected or until the maximum number of iterations is reached. This ensures that all quality standards are fully enforced, as changes made by one script may require additional changes by another script.

## Features

- **Iterative Execution** - Continues until no further changes are needed
- **Comprehensive Reporting** - Generates a detailed final report
- **Knowledge Graph Integration** - Updates the knowledge graph with the final state
- **Error Handling** - Gracefully handles errors and provides detailed logging
- **Dry Run Mode** - Allows previewing changes without actually making them
- **Configurable Iterations** - Allows setting a maximum number of iterations

## Usage

### Basic Usage

```bash
python enforce_quality_standards.py
```

This will run the quality standards enforcer with default settings, using the current directory as the project directory.

### Advanced Usage

```bash
python enforce_quality_standards.py --project-dir /path/to/project --max-iterations 5 --verbose
```

### Command-Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--project-dir` | Path to the project directory | `.` (current directory) |
| `--max-iterations` | Maximum number of iterations to perform | `10` |
| `--output` | Path to the output report file | `data/reports/quality-standards-report.json` |
| `--verbose` | Enable verbose logging | `False` |
| `--dry-run` | Run in dry-run mode (don't actually modify files) | `False` |
| `--skip-kg-update` | Skip updating the knowledge graph | `False` |

## Output

The Quality Standards Enforcer generates a comprehensive report in JSON format, which includes:

- **Summary** - Overall statistics about the enforcement process
- **Iterations** - Detailed information about each iteration
- **Final State** - The final state of the project after enforcement

Example report structure:

```json
{
  "project_dir": "/path/to/project",
  "timestamp": "2025-04-08T07:30:00.000000",
  "summary": {
    "total_iterations": 3,
    "total_changes": 42,
    "scripts_executed": 15,
    "scripts_succeeded": 15,
    "scripts_failed": 0,
    "total_execution_time": 120.5
  },
  "iterations": [
    {
      "iteration": 1,
      "timestamp": "2025-04-08T07:25:00.000000",
      "scripts": [
        {
          "name": "code_structure",
          "success": true,
          "changes_made": true,
          "result": { ... }
        },
        ...
      ],
      "changes_made": true,
      "execution_time": 45.2
    },
    ...
  ],
  "final_state": {
    "code_quality": { ... },
    "file_structure": { ... },
    "essential_files": { ... },
    "dependencies": { ... }
  }
}
```

## Integration with Knowledge Graph

After completing the quality enforcement process, the enforcer updates the knowledge graph with the final state. This ensures that the knowledge graph remains the single source of truth for the project's quality status.

To update the knowledge graph manually, you can run:

```bash
python core/kg/scripts/record_quality_standards_enforcer.py
```

## Troubleshooting

### Common Issues

1. **Script Not Found**
   - Ensure that all required quality enforcement scripts are present in the expected locations
   - Check the script paths in the `QualityStandardsEnforcer` class

2. **Permission Denied**
   - Ensure that you have the necessary permissions to execute the scripts
   - Make sure the scripts are executable (`chmod +x script.sh`)

3. **Maximum Iterations Reached**
   - If the enforcer reaches the maximum number of iterations without converging, it may indicate a cycle in the quality enforcement process
   - Check the logs to identify which scripts are making changes in each iteration

### Logs

The enforcer logs detailed information about its execution to:

- Console (if `--verbose` is specified)
- `data/logs/enforce_quality_standards.log`

## Best Practices

1. **Run Regularly**
   - Schedule the enforcer to run regularly (e.g., daily or weekly) to maintain high quality standards

2. **Review Reports**
   - Regularly review the generated reports to identify recurring issues

3. **Update Scripts**
   - Keep the individual quality enforcement scripts up-to-date with the latest best practices

4. **Customize for Project Needs**
   - Adjust the enforcer's configuration to match the specific needs of your project

## Related Documentation

- [Code Quality Enforcement](./quality-enforcement.md)
- [File Cleanup Guide](../file-cleanup-guide.md)
- [Knowledge Graph Integration](./knowledge-graph-integration.md)