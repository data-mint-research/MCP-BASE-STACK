#!/usr/bin/env python3
"""
Quality Standards Enforcement Setup Script

This script sets up the complete code quality enforcement system by:
1. Installing and configuring essential quality tools
2. Setting up pre-commit hooks for quality enforcement
3. Configuring CI/CD for automated quality checks
4. Updating the knowledge graph with quality metrics

Usage:
    python enforce_quality_standards.py

The script will automatically update the knowledge graph with quality metrics
after setting up the enforcement system.
"""

import os
import subprocess
import sys
from pathlib import Path
import logging
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"data/logs/quality_setup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

def run_command(command, cwd=None, shell=False):
    """Run a shell command and log the output."""
    logger.info(f"Running command: {command}")
    try:
        if isinstance(command, list) and shell:
            command = " ".join(command)
        
        result = subprocess.run(
            command,
            cwd=cwd,
            shell=shell,
            check=True,
            text=True,
            capture_output=True
        )
        logger.info(f"Command output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with error: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False

def install_quality_tools():
    """Install essential quality tools."""
    logger.info("Installing essential quality tools...")
    
    # Install Python packages from requirements.txt
    if not run_command(["pip", "install", "-r", "requirements.txt"]):
        logger.error("Failed to install Python packages from requirements.txt")
        return False
    
    # Install additional quality tools
    script_path = Path("scripts/utils/installation/install-quality-tools.sh")
    if not script_path.exists():
        logger.error(f"Quality tools installation script not found at {script_path}")
        return False
    
    if not run_command(["bash", str(script_path)], shell=True):
        logger.error("Failed to install additional quality tools")
        return False
    
    logger.info("Quality tools installation completed successfully")
    return True

def setup_pre_commit_hooks():
    """Set up pre-commit hooks for quality enforcement."""
    logger.info("Setting up pre-commit hooks...")
    
    # Install pre-commit hooks
    script_path = Path("scripts/utils/installation/install-pre-commit-hooks.sh")
    if not script_path.exists():
        logger.error(f"Pre-commit hooks installation script not found at {script_path}")
        return False
    
    if not run_command(["bash", str(script_path)], shell=True):
        logger.error("Failed to install pre-commit hooks")
        return False
    
    logger.info("Pre-commit hooks setup completed successfully")
    return True

def update_knowledge_graph():
    """Update the knowledge graph with quality metrics."""
    logger.info("Updating knowledge graph with quality metrics...")
    
    try:
        from core.quality.enforcer import enforcer
        
        # Run all quality checks
        results = enforcer.run_all_checks()
        
        # Update knowledge graph with quality metrics
        enforcer.update_knowledge_graph(results)
        
        logger.info("Knowledge graph updated successfully with quality metrics")
        return True
    except Exception as e:
        logger.error(f"Failed to update knowledge graph: {e}")
        return False

def main():
    """Main function to set up the quality enforcement system."""
    logger.info("Starting quality standards enforcement setup...")
    
    # Create necessary directories
    os.makedirs("data/logs", exist_ok=True)
    os.makedirs(".git-hooks", exist_ok=True)
    
    # Step 1: Install quality tools
    if not install_quality_tools():
        logger.error("Failed to install quality tools. Aborting setup.")
        return False
    
    # Step 2: Set up pre-commit hooks
    if not setup_pre_commit_hooks():
        logger.error("Failed to set up pre-commit hooks. Aborting setup.")
        return False
    
    # Step 3: Update knowledge graph
    if not update_knowledge_graph():
        logger.warning("Failed to update knowledge graph. Setup will continue, but knowledge graph may be out of date.")
    
    logger.info("Quality standards enforcement setup completed successfully")
    logger.info("You can now run quality checks with: python -c 'from core.quality.enforcer import enforcer; enforcer.run_all_checks()'")
    logger.info("Pre-commit hooks will automatically run quality checks before each commit")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)