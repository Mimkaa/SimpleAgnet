import json
from pathlib import Path
from datetime import datetime

class EventLog:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def write(self, event_type: str, payload: dict):
        event = {
            "time": datetime.utcnow().isoformat(),
            "type": event_type,
            "payload": payload,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

    def tail(self, limit: int = 10):
        lines = self.path.read_text(encoding="utf-8").splitlines()
        return lines[-limit:]
