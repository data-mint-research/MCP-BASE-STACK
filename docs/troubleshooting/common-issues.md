# Common Issues and Resolutions

This guide addresses common issues you might encounter with the MCP-BASE-STACK and provides step-by-step solutions.

## Connectivity Issues

### LibreChat can't connect to Ollama

If LibreChat is unable to connect to the Ollama service:

1. Check network connectivity between containers:

```bash
docker exec LibreChat ping -c 3 ollama
```

2. Verify that Ollama is running:

```bash
docker ps | grep ollama
```

3. Check Ollama logs for errors:

```bash
docker logs ollama
```

4. Ensure both containers are on the same Docker network:

```bash
docker network inspect LibreChat_default
```

5. Restart the Ollama container:

```bash
docker restart ollama
```

## Model Issues

### Models not loading in Ollama

If models fail to load in Ollama:

1. Verify model files exist:

```bash
docker exec ollama ls -la /root/.ollama/models
```

2. Check available disk space:

```bash
df -h
```

3. Attempt to pull the model again:

```bash
docker exec ollama ollama pull mistral
```

4. Check Ollama logs for download errors:

```bash
docker logs ollama | grep -i error
```

5. Try removing and re-pulling the model:

```bash
docker exec ollama ollama rm mistral
docker exec ollama ollama pull mistral
```

## Server Issues

### MCP Server fails to start

If the MCP Server fails to start:

1. Check for port conflicts:

```bash
ss -tln | grep 8000
```

2. Verify the server isn't already running:

```bash
ps aux | grep mcp_server.py
```

3. Check the server logs for errors:

```bash
tail -n 50 mcp_server.log
tail -n 50 mcp_debug.log
```

4. Ensure all dependencies are installed:

```bash
pip install -r mcp_requirements.txt
```

5. Try starting the server with debug output:

```bash
python mcp_server.py --debug
```

## GPU Issues

### GPU not accessible in container

If the GPU is not accessible in the container:

1. Verify Docker GPU runtime:

```bash
docker run --rm --gpus=all nvidia/cuda:11.8.0-base nvidia-smi
```

2. Check NVIDIA driver installation:

```bash
nvidia-smi
```

3. Verify the nvidia-container-toolkit is installed:

```bash
dpkg -l | grep nvidia-container-toolkit
```

4. Restart the Docker service:

```bash
sudo systemctl restart docker
```

5. Check Docker daemon configuration:

```bash
cat /etc/docker/daemon.json
```

## LibreChat Configuration Issues

### Custom endpoints not appearing

If custom endpoints are not appearing in LibreChat:

1. Verify librechat.yaml exists in the container:

```bash
docker exec LibreChat ls -la /app/librechat.yaml
```

2. Check the format of the configuration file:

```bash
docker exec LibreChat cat /app/librechat.yaml
```

3. Restart the LibreChat container:

```bash
cd LibreChat
docker compose restart
```

4. Check LibreChat logs for configuration errors:

```bash
cd LibreChat
docker compose logs api | grep -i config
```

## MCP Server Connection Issues

### MCP Server not responding

If the MCP Server is not responding:

1. Check if the server process is running:

```bash
ps aux | grep mcp_server.py
```

2. Verify the server is listening on the expected port:

```bash
curl http://localhost:8000/debug/health
```

3. Check server logs for errors:

```bash
tail -n 50 mcp_server.log
```

4. Restart the server:

```bash
kill $(cat mcp_server.pid)
./start_mcp_server.sh
```

5. Verify connectivity from LibreChat to MCP Server:

```bash
docker exec LibreChat curl -s http://host.docker.internal:8000/debug/health