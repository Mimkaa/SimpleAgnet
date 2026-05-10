import json
import os
from typing import List

from openai import OpenAI

from agent.state.task_state import Task
from agent.planners.task_validator import TaskValidator


class OpenAITaskPlanner:
    """
    Uses OpenAI to turn a user goal into executable Task objects.

    It should return tasks with:
    - title
    - description
    - tool_hint
    - kind
    - inputs
    - outputs
    - action
    """

    def __init__(self):
        self.client = OpenAI()
        self.model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        self.validator = TaskValidator()

    def create_tasks(self, goal: str, available_tools: list[str]) -> List[Task]:
        prompt = self._build_prompt(goal, available_tools)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a cautious task planner for a local repo automation agent. "
                        "Return only valid JSON. Do not include markdown."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.2,
        )

        text = response.choices[0].message.content.strip()
        data = json.loads(text)

        if not isinstance(data, dict):
            raise ValueError("Planner response must be a JSON object.")

        tasks_data = data.get("tasks", [])

        if not isinstance(tasks_data, list):
            raise ValueError("Planner response must contain a tasks list.")

        tasks = []

        for item in tasks_data:
            tasks.append(
                Task(
                    title=item["title"],
                    description=item.get("description", ""),
                    inputs=item.get("inputs", []),
                    outputs=item.get("outputs", []),
                    tool_hint=item.get("tool_hint"),
                    action=item.get("action", {}),
                    kind=item.get("kind", "normal"),
                )
            )

        return self.validator.validate_tasks(tasks)

    def _build_prompt(self, goal: str, available_tools: list[str]) -> str:
        return f"""
Create a safe task plan for this goal:

{goal}

Available tools:
{available_tools}

The agent can execute these action tool types:

1. shell

Example:
{{
  "tool": "shell",
  "command": "dir /s /b",
  "outputs": ["project_structure_raw.txt"],
  "reason": "List project files."
}}

2. artifact_transform

Example:
{{
  "tool": "artifact_transform",
  "inputs": ["project_structure_summary.md"],
  "outputs": ["entry_point.md"],
  "reason": "Analyze an existing artifact."
}}

3. source_snapshot

Example:
{{
  "tool": "source_snapshot",
  "files": ["src/main.py", "README.md"],
  "outputs": ["core_source_snapshot.md"],
  "reason": "Read important source files."
}}

4. apply_safe_change

Example:
{{
  "tool": "apply_safe_change",
  "target_file": "src/logger.py",
  "outputs": ["change_report.md"],
  "reason": "Apply a tiny safe change."
}}

Return JSON only with this exact shape:

{{
  "tasks": [
    {{
      "title": "...",
      "description": "...",
      "kind": "normal",
      "inputs": [],
      "outputs": [],
      "tool_hint": "shell",
      "action": {{
        "tool": "shell",
        "command": "...",
        "outputs": [],
        "reason": "..."
      }}
    }}
  ]
}}

Important safety rules:
- Return valid JSON only.
- Do not include markdown.
- Do not suggest destructive commands.
- Do not delete files.
- Do not use network commands.
- Do not run git push.
- Prefer inspection and analysis before changes.
- Every executable task must include an explicit action object.
- Use Windows-compatible shell commands.
- For project structure on Windows, use exactly: dir /s /b
- Use artifact names consistently between task outputs and later task inputs.
- Only include apply_safe_change if the user goal explicitly asks to apply a safe code change.

General planning rules:
- Prefer small, sequential tasks.
- Each task should have a clear purpose.
- Analysis tasks should usually read artifacts created by earlier tasks.
- Do not stop immediately after reading source files if the goal asks for an explanation.
- After source_snapshot, include at least one artifact_transform task to analyze the source snapshot.
- When analyzing any software project, create a project_profile.md artifact after reading project structure and relevant source files.
- project_profile.md should summarize:
  - project type / language
  - source layout
  - test layout
  - important files
  - likely run command
  - likely test command
  - special environment or import path rules
  - warnings or assumptions
- Future run/test tasks should use project_profile.md when choosing commands.
- Do not invent file names unless they are common project files or produced artifacts.
- If the exact source files are unknown, first inspect the project structure, then choose likely files.
- Every artifact_transform action must include at least one output artifact.
- Never use empty outputs.
- For final explanation tasks, write to a named artifact such as runtime_flow_explanation.md.
- Shell commands must be Windows cmd compatible. Do not use POSIX shell syntax like [ -f ], sed, wc, grep, cat.
- Do not use here-documents or shell redirection syntax like <<. Use python -c "..." for portable Python diagnostics on Windows.
- Do not use shell commands to inspect agent artifacts unless you know their full path.
- Do not use the same artifact name as both the main input and the only output of an artifact_transform task.
- If the plan includes a run/verification task for a repo, prefer the discovered entry point.
- If entry_point.md exists or is produced earlier, use it as input to the verification-planning task.
- Do not run arbitrary component/module files unless they are confirmed as entry points.
- If a common entry file exists, such as src/main.py, main.py, or app.py, prefer the matching run command.
- If the project has a tests folder and the goal asks to verify behavior, include a safe test command.
- For Python projects, prefer: python -m pytest
- When planning a Python project with a src directory and tests import modules from src, prefer running pytest with src temporarily added to PYTHONPATH using this Windows-safe command:
  python -c "import os, subprocess, sys; env=os.environ.copy(); env['PYTHONPATH']='src'; raise SystemExit(subprocess.run([sys.executable, '-m', 'pytest'], env=env).returncode)"
- Use outputs: ["test_results.txt"] for test commands.
- Do not require the user to manually set PYTHONPATH.
- If pytest is unavailable, a repair task may suggest: python -m unittest discover
- Test commands must be read-only verification commands.
- Do not create destructive test commands.
- If tests are run, the shell test task must declare test_results.txt in both:
  - the task outputs field
  - the action outputs field
- If tests are run, create a follow-up artifact_transform task that explains whether the relevant behavior is correct.
- The test explanation task must use a different output artifact than its input artifact.
- If the input is test_results.txt, output test_behavior_report.md.
- Never use test_behavior_report.md as both the only input and the only output.

Repository analysis planning pattern:
For repository analysis goals, prefer this pattern unless the user goal clearly requires something else:

1. Inspect project structure.
   - tool_hint: shell
   - action.tool: shell
   - command: dir /s /b
   - outputs should include:
     - project_structure_raw.txt
     - project_structure_summary.md
   - action.outputs may include:
     - project_structure_raw.txt

2. Identify the main entry point.
   - tool_hint: artifact_transform
   - input:
     - project_structure_summary.md
   - output:
     - entry_point.md

3. Map core components.
   - tool_hint: artifact_transform
   - input:
     - project_structure_summary.md
   - output:
     - core_components.md

4. Read relevant source files.
   - tool_hint: source_snapshot
   - action.tool: source_snapshot
   - files should include likely entry point and core files.
   - For a small Python project, likely useful files include:
     - src/main.py
     - README.md
   - If the goal mentions firewall, packet, rules, or network behavior, also include likely files:
     - src/firewall.py
     - src/rule_engine.py
     - src/packet.py
     - src/decision.py
     - src/logger.py
     - rules/rules.json
   - output:
     - core_source_snapshot.md

5. Create a reusable project profile.
   - tool_hint: artifact_transform
   - inputs:
     - project_structure_summary.md
     - core_source_snapshot.md
   - output:
     - project_profile.md
   - The project profile should summarize:
     - project type / language
     - source layout
     - test layout
     - important files
     - likely run command
     - likely test command
     - special environment or import path rules
     - warnings or assumptions

6. Analyze the source snapshot.
   - tool_hint: artifact_transform
   - input:
     - core_source_snapshot.md
     - project_profile.md
   - output:
     - confirmed_runtime_flow.md

7. Produce the requested final explanation.
   - Use artifact_transform.
   - Inputs should include:
     - confirmed_runtime_flow.md
     - project_profile.md
   - Every final explanation task must have a non-empty outputs list.
   - If the goal asks for runtime flow, output:
     - runtime_flow_explanation.md
   - If the goal asks for packet/request flow, output:
     - packet_flow.md
   - If the goal asks for architecture summary, output:
     - architecture_summary.md

8. If and only if the goal asks for a tiny safe change:
   - First create a suggestion artifact:
     - safe_change_suggestion.md
   - Then apply the change with apply_safe_change.
   - The change must be tiny and reversible.

9. If the goal asks to verify that the project runs:
   - Use shell.
   - Prefer the confirmed or likely main entry point.
   - Use project_profile.md if it exists to choose the run command.
   - If an earlier task produced entry_point.md, use that artifact to guide the run command.
   - Do not run random component/module files as verification commands.
   - For common Python projects, typical entry commands may be:
     - python src/main.py
     - python main.py
     - python app.py
   - Choose the command that matches the discovered project structure.

10. If the goal asks to verify tests or behavior:
   - Use shell.
   - Prefer the project test command.
   - Use project_profile.md if it exists to choose the test command.
   - For Python projects with a tests folder, prefer:
     - python -m pytest
   - If the project uses a src layout or imports modules from src, prefer:
     - python -c "import os, subprocess, sys; env=os.environ.copy(); env['PYTHONPATH']='src'; raise SystemExit(subprocess.run([sys.executable, '-m', 'pytest'], env=env).returncode)"
   - If pytest is unavailable, a repair task may suggest:
     - python -m unittest discover
   - The test shell task must declare this output artifact in the task outputs:
     - test_results.txt
   - The test shell task must also declare this output artifact in action.outputs:
     - test_results.txt
   - After running tests, create an artifact_transform task that explains whether the relevant behavior is correct.
   - That analysis task should use:
     - input: test_results.txt
     - output: test_behavior_report.md
   - Never use the same artifact name as both input and output.
   - Never use test_behavior_report.md as both the only input and the only output.

For this specific goal, create enough tasks to fully satisfy the user request.
Do not create only 2 or 3 vague tasks if the goal asks for runtime flow, request tracing, tests, or behavior verification.
"""