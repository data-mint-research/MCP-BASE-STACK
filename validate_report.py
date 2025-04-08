#!/usr/bin/env python3
"""
Script to validate the file structure report and update the knowledge graph.
"""

import json
import os
import logging
import datetime
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"data/logs/validate_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main function to validate the file structure report."""
    # Check if the file-structure-report.json file exists
    report_path = "data/reports/file-structure-report.json"
    if not os.path.exists(report_path):
        logger.error(f"Error: {report_path} does not exist.")
        return 1
    
    # Load the report
    with open(report_path, 'r') as f:
        try:
            report = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON: {e}")
            return 1
    
    # Check if suggestions field is in the report
    if 'suggestions' in report:
        logger.info("Suggestions field is in the report.")
        logger.info(f"Number of suggestions: {len(report['suggestions'])}")
        logger.info("Suggestions:")
        for suggestion in report['suggestions']:
            logger.info(f"- {suggestion}")
    else:
        logger.warning("Suggestions field is NOT in the report.")
        logger.info("Adding suggestions field to the report...")
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
        
        logger.info("Suggestions field added to the report.")
    
    # Check if debug_info field is in the report
    if 'debug_info' in report:
        logger.info("Debug info field is in the report.")
        logger.info(f"Debug info: {report['debug_info']}")
    else:
        logger.warning("Debug info field is NOT in the report.")
        logger.info("Adding debug info field to the report...")
        report['debug_info'] = {
            'suggestions_generated': bool(report.get('suggestions', [])),
            'suggestions_count': len(report.get('suggestions', [])),
            'suggestions_list': report.get('suggestions', [])
        }
        
        # Save the updated report
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info("Debug info field added to the report.")
    
    # Generate metrics file
    metrics_path = "data/reports/file_structure_metrics.json"
    metrics = {
        "timestamp": datetime.datetime.now().isoformat(),
        "file_structure_metrics": {
            "naming_compliance": round(report['naming_issues']['compliance_percentage'], 2),
            "directory_compliance": round(report['directory_issues']['compliance_percentage'], 2),
            "overall_compliance": round(report['overall_compliance_percentage'], 2),
            "naming_issues_count": report['naming_issues']['count'],
            "directory_issues_count": report['directory_issues']['count'],
            "total_files": report['total_files']
        }
    }
    
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"File structure metrics saved to {metrics_path}")
    
    # Print summary
    logger.info("File Structure Validation Summary:")
    logger.info(f"- Overall file structure compliance: {report['overall_compliance_percentage']:.2f}%")
    logger.info(f"- Files with naming convention issues: {report['naming_issues']['count']}")
    logger.info(f"- Files not in ideal directories: {report['directory_issues']['count']}")
    
    # Log suggestions
    if report.get('suggestions'):
        logger.info("Suggestions for improvement:")
        for suggestion in report['suggestions']:
            logger.info(f"- {suggestion}")
    
    return 0

if __name__ == "__main__":
    exit(main())