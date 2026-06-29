from __future__ import annotations

import json
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
    review_feedback=None,
    next_prompt=None,
):
    goal_id = goal["metadata"]["id"]
    decision_id = _stable_id(
        "decision",
        goal_id,
        action,
        reason,
        _stable_json(next_task),
        _stable_json(required_approval),
        _stable_json(review_feedback),
        next_prompt or "",
    )
    decision = {
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
    if review_feedback is not None:
        decision["spec"]["review_feedback"] = dict(review_feedback)
    if next_prompt is not None:
        decision["spec"]["next_prompt"] = next_prompt
    return decision


def _stable_id(prefix, *parts):
    digest = sha1("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def _stable_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True) if value is not None else ""


def _now():
    return datetime.now(timezone.utc).isoformat()
