from pathlib import Path
import fnmatch


def create_source_snapshot(agent_loop, task, action: dict):
    """
    Create a source snapshot artifact from selected files in a root directory.

    This function was moved out of AgentLoop so source snapshot behavior can
    live in a dedicated tool module while still using AgentLoop services for
    artifacts, event logging, and low-level file reads.
    """
    root_value = action.get("root", "target_project")

    if root_value == "target_project":
        root = Path(agent_loop.target_project_dir)
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
            result = agent_loop.run_tool(
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

    artifact_path = agent_loop.artifacts.write_text(output_name, artifact_content)

    agent_loop.event_log.write(
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
