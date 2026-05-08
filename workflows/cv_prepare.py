class CvPrepareWorkflow:
    def can_handle(self, goal: str) -> bool:
        return any(k in goal.lower() for k in ["cv", "resume", "cover letter", "job"])

    def create_tasks(self, goal: str):
        return []
