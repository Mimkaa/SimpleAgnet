import json
from pathlib import Path
from agent.state.task_state import Task

class TaskStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def _load(self):
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return [Task.from_dict(item) for item in data]

    def _save(self, tasks):
        self.path.write_text(
            json.dumps([t.to_dict() for t in tasks], indent=2),
            encoding="utf-8"
        )

    def add_tasks(self, new_tasks):
        tasks = self._load()
        tasks.extend(new_tasks)
        self._save(tasks)

    def list_tasks(self):
        return self._load()

    def next_pending(self):
        for task in self._load():
            if task.status == "pending":
                return task
        return None

    def update_status(self, task_id, status):
        tasks = self._load()
        for task in tasks:
            if task.id == task_id:
                task.status = status
                self._save(tasks)
                return task
        raise ValueError(f"Task not found: {task_id}")
