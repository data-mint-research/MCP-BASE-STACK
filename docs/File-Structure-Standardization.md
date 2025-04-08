# File Structure Standardization

This document outlines the file structure standardization improvements implemented in the MCP-BASE-STACK project.

## Overview

The file structure standardization system ensures that all files in the project follow consistent naming conventions and are located in their ideal directories. This improves code organization, makes the codebase more maintainable, and enhances developer productivity.

## Current Status

As of the latest validation (April 8, 2025):
- Total files in the project: 249
- Naming convention compliance: 100%
- Directory structure compliance: 100%
- Overall compliance: 100%

The project has achieved full compliance with file structure standards after fixing 34 files with naming convention issues (primarily markdown files) and relocating 5 files to their ideal directories.

## Key Features

1. **Naming Convention Enforcement**: Ensures all files follow language-specific naming conventions:
   - Python files: `snake_case.py`
   - JavaScript files: `camelCase.js`
   - TypeScript files: `camelCase.ts`
   - React JSX files: `PascalCase.jsx`
   - React TSX files: `PascalCase.tsx`
   - Markdown files: `PascalCase-or-hyphenated.md`
   - Shell scripts: `lowercase-with-hyphens.sh`

2. **Directory Structure Organization**: Ensures files are located in their ideal directories based on their purpose:
   - Core application code in `core/` directory
   - Documentation in `docs/` directory
   - Tests in `tests/` directory
   - Scripts in `scripts/` directory
   - Configuration in `config/` directory

3. **Automated Validation**: Provides automated validation of file structure through:
   - Pre-commit hooks that prevent commits with file structure issues
   - Integration with the quality enforcement system
   - Detailed reports on file structure compliance

4. **Special File Handling**: Implements special handling for certain file types:
   - `__init__.py` files are preserved with their exact naming (not subject to renaming)
   - `README.md` files are kept in their original directories (not subject to relocation)

## Usage

### Manual Standardization

You can manually standardize the file structure using the `standardize_file_structure.py` script:

```bash
# Fix naming convention issues
python standardize_file_structure.py --fix-naming

# Relocate files to ideal directories
python standardize_file_structure.py --relocate

# Validate file structure without making changes
python standardize_file_structure.py --validate

# Show what would be done without making changes
python standardize_file_structure.py --dry-run

# Do all of the above
python standardize_file_structure.py
```

### Automated Validation

File structure validation is automatically performed as part of the quality checks:

```bash
# Run all quality checks including file structure validation
python -c 'from core.quality.enforcer import enforcer; enforcer.run_all_checks()'

# Run only structure checks
python -c 'from core.quality.enforcer import enforcer; enforcer.run_component_checks("structure")'
```

## Compliance Metrics

The file structure standardization system tracks the following compliance metrics:

1. **Naming Convention Compliance**: Percentage of files that follow the naming conventions
2. **Directory Structure Compliance**: Percentage of files that are in their ideal directories
3. **Overall Compliance**: Combined metric of naming and directory compliance

These metrics are automatically updated in the knowledge graph after each validation.

## Integration with Knowledge Graph

The file structure standardization system is integrated with the knowledge graph, which serves as the single source of truth for the project. After each validation, the knowledge graph is updated with the latest compliance metrics.

## Implementation Details

The file structure standardization system consists of the following components:

1. **standardize_file_structure.py**: Main script for standardizing file structure
2. **core/quality/components/fixes/file_structure_validator.py**: Integration with the quality enforcement system
3. **core/quality/components/structure.py**: File structure quality checks
4. **core/quality/components/fixes/structure.py**: Auto-fix capabilities for structure issues

## Best Practices

1. **Run validation regularly**: Regularly run the validation to ensure file structure compliance
2. **Fix issues early**: Address file structure issues as soon as they are detected
3. **Use pre-commit hooks**: Enable pre-commit hooks to prevent file structure issues from being committed
4. **Update knowledge graph**: Ensure the knowledge graph is updated after making changes to the file structure

## Troubleshooting

If you encounter issues with the file structure standardization system:

1. **Check logs**: Review the logs in `data/logs/` for error messages
2. **Validate manually**: Run the validation script manually to identify issues
3. **Use dry run**: Use the `--dry-run` option to see what changes would be made without actually making them
4. **Check reports**: Review the reports in `data/reports/` for detailed information on file structure issues