import subprocess
import logging

logger = logging.getLogger("mcp_server.tools.shell")

def execute_shell_command(command: str, timeout: int = 60):
    """
    Execute a shell command and return the result
    
    Args:
        command: The shell command to execute
        timeout: Maximum execution time in seconds
        
    Returns:
        tuple: (success, output) where success is a boolean and output is the command output or error
    """
    if not command:
        return False, "Error: No command provided."
        
    try:
        logger.info(f"Executing shell command: {command}")
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, timeout=timeout)
        return True, result.stdout[:1000]  # return tool output (truncated if long)
    except subprocess.CalledProcessError as e:
        logger.error(f"Shell command failed: {e}")
        return False, f"Error: {e.stderr[:200]}"
    except Exception as e:
        logger.error(f"Shell command execution error: {str(e)}")
        return False, f"Error: {str(e)}"