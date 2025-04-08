import logging
import time
import platform
import os
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
import requests

# Import dependency injection container
from temp.di.containers import Container
from temp.services.prompt_processor import PromptProcessor
from temp.services.example_service import ExampleService

# Create and configure the DI container
container = Container()
container.init_resources()

# Get logger from container
logger = container.logger()
logger.info("MCP Server starting up with dependency injection")

# Create FastAPI app
app = FastAPI(title="MINTYcoder MCP Server")

# Register container with FastAPI
app.container = container

# Define request and response data models
class InferRequest(BaseModel):
    prompt: str

class InferResponse(BaseModel):
    answer: str
    tool_output: Optional[str] = None

# Dependency to get the prompt processor service
def get_prompt_processor() -> PromptProcessor:
    return container.prompt_processor()

# Dependency to get the LLM client
def get_llm_client():
    return container.llm_client()

# Dependency to get the example service
def get_example_service() -> ExampleService:
    return container.example_service()

@app.post("/mcp/infer", response_model=InferResponse)
def mcp_infer(
    request: InferRequest,
    prompt_processor: PromptProcessor = Depends(get_prompt_processor),
    llm_client = Depends(get_llm_client)
):
    """
    Main inference endpoint: takes a prompt and either handles it via tools or LLM.
    """
    user_prompt = request.prompt
    llm_query, tool_output = prompt_processor.process(user_prompt)
    
    if llm_query is not None:
        # Query the LLM using the injected LLM client
        try:
            answer_text = llm_client.generate(llm_query)
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
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/debug/llm-server-status")
async def check_llm_connection(llm_client = Depends(get_llm_client)):
    """
    Debug endpoint to check connection to LLM Server
    """
    return llm_client.check_connection()

@app.get("/debug/system-info")
def system_info():
    """
    Returns system information for debugging
    """
    config = container.config()
    return {
        "hostname": platform.node(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "environment_vars": {k: v for k, v in os.environ.items() if k.startswith(("MCP_", "LLM_SERVER_"))},
        "working_directory": os.getcwd(),
        "config": config
    }
# Example endpoint that demonstrates the use of the example service
@app.get("/example/info")
def example_info(example_service: ExampleService = Depends(get_example_service)):
    """
    Example endpoint that demonstrates dependency injection.
    
    This endpoint uses the ExampleService which is injected via dependency injection.
    """
    return example_service.get_service_info()

@app.post("/example/process")
def example_process(data: str, example_service: ExampleService = Depends(get_example_service)):
    """
    Example endpoint that processes data using the example service.
    
    Args:
        data: Input data to process
        
    Returns:
        str: Processed data
    """
    return {"result": example_service.process_data(data)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    uvicorn.run(app, host="0.0.0.0", port=8000)