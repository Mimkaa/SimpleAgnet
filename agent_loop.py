import json
import re

from typing import List, Optional

from agent.state.task_state import Task
from agent.planners.action_selector import ActionSelector
from agent.planners.verifier import Verifier
from agent.tools.shell_tool import ShellTool
from agent.tools.file_tool import FileTool
from agent.analyzers.openai_artifact_analyzer import OpenAIArtifactAnalyzer
from agent.planners.openai_task_planner import OpenAITaskPlanner


class AgentLoop:
    def __init__(self, task_store, event_log, workflows, artifacts, target_project_dir):
        self.task_store = task_store
        self.event_log = event_log
        self.workflows = workflows
        self.artifacts = artifacts
        self.target_project_dir = target_project_dir

        self.tools = {
            "shell": ShellTool(),
            "file": FileTool(),
        }

        self.selector = ActionSelector()
        self.verifier = Verifier()
        self.artifact_analyzer = OpenAIArtifactAnalyzer()
        self.openai_task_planner = OpenAITaskPlanner()



    def create_goal(self, goal: str) -> List[Task]:
        if goal.lower().startswith("ai plan:"):
            clean_goal = goal[len("ai plan:"):].strip()

            tasks = self.openai_task_planner.create_tasks(
                goal=clean_goal,
                available_tools=[
                    "shell",
                    "artifact_transform",
                    "source_snapshot",
                    "apply_safe_change",
                    "file",
                ],
            )

            self.task_store.add_tasks(tasks)
            self.event_log.write(
                "ai_goal_created",
                {
                    "goal": clean_goal,
                    "tasks": [t.to_dict() for t in tasks],
                },
            )
            return tasks

        for workflow in self.workflows:
            if workflow.can_handle(goal):
                tasks = workflow.create_tasks(goal)
                self.task_store.add_tasks(tasks)
                self.event_log.write(
                    "goal_created",
                    {
                        "goal": goal,
                        "tasks": [t.to_dict() for t in tasks],
                    },
                )
                return tasks

        fallback = self.create_fallback_task_from_goal(goal)

        self.task_store.add_tasks([fallback])
        self.event_log.write(
            "goal_created",
            {
                "goal": goal,
                "tasks": [fallback.to_dict()],
            },
        )
        return [fallback]

    def list_tasks(self):
        return self.task_store.list_tasks()

    def next_task(self) -> Optional[Task]:
        return self.task_store.next_pending()

    def mark_done(self, task_id: str):
        task = self.task_store.update_status(task_id, "done")
        self.event_log.write("task_done", {"task_id": task_id})
        return task

    def mark_failed(self, task_id: str, reason: str = ""):
        task = self.task_store.update_status(task_id, "failed")
        self.event_log.write(
            "task_failed",
            {
                "task_id": task_id,
                "reason": reason,
            },
        )
        return task

    def suggest_next_action(self):
        task = self.next_task()

        if not task:
            return "No pending tasks."

        action = self.selector.select_action(task)

        self.event_log.write(
            "action_suggested",
            {
                "task_id": task.id,
                "action": action,
            },
        )

        return action

    def run_tool(self, tool_name: str, **kwargs):
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        result = self.tools[tool_name].run(**kwargs)

        self.event_log.write(
            "tool_run",
            {
                "tool": tool_name,
                "kwargs": kwargs,
                "result": result,
            },
        )

        return result

    def recent_events(self, limit: int = 10):
        return self.event_log.tail(limit)

    def summarize_project_structure(self, raw_output: str) -> str:
        lines = [
            line.strip()
            for line in raw_output.splitlines()
            if line.strip()
        ]

        normalized = [line.replace("\\", "/") for line in lines]

        candidate_entry_points = []
        source_files = []
        config_files = []
        test_files = []
        data_or_rule_files = []
        docs = []

        for path in normalized:
            lower = path.lower()
            filename = lower.split("/")[-1]

            if filename in ["main.py", "app.py", "run.py", "cli.py"]:
                candidate_entry_points.append(path)

            if lower.endswith(".py"):
                source_files.append(path)

            if filename in [
                "requirements.txt",
                "pyproject.toml",
                "setup.py",
                "setup.cfg",
                "package.json",
                "makefile",
                "dockerfile",
                "docker-compose.yml",
            ]:
                config_files.append(path)

            if "/tests/" in lower or filename.startswith("test_"):
                test_files.append(path)

            if (
                "/rules/" in lower
                or lower.endswith(".json")
                or lower.endswith(".yaml")
                or lower.endswith(".yml")
                or lower.endswith(".toml")
            ):
                data_or_rule_files.append(path)

            if filename.startswith("readme") or lower.endswith(".md"):
                docs.append(path)

        def add_section(summary: list[str], title: str, items: list[str], empty_text: str):
            summary.append(f"## {title}")

            if items:
                for item in items:
                    summary.append(f"- `{item}`")
            else:
                summary.append(f"- {empty_text}")

            summary.append("")

        summary = []
        summary.append("# Project Structure Summary")
        summary.append("")

        add_section(
            summary,
            "Candidate entry points",
            candidate_entry_points,
            "No obvious entry point found.",
        )

        add_section(
            summary,
            "Source files",
            source_files,
            "No source files found.",
        )

        add_section(
            summary,
            "Config / dependency files",
            config_files,
            "No config/dependency files found.",
        )

        add_section(
            summary,
            "Test files",
            test_files,
            "No test files found.",
        )

        add_section(
            summary,
            "Data / rule files",
            data_or_rule_files,
            "No data or rule files found.",
        )

        add_section(
            summary,
            "Documentation",
            docs,
            "No documentation files found.",
        )

        summary.append("## Interpretation")
        summary.append("")
        summary.append("- This summary is based on file names and paths only.")
        summary.append(
            "- Candidate entry points are guessed from common names like `main.py`, `app.py`, `run.py`, and `cli.py`."
        )
        summary.append("- Source-level confirmation requires reading the candidate source files.")
        summary.append("- This summary does not assume the project is an agent project.")

        return "\n".join(summary)

    def maybe_create_artifact(self, task: Task, action: dict, result: dict):
        if action.get("tool") != "shell":
            return None

        command = action.get("command", "")
        outputs = action.get("outputs", task.outputs)

        stdout = result.get("stdout", "")
        stderr = result.get("stderr", "")
        returncode = result.get("returncode")

        if outputs:
            content = [
                "# Shell Command Result",
                "",
                "## Command",
                "",
                "```bash",
                command,
                "```",
                "",
                "## Return code",
                "",
                f"`{returncode}`",
                "",
                "## stdout",
                "",
                "```text",
                stdout,
                "```",
                "",
                "## stderr",
                "",
                "```text",
                stderr,
                "```",
                "",
            ]

            artifact_paths = []

            for output_name in outputs:
                artifact_path = self.artifacts.write_text(
                    output_name,
                    "\n".join(content),
                )
                artifact_paths.append(str(artifact_path))

            self.event_log.write(
                "artifact_created",
                {
                    "task_id": task.id,
                    "artifacts": artifact_paths,
                    "reason": "Saved shell command result to declared output artifact.",
                },
            )

        if result.get("ok") and "dir /s /b" in command:
            raw_artifact_path = self.artifacts.write_text(
                "project_structure_raw.txt",
                stdout,
            )

            summary = self.summarize_project_structure(stdout)

            summary_artifact_path = self.artifacts.write_text(
                "project_structure_summary.md",
                summary,
            )

            self.event_log.write(
                "artifact_created",
                {
                    "task_id": task.id,
                    "artifacts": [
                        str(raw_artifact_path),
                        str(summary_artifact_path),
                    ],
                    "reason": "Saved raw project structure and generated summary.",
                },
            )

            return summary_artifact_path

        return None

    def simple_artifact_analysis(self, task: Task, input_contents: dict, output_name: str) -> str:
        combined_input = "\n\n".join(input_contents.values())

        if output_name.startswith("repair_report_"):
            return (
                "# Repair Report\n\n"
                "## Failed / investigated task\n\n"
                f"{task.title}\n\n"
                "## Failure details\n\n"
                "```text\n"
                f"{task.description}\n"
                "```\n\n"
                "## Smallest safe next step\n\n"
                "- The advanced analyzer failed, so no specific repair was generated.\n"
                "- Run a harmless diagnostic command to confirm the agent can continue.\n\n"
                "## NEXT_ACTION_JSON\n\n"
                "```json\n"
                "{\n"
                '  "title": "Run safe diagnostic after failure",\n'
                '  "description": "Run a harmless command after the failure to confirm the agent can continue.",\n'
                '  "tool_hint": "shell",\n'
                '  "kind": "normal",\n'
                '  "action": {\n'
                '    "tool": "shell",\n'
                '    "command": "py -3 --version",\n'
                '    "outputs": [],\n'
                '    "reason": "Safe diagnostic follow-up after a failed command."\n'
                "  }\n"
                "}\n"
                "```\n"
            )

        if output_name == "entry_point.md":
            if "agent/main.py" in combined_input.replace("\\", "/"):
                return (
                    "# Entry Point\n\n"
                    "Likely entry point:\n\n"
                    "- `agent/main.py`\n\n"
                    "Reason:\n\n"
                    "- The project is run as `python -m agent.main`.\n"
                    "- The file `agent/main.py` initializes config, storage, workflows, the agent loop, and the CLI interface.\n"
                )

            return "# Entry Point\n\nNo obvious entry point found from the available project structure summary.\n"

        if output_name == "core_components.md":
            return (
                "# Core Components\n\n"
                "Based on the project structure summary, the likely core components are:\n\n"
                "- `agent/main.py` — starts the program.\n"
                "- `agent/agent_loop.py` — coordinates task execution, tools, events, and artifacts.\n"
                "- `agent/planners/action_selector.py` — chooses the next action.\n"
                "- `agent/planners/verifier.py` — verifies whether tool results should count as PASS or FAIL.\n"
                "- `agent/interfaces/cli_interface.py` — provides the CLI interface.\n"
                "- `agent/storage/task_store.py` — stores task state.\n"
                "- `agent/storage/event_log.py` — stores execution logs.\n"
                "- `agent/storage/artifacts.py` — stores reusable outputs.\n"
                "- `agent/tools/` — contains executable tools.\n"
                "- `agent/workflows/` — creates task plans for specific goals.\n"
            )

        if output_name == "packet_flow.md":
            return (
                "# Packet / Request Flow\n\n"
                "No real firewall packet flow can be inferred yet from the current artifact.\n\n"
                "Next needed step:\n\n"
                "- Read the actual firewall source files.\n"
                "- Identify where packets enter the system.\n"
                "- Identify where rules are applied.\n"
                "- Identify where allow/drop/log decisions happen.\n"
            )

        if output_name == "safe_change_suggestion.md":
            return (
                "# Safe Change Suggestion\n\n"
                "A safe first change would be to add logging around the decision point.\n\n"
                "Suggested change:\n\n"
                "- Log each packet/request before and after rule evaluation.\n"
                "- Do not change firewall behavior yet.\n"
                "- Only add observability.\n"
            )

        return (
            f"# {task.title}\n\n"
            "Generated from input artifacts:\n\n"
            + "\n".join(f"- `{name}`" for name in input_contents.keys())
            + "\n\nNo specialized analyzer exists for this output yet.\n"
        )

    def transform_artifacts(self, task: Task, action: dict):
        inputs = action.get("inputs", [])
        outputs = action.get("outputs", [])

        if not outputs:
            return {
                "ok": False,
                "message": "No output artifact specified.",
            }

        input_contents = {}

        for input_name in inputs:
            if not self.artifacts.exists(input_name):
                return {
                    "ok": False,
                    "message": f"Missing input artifact: {input_name}",
                }

            input_contents[input_name] = self.artifacts.read_text(input_name)

        output_name = outputs[0]

        try:
            content = self.artifact_analyzer.analyze(
                task=task,
                input_contents=input_contents,
                output_name=output_name,
            )

            analyzer_used = "openai"

        except Exception as e:
            content = self.simple_artifact_analysis(
                task=task,
                input_contents=input_contents,
                output_name=output_name,
            )

            analyzer_used = "fallback_simple"
            self.event_log.write(
                "artifact_analyzer_failed",
                {
                    "task_id": task.id,
                    "error": str(e),
                    "fallback": "simple_artifact_analysis",
                },
            )

        artifact_path = self.artifacts.write_text(output_name, content)

        self.event_log.write(
            "artifact_created",
            {
                "task_id": task.id,
                "artifact": str(artifact_path),
                "reason": "Generated artifact from input artifacts.",
                "analyzer": analyzer_used,
            },
        )

        return {
            "ok": True,
            "artifact": str(artifact_path),
            "output": output_name,
            "analyzer": analyzer_used,
        }

    def create_source_snapshot(self, task: Task, action: dict):
        from pathlib import Path

        root = Path(action.get("root", self.target_project_dir))
        files = action.get("files", [])
        outputs = action.get("outputs", [])

        output_name = action.get("output")
        if output_name:
            output_name = Path(output_name).name
        elif outputs:
            output_name = outputs[0]
        else:
            return {
                "ok": False,
                "message": "No output artifact specified.",
            }

        parts = []

        for file_path in files:
            target_file_path = root / file_path

            result = self.run_tool(
                "file",
                action="read",
                path=str(target_file_path),
            )

            if not result.get("ok"):
                parts.append(
                    f"## `{file_path}`\n\n"
                    f"Could not read file from target project.\n\n"
                    f"Target path:\n\n"
                    f"```text\n{target_file_path}\n```\n\n"
                    f"Error:\n\n"
                    f"```text\n{result}\n```\n"
                )
                continue

            content = result.get("content", "")

            parts.append(
                f"## `{file_path}`\n\n"
                f"Target path:\n\n"
                f"```text\n{target_file_path}\n```\n\n"
                f"Source:\n\n"
                f"```python\n{content}\n```\n"
            )

        artifact_content = (
                "# Core Source Snapshot\n\n"
                "This artifact contains the source files used to confirm runtime behavior.\n\n"
                f"Target project directory:\n\n"
                f"```text\n{root}\n```\n\n"
                + "\n\n".join(parts)
        )

        artifact_path = self.artifacts.write_text(output_name, artifact_content)

        self.event_log.write(
            "artifact_created",
            {
                "task_id": task.id,
                "artifact": str(artifact_path),
                "reason": "Created source snapshot from selected files.",
            },
        )

        return {
            "ok": True,
            "artifact": str(artifact_path),
            "output": output_name,
        }

    def apply_safe_change(self, task: Task, action: dict):
        target_file = action.get("target_file")
        outputs = action.get("outputs", [])

        if not target_file:
            return {"ok": False, "message": "No target file specified."}

        if not outputs:
            return {"ok": False, "message": "No output artifact specified."}

        target_path = self.target_project_dir / target_file

        expected_text = action.get("expected_text", "datetime.now(timezone.utc)")
        forbidden_text = action.get("forbidden_text", "datetime.utcnow()")
        old_text = action.get("old_text")
        new_text_value = action.get("new_text")
        setup_text = action.get("setup_text")
        cleanup_after = bool(action.get("cleanup_after", False))
        run_command = action.get("run_command", "python src/main.py")

        setup_created_file = False

        if setup_text is not None and not target_path.exists():
            write_setup_result = self.run_tool(
                "file",
                action="write",
                path=str(target_path),
                content=setup_text,
            )

            if not write_setup_result.get("ok"):
                return {
                    "ok": False,
                    "message": "Could not create setup file.",
                    "target_file": str(target_path),
                    "write_setup_result": write_setup_result,
                }

            setup_created_file = True

        read_result = self.run_tool("file", action="read", path=str(target_path))

        if not read_result.get("ok"):
            return {
                "ok": False,
                "message": "Could not read target file.",
                "target_file": str(target_path),
                "read_result": read_result,
            }

        old_content = read_result.get("content", "")

        backup_path = target_path.with_suffix(target_path.suffix + ".bak")
        backup_written = False
        rollback_done = False
        rollback_result = None

        if expected_text in old_content and forbidden_text not in old_content:
            run_result = self.run_tool(
                "shell",
                command=run_command,
                cwd=str(self.target_project_dir),
            )

            cleanup_result = None

            if cleanup_after :
                cleanup_result = self.run_tool(
                    "file",
                    action="delete",
                    path=str(target_path),
                )

            ok = bool(run_result.get("ok"))

            report = [
                "# Change Report",
                "",
                "## No change needed",
                "",
                f"Target file: `{target_file}`",
                "",
                f"Expected text found: `{expected_text}`",
                f"Forbidden text absent: `{forbidden_text}`",
                f"Setup file created: `{setup_created_file}`",
                f"Cleanup requested: `{cleanup_after}`",
                f"Cleanup result ok: `{cleanup_result.get('ok') if cleanup_result else None}`",
                f"Run command: `{run_command}`",
                "",
                "## Verification",
                "",
                f"Program run ok: `{ok}`",
            ]

            artifact_path = self.artifacts.write_text(outputs[0], "\n".join(report))

            return {
                "ok": ok,
                "message": "Change already applied and verified.",
                "target_file": str(target_path),
                "artifact": str(artifact_path),
                "run_result": run_result,
                "setup_created_file": setup_created_file,
                "cleanup_result": cleanup_result,
                "run_command": run_command,
            }

        new_content = old_content

        if old_text and new_text_value:
            if old_text not in old_content:
                report = (
                    "# Change Report\n\n"
                    "Change was not applied.\n\n"
                    f"`old_text` was not found in `{target_file}`.\n\n"
                    "Expected old text:\n\n"
                    "```text\n"
                    f"{old_text}\n"
                    "```\n"
                )
                artifact_path = self.artifacts.write_text(outputs[0], report)

                return {
                    "ok": False,
                    "message": "old_text was not found in target file.",
                    "artifact": str(artifact_path),
                    "setup_created_file": setup_created_file,
                    "run_command": run_command,
                }

            new_content = old_content.replace(old_text, new_text_value, 1)

        else:
            new_content = new_content.replace(
                "from datetime import datetime",
                "from datetime import datetime, timezone",
                1,
            )

            new_content = new_content.replace(
                'f"{datetime.utcnow().isoformat()}Z "',
                'f"{datetime.now(timezone.utc).isoformat().replace(\'+00:00\', \'Z\')} "',
                1,
            )

        if new_content == old_content:
            report = (
                "# Change Report\n\n"
                "Change was not applied.\n\n"
                f"No safe replacement changed `{target_file}`.\n"
            )
            artifact_path = self.artifacts.write_text(outputs[0], report)

            return {
                "ok": False,
                "message": "No safe replacement changed the target file.",
                "artifact": str(artifact_path),
                "setup_created_file": setup_created_file,
                "run_command": run_command,
            }

        backup_result = self.run_tool(
            "file",
            action="write",
            path=str(backup_path),
            content=old_content,
        )

        if not backup_result.get("ok"):
            return {
                "ok": False,
                "message": "Could not write backup file.",
                "target_file": str(target_path),
                "backup_file": str(backup_path),
                "backup_result": backup_result,
                "setup_created_file": setup_created_file,
                "run_command": run_command,
            }

        backup_written = True

        write_result = self.run_tool(
            "file",
            action="write",
            path=str(target_path),
            content=new_content,
        )

        if not write_result.get("ok"):
            rollback_result = self.run_tool(
                "file",
                action="write",
                path=str(target_path),
                content=old_content,
            )
            rollback_done = bool(rollback_result.get("ok"))

            return {
                "ok": False,
                "message": "Could not write patched file.",
                "target_file": str(target_path),
                "write_result": write_result,
                "backup_file": str(backup_path),
                "backup_written": backup_written,
                "rollback_done": rollback_done,
                "rollback_result": rollback_result,
                "setup_created_file": setup_created_file,
                "run_command": run_command,
            }

        verify_read_result = self.run_tool("file", action="read", path=str(target_path))
        verify_content = verify_read_result.get("content", "")

        content_verified = (
                verify_read_result.get("ok")
                and expected_text in verify_content
                and forbidden_text not in verify_content
        )

        run_result = self.run_tool(
            "shell",
            command=run_command,
            cwd=str(self.target_project_dir),
        )

        cleanup_result = None

        if cleanup_after:
            cleanup_result = self.run_tool(
                "file",
                action="delete",
                path=str(target_path),
            )

        cleanup_ok = (
            True
            if not cleanup_after
            else bool(cleanup_result and cleanup_result.get("ok"))
        )

        ok = bool(run_result.get("ok")) and content_verified and cleanup_ok

        backup_cleanup_result = None
        rollback_cleanup_result = None

        if ok and backup_written:
            backup_cleanup_result = self.run_tool(
                "file",
                action="delete",
                path=str(backup_path),
            )

        if not ok and backup_written:
            rollback_result = self.run_tool(
                "file",
                action="write",
                path=str(target_path),
                content=old_content,
            )
            rollback_done = bool(rollback_result.get("ok"))

            if cleanup_after:
                rollback_cleanup_result = self.run_tool(
                    "file",
                    action="delete",
                    path=str(target_path),
                )

            backup_cleanup_result = self.run_tool(
                "file",
                action="delete",
                path=str(backup_path),
            )

        report = [
            "# Change Report",
            "",
            "## Applied change",
            "",
            f"Target file: `{target_file}`",
            "",
            f"Used custom old_text/new_text: `{bool(old_text and new_text_value)}`",
            f"Setup text provided: `{setup_text is not None}`",
            f"Setup file created: `{setup_created_file}`",
            f"Cleanup requested: `{cleanup_after}`",
            f"Cleanup result ok: `{cleanup_result.get('ok') if cleanup_result else None}`",
            f"Backup written: `{backup_written}`",
            f"Backup file: `{backup_path}`",
            f"Backup cleanup result ok: `{backup_cleanup_result.get('ok') if backup_cleanup_result else None}`",
            f"Rollback done: `{rollback_done}`",
            f"Expected text found: `{expected_text in verify_content}`",
            f"Forbidden text absent: `{forbidden_text not in verify_content}`",
            f"Run command: `{run_command}`",
            f"Program run ok: `{bool(run_result.get('ok'))}`",
            f"Rollback cleanup result ok: `{rollback_cleanup_result.get('ok') if rollback_cleanup_result else None}`",
            "",
            "## Verification result",
            "",
            f"Overall ok: `{ok}`",
            "",
            "### stdout",
            "",
            "```text",
            run_result.get("stdout", ""),
            "```",
            "",
            "### stderr",
            "",
            "```text",
            run_result.get("stderr", ""),
            "```",
        ]

        artifact_path = self.artifacts.write_text(outputs[0], "\n".join(report))

        self.event_log.write(
            "safe_change_applied",
            {
                "task_id": task.id,
                "target_file": str(target_path),
                "artifact": str(artifact_path),
                "run_ok": run_result.get("ok"),
                "run_command": run_command,
                "content_verified": content_verified,
                "used_custom_replacement": bool(old_text and new_text_value),
                "setup_created_file": setup_created_file,
                "cleanup_after": cleanup_after,
                "cleanup_ok": cleanup_ok,
                "backup_file": str(backup_path),
                "backup_written": backup_written,
                "backup_cleanup_result": backup_cleanup_result,
                "rollback_done": rollback_done,
            },
        )

        return {
            "ok": ok,
            "message": "Applied safe text replacement." if ok else "Change verification failed; rollback attempted.",
            "target_file": str(target_path),
            "artifact": str(artifact_path),
            "run_result": run_result,
            "run_command": run_command,
            "content_verified": content_verified,
            "used_custom_replacement": bool(old_text and new_text_value),
            "setup_created_file": setup_created_file,
            "cleanup_after": cleanup_after,
            "cleanup_result": cleanup_result,
            "backup_file": str(backup_path),
            "backup_written": backup_written,
            "rollback_done": rollback_done,
            "rollback_result": rollback_result,
            "backup_cleanup_result": backup_cleanup_result,
            "rollback_cleanup_result": rollback_cleanup_result,

        }

    def create_repair_task_from_failure(self, failed_task, action, result, verification):
        stderr = result.get("stderr", "")
        stdout = result.get("stdout", "")

        failure_details = stderr.strip() or stdout.strip() or verification.reason

        repair_task = Task(
            title=f"Investigate failure from: {failed_task.title}",
            description=(
                "The previous task failed. Investigate the failure, explain what happened, "
                "and suggest the smallest safe next step.\n\n"
                f"Failed task: {failed_task.title}\n"
                f"Verification reason: {verification.reason}\n"
                f"Action: {action}\n\n"
                f"Failure details:\n{failure_details}\n\n"
                "At the end of the report, include a section exactly named:\n\n"
                "## NEXT_ACTION_JSON\n\n"
                "Inside a JSON code block, suggest one safe executable follow-up task with this schema:\n\n"
                "```json\n"
                "{\n"
                '  "title": "...",\n'
                '  "description": "...",\n'
                '  "tool_hint": "shell",\n'
                '  "kind": "normal",\n'
                '  "action": {\n'
                '    "tool": "shell",\n'
                '    "command": "...",\n'
                '    "outputs": [],\n'
                '    "reason": "..."\n'
                "  }\n"
                "}\n"
                "```\n\n"
                "Only suggest a safe diagnostic or verification command. "
                "Do not suggest destructive commands. "
                "Do not repeat the exact same failing command unless the failure was expected.\n\n"
                "Special test fallback rule:\n"
                "- If the failed command was `python -m pytest` and the failure says `No module named pytest`, "
                "suggest `python -m unittest discover` as the next safe follow-up command.\n"
                "- If `python -m unittest discover` returns `NO TESTS RAN`, suggest "
                "`python -m unittest discover -s tests -p \"test*.py\"` as the next safe follow-up command.\n"
                "- If pytest or unittest fails with `ModuleNotFoundError` for a project module such as `decision`, "
                "and the source snapshot or structure shows that the module exists inside `src`, suggest running pytest "
                "with `src` temporarily added to `PYTHONPATH` using this Windows-safe one-process command:\n"
                "`python -c \"import os, subprocess, sys; "
                "env=os.environ.copy(); "
                "env['PYTHONPATH']='src'; "
                "raise SystemExit(subprocess.run([sys.executable, '-m', 'pytest'], env=env).returncode)\"`.\n"
                "- This command does not permanently change environment variables and does not modify project files.\n"
                "- Prefer this temporary `PYTHONPATH=src` pytest command over manually asking the user to set `$env:PYTHONPATH`.\n"
                "- If pytest is still unavailable, then use built-in unittest fallback commands.\n"
                "- If unittest discovery fails with `ModuleNotFoundError` for a module such as `decision`, "
                "and diagnostics show that the module exists inside `src`, suggest this Windows-safe Python command:\n"
                "`python -c \"import sys, unittest; sys.path.insert(0, 'src'); "
                "suite=unittest.defaultTestLoader.discover('tests', pattern='test*.py'); "
                "count=suite.countTestCases(); "
                "result=unittest.TextTestRunner(verbosity=2).run(suite); "
                "raise SystemExit(0 if count > 0 and result.wasSuccessful() else 1)\"`.\n"
                "- This command temporarily adds `src` to `sys.path` only inside that Python process.\n"
                "- This command must fail if zero tests are discovered.\n"
                "- If unittest discovery still returns `NO TESTS RAN`, but diagnostics show that a file such as "
                "`tests/test_rule_engine.py` exists, inspect the test file structure. It may contain pytest-style "
                "top-level test functions that unittest cannot collect.\n"
                "- If the failed task was a test task or had `test_results.txt` in its outputs/action outputs, "
                "the follow-up action must include `outputs`: [`test_results.txt`].\n"
                "- Do not suggest installing packages automatically yet. Prefer built-in diagnostics first.\n"
                "- Do not use Unix shell tools such as `sh`, `find`, `tee`, `grep`, `sed`, or `wc` on Windows.\n"
                "- Prefer Python-only diagnostics using `python -c \"...\"` when inspection is needed."
            ),
            inputs=[],
            outputs=[
                f"repair_report_{failed_task.id}.md",
            ],
            tool_hint="analyze_artifact",
            kind="repair",
        )

        self.task_store.add_tasks([repair_task])

        self.event_log.write(
            "repair_task_created",
            {
                "failed_task_id": failed_task.id,
                "repair_task_id": repair_task.id,
                "repair_task_title": repair_task.title,
                "verification_reason": verification.reason,
            },
        )

        return repair_task

    def extract_next_action_from_report(self, report_text: str):
        marker = "NEXT_ACTION_JSON"

        if marker not in report_text:
            return None

        pattern = r"NEXT_ACTION_JSON.*?```json\s*(\{.*?\})\s*```"
        match = re.search(pattern, report_text, flags=re.DOTALL | re.IGNORECASE)

        if not match:
            return None

        json_text = match.group(1)

        try:
            data = json.loads(json_text)
        except json.JSONDecodeError:
            return None

        if not isinstance(data, dict):
            return None

        title = data.get("title", "")

        if not title or title.strip() == "...":
            return None

        action = data.get("action")

        if not isinstance(action, dict):
            return None

        tool = action.get("tool", "")

        if not tool or tool.strip() == "...":
            return None

        if tool == "shell":
            command = action.get("command", "")

            if not command or command.strip() == "...":
                return None

        return data

    def create_followup_task_from_repair_report(self, repair_task, repair_result):
        output_name = repair_result.get("output")

        if not output_name:
            return None

        if not self.artifacts.exists(output_name):
            return None

        report_text = self.artifacts.read_text(output_name)

        next_action_data = self.extract_next_action_from_report(report_text)

        if not next_action_data:
            self.event_log.write(
                "next_action_extraction_failed",
                {
                    "repair_task_id": repair_task.id,
                    "output": output_name,
                    "reason": "No valid NEXT_ACTION_JSON block found.",
                },
            )
            return None

        followup_task = Task(
            title=next_action_data["title"],
            description=next_action_data.get(
                "description",
                "Executable follow-up task created from repair report.",
            ),
            inputs=[],
            outputs=[],
            tool_hint=next_action_data.get("tool_hint", "shell"),
            action=next_action_data["action"],
            kind=next_action_data.get("kind", "normal"),
        )

        self.task_store.add_tasks([followup_task])

        self.event_log.write(
            "followup_task_created",
            {
                "repair_task_id": repair_task.id,
                "followup_task_id": followup_task.id,
                "followup_task_title": followup_task.title,
                "action": followup_task.action,
            },
        )

        return followup_task

    def read_artifact(self, artifact_name: str) -> str:
        if not self.artifacts.exists(artifact_name):
            raise FileNotFoundError(f"Artifact not found: {artifact_name}")

        return self.artifacts.read_text(artifact_name)

    def execute_next_action(self):
        task = self.next_task()

        if not task:
            return {
                "ok": False,
                "message": "No pending tasks.",
            }

        action = self.selector.select_action(task)

        if action["tool"] == "shell":
            result = self.run_tool(
                "shell",
                command=action["command"],
                cwd=str(self.target_project_dir),
            )

        elif action["tool"] == "file":
            result = self.run_tool(
                "file",
                action=action["action"],
                path=action["path"],
                content=action.get("content", ""),
            )

        elif action["tool"] == "artifact_transform":
            result = self.transform_artifacts(task, action)

        elif action["tool"] == "source_snapshot":
            result = self.create_source_snapshot(task, action)

        elif action["tool"] == "apply_safe_change":
            result = self.apply_safe_change(task, action)

        else:
            return {
                "ok": False,
                "message": "No executable action.",
            }

        self.maybe_create_artifact(task, action, result)

        verification = self.verifier.verify_action_result(task, action, result)

        if action.get("expected_failure") and verification.status == "FAIL":
            verification.status = "PASS"
            verification.reason = "Expected failure occurred."

        result["verification"] = {
            "status": verification.status,
            "reason": verification.reason,
            "exit_code": verification.exit_code,
        }

        if verification.status == "PASS":
            self.mark_done(task.id)

            if getattr(task, "kind", "normal") == "repair":
                followup_task = self.create_followup_task_from_repair_report(
                    repair_task=task,
                    repair_result=result,
                )

                if followup_task:
                    result["created_followup_task"] = {
                        "id": followup_task.id,
                        "title": followup_task.title,
                        "status": followup_task.status,
                        "action": followup_task.action,
                    }
                else:
                    result["created_followup_task"] = None

        else:
            self.mark_failed(task.id, verification.reason)

            if getattr(task, "kind", "normal") != "repair":
                repair_task = self.create_repair_task_from_failure(
                    failed_task=task,
                    action=action,
                    result=result,
                    verification=verification,
                )

                result["created_repair_task"] = {
                    "id": repair_task.id,
                    "title": repair_task.title,
                    "status": repair_task.status,
                }

            else:
                result["created_repair_task"] = None
                result["repair_task_skipped"] = (
                    "Repair task failed; not creating another nested repair task."
                )

        return result

    def create_fallback_task_from_goal(self, goal: str) -> Task:
        lower_goal = goal.lower()
        if "test safe change rollback" in lower_goal:
            return Task(
                title="Test safe change rollback",
                description="Create a temp file, apply a change, force verification to fail, and confirm rollback restores OLD_VALUE.",
                inputs=[],
                outputs=["rollback_test_report.md"],
                tool_hint="apply_safe_change",
                kind="normal",
                action={
                    "tool": "apply_safe_change",
                    "target_file": "tmp_rollback_test.txt",
                    "outputs": ["rollback_test_report.md"],
                    "old_text": "OLD_VALUE",
                    "new_text": "NEW_VALUE",
                    "expected_text": "IMPOSSIBLE_EXPECTED_TEXT",
                    "forbidden_text": "OLD_VALUE",
                    "setup_text": "OLD_VALUE",
                    "cleanup_after": True,
                    "run_command": "python src/main.py",
                    "reason": "Test rollback when content verification fails.",
                    "expected_failure": True,
                },
            )

        if "test generic safe text replacement" in lower_goal:
            return Task(
                title="Test generic safe text replacement",
                description="Create a temp file and replace OLD_VALUE with NEW_VALUE using apply_safe_change.",
                inputs=[],
                outputs=[
                    "generic_safe_change_test_report.md",
                ],
                tool_hint="apply_safe_change",
                kind="normal",
                action={
                    "tool": "apply_safe_change",
                    "target_file": "tmp_safe_change_test.txt",
                    "outputs": [
                        "generic_safe_change_test_report.md",
                    ],
                    "old_text": "OLD_VALUE",
                    "new_text": "NEW_VALUE",
                    "expected_text": "NEW_VALUE",
                    "forbidden_text": "OLD_VALUE",
                    "setup_text": "OLD_VALUE",
                    "cleanup_after": True,
                    "reason": "Test generic safe text replacement on a harmless temp file.",
                    "run_command": "python src/main.py",
                },
            )

        if "apply safe logger timestamp change" in lower_goal:
            return Task(
                title="Apply safe logger timestamp change",
                description="Update src/logger.py so UTC timestamps in the log end with Z.",
                inputs=[],
                outputs=[
                    "change_report.md",
                ],
                tool_hint="apply_safe_change",
                kind="normal",
                action={
                    "tool": "apply_safe_change",
                    "target_file": "src/logger.py",
                    "outputs": [
                        "change_report.md",
                    ],
                    "old_text": 'f"{datetime.utcnow().isoformat()}Z "',
                    "new_text": 'f"{datetime.now(timezone.utc).isoformat().replace(\'+00:00\', \'Z\')} "',
                    "expected_text": "datetime.now(timezone.utc)",
                    "forbidden_text": "datetime.utcnow()",
                    "reason": "Apply the approved tiny safe logger timestamp change.",
                    "run_command": "python src/main.py",
                },
            )

        if "failing shell command" in lower_goal or "fail shell command" in lower_goal:
            return Task(
                title=goal,
                description="Run a command that intentionally fails to test verifier and repair loop.",
                tool_hint="shell",
                kind="test",
                action={
                    "tool": "shell",
                    "command": "py -3 -c \"raise Exception('boom')\"",
                    "outputs": [],
                    "reason": "Intentional verifier failure test.",
                },
            )

        if "shell command" in lower_goal and "pass" in lower_goal:
            return Task(
                title=goal,
                description="Run a safe command that should pass to test verifier logic.",
                tool_hint="shell",
                kind="test",
                action={
                    "tool": "shell",
                    "command": "py -3 --version",
                    "outputs": [],
                    "reason": "Intentional verifier PASS test.",
                },
            )

        return Task(
            title=goal,
            description="Manually created task from user goal.",
            kind="normal",
        )