from pathlib import Path
from agent.tools.base import Tool

class FileTool(Tool):
    name = "file"

    def run(self, action: str, path: str, content: str | None = None):
        p = Path(path)

        if action == "read":
            return {"ok": True, "content": p.read_text(encoding="utf-8")}

        if action == "write":
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content or "", encoding="utf-8")
            return {"ok": True, "path": str(p)}

        if action == "exists":
            return {"ok": True, "exists": p.exists()}

        raise ValueError(f"Unknown file action: {action}")
