#!/bin/bash
# Run the MCP Host application
# This script starts the FastAPI application that uses the MCP Host component

# Set environment variables
export MCP_HOST_ID="main-host"
export MCP_SERVER_ID="main-server"
export MCP_CLIENT_ID="main-client"
export PORT=8000

# Navigate to the project root directory
cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install requirements if needed
if [ "$1" == "--install" ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt
fi

# Run the application
echo "Starting MCP Host application on port $PORT..."
python app.py