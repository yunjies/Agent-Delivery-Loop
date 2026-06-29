from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha1


def create_loop_decision(
    goal,
    action,
    reason,
    next_task=None,
    required_approval=None,
    budget_assessment=None,
    risk_assessment=None,
):
    goal_id = goal["metadata"]["id"]
    decision_id = _stable_id("decision", goal_id, action, reason)
    return {
        "apiVersion": "agent.delivery.loop/v0",
        "kind": "LoopDecision",
        "metadata": {
            "id": decision_id,
            "goal_id": goal_id,
            "created_at": _now(),
        },
        "spec": {
            "action": action,
            "reason": reason,
            "next_task": next_task,
            "required_approval": required_approval,
            "budget_assessment": dict(budget_assessment or {}),
            "risk_assessment": dict(risk_assessment or {}),
        },
    }


def _stable_id(prefix, *parts):
    digest = sha1("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def _now():
    return datetime.now(timezone.utc).isoformat()
