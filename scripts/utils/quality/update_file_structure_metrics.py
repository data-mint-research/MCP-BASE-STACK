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

def update_file_structure_metrics():
    """Update the knowledge graph with file structure metrics."""
    logger.info("Updating knowledge graph with file structure metrics...")
    
    try:
        # Run file structure validation
        validation_report = validate_file_structure()
        
        # Create metrics report
        metrics_report = {
            "timestamp": datetime.datetime.now().isoformat(),
            "file_structure_metrics": {
                "naming_compliance": validation_report['naming_issues']['compliance_percentage'],
                "directory_compliance": validation_report['directory_issues']['compliance_percentage'],
                "overall_compliance": validation_report['overall_compliance_percentage'],
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

if __name__ == "__main__":
    main()