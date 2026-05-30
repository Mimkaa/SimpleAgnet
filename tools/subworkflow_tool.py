def execute_subworkflow(agent_loop, task, action: dict):
    """
    Expand a subworkflow action into concrete tasks.

    This function was moved out of AgentLoop so subworkflow behavior can live in
    a dedicated tool module while still using AgentLoop's workflow list, task
    store, and event log.
    """
    goal = action.get("goal")

    if not goal:
        return {
            "ok": False,
            "message": "Subworkflow action missing goal.",
        }

    matching_workflow = None

    for workflow in agent_loop.workflows:
        if workflow.can_handle(goal):
            matching_workflow = workflow
            break

    if matching_workflow is None:
        return {
            "ok": False,
            "message": f"No workflow can handle subworkflow goal: {goal}",
        }

    sub_tasks = matching_workflow.create_tasks(goal)

    if not sub_tasks:
        return {
            "ok": False,
            "message": f"Subworkflow produced no tasks for goal: {goal}",
        }

    workflow_group_id = task.workflow_group_id or task.id

    for sub_task in sub_tasks:
        sub_task.parent_task_id = task.id
        sub_task.workflow_group_id = workflow_group_id

    agent_loop.task_store.insert_tasks_after(task.id, sub_tasks)

    agent_loop.task_store.assign_workflow_group_after(
        task_id=task.id,
        workflow_group_id=workflow_group_id,
    )

    agent_loop.event_log.write(
        "subworkflow_expanded",
        {
            "task_id": task.id,
            "goal": goal,
            "workflow": matching_workflow.__class__.__name__,
            "created_tasks": [
                {
                    "id": sub_task.id,
                    "title": sub_task.title,
                }
                for sub_task in sub_tasks
            ],
        },
    )

    return {
        "ok": True,
        "message": f"Expanded subworkflow goal: {goal}",
        "workflow": matching_workflow.__class__.__name__,
        "created_task_count": len(sub_tasks),
        "created_tasks": [
            {
                "id": sub_task.id,
                "title": sub_task.title,
            }
            for sub_task in sub_tasks
        ],
    }
