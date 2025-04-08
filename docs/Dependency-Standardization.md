# Dependency Standardization

This document outlines the dependency standardization work performed as part of the dependency management improvement plan.

## Overview

The dependency standardization process involved:

1. Identifying inconsistent dependency versions across the project
2. Creating a plan for standardizing dependency versions
3. Updating all dependency references to use consistent versions
4. Verifying that all dependencies use consistent versions

## Identified Issues

The following inconsistencies were identified:

### Python Dependencies

1. Inconsistent version specifications in requirements.txt:
   - Some dependencies used flexible version constraints (e.g., `numpy>=1.22.0`)
   - Others used pinned versions (e.g., `black==21.9b0`)

2. Inconsistencies between requirements.txt and temp_requirements.txt:
   - numpy: requirements.txt had `numpy>=1.22.0` while temp_requirements.txt had `numpy==1.20.0`
   - pandas: requirements.txt had `pandas>=1.4.0` while temp_requirements.txt had `pandas==1.3.0`
   - requirements.txt had additional dependencies not in temp_requirements.txt

### Docker Dependencies

1. Use of "latest" tags in Docker images:
   - librechat/docker-compose.yml used "latest" tags for all images (librechat/librechat:latest, ollama/ollama:latest, mongo:latest)
   - llm-server/docker-compose.yml used "latest" tag for ollama/ollama:latest

## Standardization Approach

### Python Dependencies

1. All Python dependencies were updated to use pinned versions (e.g., `package==version`) to ensure consistency and reproducibility.
2. The temp_requirements.txt file was updated to match requirements.txt.
3. Version numbers were standardized across all Python dependency files.

### Docker Dependencies

1. All Docker images were updated to use specific version tags instead of "latest":
   - librechat/librechat:latest → librechat/librechat:0.6.9
   - ollama/ollama:latest → ollama/ollama:0.1.27
   - mongo:latest → mongo:6.0.12

2. All docker-compose.yml files were updated to maintain consistency across the project.

## Files Updated

### Python Dependency Files
- requirements.txt
- temp_requirements.txt

### Docker Compose Files
- services/librechat/docker-compose.yml
- services/llm-server/docker-compose.yml
- services/mcp-server/docker-compose.yml
- config/services/librechat/docker-compose.yml
- config/services/llm-server/docker-compose.yml
- config/services/mcp-server/docker-compose.yml
- deploy/docker-compose.yml
- config/deploy/docker-compose.yml

## Verification

The dependency audit script was run to verify that all dependencies use consistent versions. The audit report showed no inconsistent dependencies.

## Best Practices

1. Always use pinned versions for dependencies (e.g., `package==1.0.0`) to ensure consistency and reproducibility.
2. Avoid using "latest" tags in Docker images, as they can lead to inconsistent behavior.
3. Regularly run the dependency audit script to check for inconsistencies.
4. Update the knowledge graph after making changes to dependencies.

## Future Work

1. Implement automated checks to prevent the use of "latest" tags in Docker images.
2. Enhance the dependency audit script to check for outdated dependencies and security vulnerabilities.
3. Set up a regular schedule for dependency updates to ensure the project stays up-to-date with security patches and bug fixes.