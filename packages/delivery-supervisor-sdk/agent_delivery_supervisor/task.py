from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha1


def create_task(
    goal,
    task_type,
    objective,
    assignee,
    permissions,
    acceptance,
    budget=None,
    required_capabilities=None,
    path_governance=None,
):
    goal_id = goal["metadata"]["id"]
    task_id = _stable_id("task", goal_id, task_type, objective, assignee.get("id", ""))
    spec = {
        "task_type": task_type,
        "objective": objective,
        "assignee": dict(assignee),
        "permissions": dict(permissions),
        "budget": dict(budget or {}),
        "acceptance": dict(acceptance),
        "state": {
            "status": "pending",
            "latest_attempt_id": None,
        },
    }
    if required_capabilities:
        spec["required_capabilities"] = list(required_capabilities)
    if path_governance:
        spec["path_governance"] = dict(path_governance)
    return {
        "apiVersion": "agent.delivery.loop/v0",
        "kind": "Task",
        "metadata": {
            "id": task_id,
            "goal_id": goal_id,
            "created_at": _now(),
        },
        "spec": spec,
    }


def _stable_id(prefix, *parts):
    digest = sha1("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def _now():
    return datetime.now(timezone.utc).isoformat()
