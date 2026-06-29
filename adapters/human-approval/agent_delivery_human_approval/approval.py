from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha1


def create_approval_request(goal, approval_type, question, requester=None, task=None, context=None):
    goal_id = goal["metadata"]["id"]
    task_id = task["metadata"]["id"] if task else None
    approval_id = _stable_id("approval", goal_id, task_id or "", approval_type, question)
    return {
        "apiVersion": "agent.delivery.loop/v0",
        "kind": "Approval",
        "metadata": {
            "id": approval_id,
            "goal_id": goal_id,
            "task_id": task_id,
            "created_at": _now(),
            "resolved_at": None,
        },
        "spec": {
            "requester": dict(requester or goal["spec"]["requester"]),
            "approval_type": approval_type,
            "question": question,
            "context": dict(context or {}),
            "state": {
                "status": "pending",
                "decision_by": None,
                "reason": None,
            },
        },
    }


def approve(approval, actor, reason=None):
    return _resolve(approval, "approved", actor, reason)


def reject(approval, actor, reason=None):
    return _resolve(approval, "rejected", actor, reason)


def _resolve(approval, status, actor, reason):
    current = approval["spec"]["state"]["status"]
    if current != "pending":
        raise ValueError(f"approval is already resolved: {current}")
    approval["spec"]["state"]["status"] = status
    approval["spec"]["state"]["decision_by"] = dict(actor)
    approval["spec"]["state"]["reason"] = reason
    approval["metadata"]["resolved_at"] = _now()
    return approval


def _stable_id(prefix, *parts):
    digest = sha1("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def _now():
    return datetime.now(timezone.utc).isoformat()
