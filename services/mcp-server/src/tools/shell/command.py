import subprocess
import logging
from typing import Dict, Any
from mcp import tool

logger = logging.getLogger("mcp_server.tools.shell")

@tool(
    name="execute_shell_command",
    description="Execute a shell command on the server",
    inputSchema={
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute"
            },
            "timeout": {
                "type": "integer",
                "description": "Maximum execution time in seconds",
                "default": 60
            }
        },
        "required": ["command"]
    },
    dangerous=True
)
def execute_shell_command(command: str, timeout: int = 60) -> Dict[str, Any]:
    """
    Execute a shell command and return the result
    
    Args:
        command: The shell command to execute
        timeout: Maximum execution time in seconds
        
    Returns:
        Dict[str, Any]: A dictionary containing success status and output/error
    """
    if not command:
        return {
            "success": False,
            "error": "No command provided."
        }
        
    try:
        logger.info(f"Executing shell command: {command}")
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, timeout=timeout)
        return {
            "success": True,
            "output": result.stdout[:1000]  # return tool output (truncated if long)
        }
    except subprocess.CalledProcessError as e:
        logger.error(f"Shell command failed: {e}")
        return {
            "success": False,
            "error": f"Command failed: {e.stderr[:200]}"
        }
    except Exception as e:
        logger.error(f"Shell command execution error: {str(e)}")
        return {
            "success": False,
            "error": f"Execution error: {str(e)}"
        }