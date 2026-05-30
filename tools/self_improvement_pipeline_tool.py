def execute_approved_self_improvement_pipeline(agent_loop, task, action: dict):
    """
    Execute the approved self-improvement pipeline.

    This function was moved out of AgentLoop so pipeline execution can live in a
    dedicated tool module while still using AgentLoop's existing helpers for
    creating apply tasks, selecting actions, verifying results, marking task
    state, and running regression tests.
    """
    apply_task = agent_loop.create_task_from_self_improvement_apply_artifact(
        "self_improvement_apply_task.md"
    )

    if not apply_task:
        return {
            "ok": False,
            "message": "Could not create approved self-improvement apply task.",
        }

    apply_action = agent_loop.selector.select_action(apply_task)
    result = agent_loop.apply_safe_change(apply_task, apply_action)

    verification = agent_loop.verifier.verify_action_result(
        apply_task,
        apply_action,
        result,
    )

    result["verification"] = {
        "status": verification.status,
        "reason": verification.reason,
        "exit_code": verification.exit_code,
    }

    if verification.status == "PASS":
        agent_loop.mark_done(apply_task.id)

        regression_result = agent_loop.run_agent_regression_tests_now()
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
        agent_loop.mark_failed(apply_task.id, verification.reason)

    return result
