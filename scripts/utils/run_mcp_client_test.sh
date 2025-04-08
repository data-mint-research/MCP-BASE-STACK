#!/bin/bash
# Run the MCP Client test script

# Set up environment
echo "Setting up environment..."
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Check if the client component is implemented
if [ ! -d "services/mcp-server/src/client" ]; then
    echo "Client component not found. Implementing it now..."
    python3 scripts/migration/mcp/implement_client_component.py --verbose
    if [ $? -ne 0 ]; then
        echo "Failed to implement client component. Exiting."
        exit 1
    fi
fi

# Check if the host component is implemented
if [ ! -d "services/mcp-server/src/host" ]; then
    echo "Host component not found. Implementing it now..."
    python3 scripts/migration/mcp/implement_host_component.py --verbose
    if [ $? -ne 0 ]; then
        echo "Failed to implement host component. Exiting."
        exit 1
    fi
fi

# Run the test script
echo "Running MCP Client tests..."
python3 scripts/test_mcp_client.py --verbose

# Check the result
if [ $? -eq 0 ]; then
    echo "MCP Client tests completed successfully!"
    echo "You can now use the MCP Client component in your applications."
    echo "See docs/MCP/client-usage.md for usage instructions."
else
    echo "MCP Client tests failed. Please check the logs for details."
    exit 1
fi

# Suggest next steps
echo ""
echo "Next steps:"
echo "1. Review the client implementation in services/mcp-server/src/client"
echo "2. Check the example in examples/mcp_client_usage_example.py"
echo "3. Read the documentation in docs/MCP/client-usage.md"
echo ""
echo "To run the example:"
echo "python3 examples/mcp_client_usage_example.py"