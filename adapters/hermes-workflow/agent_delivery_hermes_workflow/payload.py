from __future__ import annotations


def create_workflow_task_payload(task, workflow, trigger, mode="production", max_ticks=None):
    """Create a serializable Hermes workflow invocation plan.

    This function does not execute Hermes or mutate workflow state.
    """

    payload = {
        "adapter": "hermes_workflow",
        "workflow": workflow,
        "trigger": trigger,
        "mode": mode,
        "task_id": task["metadata"]["id"],
        "goal_id": task["metadata"]["goal_id"],
        "permissions": dict(task["spec"].get("permissions") or {}),
        "acceptance": dict(task["spec"].get("acceptance") or {}),
    }
    if max_ticks is not None:
        payload["max_ticks"] = int(max_ticks)
    return payload
