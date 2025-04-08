# Resource Management

This guide explains how to monitor and manage system resources for the MCP-BASE-STACK.

## GPU Monitoring

Monitor GPU usage with the following commands:

```bash
# Basic GPU information
nvidia-smi

# Continuous monitoring (updates every second)
watch -n 1 nvidia-smi

# Detailed GPU statistics
nvidia-smi --query-compute-apps=pid,used_memory --format=csv

# Monitor GPU utilization over time
nvidia-smi dmon -i 0 -s u
```

## Memory Management

Monitor system memory usage:

```bash
# View memory usage
free -h

# Monitor memory usage over time
watch -n 5 free -h

# Check memory usage of Docker containers
docker stats
```

## Managing Resources

When not actively using the stack, you can stop components to free resources:

```bash
# Stop Ollama (frees GPU memory)
docker stop ollama

# Stop LibreChat stack
cd LibreChat
docker compose down

# Stop MCP Server
kill $(cat mcp_server.pid)
```

To restart the complete stack, use the restart script or follow the original deployment steps in sequence:

```bash
# Using the restart script
./restart-stack.sh

# Or manually restart components in the correct order
cd LibreChat
docker compose up -d
cd ..
docker start ollama
./start-mcp-server.sh
```

## Resource Optimization

### GPU Memory Optimization

If you're experiencing GPU memory issues:

1. Use smaller model variants when possible
2. Adjust model parameters to reduce memory usage:
   ```bash
   # Example: Reduce context size for Ollama models
   ollama run mistral --contextsize 2048
   ```
3. Consider running only one model at a time

### System Resource Limits

You can set resource limits for Docker containers:

```bash
# Restart Ollama with memory limits
docker run -d --gpus=all --name ollama \
  --memory=8g --memory-swap=10g \
  --network LibreChat_default \
  -v ollama:/root/.ollama \
  -p 11434:11434 \
  ollama/ollama:latest
```

## Troubleshooting Resource Issues

### Common GPU Issues

- **CUDA out of memory**: Reduce batch size or model size
- **GPU not detected**: Check NVIDIA drivers and Docker GPU runtime
- **Slow inference**: Check for thermal throttling with `nvidia-smi dmon`

### Common Memory Issues

- **Container OOM (Out of Memory)**: Increase container memory limits
- **System OOM**: Add swap space or reduce concurrent workloads
- **Memory leaks**: Restart services periodically to reclaim memory