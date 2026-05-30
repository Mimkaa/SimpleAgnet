from pathlib import Path


def materialize_artifact(agent_loop, task, action: dict):
    """
    Materialize an artifact into a real target project file.

    This function was moved out of AgentLoop so the tool registry can dispatch
    to dedicated tool modules instead of keeping all tool logic inside
    agent_loop.py.
    """
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

    if not agent_loop.artifacts.exists(input_name):
        return {
            "ok": False,
            "message": f"Input artifact not found: {input_name}",
        }

    if root_value == "target_project":
        root = Path(agent_loop.target_project_dir)
    else:
        root = Path(root_value)

    target_path = root / target_file

    content = agent_loop.artifacts.read_text(input_name)

    if target_file.endswith(".tex"):
        content = agent_loop.clean_latex_artifact(content)

    try:
        write_result = agent_loop.run_tool(
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

    agent_loop.event_log.write(
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
