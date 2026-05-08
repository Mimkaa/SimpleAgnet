import subprocess
from agent.tools.base import Tool

class ShellTool(Tool):
    name = "shell"

    def run(self, command: str, cwd: str | None = None, timeout: int = 30):
        try:
            completed = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                timeout=timeout,
                capture_output=True,
                text=True,
            )
            return {
                "ok": completed.returncode == 0,
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
        except subprocess.TimeoutExpired as e:
            return {
                "ok": False,
                "error": "timeout",
                "stdout": e.stdout or "",
                "stderr": e.stderr or "",
            }
