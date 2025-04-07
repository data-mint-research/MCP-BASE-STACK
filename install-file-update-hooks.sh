#!/bin/bash

# ============================================================================
# Git Hooks Installation Script for File Updates
# ============================================================================
# This script installs Git hooks that automatically update README.md,
# .gitignore, LICENSE files, and the Knowledge Graph before every commit.
#
# The script:
# 1. Copies the pre-commit hook to the .git/hooks directory
# 2. Makes the hook executable
# 3. Adds a setup instruction to README.md if not already present
# ============================================================================

echo "Installing Git hooks for automatic file updates..."

# Ensure the .git-hooks directory exists
if [ ! -d ".git-hooks" ]; then
    echo "Error: .git-hooks directory not found."
    echo "Please run this script from the repository root directory."
    exit 1
fi

# Ensure the .git directory exists
if [ ! -d ".git" ]; then
    echo "Error: .git directory not found."
    echo "Please run this script from a Git repository."
    exit 1
fi

# Create hooks directory if it doesn't exist
mkdir -p .git/hooks

# Copy the pre-commit hook
cp .git-hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

echo "Pre-commit hook installed successfully."

# Add setup instructions to README.md if not already present
if [ -f "README.md" ] && ! grep -q "File Update Hooks" README.md; then
    echo -e "\n## File Update Hooks\n\nThis repository includes Git hooks that automatically update README.md, .gitignore, LICENSE files, and the Knowledge Graph before every commit.\n\nTo install the hooks, run:\n\n\`\`\`bash\n./install-file-update-hooks.sh\n\`\`\`" >> README.md
    echo "Added setup instructions to README.md"
fi

# Create a Git configuration to use our hooks directory
git config core.hooksPath .git-hooks

echo "Git hooks installation completed."
echo "The hooks will automatically update README.md, .gitignore, LICENSE files, and the Knowledge Graph before every commit."