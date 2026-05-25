from agent.state.task_state import Task


class CleanBestOfferApplicationWorkflow:
    def can_handle(self, goal: str) -> bool:
        lower_goal = goal.lower()

        return (
            "prepare clean best offer application" in lower_goal
            or "clean best offer application" in lower_goal
            or "prepare cleaned best offer application" in lower_goal
        )

    def create_tasks(self, goal: str):
        return [
            Task(
                title="Clean duplicate job offers",
                description=(
                    "Create a report identifying duplicate job offers before ranking."
                ),
                inputs=[],
                outputs=[],
                tool_hint="subworkflow",
                kind="normal",
                action={
                    "tool": "subworkflow",
                    "goal": "clean duplicate job offers",
                    "reason": (
                        "Before ranking offers, identify likely duplicate job offer files."
                    ),
                },
            ),

            Task(
                title="Archive duplicate job offers",
                description=(
                    "Archive duplicate job offers so only the canonical offers remain active."
                ),
                inputs=[],
                outputs=[],
                tool_hint="subworkflow",
                kind="normal",
                action={
                    "tool": "subworkflow",
                    "goal": "archive duplicate job offers",
                    "reason": (
                        "Archive duplicate offers after the duplicate report has identified the canonical file."
                    ),
                },
            ),

            Task(
                title="Rank cleaned job offers",
                description=(
                    "Rank the cleaned set of job offers against the candidate profile."
                ),
                inputs=[],
                outputs=[],
                tool_hint="subworkflow",
                kind="normal",
                action={
                    "tool": "subworkflow",
                    "goal": "rank job offers",
                    "reason": (
                        "After duplicates are archived, rank the remaining active job offers."
                    ),
                },
            ),

            Task(
                title="Select top cleaned offer",
                description=(
                    "Select the best ranked job offer after cleanup."
                ),
                inputs=[],
                outputs=[],
                tool_hint="subworkflow",
                kind="normal",
                action={
                    "tool": "subworkflow",
                    "goal": "select top offer",
                    "reason": (
                        "Use the cleaned ranking result to select the best offer."
                    ),
                },
            ),

            Task(
                title="Create application for cleaned top offer",
                description=(
                    "Create the application package for the selected top offer."
                ),
                inputs=[],
                outputs=[],
                tool_hint="subworkflow",
                kind="normal",
                action={
                    "tool": "subworkflow",
                    "goal": "create a job application for this internship",
                    "reason": (
                        "Create application materials for the selected top offer after cleanup and ranking."
                    ),
                },
            ),
        ]