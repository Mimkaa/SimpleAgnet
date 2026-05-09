from agent.state.task_state import Task


class TaskValidationError(ValueError):
    pass


class TaskValidator:
    """
    Validates AI-created tasks before they enter the task store.

    This is a safety layer:
    OpenAI proposes tasks, but this validator decides whether they are acceptable.
    """

    DISALLOWED_COMMAND_PARTS = [
        "del ",
        "erase ",
        "rmdir",
        "rd ",
        "format",
        "shutdown",
        "restart",
        "git push",
        "git reset --hard",
        "git clean",
        "curl ",
        "wget ",
        "invoke-webrequest",
        "start-bitstransfer",
        "powershell -enc",
        "remove-item",
    ]

    POSIX_ONLY_PARTS = [
        "if [",
        "<<",
        "sed ",
        "wc ",
        "grep ",
        "cat ",
        "rm ",
        "chmod ",
        "chown ",
        "touch ",
        "find .",
    ]

    ALLOWED_TOOLS = {
        "shell",
        "file",
        "artifact_transform",
        "source_snapshot",
        "apply_safe_change",
    }

    def validate_tasks(self, tasks: list[Task]) -> list[Task]:
        if not tasks:
            raise TaskValidationError("Planner returned no tasks.")

        for index, task in enumerate(tasks):
            self.validate_task(task, index)

        return tasks

    def validate_task(self, task: Task, index: int):
        if not task.title or not task.title.strip():
            raise TaskValidationError(f"Task {index} has no title.")

        action = getattr(task, "action", {}) or {}

        if not action:
            raise TaskValidationError(
                f"Task {index} ({task.title}) has no action. "
                "AI-created tasks must include explicit action objects."
            )

        tool = action.get("tool")

        if not tool:
            raise TaskValidationError(
                f"Task {index} ({task.title}) action has no tool."
            )

        if tool not in self.ALLOWED_TOOLS:
            raise TaskValidationError(
                f"Task {index} ({task.title}) uses unsupported tool: {tool}"
            )

        if tool == "shell":
            self.validate_shell_task(task, index, action)

        elif tool == "file":
            self.validate_file_task(task, index, action)

        elif tool == "artifact_transform":
            self.validate_artifact_transform_task(task, index, action)

        elif tool == "source_snapshot":
            self.validate_source_snapshot_task(task, index, action)

        elif tool == "apply_safe_change":
            self.validate_apply_safe_change_task(task, index, action)

    def validate_shell_task(self, task: Task, index: int, action: dict):
        command = action.get("command", "")

        if not command or not command.strip():
            raise TaskValidationError(
                f"Task {index} ({task.title}) shell action has no command."
            )

        lowered = command.lower()

        for bad in self.DISALLOWED_COMMAND_PARTS:
            if bad in lowered:
                raise TaskValidationError(
                    f"Task {index} ({task.title}) contains unsafe shell command part: {bad}"
                )

        for bad in self.POSIX_ONLY_PARTS:
            if bad in lowered:
                raise TaskValidationError(
                    f"Task {index} ({task.title}) contains POSIX-only shell syntax: {bad}"
                )

    def validate_file_task(self, task: Task, index: int, action: dict):
        file_action = action.get("action")

        if file_action not in {"read", "write"}:
            raise TaskValidationError(
                f"Task {index} ({task.title}) file action must be read or write."
            )

        path = action.get("path", "")

        if not path:
            raise TaskValidationError(
                f"Task {index} ({task.title}) file action has no path."
            )

        lowered = path.lower()

        if ".." in lowered:
            raise TaskValidationError(
                f"Task {index} ({task.title}) file path must not contain '..'."
            )

    def validate_artifact_transform_task(self, task: Task, index: int, action: dict):
        inputs = action.get("inputs", task.inputs)
        outputs = action.get("outputs", task.outputs)

        if not isinstance(inputs, list):
            raise TaskValidationError(
                f"Task {index} ({task.title}) artifact_transform inputs must be a list."
            )

        if not isinstance(outputs, list):
            raise TaskValidationError(
                f"Task {index} ({task.title}) artifact_transform outputs must be a list."
            )

        if not outputs:
            raise TaskValidationError(
                f"Task {index} ({task.title}) artifact_transform must have at least one output."
            )

        for output in outputs:
            self.validate_artifact_name(task, index, output, "output")

        for input_name in inputs:
            self.validate_artifact_name(task, index, input_name, "input")

        if len(inputs) == 1 and len(outputs) == 1 and inputs[0] == outputs[0]:
            raise TaskValidationError(
                f"Task {index} ({task.title}) must not use the same artifact as only input and only output."
            )

    def validate_source_snapshot_task(self, task: Task, index: int, action: dict):
        files = action.get("files", [])
        outputs = action.get("outputs", task.outputs)

        if not isinstance(files, list):
            raise TaskValidationError(
                f"Task {index} ({task.title}) source_snapshot files must be a list."
            )

        if not files:
            raise TaskValidationError(
                f"Task {index} ({task.title}) source_snapshot must include files."
            )

        if not isinstance(outputs, list):
            raise TaskValidationError(
                f"Task {index} ({task.title}) source_snapshot outputs must be a list."
            )

        if not outputs:
            raise TaskValidationError(
                f"Task {index} ({task.title}) source_snapshot must have at least one output."
            )

        for file_path in files:
            if not isinstance(file_path, str) or not file_path.strip():
                raise TaskValidationError(
                    f"Task {index} ({task.title}) has invalid source file path."
                )

            if ".." in file_path:
                raise TaskValidationError(
                    f"Task {index} ({task.title}) source file path must not contain '..'."
                )

        for output in outputs:
            self.validate_artifact_name(task, index, output, "output")

    def validate_apply_safe_change_task(self, task: Task, index: int, action: dict):
        target_file = action.get("target_file", "")
        outputs = action.get("outputs", task.outputs)

        if not target_file:
            raise TaskValidationError(
                f"Task {index} ({task.title}) apply_safe_change requires target_file."
            )

        if ".." in target_file:
            raise TaskValidationError(
                f"Task {index} ({task.title}) target_file must not contain '..'."
            )

        if not outputs:
            raise TaskValidationError(
                f"Task {index} ({task.title}) apply_safe_change must have an output report."
            )

        for output in outputs:
            self.validate_artifact_name(task, index, output, "output")

    def validate_artifact_name(self, task: Task, index: int, name: str, field_name: str):
        if not isinstance(name, str) or not name.strip():
            raise TaskValidationError(
                f"Task {index} ({task.title}) has invalid artifact {field_name}."
            )

        lowered = name.lower()

        if ".." in lowered or "\\" in name or "/" in name:
            raise TaskValidationError(
                f"Task {index} ({task.title}) artifact {field_name} must be a simple file name: {name}"
            )

        if not (
            lowered.endswith(".md")
            or lowered.endswith(".txt")
            or lowered.endswith(".json")
        ):
            raise TaskValidationError(
                f"Task {index} ({task.title}) artifact {field_name} must end with .md, .txt, or .json: {name}"
            )