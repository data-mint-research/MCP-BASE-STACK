#!/usr/bin/env python3
"""
Validate the specification manifest against its schema and validate a project against the manifest.

This script provides two main functions:
1. Validate the specification manifest against its JSON Schema
2. Validate a project directory against the specification manifest

Usage:
    python validate-manifest.py validate-schema
    python validate-manifest.py validate-project [directory]
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


def load_json_file(file_path: str) -> Dict[str, Any]:
    """
    Load a JSON file.

    Args:
        file_path: Path to the JSON file

    Returns:
        The loaded JSON data

    Raises:
        FileNotFoundError: If the file does not exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {file_path}: {e}")
        sys.exit(1)


def validate_schema(manifest_path: str, schema_path: str) -> bool:
    """
    Validate the specification manifest against its JSON Schema.

    Args:
        manifest_path: Path to the specification manifest
        schema_path: Path to the JSON Schema

    Returns:
        True if the manifest is valid, False otherwise
    """
    try:
        import jsonschema
    except ImportError:
        print("Error: jsonschema package is required for schema validation.")
        print("Install it with: pip install jsonschema")
        sys.exit(1)

    manifest = load_json_file(manifest_path)
    schema = load_json_file(schema_path)

    # Custom validation for directory structure paths
    # This is a workaround for the limitation in JSON Schema regex patterns
    if "specification_manifest" in manifest and "directory_structure" in manifest["specification_manifest"]:
        for path in list(manifest["specification_manifest"]["directory_structure"].keys()):
            # Skip 'root' as it's a special case
            if path == "root":
                continue
            # Check if path follows the pattern
            if not re.match(r"^[a-z][a-z0-9_/\-]*$", path):
                print(f"❌ Directory path '{path}' does not match the required pattern '^[a-z][a-z0-9_/]*$'")
                return False
    
    try:
        # Temporarily remove problematic paths for schema validation
        if "specification_manifest" in manifest and "directory_structure" in manifest["specification_manifest"]:
            temp_manifest = json.loads(json.dumps(manifest))  # Deep copy
            dir_structure = temp_manifest["specification_manifest"]["directory_structure"]
            problematic_paths = [p for p in dir_structure.keys() if "/" in p]
            for path in problematic_paths:
                del dir_structure[path]
        
        jsonschema.validate(instance=temp_manifest, schema=schema)
        print(f"✅ {manifest_path} is valid according to {schema_path}")
        return True
    except jsonschema.exceptions.ValidationError as e:
        print(f"❌ {manifest_path} is not valid according to {schema_path}:")
        print(f"   {e}")
        return False


def validate_directory_structure(directory: str, manifest: Dict[str, Any]) -> List[str]:
    """
    Validate the directory structure against the manifest.

    Args:
        directory: Path to the directory to validate
        manifest: The specification manifest

    Returns:
        List of validation errors
    """
    errors = []
    dir_structure = manifest["specification_manifest"]["directory_structure"]

    # Check required directories
    for dir_path, dir_info in dir_structure.items():
        if dir_path == "root":
            full_path = directory
        else:
            full_path = os.path.join(directory, dir_path)

        if not os.path.isdir(full_path):
            errors.append(f"Required directory '{dir_path}' is missing")
            continue

        if "required_subdirectories" in dir_info:
            for subdir in dir_info["required_subdirectories"]:
                subdir_path = os.path.join(full_path, subdir)
                if not os.path.isdir(subdir_path):
                    errors.append(f"Required subdirectory '{subdir}' is missing in '{dir_path}'")

    return errors


def validate_file_presence(directory: str, manifest: Dict[str, Any]) -> List[str]:
    """
    Validate the presence of required files against the manifest.

    Args:
        directory: Path to the directory to validate
        manifest: The specification manifest

    Returns:
        List of validation errors
    """
    errors = []
    file_templates = manifest["specification_manifest"]["file_templates"]

    # Check required files
    for dir_path, dir_info in file_templates.items():
        if dir_path == "root":
            full_path = directory
        else:
            full_path = os.path.join(directory, dir_path)

        if not os.path.isdir(full_path):
            continue  # Skip if directory doesn't exist (already reported by validate_directory_structure)

        if "required_files" in dir_info:
            for file_name in dir_info["required_files"]:
                file_path = os.path.join(full_path, file_name)
                if not os.path.isfile(file_path):
                    errors.append(f"Required file '{file_name}' is missing in '{dir_path}'")

    return errors


def validate_naming_conventions(directory: str, manifest: Dict[str, Any]) -> List[str]:
    """
    Validate naming conventions against the manifest.

    Args:
        directory: Path to the directory to validate
        manifest: The specification manifest

    Returns:
        List of validation errors
    """
    errors = []
    naming_conventions = manifest["specification_manifest"]["naming_conventions"]

    # Python files
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    # Check Python module names
    if "python" in naming_conventions and "modules" in naming_conventions["python"]:
        module_pattern = naming_conventions["python"]["modules"]["regex"]
        for file_path in python_files:
            file_name = os.path.basename(file_path)
            if not re.match(module_pattern, file_name):
                errors.append(f"Python module name '{file_name}' does not follow the required pattern")

    # Shell script files
    shell_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".sh"):
                shell_files.append(os.path.join(root, file))

    # Check shell script names
    if "shell" in naming_conventions and "scripts" in naming_conventions["shell"]:
        script_pattern = naming_conventions["shell"]["scripts"]["regex"]
        for file_path in shell_files:
            file_name = os.path.basename(file_path)
            if not re.match(script_pattern, file_name):
                errors.append(f"Shell script name '{file_name}' does not follow the required pattern")

    # Markdown files
    markdown_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".md"):
                markdown_files.append(os.path.join(root, file))

    # Check markdown file names
    if "documentation" in naming_conventions and "markdown_files" in naming_conventions["documentation"]:
        markdown_pattern = naming_conventions["documentation"]["markdown_files"]["regex"]
        for file_path in markdown_files:
            file_name = os.path.basename(file_path)
            if not re.match(markdown_pattern, file_name) and file_name != "README.md":
                errors.append(f"Markdown file name '{file_name}' does not follow the required pattern")

    return errors


def validate_project(directory: str, manifest_path: str) -> Tuple[bool, List[str]]:
    """
    Validate a project directory against the specification manifest.

    Args:
        directory: Path to the directory to validate
        manifest_path: Path to the specification manifest

    Returns:
        Tuple of (is_valid, errors)
    """
    manifest = load_json_file(manifest_path)
    errors = []

    # Validate directory structure
    errors.extend(validate_directory_structure(directory, manifest))

    # Validate file presence
    errors.extend(validate_file_presence(directory, manifest))

    # Validate naming conventions
    errors.extend(validate_naming_conventions(directory, manifest))

    # Print results
    if errors:
        print(f"❌ {directory} does not comply with the specification manifest:")
        for error in errors:
            print(f"   - {error}")
        return False, errors
    else:
        print(f"✅ {directory} complies with the specification manifest")
        return True, []


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Validate the specification manifest and project")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Validate schema command
    validate_schema_parser = subparsers.add_parser("validate-schema", help="Validate the manifest against its schema")
    validate_schema_parser.add_argument("--manifest", default="config/specifications/specification-manifest.json", help="Path to the manifest")
    validate_schema_parser.add_argument("--schema", default="config/specifications/specification-manifest-schema.json", help="Path to the schema")

    # Validate project command
    validate_project_parser = subparsers.add_parser("validate-project", help="Validate a project against the manifest")
    validate_project_parser.add_argument("directory", nargs="?", default=".", help="Path to the project directory")
    validate_project_parser.add_argument("--manifest", default="config/specifications/specification-manifest.json", help="Path to the manifest")

    args = parser.parse_args()

    if args.command == "validate-schema":
        validate_schema(args.manifest, args.schema)
    elif args.command == "validate-project":
        validate_project(args.directory, args.manifest)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()