# Integration Tests

This directory contains integration tests for the MCP-BASE-STACK components.

## Contents

- Component interaction tests
- API endpoint tests
- Service integration tests
- End-to-end workflow tests

## Usage

Integration tests in this directory focus on testing how components work together. They verify that different parts of the system interact correctly and that data flows properly between components.

These tests may require external services or resources to be available, and they typically take longer to run than unit tests.

Run integration tests with:

```bash
python -m pytest tests/integration