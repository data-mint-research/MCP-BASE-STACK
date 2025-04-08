# Dependency Lockfiles

This document outlines the dependency lockfile system implemented in the MCP-BASE-STACK project.

## Overview

Dependency lockfiles ensure that:

1. All dependencies are pinned to exact versions, including transitive dependencies
2. Builds are reproducible across different environments
3. Dependency updates are intentional and controlled
4. CI/CD pipelines can validate that lockfiles are up-to-date

## Lockfile Types

The project uses the following lockfile types:

### 1. Python Lockfile (requirements.lock)

The `requirements.lock` file locks all Python dependencies to exact versions. This file:

- Contains all direct and transitive dependencies
- Includes exact version numbers for all packages
- Is generated from requirements.txt
- Should be committed to version control
- Is validated in CI/CD pipelines

### 2. Docker Lockfile (docker-compose.lock.yml)

The `docker-compose.lock.yml` file locks all Docker image versions. This file:

- Contains all Docker images used in the project
- Includes exact version tags for all images
- Is a reference file that documents the exact versions of Docker images
- Should be committed to version control
- Is validated in CI/CD pipelines

## Lockfile Management

### Creating and Updating Lockfiles

#### Python Lockfiles

To create or update the Python lockfile:

```bash
# Install pip-tools if not already installed
pip install pip-tools

# Generate requirements.lock from requirements.txt
pip-compile requirements.txt --output-file requirements.lock
```

If there are dependency conflicts, you may need to manually create the lockfile by:

```bash
# Install dependencies
pip install -r requirements.txt

# Export installed packages to requirements.lock
pip freeze > requirements.lock

# Edit requirements.lock to remove packages not in requirements.txt
```

#### Docker Lockfiles

To create or update the Docker lockfile:

1. Update the `docker-compose.lock.yml` file manually to match the image versions in your docker-compose.yml files
2. Ensure all services and their image versions are accurately documented

### Validating Lockfiles

To validate that lockfiles are up-to-date:

```bash
# Validate all lockfiles
python scripts/utils/validation/validate_lockfiles.py

# Validate with verbose output
python scripts/utils/validation/validate_lockfiles.py --verbose
```

## CI/CD Integration

The lockfile validation is integrated into the CI/CD pipeline:

1. The `quality-checks.yml` workflow includes a step to validate lockfiles
2. If lockfiles are out-of-date, the CI/CD pipeline will fail
3. Developers must update lockfiles before merging changes

## Best Practices

### 1. Always Keep Lockfiles Up-to-Date

- Update lockfiles whenever you update dependencies
- Commit lockfiles to version control
- Run lockfile validation locally before pushing changes

### 2. Use Exact Versions in Source Files

- Use exact versions in requirements.txt (e.g., `package==1.0.0`)
- Use exact version tags in docker-compose.yml files (e.g., `image: service:1.0.0`)
- Avoid using "latest" tags or version ranges

### 3. Review Lockfile Changes Carefully

- Review all changes to lockfiles during code reviews
- Pay special attention to security-related updates
- Understand the impact of version changes on the project

### 4. Handle Conflicts Appropriately

- If dependency conflicts occur, resolve them by:
  - Updating the conflicting dependencies
  - Finding compatible versions
  - Documenting known conflicts that cannot be resolved

### 5. Regular Maintenance

- Regularly update dependencies to get security patches
- Schedule periodic dependency reviews
- Keep the knowledge graph updated with dependency information

## Knowledge Graph Integration

The dependency lockfile system integrates with the knowledge graph by:

1. Recording locked dependency versions
2. Tracking dependency update history
3. Documenting known conflicts and their resolutions
4. Maintaining dependency relationships

This integration ensures that the knowledge graph remains the single source of truth for all dependency-related information.