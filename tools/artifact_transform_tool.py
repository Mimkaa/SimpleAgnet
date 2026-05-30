def transform_artifacts(agent_loop, task, action: dict):
    """
    Transform input artifacts into a new output artifact.

    This function was moved out of AgentLoop so artifact-transform behavior can
    live in a dedicated tool module while still using AgentLoop helper methods,
    artifact storage, event logging, and analyzer services.
    """
    inputs = action.get("inputs", [])
    outputs = action.get("outputs", [])

    if not outputs:
        return {
            "ok": False,
            "message": "No output artifact specified.",
        }

    input_contents = {}

    for input_name in inputs:
        if not agent_loop.artifacts.exists(input_name):
            return {
                "ok": False,
                "message": f"Missing input artifact: {input_name}",
            }

        input_contents[input_name] = agent_loop.artifacts.read_text(input_name)

    output_name = outputs[0]

    is_critical = bool(action.get("critical", False))
    strip_fences = bool(action.get("strip_fences", False))

    agent_loop.event_log.write(
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
        content = agent_loop.artifact_analyzer.analyze(
            task=task,
            input_contents=input_contents,
            output_name=output_name,
        )

        analyzer_used = "openai"

        if output_name == "cover_letter_verification_requirements.md":
            content = agent_loop.ensure_must_contain_requirements(
                content=content,
                input_contents=input_contents,
            )

    except Exception as e:
        agent_loop.event_log.write(
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

        content = agent_loop.simple_artifact_analysis(
            task=task,
            input_contents=input_contents,
            output_name=output_name,
        )

        analyzer_used = "fallback_simple"

        if output_name == "cover_letter_verification_requirements.md":
            content = agent_loop.ensure_must_contain_requirements(
                content=content,
                input_contents=input_contents,
            )

    if strip_fences:
        content = agent_loop.strip_markdown_code_fences(content)

    if output_name.endswith(".tex"):
        content = agent_loop.clean_latex_artifact(content)

    artifact_path = agent_loop.artifacts.write_text(output_name, content)

    agent_loop.event_log.write(
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
