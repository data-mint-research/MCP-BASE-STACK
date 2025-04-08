# Git File Update Hooks

This directory contains Git hooks that automatically update README.md, .gitignore, LICENSE files, and the Knowledge Graph before every commit without requiring explicit user action.

## Hooks Included

### pre-commit

The pre-commit hook performs the following actions:

1. **README.md Updates**:
   - Adds a "Last updated" timestamp if not present
   - Updates the timestamp if already present

2. **.gitignore Updates**:
   - Adds common files and patterns that should be ignored if not already present
   - Includes project-specific patterns for MCP-BASE-STACK

3. **LICENSE Updates**:
   - Updates the copyright year to the current year if needed

4. **Knowledge Graph Updates**:
   - Runs the knowledge graph update script to ensure the graph reflects the current state of the project
   - Maintains relationships between components, features, and files

All modified files are automatically staged and included in the commit.

## Installation

To install the hooks, run the installation script from the repository root:

```bash
./scripts/utils/installation/install-file-update-hooks.sh
```

This script:
1. Copies the pre-commit hook to the `.git/hooks` directory
2. Makes the hook executable
3. Configures Git to use the hooks

## For New Repository Clones

The installation script is included in the repository, so new clones can easily install the hooks by running:

```bash
./scripts/utils/installation/install-file-update-hooks.sh
```

## Manual Installation

If you prefer to install the hooks manually:

1. Copy the pre-commit hook to your `.git/hooks` directory:
   ```bash
   cp .git-hooks/pre-commit .git/hooks/
   ```

2. Make it executable:
   ```bash
   chmod +x .git/hooks/pre-commit
   ```

## How It Works

The pre-commit hook runs automatically before each commit. It:

1. Checks if README.md, .gitignore, LICENSE files, and the Knowledge Graph exist and are tracked by Git
2. Updates each file as needed
3. Stages the modified files so they're included in the commit

No manual action is required - the files are updated and staged automatically.