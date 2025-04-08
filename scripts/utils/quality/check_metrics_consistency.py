#!/usr/bin/env python3
"""
Check Consistency Between File Structure Metrics Files

This script checks for inconsistencies between file_structure_metrics.json and
file-structure-report.json without updating them. It's useful for monitoring
and debugging purposes.

Usage:
    python scripts/utils/quality/check_metrics_consistency.py

The script will log any inconsistencies found between the two files.
"""

import os
import sys
import json
import logging
import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"data/logs/metrics_consistency_check_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

def check_metrics_consistency():
    """
    Check consistency between file_structure_metrics.json and file-structure-report.json.
    
    This function checks if the metrics in both files are consistent with each other,
    accounting for rounding differences. It logs warnings if significant inconsistencies
    are found.
    
    Returns:
        bool: True if the files are consistent, False otherwise
    """
    logger.info("Checking consistency between file structure metrics files...")
    
    # Define paths to both files
    metrics_path = Path("data/reports/file_structure_metrics.json")
    report_path = Path("data/reports/file-structure-report.json")
    
    # Check if both files exist
    if not metrics_path.exists():
        logger.error(f"File not found: {metrics_path}")
        return False
    
    if not report_path.exists():
        logger.error(f"File not found: {report_path}")
        return False
    
    try:
        # Load both files
        with open(metrics_path, 'r') as f:
            metrics_data = json.load(f)
        
        with open(report_path, 'r') as f:
            report_data = json.load(f)
        
        # Extract metrics from both files
        metrics_naming = metrics_data.get("file_structure_metrics", {}).get("naming_compliance", 0)
        metrics_directory = metrics_data.get("file_structure_metrics", {}).get("directory_compliance", 0)
        metrics_overall = metrics_data.get("file_structure_metrics", {}).get("overall_compliance", 0)
        metrics_total_files = metrics_data.get("file_structure_metrics", {}).get("total_files", 0)
        
        report_naming = report_data.get("naming_issues", {}).get("compliance_percentage", 0)
        report_directory = report_data.get("directory_issues", {}).get("compliance_percentage", 0)
        report_overall = report_data.get("overall_compliance_percentage", 0)
        report_total_files = report_data.get("total_files", 0)
        
        # Define threshold for acceptable difference due to rounding
        threshold = 0.01
        
        # Check for inconsistencies
        inconsistencies = []
        
        if abs(metrics_naming - report_naming) > threshold:
            inconsistencies.append(f"Naming compliance: {metrics_naming} vs {report_naming}")
        
        if abs(metrics_directory - report_directory) > threshold:
            inconsistencies.append(f"Directory compliance: {metrics_directory} vs {report_directory}")
        
        if abs(metrics_overall - report_overall) > threshold:
            inconsistencies.append(f"Overall compliance: {metrics_overall} vs {report_overall}")
        
        if metrics_total_files != report_total_files:
            inconsistencies.append(f"Total files: {metrics_total_files} vs {report_total_files}")
        
        # Log results
        if inconsistencies:
            logger.warning("Inconsistencies found between file structure metrics files:")
            for inconsistency in inconsistencies:
                logger.warning(f"  - {inconsistency}")
            
            # Log timestamps to help identify which file might be stale
            metrics_timestamp = metrics_data.get("timestamp", "unknown")
            report_timestamp = report_data.get("timestamp", "unknown")
            logger.warning(f"Timestamps: metrics={metrics_timestamp}, report={report_timestamp}")
            
            # Print a summary of the inconsistencies
            print("\nInconsistencies found between file structure metrics files:")
            print(f"  - file_structure_metrics.json (timestamp: {metrics_timestamp})")
            print(f"  - file-structure-report.json (timestamp: {report_timestamp})")
            print("\nDetails:")
            for inconsistency in inconsistencies:
                print(f"  - {inconsistency}")
            print("\nRecommendation: Run 'python scripts/utils/quality/update_file_structure_metrics.py' to update the metrics.")
            
            return False
        else:
            logger.info("File structure metrics files are consistent")
            print("File structure metrics files are consistent")
            return True
    
    except Exception as e:
        logger.error(f"Error checking metrics consistency: {e}")
        return False

def main():
    """Main function."""
    # Create necessary directories
    os.makedirs("data/logs", exist_ok=True)
    
    # Check metrics consistency
    is_consistent = check_metrics_consistency()
    
    # Exit with appropriate status code
    sys.exit(0 if is_consistent else 1)

if __name__ == "__main__":
    main()