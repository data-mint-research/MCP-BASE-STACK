# MCP-BASE-STACK Scripts

This directory contains scripts for setting up, deploying, and maintaining the MCP-BASE-STACK services.

## Directory Structure

- `setup/`: Scripts for setting up the MCP-BASE-STACK services
- `deployment/`: Scripts for deploying the MCP-BASE-STACK services
- `maintenance/`: Scripts for maintaining the MCP-BASE-STACK services
  - `verify_librechat_integration.sh`: Script to verify the integration between LibreChat and other services
- `utils/`: Utility scripts organized by function
  - `backup/`: Scripts for creating and restoring backups
  - `cleanup/`: Scripts for cleaning up files and directories
  - `quality/`: Scripts for checking and fixing code quality
  - `analysis/`: Scripts for analyzing code and project structure
  - `installation/`: Scripts for installing hooks and other components
  - `validation/`: Scripts for validating project components
  - `test-mcp-agent.sh`: Script to test the MCP agent functionality

## File Structure Standards

All scripts in this directory follow the standardized file structure guidelines:

1. **Naming Conventions**:
   - Shell scripts use `lowercase-with-hyphens.sh` format
   - Python scripts use `snake_case.py` format

2. **Directory Organization**:
   - Scripts are organized by function in appropriate subdirectories
   - Utility scripts are placed in the `utils/` directory with further categorization

3. **Special Files**:
   - `README.md` files remain in their respective directories
   - Each subdirectory contains documentation on its specific scripts

The project has achieved 100% compliance with file structure standards, ensuring all scripts are properly named and located in their ideal directories.

## Usage

Most scripts include usage instructions when run with the `-h` or `--help` flag. For detailed documentation on specific scripts, refer to the README.md file in each subdirectory.