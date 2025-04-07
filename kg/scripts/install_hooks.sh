#!/bin/bash

# Pre-commit Hook
cat > .git/hooks/pre-commit << 'HOOK'
#!/bin/bash
echo "Updating Knowledge Graph..."
python kg/scripts/update_knowledge_graph.py

# If changes were made to the Knowledge Graph, add them to the commit
if git status --porcelain | grep -q "kg/data/"; then
    git add kg/data/knowledge_graph.graphml kg/data/knowledge_graph.ttl
    echo "Knowledge Graph updated and added to commit."
fi
HOOK

# Post-merge Hook
cat > .git/hooks/post-merge << 'HOOK'
#!/bin/bash
echo "Updating Knowledge Graph after pull/merge..."
python kg/scripts/update_knowledge_graph.py
HOOK

# Grant execution permissions
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/post-merge

echo "Git hooks for Knowledge Graph installed."