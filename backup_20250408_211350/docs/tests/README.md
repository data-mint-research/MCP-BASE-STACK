# MCP-BASE-STACK Test Suite

This directory contains the comprehensive test suite for the MCP-BASE-STACK project.

## Test Structure

The test suite is organized into the following categories:

### Unit Tests (`unit/`)

Tests for individual functions, classes, and prompts:
- `api/`: Tests for FastAPI controllers, schemas, and endpoints
- `core/`: Tests for core functions (e.g., parsers, validators, utilities)
- `langgraph/`: Tests for node and edge-specific logic
- `llm/`: Tests for prompts, tool calls, and output parsers
- `agents/`: Tests for agent logic (e.g., MINTYcoder, MINTYprocess)

### Integration Tests (`integration/`)

Tests for component interactions at the service level:
- `fastapi_langgraph/`: Tests for FastAPI ↔ LangGraph interactions
- `langgraph_llm/`: Tests for LangGraph ↔ Ollama interactions
- `toolcalls/`: Tests for tools like MongoDB, Meilisearch, MinIO, etc.
- `mcp_interface/`: Tests for `/mcp/infer` routing, middleware, and payloads

### Agent Tests (`agent_tests/`)

Tests for agent-specific scenarios:
- `dialogflows/`: Complete example flows including branches
- `behaviour/`: Individual actions, decision paths, and fallbacks
- `ruleset/`: Rule application and deviation detection

### End-to-End Tests (`e2e/`)

Realistic user flow tests:
- `inference/`: Prompt → Tool → Answer → Export flows
- `recovery/`: Tests for error cases and resilience

### Performance Tests (`performance/`)

Load, latency, and throughput measurements:
- `benchmarks/`: Comparison of different models/tools
- `stress/`: Long-running load tests, memory usage, etc.

### Regression Tests (`regression/`)

Tests for detecting changes:
- `model_versions/`: Comparing different model versions (e.g., DeepSeek vs. Mistral)
- `prompt_changes/`: Testing the impact of new prompt sets

### Test Data (`data/`)

Test data, example inputs/outputs:
- `inputs/`: Test input data
- `outputs/`: Expected output data
- `gold_standard/`: Reference data for comparison

## Running Tests

Instructions for running tests will be added as the test suite is implemented.

## Contributing Tests

When adding new tests:
1. Follow the existing directory structure
2. Include clear documentation for each test
3. Ensure tests are deterministic and repeatable
4. Add appropriate test data in the `data/` directory