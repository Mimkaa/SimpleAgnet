from __future__ import annotations

import re

from agent.state.task_state import Task


class SetTargetProjectWorkflow:
    """
    Set one folder inside target_projects/ as the active target project.

    Example goals:
    - set target project PacketGuard
    - use target project PacketGuard
    - set current target project to PacketGuard
    """

    keywords = [
        "set target project",
        "use target project",
        "set current target project",
        "switch target project",
    ]

    def can_handle(self, goal: str) -> bool:
        lower_goal = goal.lower()
        return any(keyword in lower_goal for keyword in self.keywords)

    def _extract_project_name(self, goal: str) -> str:
        patterns = [
            r"set current target project to\s+([A-Za-z0-9_.-]+)",
            r"set target project to\s+([A-Za-z0-9_.-]+)",
            r"set target project\s+([A-Za-z0-9_.-]+)",
            r"use target project\s+([A-Za-z0-9_.-]+)",
            r"switch target project to\s+([A-Za-z0-9_.-]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, goal, re.IGNORECASE)
            if match:
                return match.group(1)

        return ""

    def create_tasks(self, goal: str):
        project_name = self._extract_project_name(goal)

        return [
            Task(
                title="Set active target project",
                description=(
                    "Set a folder inside target_projects/ as the active target project "
                    "by writing a local override file used by the agent config."
                ),
                inputs=[],
                outputs=["set_target_project_result.md"],
                tool_hint="set_target_project",
                kind="normal",
                action={
                    "tool": "set_target_project",
                    "project_name": project_name,
                    "destination_root": "target_projects",
                    "reason": "Set a cloned repository as the active target project.",
                },
            ),
            Task(
                title="Verify active target project",
                description="Verify which target project the agent config now resolves.",
                inputs=["set_target_project_result.md"],
                outputs=["target_project_verify_result.md"],
                tool_hint="shell",
                kind="normal",
                action={
                    "tool": "shell",
                    "cwd": "agent_repo",
                    "command": (
                        "python -c \"from agent.config import load_config; "
                        "cfg=load_config(); "
                        "print('TARGET_PROJECT_DIR=', cfg.TARGET_PROJECT_DIR); "
                        "print('exists=', cfg.TARGET_PROJECT_DIR.exists())\""
                    ),
                    "outputs": ["target_project_verify_result.md"],
                    "reason": "Verify that load_config now points at the selected target project.",
                },
            ),
        ]
