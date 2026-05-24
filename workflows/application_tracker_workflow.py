from agent.state.task_state import Task


class ApplicationTrackerWorkflow:
    def can_handle(self, goal: str) -> bool:
        lower_goal = goal.lower()

        return (
            "update application tracker" in lower_goal
            or "update applications tracker" in lower_goal
            or "track application" in lower_goal
            or "track job application" in lower_goal
        )

    def create_tasks(self, goal: str):
        return [
            Task(
                title="Inspect application tracker inputs",
                description=(
                    "Read the active job posting and generated application package files "
                    "needed to update the application tracker."
                ),
                inputs=[],
                outputs=["application_tracker_context.md"],
                tool_hint="source_snapshot",
                kind="normal",
                action={
                    "tool": "source_snapshot",
                    "root": "target_project",
                    "files": [
                        "job_posting.md",
                        "application_package.md",
                        "final_application_package.md",
                        "job_application_final_review.md",
                        "applications_tracker.md",
                    ],
                    "patterns": [],
                    "exclude_files": [],
                    "exclude_patterns": [],
                    "outputs": ["application_tracker_context.md"],
                    "reason": (
                        "Collect the active job posting, final package information, review notes, "
                        "and existing applications tracker if present. Missing tracker file is allowed "
                        "because it may need to be created. "
                        f"Original user goal: {goal}"
                    ),
                },
            ),

            Task(
                title="Create application tracker entry",
                description=(
                    "Create one tracker entry for the prepared application."
                ),
                inputs=["application_tracker_context.md"],
                outputs=["application_tracker_entry.md"],
                tool_hint="artifact_transform",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": ["application_tracker_context.md"],
                    "outputs": ["application_tracker_entry.md"],
                    "reason": (
                        "Create one concise application tracker entry from the active job posting "
                        "and final application package context. "
                        "Use only facts from the input artifact. "
                        "The entry should be a markdown table row with columns: "
                        "Company, Position, Status, Source, Files, Notes. "
                        "Status should be 'prepared'. "
                        "Files should mention generated files if present, such as cover_letter.pdf, "
                        "tailored_cv.pdf, final_application_package.md, and application_package.md. "
                        "If source offer file is unknown, use 'unknown'. "
                        "Do not invent application submission status, dates, contacts, links, or responses. "
                        "Output only one markdown table row, no table header and no explanations."
                    ),
                },
            ),

            Task(
                title="Write application tracker to target project",
                description=(
                    "Create or append the application tracker entry to applications_tracker.md."
                ),
                inputs=["application_tracker_entry.md"],
                outputs=["applications_tracker_update_result.md"],
                tool_hint="shell",
                kind="normal",
                action={
                    "tool": "shell",
                    "command": (
                        "python -c \""
                        "from pathlib import Path; "
                        "tracker=Path('applications_tracker.md'); "
                        "entry_path=Path(r'C:\\Users\\illa9\\Downloads\\minimal_agent_repo\\minimal_agent_repo\\.agent_data\\artifacts\\application_tracker_entry.md'); "
                        "entry=entry_path.read_text(encoding='utf-8').strip(); "
                        "header='| Company | Position | Status | Source | Files | Notes |\\n'; "
                        "sep='|---|---|---|---|---|---|\\n'; "
                        "existing=tracker.read_text(encoding='utf-8') if tracker.exists() else ''; "
                        "base=existing.strip(); "
                        "prefix='# Applications Tracker\\n\\n'+header+sep; "
                        "new_text=(existing if entry in existing else ((prefix if not base else existing.rstrip()+'\\n')+entry+'\\n')); "
                        "tracker.write_text(new_text, encoding='utf-8'); "
                        "print('tracker=', tracker); "
                        "print('entry_path=', entry_path); "
                        "print('entry_chars=', len(entry)); "
                        "print('updated=', True); "
                        "raise SystemExit(0 if tracker.exists() and entry else 1)"
                        "\""
                    ),
                    "outputs": ["applications_tracker_update_result.md"],
                    "reason": (
                        "Append the generated tracker row to applications_tracker.md, creating the file "
                        "with a standard header if it does not exist."
                    ),
                },
            ),

            Task(
                title="Verify application tracker",
                description=(
                    "Verify that applications_tracker.md exists and has the expected structure."
                ),
                inputs=["applications_tracker_update_result.md"],
                outputs=["applications_tracker_verification.md"],
                tool_hint="verify_target_file",
                kind="normal",
                action={
                    "tool": "verify_target_file",
                    "root": "target_project",
                    "target_file": "applications_tracker.md",
                    "must_contain": [
                        "# Applications Tracker",
                        "| Company | Position | Status | Source | Files | Notes |",
                        "prepared",
                    ],
                    "outputs": ["applications_tracker_verification.md"],
                    "reason": (
                        "Confirm that the application tracker was created or updated."
                    ),
                },
            ),
        ]