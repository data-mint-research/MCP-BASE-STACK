#!/bin/bash

# MCP-BASE-STACK Management Script
# This script provides commands to manage the MCP-BASE-STACK services

# Set the base directory to the script's location
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$BASE_DIR"

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to display usage information
function show_usage {
    echo -e "${YELLOW}MCP-BASE-STACK Management Script${NC}"
    echo ""
    echo "Usage: ./mcp.sh [command]"
    echo ""
    echo "Commands:"
    echo "  setup       - Setup the environment and install dependencies"
    echo "  start       - Start all services"
    echo "  stop        - Stop all services"
    echo "  restart     - Restart all services"
    echo "  status      - Check the status of all services"
    echo "  logs        - View logs from all services"
    echo "  update-kg   - Update the Knowledge Graph"
    echo "  dev         - Start services in development mode"
    echo "  help        - Show this help message"
    echo ""
}

# Function to setup the environment
function setup {
    echo -e "${GREEN}Setting up MCP-BASE-STACK environment...${NC}"
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
        exit 1
    fi
    
    # Create necessary directories if they don't exist
    mkdir -p data/models/mistral
    mkdir -p data/models/deepseek
    mkdir -p data/models/other
    
    # Install Python dependencies for MCP Server
    echo -e "${GREEN}Installing Python dependencies...${NC}"
    pip install -r services/mcp-server/requirements.txt
    
    # Setup Knowledge Graph
    echo -e "${GREEN}Setting up Knowledge Graph...${NC}"
    python core/kg/scripts/setup_knowledge_graph.py
    
    echo -e "${GREEN}Setup completed successfully!${NC}"
}

# Function to start all services
function start {
    echo -e "${GREEN}Starting MCP-BASE-STACK services...${NC}"
    cd deploy && docker-compose up -d
    echo -e "${GREEN}Services started successfully!${NC}"
}

# Function to stop all services
function stop {
    echo -e "${YELLOW}Stopping MCP-BASE-STACK services...${NC}"
    cd deploy && docker-compose down
    echo -e "${GREEN}Services stopped successfully!${NC}"
}

# Function to restart all services
function restart {
    echo -e "${YELLOW}Restarting MCP-BASE-STACK services...${NC}"
    cd deploy && docker-compose restart
    echo -e "${GREEN}Services restarted successfully!${NC}"
}

# Function to check the status of all services
function status {
    echo -e "${GREEN}Checking MCP-BASE-STACK services status...${NC}"
    cd deploy && docker-compose ps
    
    # Run the health check script
    echo -e "\n${GREEN}Running health check...${NC}"
    bash scripts/utils/validation/verify_stack_health.sh
}

# Function to view logs from all services
function logs {
    echo -e "${GREEN}Viewing MCP-BASE-STACK services logs...${NC}"
    cd deploy && docker-compose logs -f
}

# Function to update the Knowledge Graph
function update_kg {
    echo -e "${GREEN}Updating Knowledge Graph...${NC}"
    python core/kg/scripts/update_knowledge_graph.py
    echo -e "${GREEN}Knowledge Graph updated successfully!${NC}"
}

# Function to start services in development mode
function dev {
    echo -e "${GREEN}Starting MCP-BASE-STACK services in development mode...${NC}"
    cd deploy && docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
    echo -e "${GREEN}Services started in development mode!${NC}"
}

# Main script logic
case "$1" in
    setup)
        setup
        ;;
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    update-kg)
        update_kg
        ;;
    dev)
        dev
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        show_usage
        ;;
esac