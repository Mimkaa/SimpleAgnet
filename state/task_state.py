from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from uuid import uuid4
from typing import Literal

TaskStatus = Literal["pending", "running", "done", "failed"]


@dataclass
class Task:
    title: str
    description: str = ""
    status: TaskStatus = "pending"
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    tool_hint: str | None = None
    action: dict = field(default_factory=dict)

    kind: str = "normal"

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data):
        return Task(**data)