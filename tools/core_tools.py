def run_shell_tool(agent_loop, task, action):
    return agent_loop.run_tool(
        "shell",
        command=action["command"],
        cwd=str(agent_loop.target_project_dir),
    )


def run_file_tool(agent_loop, task, action):
    return agent_loop.run_tool(
        "file",
        action=action["action"],
        path=action["path"],
        content=action.get("content", ""),
    )


def run_artifact_transform_tool(agent_loop, task, action):
    return agent_loop.transform_artifacts(task, action)


def run_source_snapshot_tool(agent_loop, task, action):
    return agent_loop.create_source_snapshot(task, action)


def run_apply_safe_change_tool(agent_loop, task, action):
    return agent_loop.apply_safe_change(task, action)


def run_verify_target_file_tool(agent_loop, task, action):
    return agent_loop.verify_target_file(task, action)


def run_self_improvement_pipeline_tool(agent_loop, task, action):
    return agent_loop.execute_approved_self_improvement_pipeline()


def run_materialize_artifact_tool(agent_loop, task, action):
    return agent_loop.materialize_artifact(task, action)


def run_subworkflow_tool(agent_loop, task, action):
    return agent_loop.execute_subworkflow(task, action)
