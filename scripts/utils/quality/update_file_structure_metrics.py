#!/usr/bin/env python3
"""
Update Knowledge Graph with File Structure Metrics

This script updates the knowledge graph with file structure standardization metrics.
It runs the file structure validation and adds the metrics to the knowledge graph.

Usage:
    python scripts/utils/quality/update_file_structure_metrics.py

The script will automatically update the knowledge graph with the latest file structure metrics.
"""

import os
import sys
import json
import logging
import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# Import project modules
try:
    from standardize_file_structure import validate_file_structure
    from core.kg.scripts.update_knowledge_graph import update_knowledge_graph
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure you're running this script from the project root directory.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"data/logs/file_structure_metrics_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

def validate_metrics_consistency():
    """
    Validate consistency between file_structure_metrics.json and file-structure-report.json.
    
    This function checks if the metrics in both files are consistent with each other,
    accounting for rounding differences. It logs warnings if significant inconsistencies
    are found.
    
    Returns:
        bool: True if the files are consistent, False otherwise
    """
    logger.info("Validating consistency between file structure metrics files...")
    
    # Define paths to both files
    metrics_path = Path("data/reports/file_structure_metrics.json")
    report_path = Path("data/reports/file-structure-report.json")
    
    # Check if both files exist
    if not metrics_path.exists() or not report_path.exists():
        logger.warning("Cannot validate consistency: One or both files do not exist")
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
            
            return False
        else:
            logger.info("File structure metrics files are consistent")
            return True
    
    except Exception as e:
        logger.error(f"Error validating metrics consistency: {e}")
        return False

def update_file_structure_metrics():
    """Update the knowledge graph with file structure metrics."""
    logger.info("Updating knowledge graph with file structure metrics...")
    
    try:
        # Run file structure validation
        validation_report = validate_file_structure()
        
        # Create metrics report
        # Log raw values from validation report for debugging
        logger.info(f"Raw naming compliance from validation report: {validation_report['naming_issues']['compliance_percentage']}")
        logger.info(f"Raw directory compliance from validation report: {validation_report['directory_issues']['compliance_percentage']}")
        logger.info(f"Raw overall compliance from validation report: {validation_report['overall_compliance_percentage']}")
        
        # Create metrics report with potentially rounded values
        naming_compliance = round(validation_report['naming_issues']['compliance_percentage'], 2)
        directory_compliance = round(validation_report['directory_issues']['compliance_percentage'], 2)
        overall_compliance = round(validation_report['overall_compliance_percentage'], 2)
        
        logger.info(f"Processed naming compliance for metrics report: {naming_compliance}")
        logger.info(f"Processed directory compliance for metrics report: {directory_compliance}")
        logger.info(f"Processed overall compliance for metrics report: {overall_compliance}")
        
        metrics_report = {
            "timestamp": datetime.datetime.now().isoformat(),
            "file_structure_metrics": {
                "naming_compliance": naming_compliance,
                "directory_compliance": directory_compliance,
                "overall_compliance": overall_compliance,
                "naming_issues_count": validation_report['naming_issues']['count'],
                "directory_issues_count": validation_report['directory_issues']['count'],
                "total_files": validation_report['total_files']
            }
        }
        
        # Save metrics report
        reports_dir = Path("data/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = reports_dir / "file_structure_metrics.json"
        with open(report_path, 'w') as f:
            json.dump(metrics_report, f, indent=2)
        
        logger.info(f"File structure metrics report saved to {report_path}")
        
        # Update knowledge graph
        update_knowledge_graph()
        
        # Validate consistency between metrics files
        validate_metrics_consistency()
        
        logger.info("Knowledge graph updated successfully with file structure metrics")
        return True
    except Exception as e:
        logger.error(f"Failed to update knowledge graph with file structure metrics: {e}")
        return False

def main():
    """Main function."""
    # Create necessary directories
    os.makedirs("data/logs", exist_ok=True)
    os.makedirs("data/reports", exist_ok=True)
    
    # Update file structure metrics
    success = update_file_structure_metrics()
    
    if success:
        logger.info("File structure metrics update completed successfully")
    else:
        logger.error("File structure metrics update failed")
        sys.exit(1)
    
    # Perform an additional validation check to ensure consistency
    # This helps catch inconsistencies even if we're not updating the metrics
    logger.info("Performing final validation check...")
    is_consistent = validate_metrics_consistency()
    
    if not is_consistent:
        logger.warning("Inconsistencies detected between metrics files. Manual review recommended.")

if __name__ == "__main__":
    main()