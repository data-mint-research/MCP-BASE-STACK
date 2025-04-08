#!/usr/bin/env python3
"""
Simulate Inconsistency Between File Structure Metrics Files

This script deliberately creates an inconsistency between file_structure_metrics.json
and file-structure-report.json for testing purposes. It modifies one file while
leaving the other unchanged, creating a detectable inconsistency.

Usage:
    python scripts/utils/quality/simulate_metrics_inconsistency.py [--type TYPE]

Options:
    --type TYPE    Type of inconsistency to simulate (default: naming)
                   Valid values: naming, directory, overall, files

The script will create an inconsistency and then run the consistency check
to verify that it's detected.
"""

import os
import sys
import json
import logging
import datetime
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"data/logs/simulate_inconsistency_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

def simulate_inconsistency(inconsistency_type='naming'):
    """
    Simulate an inconsistency between file_structure_metrics.json and file-structure-report.json.
    
    Args:
        inconsistency_type: Type of inconsistency to simulate (naming, directory, overall, files)
        
    Returns:
        bool: True if the inconsistency was created successfully, False otherwise
    """
    logger.info(f"Simulating {inconsistency_type} inconsistency...")
    
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
        
        # Create a backup of the original files
        backup_dir = Path("data/reports/backups")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        
        with open(backup_dir / f"file_structure_metrics_{timestamp}.json", 'w') as f:
            json.dump(metrics_data, f, indent=2)
        
        with open(backup_dir / f"file-structure-report_{timestamp}.json", 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Created backups of original files in {backup_dir}")
        
        # Modify the metrics file based on the inconsistency type
        if inconsistency_type == 'naming':
            # Modify naming compliance in metrics file
            current_value = metrics_data["file_structure_metrics"]["naming_compliance"]
            metrics_data["file_structure_metrics"]["naming_compliance"] = current_value - 10.0
            logger.info(f"Changed naming compliance from {current_value} to {current_value - 10.0}")
        
        elif inconsistency_type == 'directory':
            # Modify directory compliance in metrics file
            current_value = metrics_data["file_structure_metrics"]["directory_compliance"]
            metrics_data["file_structure_metrics"]["directory_compliance"] = current_value - 10.0
            logger.info(f"Changed directory compliance from {current_value} to {current_value - 10.0}")
        
        elif inconsistency_type == 'overall':
            # Modify overall compliance in metrics file
            current_value = metrics_data["file_structure_metrics"]["overall_compliance"]
            metrics_data["file_structure_metrics"]["overall_compliance"] = current_value - 10.0
            logger.info(f"Changed overall compliance from {current_value} to {current_value - 10.0}")
        
        elif inconsistency_type == 'files':
            # Modify total files in metrics file
            current_value = metrics_data["file_structure_metrics"]["total_files"]
            metrics_data["file_structure_metrics"]["total_files"] = current_value - 50
            logger.info(f"Changed total files from {current_value} to {current_value - 50}")
        
        else:
            logger.error(f"Invalid inconsistency type: {inconsistency_type}")
            return False
        
        # Save the modified metrics file
        with open(metrics_path, 'w') as f:
            json.dump(metrics_data, f, indent=2)
        
        logger.info(f"Created {inconsistency_type} inconsistency between metrics files")
        return True
    
    except Exception as e:
        logger.error(f"Error simulating inconsistency: {e}")
        return False

def main():
    """Main function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Simulate inconsistency between file structure metrics files")
    parser.add_argument("--type", choices=["naming", "directory", "overall", "files"], default="naming",
                        help="Type of inconsistency to simulate")
    
    args = parser.parse_args()
    
    # Create necessary directories
    os.makedirs("data/logs", exist_ok=True)
    os.makedirs("data/reports/backups", exist_ok=True)
    
    # Simulate inconsistency
    success = simulate_inconsistency(args.type)
    
    if success:
        logger.info("Inconsistency simulation completed successfully")
        
        # Run the consistency check to verify the inconsistency is detected
        logger.info("Running consistency check to verify inconsistency is detected...")
        
        try:
            # Import the check_metrics_consistency module
            sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
            from check_metrics_consistency import check_metrics_consistency
            
            # Run the consistency check
            is_consistent = check_metrics_consistency()
            
            if is_consistent:
                logger.warning("Inconsistency was not detected by the consistency check!")
            else:
                logger.info("Inconsistency was successfully detected by the consistency check")
        
        except Exception as e:
            logger.error(f"Error running consistency check: {e}")
    
    else:
        logger.error("Inconsistency simulation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()