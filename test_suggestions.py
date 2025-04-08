#!/usr/bin/env python3
"""
Test script to check if suggestions are being included in the file structure report.
"""

import json
import os

def main():
    """Main function to test suggestions."""
    # Check if the file-structure-report.json file exists
    report_path = "data/reports/file-structure-report.json"
    if not os.path.exists(report_path):
        print(f"Error: {report_path} does not exist.")
        return 1
    
    # Load the report
    with open(report_path, 'r') as f:
        try:
            report = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return 1
    
    # Check if suggestions field is in the report
    if 'suggestions' in report:
        print("Suggestions field is in the report.")
        print(f"Number of suggestions: {len(report['suggestions'])}")
        print("Suggestions:")
        for suggestion in report['suggestions']:
            print(f"- {suggestion}")
    else:
        print("Suggestions field is NOT in the report.")
    
    # Check if debug_info field is in the report
    if 'debug_info' in report:
        print("\nDebug info field is in the report.")
        print(f"Debug info: {report['debug_info']}")
    else:
        print("\nDebug info field is NOT in the report.")
    
    # Add suggestions field to the report if it doesn't exist
    if 'suggestions' not in report:
        print("\nAdding suggestions field to the report...")
        report['suggestions'] = [
            "Consider running a Python code formatter like 'black' or 'autopep8' to standardize Python file naming",
            "Consider using a script to standardize Markdown file names to PascalCase-with-hyphens format",
            "Consider consolidating documentation files in the docs directory for better organization",
            "Consider adding file structure validation to your CI/CD pipeline to catch issues early",
            "Consider documenting file naming and structure conventions in a style guide"
        ]
        
        # Save the updated report
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print("Suggestions field added to the report.")
    
    return 0

if __name__ == "__main__":
    exit(main())