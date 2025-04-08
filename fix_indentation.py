#!/usr/bin/env python3
"""
Script to fix indentation issues in standardize_file_structure.py
"""

import re

def main():
    """Main function to fix indentation issues."""
    # Read the original file
    with open('standardize_file_structure.py', 'r') as f:
        content = f.read()
    
    # Fix indentation issues
    fixed_content = fix_indentation(content)
    
    # Write the fixed content to a new file
    with open('standardize_file_structure_fixed.py', 'w') as f:
        f.write(fixed_content)
    
    print("Fixed file written to standardize_file_structure_fixed.py")
    return 0

def fix_indentation(content):
    """Fix indentation issues in the content."""
    lines = content.split('\n')
    fixed_lines = []
    
    # Track indentation level
    in_function = False
    function_indent = 0
    
    for line in lines:
        # Check if line starts a function definition
        if re.match(r'^\s*def\s+\w+\s*\(', line):
            in_function = True
            function_indent = len(line) - len(line.lstrip())
            fixed_lines.append(line)
        # Check if line is inside a function
        elif in_function:
            # Check if line is empty or has only whitespace
            if not line.strip():
                fixed_lines.append(line)
            # Check if line has less indentation than the function definition
            elif len(line) - len(line.lstrip()) <= function_indent:
                in_function = False
                fixed_lines.append(line)
            # Line is inside the function
            else:
                fixed_lines.append(line)
        # Line is outside any function
        else:
            fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

if __name__ == "__main__":
    exit(main())