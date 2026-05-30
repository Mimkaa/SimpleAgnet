from agent.tools.tool_registry import ToolRegistry
from agent.tools.core_tools import (
    run_apply_safe_change_tool,
    run_artifact_transform_tool,
    run_file_tool,
    run_materialize_artifact_tool,
    run_self_improvement_pipeline_tool,
    run_shell_tool,
    run_source_snapshot_tool,
    run_subworkflow_tool,
    run_verify_target_file_tool,
)


def build_tool_registry(agent_loop) -> ToolRegistry:
    """
    Build the core tool registry.

    This registry keeps AgentLoop behavior stable while moving dispatch
    decisions out of the execute_next_action if/elif chain.
    """
    registry = ToolRegistry()

    registry.register(
        "shell",
        lambda task, action: run_shell_tool(agent_loop, task, action),
    )
    registry.register(
        "file",
        lambda task, action: run_file_tool(agent_loop, task, action),
    )
    registry.register(
        "artifact_transform",
        lambda task, action: run_artifact_transform_tool(agent_loop, task, action),
    )
    registry.register(
        "source_snapshot",
        lambda task, action: run_source_snapshot_tool(agent_loop, task, action),
    )
    registry.register(
        "apply_safe_change",
        lambda task, action: run_apply_safe_change_tool(agent_loop, task, action),
    )
    registry.register(
        "verify_target_file",
        lambda task, action: run_verify_target_file_tool(agent_loop, task, action),
    )
    registry.register(
        "self_improvement_pipeline",
        lambda task, action: run_self_improvement_pipeline_tool(agent_loop, task, action),
    )
    registry.register(
        "materialize_artifact",
        lambda task, action: run_materialize_artifact_tool(agent_loop, task, action),
    )
    registry.register(
        "subworkflow",
        lambda task, action: run_subworkflow_tool(agent_loop, task, action),
    )

    return registry
