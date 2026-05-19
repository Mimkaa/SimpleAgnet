from agent.state.task_state import Task


class JobApplicationWorkflow:
    def can_handle(self, goal: str) -> bool:
        lower_goal = goal.lower()

        return (
            "job application" in lower_goal
            or "apply to job" in lower_goal
            or "cover letter" in lower_goal
            or "resume" in lower_goal
            or "cv" in lower_goal
        )

    def create_tasks(self, goal: str):
        return [
            Task(
                title="Create job application readiness report",
                description=(
                    "Check what job-application inputs are available and identify "
                    "what is missing before drafting application materials."
                ),
                inputs=[],
                outputs=["job_application_readiness_report.md"],
                tool_hint="artifact_transform",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": [],
                    "outputs": ["job_application_readiness_report.md"],
                    "reason": (
                        "Create a readiness report for the job application request. "
                        "Do not invent missing job description, CV, resume, or candidate profile details."
                    ),
                },
            )
        ]