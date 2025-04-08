#!/bin/bash
echo "🔧 Initializing MCPgeek Mode for Roo Code..."

mkdir -p .roo
cp "$(dirname "$0")/.roo-mode.json" .roo/config.json

echo "✅ Roo Code mode 'MCPgeek' has been initialized and set as the default for MCP-related development."
echo "📚 Reference documentation available in docs/MCP/"
