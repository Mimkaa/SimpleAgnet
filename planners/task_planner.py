from agent.state.task_state import Task

class TaskPlanner:
    def make_tasks(self, goal: str):
        return [
            Task(title="Clarify goal", description=goal),
            Task(title="Identify first concrete action"),
            Task(title="Execute and verify"),
        ]
