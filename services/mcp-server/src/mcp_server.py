import subprocess
import sys
import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

# Add the project root to the Python path to allow importing from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from core.logging.config import configure_logger

# Setup logging using the standardized logging system
logger = configure_logger("mcp_server")
logger.info("MCP Server starting up")

app = FastAPI(title="MINTYcoder MCP Server")

# Define request and response data models
class InferRequest(BaseModel):
    prompt: str

class InferResponse(BaseModel):
    answer: str
    tool_output: Optional[str] = None

# Agent logic: analyze prompt for special commands (very basic for demonstration)
def process_prompt(prompt: str):
    prompt_stripped = prompt.strip()
    logger.info(f"Processing prompt: {prompt_stripped[:50]}...")
    
    # If prompt starts with "!shell", treat the rest as a shell command
    if prompt_stripped.startswith("!shell"):
        command = prompt_stripped[len("!shell"):].strip()
        if command:
            try:
                logger.info(f"Executing shell command: {command}")
                # Execute shell command and capture output
                result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, timeout=60)
                return None, result.stdout[:1000]  # return tool output (truncated if long)
            except subprocess.CalledProcessError as e:
                logger.error(f"Shell command failed: {e}")
                return None, f"Error: {e.stderr[:200]}"
        else:
            return None, "Error: No command provided."
    # Otherwise, no tool invocation, treat entire prompt as LLM query
    return prompt, None

@app.post("/mcp/infer", response_model=InferResponse)
def mcp_infer(request: InferRequest):
    """
    Main inference endpoint: takes a prompt and either handles it via tools or LLM.
    """
    user_prompt = request.prompt
    llm_query, tool_output = process_prompt(user_prompt)
    
    if llm_query is not None:
        # Query the DeepSeek LLM via Ollama
        payload = {"model": "deepseek-coder:6.7b", "prompt": llm_query}
        try:
            logger.info(f"Querying DeepSeek model with prompt length: {len(llm_query)}")
            res = requests.post("http://localhost:11434/api/generate", json=payload, timeout=120)
            res.raise_for_status()
            # Ollama returns streamed responses; we'll take the final output
            answer_text = res.text.strip()
            logger.info(f"Got response from DeepSeek, length: {len(answer_text)}")
            return {"answer": answer_text}
        except Exception as e:
            logger.error(f"LLM inference error: {str(e)}")
            answer_text = f"LLM inference error: {str(e)}"
            return {"answer": answer_text}
    else:
        # If a shell command was executed, return its output instead of LLM answer
        logger.info(f"Returning shell command output, length: {len(tool_output or '')}")
        return {"answer": "Command executed.", "tool_output": tool_output}

# Add debugging endpoints
@app.get("/debug/health")
def health_check():
    """
    Health check endpoint to verify the server is running
    """
    import time
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/debug/ollama-status")
async def check_ollama_connection():
    """
    Debug endpoint to check connection to Ollama server
    """
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        response.raise_for_status()
        models = response.json().get("models", [])
        return {
            "status": "connected",
            "api_status": response.status_code,
            "models_available": models
        }
    except Exception as e:
        logger.error(f"Ollama connection check failed: {str(e)}")
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error_details": str(e)
        }

@app.get("/debug/system-info")
def system_info():
    """
    Returns system information for debugging
    """
    import platform
    import os
    return {
        "hostname": platform.node(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "environment_vars": {k: v for k, v in os.environ.items() if k.startswith(("MCP_", "OLLAMA_"))},
        "working_directory": os.getcwd()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)