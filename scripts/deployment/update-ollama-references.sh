#!/bin/bash
# update_ollama_references.sh

find . -type f -name "*.py" -o -name "*.md" -o -name "*.yaml" -o -name "*.yml" | xargs grep -l "ollama" | while read file; do
  # Skip files in the services/llm-server directory that might legitimately reference Ollama
  if [[ "$file" != "./services/llm-server/"* ]]; then
    sed -i 's/ollama:11434/llm-server:11434/g' "$file"
    sed -i 's/http:\/\/ollama/http:\/\/llm-server/g' "$file"
    # Replace direct references to the service name, preserving ollama in other contexts
    sed -i 's/service: ollama/service: llm-server/g' "$file"
    sed -i 's/container: ollama/container: llm-server/g' "$file"
  fi
done