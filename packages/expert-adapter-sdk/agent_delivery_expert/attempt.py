from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha1


def create_attempt(task, executor, status, summary, evidence=None, budget_used=None, error=None):
    task_id = task["metadata"]["id"]
    goal_id = task["metadata"]["goal_id"]
    attempt_id = _stable_id("attempt", task_id, executor.get("id", ""), status, summary)
    return {
        "apiVersion": "agent.delivery.loop/v0",
        "kind": "Attempt",
        "metadata": {
            "id": attempt_id,
            "task_id": task_id,
            "goal_id": goal_id,
            "started_at": _now(),
            "finished_at": _now(),
        },
        "spec": {
            "executor": dict(executor),
            "result": {
                "status": status,
                "summary": summary,
                "evidence": list(evidence or []),
                "budget_used": dict(budget_used or {}),
                "error": error,
            },
        },
    }


def _stable_id(prefix, *parts):
    digest = sha1("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def _now():
    return datetime.now(timezone.utc).isoformat()
