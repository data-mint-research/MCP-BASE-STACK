# MCP-BASE-STACK Specification Manifest

## Overview

The MCP-BASE-STACK Specification Manifest serves as the single source of truth for the Autonomous AI Coding Agent. It codifies standards for directory structure, file organization, naming conventions, and required code patterns to ensure consistency and adherence to best practices across the project.

## Purpose

This manifest provides:

1. **Standardization**: Ensures consistent coding style, naming conventions, and project structure
2. **Validation**: Enables automated validation of code against project standards
3. **Guidance**: Provides clear guidelines for developers and AI agents
4. **Documentation**: Serves as a comprehensive reference for project standards

## Structure

The specification manifest is organized into the following main sections:

### 1. Metadata

Basic information about the manifest itself, including version, creation date, and purpose.

```json
"metadata": {
  "version": "1.0.0",
  "created_at": "2025-04-07",
  "description": "Specification manifest for MCP-BASE-STACK",
  "purpose": "Single source of truth for the Autonomous AI Coding Agent"
}
```

### 2. Directory Structure

Defines the required and optional directory structure for the project.

```json
"directory_structure": {
  "root": {
    "description": "Project root directory",
    "required_subdirectories": [
      "docs",
      "config",
      "core",
      "services",
      "scripts",
      "tests"
    ],
    "optional_subdirectories": [
      "data",
      "deploy",
      "LibreChat"
    ]
  }
}
```

### 3. File Templates

Provides templates for common files in the project.

```json
"file_templates": {
  "root": {
    "required_files": {
      "README.md": {
        "description": "Project overview",
        "template": "# MCP-BASE-STACK\n\n## Overview\n\n..."
      }
    }
  }
}
```

### 4. Naming Conventions

Defines naming conventions for different types of code elements.

```json
"naming_conventions": {
  "python": {
    "classes": {
      "pattern": "CamelCase",
      "regex": "^[A-Z][a-zA-Z0-9]*$",
      "examples": [
        "ConfigManager",
        "KnowledgeGraph"
      ]
    }
  }
}
```

### 5. Code Patterns

Defines standard code patterns for different languages and contexts.

```json
"code_patterns": {
  "python": {
    "module_header": {
      "description": "Standard module header with docstring",
      "required": true,
      "template": "\"\"\"Module description.\n\n...\"\"\"\n\n# Standard library imports\n\n...",
      "validation_regex": "^\\s*\"\"\"[\\s\\S]*?\"\"\"\\s*$"
    }
  }
}
```

### 6. Validation Rules

Defines rules for validating code against the manifest.

```json
"validation_rules": {
  "directory_structure": [
    {
      "rule": "All required directories must exist",
      "severity": "error",
      "validation_function": "validateRequiredDirectories",
      "error_message": "Required directory '{directory}' is missing"
    }
  ]
}
```

### 7. Agent Integration

Defines how the Autonomous AI Coding Agent should use the manifest.

```json
"agent_integration": {
  "code_generation": {
    "directory_creation": {
      "description": "Generate directory structures that comply with project standards",
      "process": [
        "Agent consults manifest's directory_structure section",
        "Creates required directories in the correct hierarchy",
        "Ensures directory names follow naming conventions"
      ],
      "example": "When creating a new feature, agent automatically creates all required subdirectories"
    }
  }
}
```

## Usage

### Validation

To validate your project against the specification manifest, use the JSON Schema:

```bash
# Install ajv (JSON Schema validator)
npm install -g ajv-cli

# Validate the manifest itself
ajv validate -s config/specifications/specification-manifest-schema.json -d config/specifications/specification-manifest.json

# Validate your project against the manifest
# (requires a custom validator that uses the manifest)
./validate-project.sh
```

### Integration with CI/CD

Add validation to your CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
validate:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v2
    - name: Validate against specification manifest
      run: |
        npm install -g ajv-cli
        ./validate-project.sh
```

### For Developers

1. **Reference**: Use the manifest as a reference when writing code
2. **Templates**: Use the file templates when creating new files
3. **Validation**: Run validation locally before committing changes

### For the Autonomous AI Coding Agent

The Autonomous AI Coding Agent uses the manifest to:

1. **Generate Code**: Create code that follows project standards
2. **Analyze Code**: Validate existing code against standards
3. **Refactor Code**: Improve code to meet standards
4. **Make Decisions**: Decide where to place files, how to name elements, etc.
5. **Understand Context**: Build a mental model of the project structure
6. **Provide Guidance**: Explain standards to developers
7. **Improve Standards**: Suggest improvements to the manifest

## Maintenance

The specification manifest should be updated when:

1. New coding standards are adopted
2. Project structure changes
3. New file types or patterns are introduced
4. Validation rules need to be refined

When updating the manifest, ensure:

1. The manifest validates against its schema
2. Changes are backward compatible when possible
3. Changes are documented in the commit message
4. The knowledge graph is updated to reflect the changes

## Schema

The manifest is validated against a JSON Schema defined in `specification-manifest-schema.json`. This schema ensures that the manifest itself follows the correct structure and contains all required fields.