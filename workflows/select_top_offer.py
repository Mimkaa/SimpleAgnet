from agent.state.task_state import Task


class SelectTopOfferWorkflow:
    def can_handle(self, goal: str) -> bool:
        lower_goal = goal.lower()

        return (
            "select top offer" in lower_goal
            or "select best offer" in lower_goal
            or "use top ranked offer" in lower_goal
            or "use best ranked offer" in lower_goal
            or "prepare best offer application" in lower_goal
        )

    def create_tasks(self, goal: str):
        return [
            Task(
                title="Inspect job offer ranking",
                description=(
                    "Read the job offer ranking report and available local job offers."
                ),
                inputs=[],
                outputs=["top_offer_selection_context.md"],
                tool_hint="source_snapshot",
                kind="normal",
                action={
                    "tool": "source_snapshot",
                    "root": "target_project",
                    "files": [
                        "job_offer_ranking.md",
                        "job_offers/offer_1.md",
                        "job_offers/offer_2.md",
                        "job_offers/offer_3.md",
                    ],
                    "patterns": [],
                    "exclude_files": [],
                    "exclude_patterns": [],
                    "outputs": ["top_offer_selection_context.md"],
                    "reason": (
                        "Read the ranking report and the local job offer files so the best-ranked "
                        "offer can be selected and prepared as the active job posting. "
                        f"Original user goal: {goal}"
                    ),
                },
            ),

            Task(
                title="Create top offer selection report",
                description=(
                    "Create a short report explaining which offer should become the active job posting."
                ),
                inputs=["top_offer_selection_context.md"],
                outputs=["top_offer_selection_report.md"],
                tool_hint="artifact_transform",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": ["top_offer_selection_context.md"],
                    "outputs": ["top_offer_selection_report.md"],
                    "critical": True,
                    "strip_fences": True,
                    "reason": (
                        "Create a short top-offer selection report. "
                        "Use only the ranking report and local offer files. "
                        "Identify the best-ranked offer from job_offer_ranking.md. "
                        "Include the selected offer file path, position, company, and why it was selected. "
                        "Do not invent facts. "
                        "The current expected selected offer is job_offers/offer_2.md if it is ranked first."
                    ),
                },
            ),

            Task(
                title="Set top-ranked offer as active job posting",
                description=(
                    "Copy the best-ranked job offer into job_posting.md so the application workflow can use it."
                ),
                inputs=["top_offer_selection_report.md"],
                outputs=["active_job_posting_selection.md"],
                tool_hint="shell",
                kind="normal",
                action={
                    "tool": "shell",
                    "command": (
                        "python -c \""
                        "from pathlib import Path; "
                        "import re; "
                        "ranking_path=Path('job_offer_ranking.md'); "
                        "offers_dir=Path('job_offers'); "
                        "dst=Path('job_posting.md'); "
                        "ranking=ranking_path.read_text(encoding='utf-8'); "
                        "rows=[line for line in ranking.splitlines() if re.match(r'^\\|\\s*1\\s*\\|', line)]; "
                        "assert rows, 'Could not find rank 1 row in job_offer_ranking.md'; "
                        "top_line=rows[0]; "
                        "cells=[c.strip() for c in top_line.strip().strip('|').split('|')]; "
                        "assert len(cells) >= 3, f'Rank 1 row has unexpected format: {top_line}'; "
                        "offer_files=sorted(offers_dir.glob('offer_*.md')); "
                        "assert offer_files, 'No offer files found in job_offers'; "
                        "scores=[("
                        "sum(len(cell.strip().lower()) for cell in cells[1:4] "
                        "if cell.strip() and cell.strip().lower() in p.read_text(encoding='utf-8').lower()), "
                        "p"
                        ") for p in offer_files]; "
                        "best_score, selected=max(scores, key=lambda item: item[0]); "
                        "assert best_score > 0, 'Could not map rank 1 row to an offer file'; "
                        "text=selected.read_text(encoding='utf-8'); "
                        "dst.write_text(text, encoding='utf-8'); "
                        "print('rank_1_row=', top_line); "
                        "print('selected=', selected); "
                        "print('score=', best_score); "
                        "print('written=', dst); "
                        "print('chars=', len(text)); "
                        "raise SystemExit(0 if dst.exists() and len(text) > 0 else 1)"
                        "\""
                    ),
                    "outputs": ["active_job_posting_selection.md"],
                    "reason": (
                        "Read job_offer_ranking.md, detect the offer ranked first, and copy that offer "
                        "into job_posting.md as the active job posting."
                    ),
                },
            ),

            Task(
                title="Verify active job posting",
                description=(
                    "Verify that job_posting.md now contains a valid selected job offer."
                ),
                inputs=["active_job_posting_selection.md"],
                outputs=["active_job_posting_verification.md"],
                tool_hint="verify_target_file",
                kind="normal",
                action={
                    "tool": "verify_target_file",
                    "root": "target_project",
                    "target_file": "job_posting.md",
                    "must_contain": [
                        "## Position",
                        "## Company",
                        "## Location",
                    ],
                    "outputs": ["active_job_posting_verification.md"],
                    "reason": (
                        "Confirm that job_posting.md contains a valid selected job offer structure. "
                        "Use generic section checks instead of hardcoded company-specific text so this works "
                        "for whichever offer is ranked first."
                    ),
                },
            ),
        ]