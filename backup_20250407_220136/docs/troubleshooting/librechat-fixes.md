# LibreChat Container Fixes

This document contains solutions for common issues with the LibreChat container.

## Container Issues

When LibreChat containers fail to start or run properly, the following steps can help diagnose and fix the issues:

1. Check container status:
   ```bash
   docker ps -a | grep librechat
   ```

2. If the API container is not running but MongoDB is, try starting the API container specifically:
   ```bash
   docker start librechat-api-1
   ```

3. Verify that the Ollama container is running, as LibreChat depends on it:
   ```bash
   docker ps | grep ollama
   ```

4. If needed, restart the LibreChat API with modified configuration:
   ```bash
   docker-compose -f services/librechat/docker-compose.yml up -d api
   ```

## Troubleshooting Steps

1. Check container logs: 
   ```bash
   docker logs librechat-api-1
   ```

2. Verify environment variables are properly set in the `.env` file

3. Ensure volumes are correctly mounted

4. Check API accessibility:
   ```bash
   curl -I http://localhost:3080/
   ```

5. If the API is accessible (HTTP 200 OK), the container is running correctly

## Common Fixes

- If the LibreChat API container fails to start, check if it can connect to MongoDB and Ollama
- Ensure the network settings allow containers to communicate with each other
- Verify that the configuration in `librechat.yaml` is correct, especially the model endpoints
- Check that the MongoDB container is running and accessible at `mongodb:27017`