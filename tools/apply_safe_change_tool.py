from pathlib import Path


def apply_safe_change(agent_loop, task, action: dict):
    """
    Apply a guarded text replacement to a target file.

    This function was moved out of AgentLoop so safe-change behavior can live in
    a dedicated tool module while still using AgentLoop services for file/shell
    tools, artifacts, event logging, and helper behavior.
    """
    target_file = action.get("target_file")
    outputs = action.get("outputs", [])

    if not target_file:
        return {"ok": False, "message": "No target file specified."}

    if not outputs:
        return {"ok": False, "message": "No output artifact specified."}

    root = Path(action.get("root", agent_loop.target_project_dir))
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
        write_setup_result = agent_loop.run_tool(
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

    read_result = agent_loop.run_tool("file", action="read", path=str(target_path))

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
        run_result = agent_loop.run_tool(
            "shell",
            command=run_command,
            cwd=str(root),
        )

        cleanup_result = None

        if cleanup_after:
            cleanup_result = agent_loop.run_tool(
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

        artifact_path = agent_loop.artifacts.write_text(outputs[0], "\n".join(report))

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
            artifact_path = agent_loop.artifacts.write_text(outputs[0], report)

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
        artifact_path = agent_loop.artifacts.write_text(outputs[0], report)

        return {
            "ok": False,
            "message": "No safe replacement changed the target file.",
            "artifact": str(artifact_path),
            "setup_created_file": setup_created_file,
            "run_command": run_command,
        }

    backup_result = agent_loop.run_tool(
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

    write_result = agent_loop.run_tool(
        "file",
        action="write",
        path=str(target_path),
        content=new_content,
    )

    if not write_result.get("ok"):
        rollback_result = agent_loop.run_tool(
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

    verify_read_result = agent_loop.run_tool("file", action="read", path=str(target_path))
    verify_content = verify_read_result.get("content", "")

    content_verified = (
        verify_read_result.get("ok")
        and (expected_text is None or expected_text in verify_content)
        and (forbidden_text is None or forbidden_text not in verify_content)
    )

    run_result = agent_loop.run_tool(
        "shell",
        command=run_command,
        cwd=str(root),
    )

    cleanup_result = None

    if cleanup_after:
        cleanup_result = agent_loop.run_tool(
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
        backup_cleanup_result = agent_loop.run_tool(
            "file",
            action="delete",
            path=str(backup_path),
        )

    if not ok and backup_written:
        rollback_result = agent_loop.run_tool(
            "file",
            action="write",
            path=str(target_path),
            content=old_content,
        )
        rollback_done = bool(rollback_result.get("ok"))

        if cleanup_after:
            rollback_cleanup_result = agent_loop.run_tool(
                "file",
                action="delete",
                path=str(target_path),
            )

        backup_cleanup_result = agent_loop.run_tool(
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

    artifact_path = agent_loop.artifacts.write_text(outputs[0], "\n".join(report))

    agent_loop.event_log.write(
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
