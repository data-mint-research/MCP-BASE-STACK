# Documentation Standards

## Overview

This document outlines the documentation standards for the MCP-BASE-STACK project. Consistent documentation is essential for maintainability, knowledge transfer, and efficient collaboration. These standards apply to all code files, scripts, and documentation within the project.

## General Principles

1. **Completeness**: All code components must be documented, including modules, classes, functions, and scripts.
2. **Clarity**: Documentation should be clear, concise, and unambiguous.
3. **Consistency**: Documentation should follow a consistent format and style throughout the project.
4. **Maintenance**: Documentation must be kept up-to-date with code changes.
5. **Knowledge Graph Integration**: All significant documentation changes must be reflected in the knowledge graph.

## File Documentation

### Python Files

1. **Module Docstrings**:
   - Every Python file must begin with a module-level docstring.
   - The docstring should start with a one-line summary of the module's purpose.
   - Following the summary should be a more detailed description, including:
     - The module's functionality
     - Key components or classes
     - Usage examples (if applicable)
     - Dependencies or requirements

   ```python
   """
   Module Name

   This module provides functionality for X, including:
   - Feature A
   - Feature B
   - Feature C

   Usage:
       import module_name
       result = module_name.function()
   """
   ```

2. **Class Docstrings**:
   - Every class must have a docstring explaining its purpose and behavior.
   - Include information about inheritance if relevant.
   - Document class attributes.

   ```python
   class ClassName:
       """
       Class description.

       This class provides functionality for X.

       Attributes:
           attr1: Description of attribute 1
           attr2: Description of attribute 2
       """
   ```

3. **Function/Method Docstrings**:
   - Every function and method must have a docstring.
   - Document parameters, return values, and exceptions.
   - Use the following format:

   ```python
   def function_name(param1, param2):
       """
       Function description.

       Args:
           param1: Description of parameter 1
           param2: Description of parameter 2

       Returns:
           Description of return value

       Raises:
           ExceptionType: Description of when this exception is raised
       """
   ```

4. **Type Hints**:
   - Use type hints for function parameters and return values.
   - Type hints should be consistent with the docstring.

   ```python
   def function_name(param1: str, param2: int) -> bool:
       """
       Function description.

       Args:
           param1: Description of parameter 1
           param2: Description of parameter 2

       Returns:
           True if successful, False otherwise
       """
   ```

### Shell Scripts

1. **Header Comments**:
   - Every shell script must begin with a header comment block.
   - The header should include:
     - Script name/title
     - Description of the script's purpose
     - Usage instructions
     - Required environment or dependencies
     - Author information (if applicable)

   ```bash
   #!/bin/bash
   # ============================================================================
   # Script Name
   # ============================================================================
   # Description:
   #   This script performs X functionality by doing Y and Z.
   #
   # Usage:
   #   ./script_name.sh [options]
   #
   # Options:
   #   -h, --help     Display this help message
   #   -v, --verbose  Enable verbose output
   # ============================================================================
   ```

2. **Function Comments**:
   - Document each function with a comment block.
   - Include description, parameters, and return values.

   ```bash
   # ----------------------------------------------------------------------------
   # Function: function_name
   # Description: What the function does
   # Arguments:
   #   $1 - Description of first argument
   #   $2 - Description of second argument
   # Returns:
   #   Description of what the function returns or outputs
   # ----------------------------------------------------------------------------
   function_name() {
       # Function implementation
   }
   ```

3. **Section Comments**:
   - Use section comments to divide the script into logical sections.

   ```bash
   # ============================================================================
   # Section Name
   # ============================================================================
   ```

4. **Inline Comments**:
   - Use inline comments for complex or non-obvious code.

### Markdown Documentation

1. **Structure**:
   - Use a consistent heading hierarchy (# for title, ## for sections, etc.).
   - Include a table of contents for longer documents.
   - Start with an overview or introduction.

2. **Content**:
   - Be concise and focused.
   - Use code blocks with language specification for code examples.
   - Use lists and tables to organize information.

3. **File Naming**:
   - Use kebab-case for markdown file names (e.g., `file-name.md`).
   - Names should be descriptive and reflect the content.

## Directory Documentation

Each directory should include a README.md file that:

1. Explains the purpose of the directory
2. Lists key files and their functions
3. Provides usage examples if applicable
4. Includes any special instructions or dependencies

## Knowledge Graph Integration

Documentation changes must be reflected in the knowledge graph:

1. New components must be added to the knowledge graph with appropriate documentation attributes.
2. Updated components must have their documentation attributes updated.
3. Use the `update_knowledge_graph.py` script to ensure changes are properly recorded.

## Validation

Documentation coverage and quality will be validated through:

1. Automated checks using the quality enforcement system
2. Code reviews
3. Regular documentation audits

## Examples

See the following files for examples of well-documented code:

- `core/quality/enforcer.py` - Example of well-documented Python module
- `scripts/utils/cleanup/cleanup_files.py` - Example of comprehensive function documentation
- `docs/knowledge-graph/quality-metrics-schema.md` - Example of well-structured markdown documentation