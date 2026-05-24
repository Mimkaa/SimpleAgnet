from agent.state.task_state import Task


class JobOfferRankingWorkflow:
    def can_handle(self, goal: str) -> bool:
        lower_goal = goal.lower()

        return (
            "rank job offers" in lower_goal
            or "rank jobs" in lower_goal
            or "compare job offers" in lower_goal
            or "compare jobs" in lower_goal
            or "which job should i apply" in lower_goal
            or "which offer should i apply" in lower_goal
        )

    def create_tasks(self, goal: str):
        return [
            Task(
                title="Inspect local job offers",
                description=(
                    "Read local job offer files from the target project and collect them "
                    "into a source snapshot."
                ),
                inputs=[],
                outputs=["job_offer_inventory.md"],
                tool_hint="source_snapshot",
                kind="normal",
                action={
                    "tool": "source_snapshot",
                    "root": "target_project",
                    "files": [
                        "cv.md",
                        "profile.md",
                        "candidate_profile.md",
                    ],
                    "patterns": [
                        "job_offers/*.md",
                        "job_offers/*.txt",
                    ],
                    "exclude_files": [],
                    "exclude_patterns": [
                        "generated_*",
                        "*_verification.md",
                        "application_package.md",
                        "final_application_package.md",
                        "cover_letter.*",
                        "tailored_cv.*",
                        "repair_report_*.md",
                        "job_offer_ranking.md",
                    ],
                    "outputs": ["job_offer_inventory.md"],
                    "reason": (
                        "Collect candidate profile/CV information and all local job offers "
                        "from the target project. Read only local files. Missing expected "
                        "candidate files should be reported clearly. "
                        f"Original user goal: {goal}"
                    ),
                },
            ),

            Task(
                title="Extract job offer summaries",
                description=(
                    "Extract structured summaries for each job offer and the candidate profile."
                ),
                inputs=["job_offer_inventory.md"],
                outputs=["job_offer_summaries.md"],
                tool_hint="artifact_transform",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": ["job_offer_inventory.md"],
                    "outputs": ["job_offer_summaries.md"],
                    "reason": (
                        "Create structured summaries of all job offers and the candidate profile. "
                        "Use only facts from the input inventory. "
                        "For each offer, include: file name, position, company, location, main tasks, "
                        "required skills, nice-to-have skills, student/internship fit, missing information, "
                        "and possible concerns. "
                        "Also summarize the candidate's available skills, projects, education, and constraints. "
                        "Do not invent company facts, requirements, candidate experience, or missing details."
                    ),
                },
            ),

            Task(
                title="Rank job offers against candidate profile",
                description=(
                    "Rank the local job offers by fit against the candidate profile."
                ),
                inputs=[
                    "job_offer_inventory.md",
                    "job_offer_summaries.md",
                ],
                outputs=["job_offer_ranking.md"],
                tool_hint="artifact_transform",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": [
                        "job_offer_inventory.md",
                        "job_offer_summaries.md",
                    ],
                    "outputs": ["job_offer_ranking.md"],
                    "reason": (
                        "Rank the job offers by fit for the candidate. "
                        "Use only facts from the input artifacts. "
                        "Create a clear ranking from best to weakest match. "
                        "For each offer include: rank, offer file name, position, company, match score from 0 to 100, "
                        "why it fits, missing requirements, risks, and recommended application strategy. "
                        "Prefer offers that match the candidate's real Java, Python, JavaFX, Git, client-server, "
                        "debugging, documentation, internal tools, and student/internship profile. "
                        "Penalize offers requiring unsupported professional experience, unrelated technologies, "
                        "unknown location constraints, or claims that would require inventing experience. "
                        "Include a final section named 'Recommended next application' with the single best offer. "
                        "Do not invent facts. Do not suggest lying. Use strong but honest framing."
                    ),
                },
            ),

            Task(
                title="Write job offer ranking to target project",
                description=(
                    "Write the generated job offer ranking report into the target project folder."
                ),
                inputs=["job_offer_ranking.md"],
                outputs=[],
                tool_hint="materialize_artifact",
                kind="normal",
                action={
                    "tool": "materialize_artifact",
                    "input": "job_offer_ranking.md",
                    "root": "target_project",
                    "target_file": "job_offer_ranking.md",
                    "reason": (
                        "Materialize the job offer ranking report into the target project folder."
                    ),
                },
            ),
        ]