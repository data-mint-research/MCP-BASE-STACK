#!/bin/bash
echo "=== MCP-BASE-STACK HEALTH CHECK ==="
echo "$(date)" | tee stack-health-report.txt
echo "" | tee -a stack-health-report.txt

echo "=== LibreChat API Availability ===" | tee -a stack-health-report.txt
curl -I http://localhost:3080/ 2>/dev/null | head -n 1 | tee -a stack-health-report.txt
echo "" | tee -a stack-health-report.txt

echo "=== LLM Server API Availability ===" | tee -a stack-health-report.txt
if curl -s http://localhost:11434/api/tags 2>/dev/null | grep -q "models"; then
  echo "LLM Server API is responding" | tee -a stack-health-report.txt
else
  echo "LLM Server API not available" | tee -a stack-health-report.txt
fi
echo "" | tee -a stack-health-report.txt

echo "=== MCP Server Availability ===" | tee -a stack-health-report.txt
curl -s http://localhost:8000/debug/health 2>/dev/null | tee -a stack-health-report.txt
echo "" | tee -a stack-health-report.txt

echo "=== LLM Server Models Available ===" | tee -a stack-health-report.txt
docker exec llm-server ollama list 2>/dev/null | tee -a stack-health-report.txt
echo "" | tee -a stack-health-report.txt

echo "=== System Resource Usage ===" | tee -a stack-health-report.txt
echo "Memory:" | tee -a stack-health-report.txt
free -h | tee -a stack-health-report.txt
echo "" | tee -a stack-health-report.txt
echo "GPU:" | tee -a stack-health-report.txt
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv | tee -a stack-health-report.txt
echo "" | tee -a stack-health-report.txt

echo "Health check completed - see stack-health-report.txt for details"
