class RepoFixWorkflow:
    def can_handle(self, goal: str) -> bool:
        return any(k in goal.lower() for k in ["fix repo", "build error", "gradle", "compile"])

    def create_tasks(self, goal: str):
        return []
