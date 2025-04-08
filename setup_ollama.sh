#!/bin/bash

# Setup Ollama and pull required LLMs
# This script installs Ollama and pulls the required models

echo "Setting up Ollama and pulling required LLMs..."

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "Ollama is not installed. Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    
    # Wait for Ollama to start
    echo "Waiting for Ollama to start..."
    sleep 5
else
    echo "Ollama is already installed."
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "Starting Ollama service..."
    ollama serve &
    
    # Wait for Ollama to start
    echo "Waiting for Ollama to start..."
    sleep 5
fi

# Pull required models
echo "Pulling required models..."

# Pull Mistral model (7B version)
echo "Pulling Mistral 7B model..."
ollama pull mistral:7b

# Pull DeepSeek Coder model (6.7B version)
echo "Pulling DeepSeek Coder 6.7B model..."
ollama pull deepseek-coder:6.7b

# Pull Command-RP model (latest version)
echo "Pulling Command-RP latest model..."
ollama pull command-rp:latest

echo "Ollama setup complete!"
echo "Available models:"
ollama list

echo ""
echo "You can now start the MCP stack with: ./start_mcp_stack.sh"
