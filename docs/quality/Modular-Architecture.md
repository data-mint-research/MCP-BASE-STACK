# Quality Modules Modular Architecture

## Overview

The Quality Modules architecture provides a flexible, extensible framework for enforcing code quality standards across the project. It replaces the monolithic QualityEnforcer with a component-based system that improves maintainability, testability, and extensibility.

## Architecture Components

### Core Components

The architecture consists of the following core components:

1. **QualityEnforcer**: A facade that provides a unified interface to the quality enforcement system while maintaining backward compatibility with existing hooks.

2. **QualityComponent**: Base class for quality components, which group related quality checks.

3. **QualityCheck**: Interface for individual quality checks, which perform specific validations.

4. **QualityCheckResult**: Class representing the result of a quality check, including severity, message, and location.

5. **QualityCheckRegistry**: Registry for quality check plugins, enabling dynamic loading of custom checks.

### Component Types

The system includes the following specialized components:

1. **Code Style Component**: Checks for code style and formatting consistency.
   - Black (Python formatter)
   - isort (Python import sorter)
   - Line ending consistency

2. **Static Analysis Component**: Performs static code analysis to identify potential issues.
   - mypy (Python type checker)
   - pylint (Python linter)
   - flake8 (Python linter)
   - shellcheck (Shell script linter)

3. **Documentation Component**: Checks for documentation quality and coverage.
   - Docstring presence and completeness
   - README presence and completeness
   - Documentation coverage

4. **Structure Component**: Validates project structure and organization.
   - Directory structure
   - File naming conventions
   - Import organization
   - Circular dependency detection

## Plugin System

The architecture includes a plugin system that allows for dynamic loading of custom quality checks and components. Plugins can be registered with the QualityCheckRegistry and will be automatically discovered and loaded by the QualityEnforcer.

### Creating a Custom Plugin

To create a custom quality check plugin:

1. Create a new Python module in a plugin directory.
2. Define a class that inherits from QualityCheck.
3. Implement the required methods: id, name, description, and run.
4. Optionally implement can_fix and fix methods for automatic issue fixing.

Example:

```python
from core.quality.components.base import QualityCheck, QualityCheckResult, QualityCheckSeverity

class CustomCheck(QualityCheck):
    @property
    def id(self) -> str:
        return "custom_check"
    
    @property
    def name(self) -> str:
        return "Custom Check"
    
    @property
    def description(self) -> str:
        return "A custom quality check."
    
    def run(self, file_paths=None, **kwargs):
        # Implement check logic
        results = []
        # ...
        return results
```

## Backward Compatibility

The new architecture maintains backward compatibility with the existing hooks system through the QualityEnforcer facade. The following hooks are supported:

- check_code_quality
- check_documentation_quality
- validate_file_structure
- suggest_improvements
- update_knowledge_graph

These hooks are re-exported from the core.quality.hooks module and delegate to the corresponding methods in the QualityEnforcer.

## Configuration

Quality checks can be configured through the configuration system. Each check can have the following settings:

- enabled: Whether the check is enabled (default: true)
- severity: The default severity for issues found by the check (default: warning)

Example configuration:

```yaml
quality:
  checks:
    black:
      enabled: true
      severity: warning
    mypy:
      enabled: true
      severity: error
  plugin_dirs:
    - plugins/quality
```

## Knowledge Graph Integration

The quality modules are integrated with the knowledge graph to track quality metrics and relationships. The following nodes and relationships are maintained:

- quality_modules: The root node for the quality modules system
- Component nodes: Nodes for each component type (base, code_style, static_analysis, documentation, structure)
- Plugin system node: Node for the plugin system
- Enforcer node: Node for the QualityEnforcer facade
- Hooks compatibility node: Node for backward compatibility with existing hooks
- File nodes: Nodes for each file in the quality modules system
- Relationships: Edges between nodes representing their relationships (contains, implements, uses, etc.)

The knowledge graph is updated by the record_quality_modules.py script.

## Usage Examples

### Running All Quality Checks

```python
from core.quality import enforcer

# Run all quality checks
results = enforcer.run_all_checks()

# Print results
for result in results:
    print(f"{result.severity.value}: {result.message} in {result.file_path}")
```

### Running Specific Component Checks

```python
from core.quality import enforcer

# Run only code style checks
results = enforcer.run_component_checks("code_style")

# Print results
for result in results:
    print(f"{result.severity.value}: {result.message} in {result.file_path}")
```

### Fixing Issues

```python
from core.quality import enforcer

# Run checks
results = enforcer.run_all_checks()

# Fix issues
unfixed = enforcer.fix_issues(results)

# Print unfixed issues
for result in unfixed:
    print(f"Could not fix: {result.message} in {result.file_path}")
```

### Using the Hooks API

```python
from core.quality.hooks import check_code_quality

# Check code quality using the hooks API
issues = check_code_quality(["file.py"])

# Print issues
for issue_type, issue_list in issues.items():
    for issue in issue_list:
        print(f"{issue_type}: {issue['message']} in {issue['file']}")
```

## Future Enhancements

Potential future enhancements to the quality modules architecture include:

1. **Quality Metrics Dashboard**: A web-based dashboard for visualizing quality metrics over time.
2. **CI/CD Integration**: Deeper integration with CI/CD pipelines for automated quality enforcement.
3. **Language-Specific Plugins**: Additional plugins for other programming languages (JavaScript, TypeScript, etc.).
4. **Custom Rule Definition**: A DSL for defining custom quality rules without writing Python code.
5. **Performance Optimization**: Caching and incremental checking for faster quality validation.