class ActionSelector:
    def select_action(self, task):
        action_config = getattr(task, "action", {}) or {}

        # 1. Preferred path: task provides exact executable action.
        if action_config:
            return self.action_from_config(task, action_config)

        # 2. Fallback path: no exact action, use generic tool_hint.
        return self.action_from_hint(task)

    def action_from_config(self, task, action_config: dict):
        tool = action_config.get("tool", task.tool_hint)

        if tool == "shell":
            return {
                "tool": "shell",
                "command": action_config["command"],
                "reason": action_config.get(
                    "reason",
                    "Task provided explicit shell action.",
                ),
            }

        if tool == "file":
            return {
                "tool": "file",
                "action": action_config.get("action", "write"),
                "path": action_config["path"],
                "content": action_config.get("content", ""),
                "reason": action_config.get(
                    "reason",
                    "Task provided explicit file action.",
                ),
            }

        if tool == "artifact_transform":
            return {
                "tool": "artifact_transform",
                "inputs": action_config.get("inputs", task.inputs),
                "outputs": action_config.get("outputs", task.outputs),
                "reason": action_config.get(
                    "reason",
                    "Task provided explicit artifact transform action.",
                ),
            }

        if tool == "source_snapshot":
            return {
                "tool": "source_snapshot",
                "files": action_config.get("files", []),
                "outputs": action_config.get("outputs", task.outputs),
                "reason": action_config.get(
                    "reason",
                    "Task provided explicit source snapshot action.",
                ),
            }

        if tool == "apply_safe_change":
            return {
                "tool": "apply_safe_change",
                "target_file": action_config.get("target_file", "src/logger.py"),
                "outputs": action_config.get("outputs", task.outputs),
                "reason": action_config.get(
                    "reason",
                    "Task provided explicit safe change action.",
                ),
            }

        return {
            "tool": "none",
            "reason": f"Unknown explicit tool: {tool}",
        }

    def action_from_hint(self, task):
        """
        Fallback only. This should become less important over time.
        """

        if task.tool_hint == "analyze_artifact":
            return {
                "tool": "artifact_transform",
                "inputs": task.inputs,
                "outputs": task.outputs,
                "reason": "Fallback: task requested artifact analysis/transformation.",
            }

        if task.tool_hint == "shell":
            return {
                "tool": "shell",
                "command": "dir",
                "reason": "Fallback: shell task had no explicit command.",
            }

        if task.tool_hint == "file":
            return {
                "tool": "file",
                "action": "write",
                "path": ".agent_data/artifacts/notes.txt",
                "content": "Notes:\n",
                "reason": "Fallback: file task had no explicit file action.",
            }

        return {
            "tool": "none",
            "reason": "No explicit action and no supported fallback tool_hint.",
        }