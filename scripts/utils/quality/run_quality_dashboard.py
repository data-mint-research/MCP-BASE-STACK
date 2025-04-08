#!/usr/bin/env python3
"""
Quality Metrics Dashboard Runner

This script runs the Quality Metrics Dashboard, which provides a centralized
view of quality metrics, trend analysis, and improvement tracking.

Usage:
    python scripts/utils/quality/run_quality_dashboard.py [--port PORT] [--host HOST] [--debug]

Options:
    --port PORT     Port to run the dashboard on [default: 5000]
    --host HOST     Host to run the dashboard on [default: 0.0.0.0]
    --debug         Run in debug mode [default: False]
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).resolve().parents[3]))

from core.logging.config import configure_logger
from core.quality.dashboard import QualityMetricsDashboard

# Configure logging
logger = configure_logger("quality_dashboard")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the Quality Metrics Dashboard")
    
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to run the dashboard on"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to run the dashboard on"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run in debug mode"
    )
    
    return parser.parse_args()

def main():
    """Run the Quality Metrics Dashboard."""
    args = parse_args()
    
    logger.info(f"Starting Quality Metrics Dashboard on {args.host}:{args.port}")
    
    # Create and run the dashboard
    dashboard = QualityMetricsDashboard()
    dashboard.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    main()