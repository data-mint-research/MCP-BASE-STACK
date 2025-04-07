# Monitoring and Logging

This guide explains how to monitor the MCP-BASE-STACK components and access their logs for troubleshooting.

## Viewing Logs

### LibreChat Logs

To view logs from the LibreChat application:

```bash
# View logs for all LibreChat services
cd LibreChat
docker compose logs -f

# View logs for a specific service
docker compose logs -f api
```

### Ollama Logs

To view logs from the Ollama LLM server:

```bash
docker logs -f ollama
```

### MCP Server Logs

To view logs from the MCP Server:

```bash
# View main server log
tail -f mcp_server.log

# View debug log with more detailed information
tail -f mcp_debug.log
```

## Health Checks

Run periodic health checks to ensure all components are functioning properly:

```bash
./verify_stack_health.sh
```

This script checks:
- LibreChat API availability
- Ollama API availability
- MCP Server availability
- Loaded models in Ollama
- System resource usage (memory and GPU)

The results are saved to `stack-health-report.txt` for review.

## Setting Up Monitoring

### Automated Health Checks

You can set up automated health checks using cron:

```bash
# Edit crontab
crontab -e

# Add a line to run health check every hour
0 * * * * cd /home/skr/projects/MCP-BASE-STACK && ./verify_stack_health.sh
```

### Log Rotation

To prevent logs from growing too large, set up log rotation:

```bash
# Create a logrotate configuration
sudo nano /etc/logrotate.d/mcp-stack

# Add configuration
/home/skr/projects/MCP-BASE-STACK/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

## Interpreting Logs

### Common Log Patterns

- Connection issues: Look for "connection refused" or timeout errors
- Model loading issues: Check Ollama logs for model loading errors
- API errors: HTTP status codes 4xx or 5xx indicate client or server errors
- Resource constraints: Watch for "out of memory" or GPU-related errors

### Using grep for Log Analysis

```bash
# Find error messages
grep -i error mcp_server.log

# Find warnings
grep -i warn mcp_server.log

# Find specific component issues
grep -i "ollama" mcp_server.log