from agent.tools.apply_safe_change_tool import apply_safe_change
from agent.tools.artifact_transform_tool import transform_artifacts
from agent.tools.materialize_artifact_tool import materialize_artifact
from agent.tools.self_improvement_pipeline_tool import execute_approved_self_improvement_pipeline
from agent.tools.source_snapshot_tool import create_source_snapshot
from agent.tools.subworkflow_tool import execute_subworkflow
from agent.tools.verify_target_file_tool import verify_target_file


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
    return transform_artifacts(agent_loop, task, action)


def run_source_snapshot_tool(agent_loop, task, action):
    return create_source_snapshot(agent_loop, task, action)


def run_apply_safe_change_tool(agent_loop, task, action):
    return apply_safe_change(agent_loop, task, action)


def run_verify_target_file_tool(agent_loop, task, action):
    return verify_target_file(agent_loop, task, action)


def run_self_improvement_pipeline_tool(agent_loop, task, action):
    return execute_approved_self_improvement_pipeline(agent_loop, task, action)


def run_materialize_artifact_tool(agent_loop, task, action):
    return materialize_artifact(agent_loop, task, action)


def run_subworkflow_tool(agent_loop, task, action):
    return execute_subworkflow(agent_loop, task, action)
