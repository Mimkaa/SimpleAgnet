from pathlib import Path


def verify_target_file(agent_loop, task, action: dict):
    """
    Verify that a target file exists, can be read, and contains required text.

    This function was moved out of AgentLoop so verification tool behavior can
    live in a dedicated tool module while keeping compatibility with existing
    helper methods and artifact storage.
    """
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
        if not agent_loop.artifacts.exists(must_contain_from_artifact):
            return {
                "ok": False,
                "message": f"Verification requirements artifact not found: {must_contain_from_artifact}",
            }

        requirements_text = agent_loop.artifacts.read_text(must_contain_from_artifact)
        extracted = agent_loop.extract_must_contain_requirements(requirements_text)

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

    seen = set()
    must_contain = [
        item for item in must_contain
        if item and not (item in seen or seen.add(item))
    ]

    if root_value == "target_project":
        root = Path(agent_loop.target_project_dir)
    else:
        root = Path(root_value)

    target_path = root / target_file

    try:
        result = agent_loop.run_tool(
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

    artifact_path = agent_loop.artifacts.write_text(outputs[0], "\n".join(report))

    agent_loop.event_log.write(
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
