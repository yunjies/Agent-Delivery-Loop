from __future__ import annotations


def create_profile_task_payload(task, profile, prompt, skills=None, mode="supervised"):
    """Create a serializable Hermes profile invocation plan.

    This function does not execute Hermes. It only creates the adapter payload a
    controlled runner can inspect and execute later.
    """

    return {
        "adapter": "hermes_profile",
        "profile": profile,
        "mode": mode,
        "task_id": task["metadata"]["id"],
        "goal_id": task["metadata"]["goal_id"],
        "prompt": prompt,
        "skills": list(skills or []),
        "permissions": dict(task["spec"].get("permissions") or {}),
        "acceptance": dict(task["spec"].get("acceptance") or {}),
    }
