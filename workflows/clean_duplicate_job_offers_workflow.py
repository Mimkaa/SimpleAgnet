from agent.state.task_state import Task


class CleanDuplicateJobOffersWorkflow:
    def can_handle(self, goal: str) -> bool:
        lower_goal = goal.lower()

        return (
            "clean duplicate job offers" in lower_goal
            or "find duplicate job offers" in lower_goal
            or "deduplicate job offers" in lower_goal
            or "duplicate job offer report" in lower_goal
        )

    def create_tasks(self, goal: str):
        return [
            Task(
                title="Inspect local job offers for duplicates",
                description=(
                    "Read all local job offer files so possible duplicates can be detected."
                ),
                inputs=[],
                outputs=["duplicate_job_offers_context.md"],
                tool_hint="source_snapshot",
                kind="normal",
                action={
                    "tool": "source_snapshot",
                    "root": "target_project",
                    "files": [],
                    "patterns": ["job_offers/*.md", "job_offers/*.txt"],
                    "exclude_files": [],
                    "exclude_patterns": [
                        "generated_*",
                        "*_verification.md",
                        "repair_report_*.md",
                    ],
                    "outputs": ["duplicate_job_offers_context.md"],
                    "reason": (
                        "Read all local job offer files from the target project. "
                        "This workflow is report-only and must not delete, rename, archive, "
                        "or modify any offer files. "
                        f"Original user goal: {goal}"
                    ),
                },
            ),

            Task(
                title="Create duplicate job offers report",
                description=(
                    "Analyze local job offers and report likely duplicates without modifying files."
                ),
                inputs=["duplicate_job_offers_context.md"],
                outputs=["duplicate_job_offers_report.md"],
                tool_hint="artifact_transform",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": ["duplicate_job_offers_context.md"],
                    "outputs": ["duplicate_job_offers_report.md"],
                    "critical": True,
                    "strip_fences": True,
                    "reason": (
                        "Create a report identifying likely duplicate job offer files. "
                        "Use only facts from the input artifact. "
                        "Do not delete, rename, archive, or modify any files. "
                        "Group offers that appear to describe the same job. "
                        "Compare position title, company, location, requirements, responsibilities, salary, "
                        "application email, and repeated wording. "
                        "For each duplicate group, include: files, reason they appear duplicated, "
                        "which one should likely be kept, and which ones could be archived later. "
                        "If no duplicates are found, say so clearly. "
                        "Do not invent files. "
                        "Do not recommend automatic deletion."
                    ),
                },
            ),

            Task(
                title="Canonicalize duplicate job offers report",
                description=(
                    "Rewrite the duplicate job offers report into a stable canonical structure."
                ),
                inputs=["duplicate_job_offers_report.md"],
                outputs=["duplicate_job_offers_canonical_report.md"],
                tool_hint="artifact_transform",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": ["duplicate_job_offers_report.md"],
                    "outputs": ["duplicate_job_offers_canonical_report.md"],
                    "critical": True,
                    "strip_fences": True,
                    "reason": (
                        "Rewrite the duplicate job offers report into a stable canonical markdown structure. "
                        "Use only facts from the input report. "
                        "Output only markdown content, no explanations and no code fences. "

                        "The output MUST use exactly these headings:\n\n"
                        "# Duplicate Job Offers Report\n\n"
                        "## Summary\n"
                        "<brief summary of whether duplicates were found>\n\n"
                        "## Duplicate Groups\n"
                        "<groups of likely duplicate offers, or 'No duplicate groups found.'>\n\n"
                        "## Files Recommended to Keep\n"
                        "<files that should likely be kept, or 'Manual review required.'>\n\n"
                        "## Files Recommended to Archive Later\n"
                        "<files that could be archived later, or 'None.'>\n\n"
                        "## Safe Next Step\n"
                        "<one safe next step. This must be report-only and must not recommend automatic deletion.>\n\n"

                        "Do not invent files. "
                        "Do not recommend deletion. "
                        "If uncertain, recommend manual review."
                    ),
                },
            ),

            Task(
                title="Write duplicate job offers report to target project",
                description=(
                    "Write the canonical duplicate job offers report into the target project folder."
                ),
                inputs=["duplicate_job_offers_canonical_report.md"],
                outputs=["duplicate_job_offers_write_result.md"],
                tool_hint="shell",
                kind="normal",
                action={
                    "tool": "shell",
                    "command": (
                        "python -c \""
                        "from pathlib import Path; "
                        "artifact=Path(r'C:\\Users\\illa9\\Downloads\\minimal_agent_repo\\minimal_agent_repo\\.agent_data\\artifacts\\duplicate_job_offers_canonical_report.md'); "
                        "target=Path('duplicate_job_offers_report.md'); "
                        "text=artifact.read_text(encoding='utf-8').strip(); "
                        "required=['# Duplicate Job Offers Report','## Summary','## Duplicate Groups','## Files Recommended to Keep','## Files Recommended to Archive Later','## Safe Next Step']; "
                        "missing=[h for h in required if h not in text]; "
                        "canonical=('# Duplicate Job Offers Report\\n\\n'"
                        "+'## Summary\\nManual review required. The AI-generated report did not fully follow the canonical structure.\\n\\n'"
                        "+'## Duplicate Groups\\nSee Additional Details below.\\n\\n'"
                        "+'## Files Recommended to Keep\\nManual review required.\\n\\n'"
                        "+'## Files Recommended to Archive Later\\nManual review required. Do not archive automatically.\\n\\n'"
                        "+'## Safe Next Step\\nReview the duplicate groups manually before archiving or deleting any job offer files.\\n'); "
                        "final_text=text if not missing else canonical+'\\n\\n## Additional Details\\n\\n'+text; "
                        "missing2=[h for h in required if h not in final_text]; "
                        "assert not missing2, f'Final duplicate report missing required headings: {missing2}'; "
                        "target.write_text(final_text+'\\n', encoding='utf-8'); "
                        "print('target=', target); "
                        "print('chars=', len(final_text)); "
                        "print('wrapped=', bool(missing)); "
                        "raise SystemExit(0 if target.exists() and len(final_text.strip()) > 0 else 1)"
                        "\""
                    ),
                    "outputs": ["duplicate_job_offers_write_result.md"],
                    "reason": (
                        "Write the duplicate report with deterministic canonical headings. "
                        "If the AI canonical report is missing required headings, wrap it in a safe canonical structure."
                    ),
                },
            ),

            Task(
                title="Verify duplicate job offers report",
                description=(
                    "Verify that the duplicate job offers report exists and has the canonical structure."
                ),
                inputs=["duplicate_job_offers_write_result.md"],
                outputs=["duplicate_job_offers_verification.md"],
                tool_hint="verify_target_file",
                kind="normal",
                action={
                    "tool": "verify_target_file",
                    "root": "target_project",
                    "target_file": "duplicate_job_offers_report.md",
                    "must_contain": [
                        "# Duplicate Job Offers Report",
                        "## Summary",
                        "## Duplicate Groups",
                        "## Files Recommended to Keep",
                        "## Files Recommended to Archive Later",
                        "## Safe Next Step",
                    ],
                    "outputs": ["duplicate_job_offers_verification.md"],
                    "reason": (
                        "Confirm that the duplicate job offers report was written with the canonical headings."
                    ),
                },
            ),
        ]