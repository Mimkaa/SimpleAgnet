from __future__ import annotations

import re

from agent.state.task_state import Task


class CloneRepoWorkflow:
    keywords = [
        "clone repo",
        "clone github repo",
        "clone repository",
        "clone github repository",
    ]

    def can_handle(self, goal: str) -> bool:
        lower_goal = goal.lower()
        return any(keyword in lower_goal for keyword in self.keywords)

    def _extract_github_url(self, goal: str) -> str:
        match = re.search(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?/?", goal)
        return match.group(0) if match else ""

    def create_tasks(self, goal: str):
        repo_url = self._extract_github_url(goal)

        return [
            Task(
                title="Clone GitHub repository",
                description=(
                    "Safely clone the requested GitHub repository into target_projects/. "
                    "Only normal HTTPS GitHub repository URLs are allowed."
                ),
                inputs=[],
                outputs=["clone_repo_result.md"],
                tool_hint="git_clone",
                kind="normal",
                action={
                    "tool": "git_clone",
                    "repo_url": repo_url,
                    "destination_root": "target_projects",
                    "depth": 1,
                    "reason": "Clone a GitHub repository into a controlled local target_projects folder.",
                },
            ),
            Task(
                title="Inspect cloned repositories folder",
                description="List the target_projects folder in the agent repo after cloning.",
                inputs=["clone_repo_result.md"],
                outputs=["target_projects_listing.md"],
                tool_hint="shell",
                kind="normal",
                action={
                    "tool": "shell",
                    "cwd": "agent_repo",
                    "command": (
                        "python -c \"from pathlib import Path; "
                        "root=Path('target_projects'); "
                        "print('exists=', root.exists()); "
                        "print('\\n'.join(str(p) for p in sorted(root.rglob('*'))[:200]) if root.exists() else 'MISSING')\""
                    ),
                    "outputs": ["target_projects_listing.md"],
                    "reason": "Verify that target_projects exists in the agent repo and show a safe limited listing.",
                },
            ),
        ]
