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
from pathlib import Path


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

    def clear_pending_tasks(self) -> int:
        removed = self.task_store.clear_pending()

        self.event_log.write(
            "pending_tasks_cleared",
            {
                "removed": removed,
            },
        )

        return removed

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

    def protect_latex_square_bracket_placeholders(self, content: str) -> str:
        def replace_placeholder(match):
            inner = match.group(1).strip()
            lower = inner.lower()

            placeholder_keywords = [
                "candidate",
                "email",
                "phone",
                "address",
                "linkedin",
                "github",
                "portfolio",
                "date",
                "hiring",
                "manager",
                "company",
                "city",
                "country",
                "missing",
                "available",
            ]

            if not any(keyword in lower for keyword in placeholder_keywords):
                return match.group(0)

            return "\\textnormal{\\lbrack{}" + inner + "\\rbrack{}}"

        return re.sub(r"\[([^\[\]\n]+)\]", replace_placeholder, content)

    def clean_latex_artifact(self, content: str) -> str:
        content = self.strip_markdown_code_fences(content)

        start = content.find("\\documentclass")
        if start != -1:
            content = content[start:]

        end_marker = "\\end{document}"
        end = content.find(end_marker)
        if end != -1:
            content = content[: end + len(end_marker)]

        content = self.protect_latex_square_bracket_placeholders(content)

        return content.strip() + "\n"

    def strip_markdown_code_fences(self, content: str) -> str:
        lines = content.splitlines()
        cleaned = []
        removed_any = False

        fence_markers = {
            "```",
            "```markdown",
            "```md",
            "```text",
            "```latex",
            "```tex",
        }

        for line in lines:
            stripped = line.strip().lower()

            if stripped in fence_markers:
                removed_any = True
                continue

            cleaned.append(line)

        if removed_any:
            return "\n".join(cleaned).strip() + "\n"

        return content

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

        is_critical = bool(action.get("critical", False))
        strip_fences = bool(action.get("strip_fences", False))

        self.event_log.write(
            "artifact_transform_policy",
            {
                "task_id": task.id,
                "output": output_name,
                "critical_from_action": is_critical,
                "strip_fences_from_action": strip_fences,
                "is_critical": is_critical,
                "strip_fences": strip_fences,
            },
        )

        try:
            content = self.artifact_analyzer.analyze(
                task=task,
                input_contents=input_contents,
                output_name=output_name,
            )

            analyzer_used = "openai"

            if output_name == "cover_letter_verification_requirements.md":
                content = self.ensure_must_contain_requirements(
                    content=content,
                    input_contents=input_contents,
                )

        except Exception as e:
            self.event_log.write(
                "artifact_analyzer_failed",
                {
                    "task_id": task.id,
                    "output": output_name,
                    "error": str(e),
                    "fallback": (
                        "blocked_for_critical_output"
                        if is_critical
                        else "simple_artifact_analysis"
                    ),
                },
            )

            if is_critical:
                return {
                    "ok": False,
                    "message": (
                        f"OpenAI artifact analyzer failed for critical output: {output_name}. "
                        "Refusing to use generic fallback because it would create misleading artifacts."
                    ),
                    "output": output_name,
                    "error": str(e),
                }

            content = self.simple_artifact_analysis(
                task=task,
                input_contents=input_contents,
                output_name=output_name,
            )

            analyzer_used = "fallback_simple"

            if output_name == "cover_letter_verification_requirements.md":
                content = self.ensure_must_contain_requirements(
                    content=content,
                    input_contents=input_contents,
                )

        if strip_fences:
            content = self.strip_markdown_code_fences(content)

        if output_name.endswith(".tex"):
            content = self.clean_latex_artifact(content)

        artifact_path = self.artifacts.write_text(output_name, content)

        self.event_log.write(
            "artifact_created",
            {
                "task_id": task.id,
                "artifact": str(artifact_path),
                "reason": "Generated artifact from input artifacts.",
                "analyzer": analyzer_used,
                "critical": is_critical,
                "strip_fences": strip_fences,
            },
        )

        return {
            "ok": True,
            "artifact": str(artifact_path),
            "output": output_name,
            "analyzer": analyzer_used,
        }

    def strip_outer_markdown_code_fence(self, content: str) -> str:
        text = content.strip()

        if not text.startswith("```"):
            return content

        lines = text.splitlines()

        if len(lines) < 3:
            return content

        first_line = lines[0].strip().lower()
        last_line = lines[-1].strip()

        if first_line in {"```", "```markdown", "```md", "```text"} and last_line == "```":
            return "\n".join(lines[1:-1]).strip() + "\n"

        return content

    def create_source_snapshot(self, task: Task, action: dict):
        from pathlib import Path
        import fnmatch

        root_value = action.get("root", "target_project")

        if root_value == "target_project":
            root = Path(self.target_project_dir)
        else:
            root = Path(root_value)

        files = list(action.get("files", []) or [])
        patterns = list(action.get("patterns", []) or [])

        exclude_files = set(action.get("exclude_files", []) or [])
        exclude_patterns = list(action.get("exclude_patterns", []) or [])

        outputs = action.get("outputs", [])

        if outputs:
            output_name = outputs[0]
        else:
            output_name = action.get("output")
            if output_name:
                output_name = Path(output_name).name
            else:
                return {
                    "ok": False,
                    "message": "No output artifact specified.",
                }

        def is_excluded(relative_name: str) -> bool:
            normalized = relative_name.replace("\\", "/")

            if normalized in exclude_files or relative_name in exclude_files:
                return True

            for pattern in exclude_patterns:
                if fnmatch.fnmatch(normalized, pattern):
                    return True

            return False

        resolved_files = []

        if patterns and root.exists():
            for pattern in patterns:
                for path in sorted(root.glob(pattern)):
                    if not path.is_file():
                        continue

                    try:
                        relative_path = path.relative_to(root)
                        relative_name = str(relative_path).replace("\\", "/")
                    except ValueError:
                        relative_name = str(path)

                    if not is_excluded(relative_name):
                        resolved_files.append(relative_name)

        files = files + resolved_files

        seen_files = set()
        files = [
            file.replace("\\", "/")
            for file in files
            if file and not is_excluded(file.replace("\\", "/"))
        ]

        files = [
            file
            for file in files
            if not (file in seen_files or seen_files.add(file))
        ]

        parts = []

        if not root.exists():
            parts.append(
                "## Target project directory missing\n\n"
                "Could not read files because the target project directory does not exist.\n\n"
                "Target path:\n\n"
                f"```text\n{root}\n```\n"
            )

        for file_path in files:
            target_file_path = root / file_path

            try:
                result = self.run_tool(
                    "file",
                    action="read",
                    path=str(target_file_path),
                )
            except Exception as e:
                result = {
                    "ok": False,
                    "error": repr(e),
                }

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
                f"```text\n{content}\n```\n"
            )

        artifact_content = (
                "# Source Snapshot\n\n"
                "This artifact contains selected files from the target project.\n\n"
                f"Target project directory:\n\n"
                f"```text\n{root}\n```\n\n"
                "## Snapshot configuration\n\n"
                f"- Exact files requested: `{len(action.get('files', []) or [])}`\n"
                f"- Patterns requested: `{patterns}`\n"
                f"- Files after pattern resolution and filtering: `{len(files)}`\n\n"
                + "\n\n".join(parts)
        )

        artifact_path = self.artifacts.write_text(output_name, artifact_content)

        self.event_log.write(
            "artifact_created",
            {
                "task_id": task.id,
                "artifact": str(artifact_path),
                "reason": "Created source snapshot from selected files.",
                "root": str(root),
                "files": files,
                "patterns": patterns,
                "exclude_files": list(exclude_files),
                "exclude_patterns": exclude_patterns,
            },
        )

        return {
            "ok": True,
            "artifact": str(artifact_path),
            "output": output_name,
            "files": files,
            "patterns": patterns,
        }

    def ensure_must_contain_requirements(self, content: str, input_contents: dict) -> str:
        extracted = self.extract_must_contain_requirements(content)

        if extracted:
            return content

        cover_letter = input_contents.get("tailored_cover_letter.md", "")

        candidates = [
            "Test Candidate",
            "Junior Software Developer Intern",
            "ExampleTech AG",
            "University of Basel",
            "Java",
            "Python",
            "Git",
            "JavaFX",
            "client-server",
            "Client-server",
            "Minimal Agent CLI",
            "multiplayer game",
            "Multiplayer Java Game",
        ]

        found = []

        for item in candidates:
            if item in cover_letter:
                found.append(item)

        if not found:
            # Emergency fallback: use short non-empty lines from the cover letter.
            for line in cover_letter.splitlines():
                clean = line.strip().strip("*").strip()

                if not clean:
                    continue

                if clean.startswith("#"):
                    continue

                if len(clean) > 80:
                    continue

                found.append(clean)

                if len(found) >= 5:
                    break

        # Deduplicate while preserving order.
        seen = set()
        found = [
            item for item in found
            if item and not (item in seen or seen.add(item))
        ]

        found = found[:10]

        if not found:
            return (
                "# Cover Letter Verification Requirements\n\n"
                "## Must contain\n"
            )

        return (
                "# Cover Letter Verification Requirements\n\n"
                "## Must contain\n"
                + "\n".join(f"- {item}" for item in found)
                + "\n"
        )

    def extract_must_contain_requirements(self, text: str) -> list[str]:
        lines = text.splitlines()

        in_section = False
        items = []

        for line in lines:
            stripped = line.strip()

            if stripped.lower() == "## must contain":
                in_section = True
                continue

            if in_section and stripped.startswith("## "):
                break

            if not in_section:
                continue

            if stripped.startswith("- "):
                item = stripped[2:].strip()

                # Remove common markdown formatting.
                item = item.strip("`").strip()
                item = item.strip("*").strip()

                if item:
                    items.append(item)

        return items

    def verify_target_file(self, task: Task, action: dict):
        from pathlib import Path

        root_value = action.get("root", "target_project")
        target_file = action.get("target_file")
        must_contain = list(action.get("must_contain", []) or [])
        must_contain_from_artifact = action.get("must_contain_from_artifact")
        outputs = action.get("outputs", [])

        if not target_file:
            return {
                "ok": False,
                "message": "No target file specified.",
            }

        if not outputs:
            return {
                "ok": False,
                "message": "No output artifact specified.",
            }

        if must_contain_from_artifact:
            if not self.artifacts.exists(must_contain_from_artifact):
                return {
                    "ok": False,
                    "message": f"Verification requirements artifact not found: {must_contain_from_artifact}",
                }

            requirements_text = self.artifacts.read_text(must_contain_from_artifact)
            extracted = self.extract_must_contain_requirements(requirements_text)

            if not extracted:
                return {
                    "ok": False,
                    "message": (
                        "Verification requirements artifact was provided, "
                        "but no must-contain requirements could be extracted."
                    ),
                    "requirements_artifact": must_contain_from_artifact,
                }

            must_contain.extend(extracted)

        # Deduplicate while keeping order.
        seen = set()
        must_contain = [
            item for item in must_contain
            if item and not (item in seen or seen.add(item))
        ]

        if root_value == "target_project":
            root = Path(self.target_project_dir)
        else:
            root = Path(root_value)

        target_path = root / target_file

        try:
            result = self.run_tool(
                "file",
                action="read",
                path=str(target_path),
            )
        except Exception as e:
            result = {
                "ok": False,
                "error": repr(e),
                "content": "",
            }

        content = result.get("content", "")
        missing = [text for text in must_contain if text not in content]

        ok = bool(result.get("ok")) and not missing

        report = [
            "# Target File Verification",
            "",
            f"Target file: `{target_path}`",
            "",
            f"File readable: `{bool(result.get('ok'))}`",
            f"Overall ok: `{ok}`",
            "",
            "## Verification source",
            "",
            f"- Static requirements count: `{len(action.get('must_contain', []) or [])}`",
            f"- Dynamic requirements artifact: `{must_contain_from_artifact}`",
            f"- Total required text checks: `{len(must_contain)}`",
            "",
            "## Required text checks",
            "",
        ]

        for text in must_contain:
            status = "PASS" if text in content else "FAIL"
            report.append(f"- `{text}`: `{status}`")

        if missing:
            report.extend([
                "",
                "## Missing required text",
                "",
            ])

            for text in missing:
                report.append(f"- `{text}`")

        artifact_path = self.artifacts.write_text(outputs[0], "\n".join(report))

        self.event_log.write(
            "target_file_verified",
            {
                "task_id": task.id,
                "target_file": str(target_path),
                "ok": ok,
                "missing": missing,
                "artifact": str(artifact_path),
                "must_contain_from_artifact": must_contain_from_artifact,
            },
        )

        return {
            "ok": ok,
            "target_file": str(target_path),
            "missing": missing,
            "artifact": str(artifact_path),
            "output": outputs[0],
            "must_contain": must_contain,
            "must_contain_from_artifact": must_contain_from_artifact,
        }

    def materialize_artifact(self, task: Task, action: dict):
        from pathlib import Path

        input_name = action.get("input")
        target_file = action.get("target_file")
        root_value = action.get("root", "target_project")

        if not input_name:
            return {
                "ok": False,
                "message": "No input artifact specified.",
            }

        if not target_file:
            return {
                "ok": False,
                "message": "No target file specified.",
            }

        if not self.artifacts.exists(input_name):
            return {
                "ok": False,
                "message": f"Input artifact not found: {input_name}",
            }

        if root_value == "target_project":
            root = Path(self.target_project_dir)
        else:
            root = Path(root_value)

        target_path = root / target_file

        content = self.artifacts.read_text(input_name)

        if target_file.endswith(".tex"):
            content = self.clean_latex_artifact(content)

        try:
            write_result = self.run_tool(
                "file",
                action="write",
                path=str(target_path),
                content=content,
            )
        except Exception as e:
            return {
                "ok": False,
                "message": "Could not write artifact to target file.",
                "error": repr(e),
                "input": input_name,
                "target_file": str(target_path),
            }

        if not write_result.get("ok"):
            return {
                "ok": False,
                "message": "File tool failed while writing artifact to target file.",
                "input": input_name,
                "target_file": str(target_path),
                "write_result": write_result,
            }

        self.event_log.write(
            "artifact_materialized",
            {
                "task_id": task.id,
                "input_artifact": input_name,
                "target_file": str(target_path),
                "reason": action.get("reason", ""),
            },
        )

        return {
            "ok": True,
            "input": input_name,
            "target_file": str(target_path),
            "write_result": write_result,
        }

    def apply_safe_change(self, task: Task, action: dict):
        target_file = action.get("target_file")
        outputs = action.get("outputs", [])

        if not target_file:
            return {"ok": False, "message": "No target file specified."}

        if not outputs:
            return {"ok": False, "message": "No output artifact specified."}

        root = Path(action.get("root", self.target_project_dir))
        target_path = root / target_file

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

        expected_ok = expected_text is None or expected_text in old_content
        forbidden_ok = forbidden_text is None or forbidden_text not in old_content

        if expected_ok and forbidden_ok:
            run_result = self.run_tool(
                "shell",
                command=run_command,
                cwd=str(root),
            )

            cleanup_result = None

            if cleanup_after:
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
                f"Expected text found: `{expected_ok}`",
                f"Forbidden text absent: `{forbidden_ok}`",
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
                and (expected_text is None or expected_text in verify_content)
                and (forbidden_text is None or forbidden_text not in verify_content)
        )

        run_result = self.run_tool(
            "shell",
            command=run_command,
            cwd=str(root),
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
            f"Expected text found: `{expected_text is None or expected_text in verify_content}`",
            f"Forbidden text absent: `{forbidden_text is None or forbidden_text not in verify_content}`",
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
            "expected_failure_observed": action.get("expected_failure", False) and not ok,
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

    def build_replacement_from_patch_lines(self, patch_lines: list[str]):
        old_lines = []
        new_lines = []

        for line in patch_lines:
            if (
                    line.startswith("diff ")
                    or line.startswith("--- ")
                    or line.startswith("+++ ")
                    or line.startswith("@@")
            ):
                continue

            if line == " ":
                old_lines.append("")
                new_lines.append("")
            elif line.startswith("+"):
                new_lines.append(line[1:])
            elif line.startswith("-"):
                old_lines.append(line[1:])
            elif line.startswith(" "):
                old_lines.append(line[1:])
                new_lines.append(line[1:])
            else:
                old_lines.append(line)
                new_lines.append(line)

        old_text = "\n".join(old_lines).rstrip()
        new_text = "\n".join(new_lines).rstrip()

        if not old_text or not new_text or old_text == new_text:
            return None, None

        return old_text, new_text

    def extract_json_block(self, text: str):
        pattern = r"```json\s*(\{.*?\})\s*```"
        match = re.search(pattern, text, flags=re.DOTALL | re.IGNORECASE)

        if not match:
            return None

        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None

    def run_agent_regression_tests_now(self):
        return self.run_tool(
            "shell",
            command=(
                'cd /d "C:\\Users\\illa9\\Downloads\\minimal_agent_repo\\minimal_agent_repo" '
                '&& python -m pytest agent/tests/test_apply_safe_change.py'
            ),
            cwd=str(Path(__file__).resolve().parents[1]),
        )

    def create_agent_regression_test_task(self):
        task = Task(
            title="Run agent regression tests",
            description="Run the agent's automated regression tests after an approved self-improvement change.",
            inputs=[],
            outputs=["agent_regression_test_results.md"],
            tool_hint="shell",
            kind="test",
            action={
                "tool": "shell",
                "command": (
                    'cd /d "C:\\Users\\illa9\\Downloads\\minimal_agent_repo\\minimal_agent_repo" '
                    '&& python -m pytest agent/tests/test_apply_safe_change.py'
                ),
                "outputs": ["agent_regression_test_results.md"],
                "reason": "Automatically verify agent behavior after self-improvement.",
            },
        )

        self.task_store.add_tasks([task])
        return task

    def create_task_from_self_improvement_apply_artifact(self, artifact_name: str):
        if not self.artifacts.exists(artifact_name):
            return None

        text = self.artifacts.read_text(artifact_name)
        data = self.extract_json_block(text)

        if not data:
            return None

        action = data.get("action", {})
        old_text, new_text = self.build_replacement_from_patch_lines(
            action.get("patch_lines", [])
        )

        task = Task(
            title=data.get("title", "Apply self-improvement change"),
            description=action.get("summary", "Apply a self-improvement patch."),
            inputs=[artifact_name],
            outputs=["self_improvement_change_report.md"],
            tool_hint="apply_safe_change",
            kind=data.get("kind", "normal"),
            action={
                "tool": "apply_safe_change",
                "root": str(Path(__file__).resolve().parents[1]),
                "target_file": action.get("target_files", ["agent/agent_loop.py"])[0],
                "outputs": ["self_improvement_change_report.md"],
                "reason": "Apply self-improvement change generated from executable task artifact.",
                "old_text": old_text,
                "new_text": new_text,
                "expected_text": "preflight_artifact_check",
                "forbidden_text": None,
                "run_command": (
                    'cd /d "C:\\Users\\illa9\\Downloads\\minimal_agent_repo\\minimal_agent_repo" '
                    '&& python -m py_compile agent/agent_loop.py'
                ),
            }
        )

        self.task_store.add_tasks([task])
        return task

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

        elif action["tool"] == "verify_target_file":
            result = self.verify_target_file(task, action)

        elif action["tool"] == "self_improvement_pipeline":
            result = self.execute_approved_self_improvement_pipeline()


        elif action["tool"] == "materialize_artifact":
            result = self.materialize_artifact(task, action)

        elif action["tool"] == "subworkflow":
            result = self.execute_subworkflow(task, action)

        else:
            return {
                "ok": False,
                "message": "No executable action.",
            }

        self.maybe_create_artifact(task, action, result)

        verification = self.verifier.verify_action_result(task, action, result)

        if result.get("expected_failure_observed") and verification.status == "FAIL":
            verification.status = "PASS"
            verification.reason = "Expected failure occurred."

        result["verification"] = {
            "status": verification.status,
            "reason": verification.reason,
            "exit_code": verification.exit_code,
        }

        if verification.status == "PASS":
            self.mark_done(task.id)

            if (
                    action.get("tool") == "apply_safe_change"
                    and action.get("root") == str(Path(__file__).resolve().parents[1])
            ):
                regression_result = self.run_agent_regression_tests_now()

                result["automatic_regression_result"] = {
                    "ok": regression_result.get("ok"),
                    "returncode": regression_result.get("returncode"),
                    "stdout": regression_result.get("stdout", ""),
                    "stderr": regression_result.get("stderr", ""),
                }

                if not regression_result.get("ok"):
                    result["ok"] = False
                    result["verification"]["status"] = "FAIL"
                    result["verification"]["reason"] = "Automatic regression tests failed after self-improvement."

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

            workflow_group_id = getattr(task, "workflow_group_id", None)

            if workflow_group_id:
                blocked_tasks = self.task_store.block_pending_in_workflow_group(
                    workflow_group_id=workflow_group_id,
                    blocked_by_task_id=task.id,
                    reason=verification.reason,
                )

                result["blocked_tasks"] = [
                    {
                        "id": blocked_task.id,
                        "title": blocked_task.title,
                        "status": blocked_task.status,
                        "blocked_by_task_id": blocked_task.blocked_by_task_id,
                        "blocked_reason": blocked_task.blocked_reason,
                    }
                    for blocked_task in blocked_tasks
                ]

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

    def execute_approved_self_improvement_pipeline(self):
        apply_task = self.create_task_from_self_improvement_apply_artifact(
            "self_improvement_apply_task.md"
        )

        if not apply_task:
            return {
                "ok": False,
                "message": "Could not create approved self-improvement apply task.",
            }

        action = self.selector.select_action(apply_task)
        result = self.apply_safe_change(apply_task, action)

        verification = self.verifier.verify_action_result(apply_task, action, result)

        result["verification"] = {
            "status": verification.status,
            "reason": verification.reason,
            "exit_code": verification.exit_code,
        }

        if verification.status == "PASS":
            self.mark_done(apply_task.id)

            regression_result = self.run_agent_regression_tests_now()
            result["automatic_regression_result"] = {
                "ok": regression_result.get("ok"),
                "returncode": regression_result.get("returncode"),
                "stdout": regression_result.get("stdout", ""),
                "stderr": regression_result.get("stderr", ""),
            }

            if not regression_result.get("ok"):
                result["ok"] = False
                result["verification"]["status"] = "FAIL"
                result["verification"]["reason"] = "Automatic regression tests failed."
        else:
            self.mark_failed(apply_task.id, verification.reason)

        return result

    def execute_subworkflow(self, task, action: dict):
        goal = action.get("goal")

        if not goal:
            return {
                "ok": False,
                "message": "Subworkflow action missing goal.",
            }

        matching_workflow = None

        for workflow in self.workflows:
            if workflow.can_handle(goal):
                matching_workflow = workflow
                break

        if matching_workflow is None:
            return {
                "ok": False,
                "message": f"No workflow can handle subworkflow goal: {goal}",
            }

        sub_tasks = matching_workflow.create_tasks(goal)

        if not sub_tasks:
            return {
                "ok": False,
                "message": f"Subworkflow produced no tasks for goal: {goal}",
            }

        workflow_group_id = task.workflow_group_id or task.id

        for sub_task in sub_tasks:
            sub_task.parent_task_id = task.id
            sub_task.workflow_group_id = workflow_group_id

        self.task_store.insert_tasks_after(task.id, sub_tasks)

        self.task_store.assign_workflow_group_after(
            task_id=task.id,
            workflow_group_id=workflow_group_id,
        )

        self.event_log.write(
            "subworkflow_expanded",
            {
                "task_id": task.id,
                "goal": goal,
                "workflow": matching_workflow.__class__.__name__,
                "created_tasks": [
                    {
                        "id": sub_task.id,
                        "title": sub_task.title,
                    }
                    for sub_task in sub_tasks
                ],
            },
        )

        return {
            "ok": True,
            "message": f"Expanded subworkflow goal: {goal}",
            "workflow": matching_workflow.__class__.__name__,
            "created_task_count": len(sub_tasks),
            "created_tasks": [
                {
                    "id": sub_task.id,
                    "title": sub_task.title,
                }
                for sub_task in sub_tasks
            ],
        }

    def create_fallback_task_from_goal(self, goal: str) -> Task:
        lower_goal = goal.lower()

        if "snapshot workflow system for job application workflow" in lower_goal:
            return Task(
                title="Snapshot workflow system for job application workflow",
                description="Read workflow registration and existing workflow files before adding a job-application workflow.",
                inputs=[],
                outputs=["workflow_system_snapshot.md"],
                tool_hint="source_snapshot",
                kind="normal",
                action={
                    "tool": "source_snapshot",
                    "root": str(Path(__file__).resolve().parents[1]),
                    "files": [
                        "agent/main.py",
                        "agent/agent_loop.py",
                        "agent/workflows/__init__.py",
                        "agent/workflows/job_application.py",
                    ],
                    "output": "workflow_system_snapshot.md",
                    "outputs": ["workflow_system_snapshot.md"],
                    "reason": "Find where workflows are registered and how a new adaptive job application workflow should be added.",
                },
            )

        if "plan adaptive workflow for job applications" in lower_goal:
            return Task(
                title="Plan adaptive job application workflow",
                description=(
                    "Create a plan for an adaptive job-application workflow. "
                    "The workflow should identify what the agent can already do, "
                    "what capability is missing, and when to trigger a safe self-improvement proposal."
                ),
                inputs=[
                    "core_source_snapshot.md",
                    "self_improvement_plan.md",
                ],
                outputs=[
                    "adaptive_job_application_workflow_plan.md",
                ],
                tool_hint="artifact_transform",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": [
                        "core_source_snapshot.md",
                        "self_improvement_plan.md",
                    ],
                    "outputs": [
                        "adaptive_job_application_workflow_plan.md",
                    ],
                    "reason": (
                        "Design the first adaptive workflow for job applications, "
                        "including when to use existing tools and when to propose self-improvement."
                    ),
                },
            )

        if "execute approved self-improvement pipeline" in lower_goal:
            return Task(
                title="Execute approved self-improvement pipeline",
                description="Apply the latest approved self-improvement task and run regression tests automatically.",
                kind="normal",
                tool_hint="self_improvement_pipeline",
                action={
                    "tool": "self_improvement_pipeline",
                    "reason": "Execute approved proposal, safe apply, and automatic regression verification.",
                },
            )

        if "approve latest self-improvement proposal" in lower_goal:
            task = self.create_task_from_self_improvement_apply_artifact(
                "self_improvement_apply_task.md"
            )

            if task:
                return Task(
                    title="Approved latest self-improvement proposal",
                    description=f"Queued approved self-improvement task: {task.title}",
                    kind="normal",
                    tool_hint="shell",
                    action={
                        "tool": "shell",
                        "command": "echo approved latest self-improvement proposal",
                        "outputs": [],
                        "reason": "Confirm approved self-improvement task was queued.",
                    },
                )

            return Task(
                title="Approve latest self-improvement proposal failed",
                description="Could not queue task from self_improvement_apply_task.md.",
                kind="normal",
            )

        if "queue self-improvement apply task" in lower_goal:
            task = self.create_task_from_self_improvement_apply_artifact(
                "self_improvement_apply_task.md"
            )

            if task:
                return Task(
                    title="Queued self-improvement apply task",
                    description=f"Created queued task: {task.title}",
                    kind="normal",
                    action={
                        "tool": "shell",
                        "command": "echo queued self-improvement apply task",
                        "outputs": [],
                        "reason": "Confirm task was queued.",
                    },
                    tool_hint="shell",
                )

            return Task(
                title="Queue self-improvement apply task failed",
                description="Could not create task from self_improvement_apply_task.md.",
                kind="normal",
            )

        if "apply executable self-improvement task" in lower_goal:
            return Task(
                title="Create apply-safe-change task from executable self-improvement task",
                description="Convert the executable self-improvement task artifact into a structured apply_safe_change task JSON.",
                inputs=["self_improvement_executable_task.md"],
                outputs=["self_improvement_apply_task.md"],
                tool_hint="artifact_transform",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": ["self_improvement_executable_task.md"],
                    "outputs": ["self_improvement_apply_task.md"],
                    "reason": "Extract target file, old_text, new_text, expected_text, forbidden_text, and run_command into executable JSON.",
                },
            )

        if "create executable self-improvement task" in lower_goal:
            return Task(
                title="Create executable self-improvement task",
                description="Convert the self-improvement patch proposal into one executable safe-change task.",
                inputs=["self_improvement_patch_proposal.md"],
                outputs=["self_improvement_executable_task.md"],
                tool_hint="artifact_transform",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": ["self_improvement_patch_proposal.md"],
                    "outputs": ["self_improvement_executable_task.md"],
                    "reason": "Convert patch proposal into executable apply_safe_change JSON.",
                },
            )

        if "run agent regression tests" in lower_goal:
            return Task(
                title="Run agent regression tests",
                description="Run the agent's automated regression tests.",
                inputs=[],
                outputs=["agent_regression_test_results.md"],
                tool_hint="shell",
                kind="test",
                action={
                    "tool": "shell",
                    "command": (
                        'cd /d "C:\\Users\\illa9\\Downloads\\minimal_agent_repo\\minimal_agent_repo" '
                        '&& python -m pytest agent/tests/test_apply_safe_change.py'
                    ),
                    "outputs": ["agent_regression_test_results.md"],
                    "reason": "Verify that core safe-change behavior still works.",
                },
            )

        if "propose self-improvement patch" in lower_goal:
            return Task(
                title="Propose self-improvement patch",
                description="Use source snapshot and improvement plan to propose one safe executable code change.",
                inputs=[
                    "core_source_snapshot.md",
                    "self_improvement_plan.md",
                ],
                outputs=[
                    "self_improvement_patch_proposal.md",
                ],
                tool_hint="artifact_transform",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": [
                        "core_source_snapshot.md",
                        "self_improvement_plan.md",
                    ],
                    "outputs": [
                        "self_improvement_patch_proposal.md",
                    ],
                    "reason": "Generate one exact safe patch proposal.",
                },
            )

        if "snapshot agent source for self improvement" in lower_goal:
            return Task(
                title="Snapshot agent source for self improvement",
                description="Read the agent source files needed to plan safe self-improvements.",
                inputs=[],
                outputs=["self_improvement_source_snapshot.md"],
                tool_hint="source_snapshot",
                kind="normal",
                action={
                    "tool": "source_snapshot",
                    "root": str(Path(__file__).resolve().parents[1]),
                    "files": [
                        "agent/agent_loop.py",
                        "agent/planners/action_selector.py",
                        "agent/planners/verifier.py",
                        "agent/state/task_state.py",
                    ],
                    "outputs": ["self_improvement_source_snapshot.md"],
                    "reason": "Create source context before self-improvement planning.",
                },
            )

        if "self-improvement planning" in lower_goal or "improve agent safely" in lower_goal:
            return Task(
                title="Create self-improvement plan",
                description="Analyze what small safe improvement the agent should make next, without editing code yet.",
                inputs=[],
                outputs=["self_improvement_plan.md"],
                tool_hint="artifact_transform",
                kind="normal",
                action={
                    "tool": "artifact_transform",
                    "inputs": [],
                    "outputs": ["self_improvement_plan.md"],
                    "reason": "Create a safe plan before allowing the agent to modify itself.",
                },
            )

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
