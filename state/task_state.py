from dataclasses import dataclass, field, asdict
from datetime import datetime
from uuid import uuid4
from typing import Literal

TaskStatus = Literal["pending", "running", "done", "failed"]


@dataclass
class Task:
    title: str
    description: str = ""
    status: TaskStatus = "pending"
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Generic architecture fields
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    tool_hint: str | None = None
    action: dict = field(default_factory=dict)

    # Task role/type
    # normal = regular task
    # repair = task created to investigate/fix a failed task
    # test = temporary/internal test task
    kind: str = "normal"

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data):
        return Task(**data)