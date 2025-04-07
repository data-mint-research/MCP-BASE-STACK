#!/bin/bash
echo "=== TESTING MCP AGENT MINTY CODER ===" | tee mcp-agent-test.txt
echo "$(date)" | tee -a mcp-agent-test.txt
echo "" | tee -a mcp-agent-test.txt

echo "=== Test 1: Simple LLM Query ===" | tee -a mcp-agent-test.txt
echo "Query: What is 2+2?" | tee -a mcp-agent-test.txt
curl -s -X POST http://localhost:8000/mcp/infer \
  -H "Content-Type: application/json" \
  -d '{ "prompt": "What is 2+2?" }' | tee -a mcp-agent-test.txt
echo "" | tee -a mcp-agent-test.txt
echo "" | tee -a mcp-agent-test.txt

echo "=== Test 2: Code Generation ===" | tee -a mcp-agent-test.txt
echo "Query: Write a Python function to check if a string is a palindrome" | tee -a mcp-agent-test.txt
curl -s -X POST http://localhost:8000/mcp/infer \
  -H "Content-Type: application/json" \
  -d '{ "prompt": "Write a Python function to check if a string is a palindrome" }' | tee -a mcp-agent-test.txt
echo "" | tee -a mcp-agent-test.txt
echo "" | tee -a mcp-agent-test.txt

echo "=== Test 3: Tool Invocation ===" | tee -a mcp-agent-test.txt
echo "Query: !shell echo Hello from MINTYcoder" | tee -a mcp-agent-test.txt
curl -s -X POST http://localhost:8000/mcp/infer \
  -H "Content-Type: application/json" \
  -d '{ "prompt": "!shell echo Hello from MINTYcoder" }' | tee -a mcp-agent-test.txt
echo "" | tee -a mcp-agent-test.txt
echo "" | tee -a mcp-agent-test.txt

echo "=== Test 4: System Info Tool ===" | tee -a mcp-agent-test.txt
echo "Query: !shell uname -a" | tee -a mcp-agent-test.txt
curl -s -X POST http://localhost:8000/mcp/infer \
  -H "Content-Type: application/json" \
  -d '{ "prompt": "!shell uname -a" }' | tee -a mcp-agent-test.txt
echo "" | tee -a mcp-agent-test.txt

echo "Tests completed - see mcp-agent-test.txt for results"