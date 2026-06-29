from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha1


def create_demand(title, request, requester, success_criteria=None, budget=None, permissions=None):
    demand_id = _stable_id("demand", title, request, requester.get("id", ""))
    return {
        "apiVersion": "agent.delivery.loop/v0",
        "kind": "Demand",
        "metadata": {
            "id": demand_id,
            "title": title,
            "created_at": _now(),
        },
        "spec": {
            "requester": dict(requester),
            "request": request,
            "success_criteria": list(success_criteria or []),
            "budget": dict(budget or {}),
            "permissions": dict(permissions or {}),
        },
    }


def create_goal_from_demand(demand, objective=None):
    title = demand["metadata"]["title"]
    goal_id = _stable_id("goal", demand["metadata"]["id"], title)
    spec = demand["spec"]
    return {
        "apiVersion": "agent.delivery.loop/v0",
        "kind": "Goal",
        "metadata": {
            "id": goal_id,
            "title": title,
            "created_at": _now(),
            "demand_id": demand["metadata"]["id"],
        },
        "spec": {
            "requester": dict(spec["requester"]),
            "objective": objective or spec["request"],
            "success_criteria": list(spec.get("success_criteria") or []),
            "risk_boundary": dict(spec.get("permissions") or {}),
            "budget": dict(spec.get("budget") or {}),
            "state": {
                "status": "active",
                "current_task_ids": [],
                "completed_task_ids": [],
                "blocked_reason": None,
            },
        },
    }


def _stable_id(prefix, *parts):
    digest = sha1("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def _now():
    return datetime.now(timezone.utc).isoformat()
