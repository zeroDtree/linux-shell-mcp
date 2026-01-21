import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from fastmcp import FastMCP

import hydra
import rootutils
from dotenv import load_dotenv
from omegaconf import DictConfig
import os

rootutils.setup_root(
    search_from=__file__,
    project_root_env_var=True,
    dotenv=True,
    pythonpath=False,
    cwd=False,
)
load_dotenv(override=True)
_config_path = os.path.join(os.environ["PROJECT_ROOT"])


mcp = FastMCP("LinuxShell")


@mcp.tool()
def run_shell_command(
    command: str,
    timeout: Optional[float] = None,
    cwd: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute a shell command on the host system.

    Args:
        command: The shell command to execute.
        timeout: Optional timeout in seconds for the command. If None, no
                 explicit timeout is applied.
        cwd: Optional working directory for the command. If None, the server's
             current working directory is used.

    Returns:
        A dictionary containing:
            - stdout: Captured standard output.
            - stderr: Captured standard error.
            - returncode: Process return code (None on timeout/error before start).
            - timeout: Whether the command timed out.
            - error: Optional error message when exceptions occur.
    """
    effective_cwd = cwd or str(Path.cwd())

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=effective_cwd,
        )

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "timeout": False,
        }

    except subprocess.TimeoutExpired as e:
        return {
            "stdout": e.stdout or "",
            "stderr": e.stderr or "",
            "returncode": None,
            "timeout": True,
            "error": f"Command timeout: {command}",
        }

    except Exception as e:
        return {
            "stdout": "",
            "stderr": "",
            "returncode": None,
            "timeout": False,
            "error": f"Execution error: {str(e)}",
        }


@hydra.main(version_base=None, config_path=_config_path, config_name="config.yaml")
def main(cfg: DictConfig):
    # stdio transport doesn't need host/port
    if cfg.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(
            transport=cfg.transport,
            host=cfg.get("host", "0.0.0.0"),
            port=cfg.get("port", 8020),
        )


if __name__ == "__main__":
    main()
