from agent.state.task_state import Task


class BestOfferApplicationWorkflow:
    def can_handle(self, goal: str) -> bool:
        lower_goal = goal.lower()

        return (
            "prepare best offer application" in lower_goal
            or "apply to best offer" in lower_goal
            or "create application for best offer" in lower_goal
        )

    def create_tasks(self, goal: str):
        return [
            Task(
                title="Rank local job offers",
                description="Rank local job offers against the candidate profile.",
                inputs=[],
                outputs=[],
                tool_hint="subworkflow",
                kind="normal",
                action={
                    "tool": "subworkflow",
                    "goal": "rank job offers",
                    "reason": "Rank all local job offers before selecting the best one.",
                },
            ),

            Task(
                title="Select top-ranked offer",
                description="Set the best-ranked offer as the active job posting.",
                inputs=[],
                outputs=[],
                tool_hint="subworkflow",
                kind="normal",
                action={
                    "tool": "subworkflow",
                    "goal": "select top offer",
                    "reason": "Select the top-ranked offer and write it to job_posting.md.",
                },
            ),

            Task(
                title="Create application for selected offer",
                description="Generate the full application package for the active job posting.",
                inputs=[],
                outputs=[],
                tool_hint="subworkflow",
                kind="normal",
                action={
                    "tool": "subworkflow",
                    "goal": "create a job application for this internship",
                    "reason": (
                        "Create cover letter, CV, PDFs, and final package index "
                        "for the selected offer."
                    ),
                },
            ),
        ]