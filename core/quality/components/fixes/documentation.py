"""
Documentation Fixes

This module provides auto-fix capabilities for documentation issues, including:
- Docstring generation and formatting
- README file creation and updates
- Documentation coverage improvements
- Comment formatting and standardization

These fixes can be applied automatically or interactively.
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

from core.quality.components.base import QualityCheckResult, QualityCheckSeverity


class DocumentationFixes:
    """Provides auto-fix capabilities for documentation issues."""

    @staticmethod
    def generate_function_docstring(file_path: str, line_number: int) -> Tuple[bool, str]:
        """
        Generate a docstring for a function.

        Args:
            file_path: Path to the Python file.
            line_number: Line number where the function is defined.

        Returns:
            Tuple of (success, error_message)
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse the Python file
            tree = ast.parse(content)

            # Find the function at the specified line
            function_node = None
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if node.lineno == line_number:
                        function_node = node
                        break

            if not function_node:
                return False, f"No function found at line {line_number}"

            # Generate docstring based on function signature
            docstring = DocumentationFixes._generate_docstring_from_node(function_node)

            # Insert the docstring into the file
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Find the line after the function definition
            insert_line = function_node.lineno
            for i in range(function_node.lineno, len(lines)):
                if ":" in lines[i]:
                    insert_line = i + 1
                    break

            # Insert the docstring
            indent = DocumentationFixes._get_indent(lines[insert_line - 1])
            docstring_lines = [f"{indent}\"\"\"" + docstring.split("\n")[0] + "\n"]
            for line in docstring.split("\n")[1:-1]:
                docstring_lines.append(f"{indent}{line}\n")
            docstring_lines.append(f"{indent}\"\"\"\n")

            lines = lines[:insert_line] + docstring_lines + lines[insert_line:]

            # Write the updated content back to the file
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)

            return True, ""
        except Exception as e:
            return False, str(e)

    @staticmethod
    def _generate_docstring_from_node(node: Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef]) -> str:
        """
        Generate a docstring from an AST node.

        Args:
            node: AST node for a function or class.

        Returns:
            Generated docstring.
        """
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Function docstring
            docstring = f"{node.name} function.\n\n"

            # Add Args section if there are arguments
            if node.args.args:
                docstring += "Args:\n"
                for arg in node.args.args:
                    if arg.arg != "self" and arg.arg != "cls":
                        docstring += f"    {arg.arg}: Description of {arg.arg}.\n"

            # Add Returns section
            docstring += "\nReturns:\n    Description of return value.\n"

            return docstring
        elif isinstance(node, ast.ClassDef):
            # Class docstring
            docstring = f"{node.name} class.\n\n"
            docstring += "Description of the class functionality.\n"
            return docstring
        else:
            return "Description.\n"

    @staticmethod
    def _get_indent(line: str) -> str:
        """
        Get the indentation of a line.

        Args:
            line: The line to analyze.

        Returns:
            The indentation string.
        """
        match = re.match(r"^(\s*)", line)
        if match:
            return match.group(1)
        return ""

    @staticmethod
    def fix_missing_module_docstring(file_path: str) -> Tuple[bool, str]:
        """
        Fix a missing module docstring.

        Args:
            file_path: Path to the Python file.

        Returns:
            Tuple of (success, error_message)
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check if the file already has a module docstring
            tree = ast.parse(content)
            if ast.get_docstring(tree):
                return False, "Module already has a docstring"

            # Generate a module docstring
            module_name = os.path.basename(file_path).replace(".py", "")
            docstring = f'"""\n{module_name.replace("_", " ").title()} Module\n\nDescription of the module functionality.\n"""\n\n'

            # Add the docstring to the beginning of the file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(docstring + content)

            return True, ""
        except Exception as e:
            return False, str(e)

    @staticmethod
    def create_readme_template(directory_path: str) -> Tuple[bool, str]:
        """
        Create a README.md template in the specified directory.

        Args:
            directory_path: Path to the directory.

        Returns:
            Tuple of (success, error_message)
        """
        try:
            readme_path = os.path.join(directory_path, "README.md")
            if os.path.exists(readme_path):
                return False, "README.md already exists"

            # Generate a README template
            dir_name = os.path.basename(os.path.abspath(directory_path))
            readme_content = f"""# {dir_name.replace("_", " ").title()}

## Overview

Brief description of the {dir_name} component.

## Features

- Feature 1
- Feature 2
- Feature 3

## Usage

```python
# Example usage code
```

## Structure

- `file1.py`: Description of file1
- `file2.py`: Description of file2

## Dependencies

- Dependency 1
- Dependency 2

## Testing

How to run tests for this component.
"""

            # Write the README file
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(readme_content)

            return True, ""
        except Exception as e:
            return False, str(e)

    @staticmethod
    def apply_fixes(results: List[QualityCheckResult]) -> Tuple[List[QualityCheckResult], List[QualityCheckResult]]:
        """
        Apply fixes to documentation issues.

        Args:
            results: List of QualityCheckResult objects to fix.

        Returns:
            Tuple of (fixed_results, unfixed_results)
        """
        # Group results by check_id
        results_by_check: Dict[str, List[QualityCheckResult]] = {}
        for result in results:
            if result.check_id not in results_by_check:
                results_by_check[result.check_id] = []
            results_by_check[result.check_id].append(result)

        fixed_results = []
        unfixed_results = []

        # Fix missing docstrings
        if "docstrings" in results_by_check:
            docstring_results = results_by_check["docstrings"]
            for result in docstring_results:
                if result.file_path and result.line_number:
                    # Check if it's a missing function docstring
                    if "function" in result.message.lower() or "method" in result.message.lower():
                        success, _ = DocumentationFixes.generate_function_docstring(
                            result.file_path, result.line_number
                        )
                        if success:
                            fixed_results.append(result)
                        else:
                            unfixed_results.append(result)
                    # Check if it's a missing module docstring
                    elif "module" in result.message.lower():
                        success, _ = DocumentationFixes.fix_missing_module_docstring(result.file_path)
                        if success:
                            fixed_results.append(result)
                        else:
                            unfixed_results.append(result)
                    else:
                        unfixed_results.append(result)
                else:
                    unfixed_results.append(result)

        # Fix missing README files
        if "readme" in results_by_check:
            readme_results = results_by_check["readme"]
            for result in readme_results:
                if result.file_path:
                    directory = os.path.dirname(result.file_path)
                    success, _ = DocumentationFixes.create_readme_template(directory)
                    if success:
                        fixed_results.append(result)
                    else:
                        unfixed_results.append(result)
                else:
                    unfixed_results.append(result)

        # Handle other documentation issues
        for check_id, check_results in results_by_check.items():
            if check_id not in ["docstrings", "readme"]:
                unfixed_results.extend(check_results)

        return fixed_results, unfixed_results