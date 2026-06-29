from __future__ import annotations


class ValidationError(ValueError):
    pass


REQUIRED = {
    "Demand": [
        ("apiVersion",),
        ("kind",),
        ("metadata", "id"),
        ("metadata", "title"),
        ("metadata", "created_at"),
        ("spec", "requester"),
        ("spec", "request"),
    ],
    "Goal": [
        ("apiVersion",),
        ("kind",),
        ("metadata", "id"),
        ("metadata", "title"),
        ("metadata", "created_at"),
        ("spec", "requester"),
        ("spec", "objective"),
        ("spec", "success_criteria"),
        ("spec", "state", "status"),
    ],
    "Task": [
        ("apiVersion",),
        ("kind",),
        ("metadata", "id"),
        ("metadata", "goal_id"),
        ("metadata", "created_at"),
        ("spec", "task_type"),
        ("spec", "objective"),
        ("spec", "assignee"),
        ("spec", "permissions"),
        ("spec", "acceptance"),
        ("spec", "state", "status"),
    ],
    "Attempt": [
        ("apiVersion",),
        ("kind",),
        ("metadata", "id"),
        ("metadata", "task_id"),
        ("metadata", "goal_id"),
        ("metadata", "started_at"),
        ("spec", "executor"),
        ("spec", "result", "status"),
        ("spec", "result", "summary"),
        ("spec", "result", "evidence"),
        ("spec", "result", "budget_used"),
    ],
    "Expert": [
        ("apiVersion",),
        ("kind",),
        ("metadata", "id"),
        ("metadata", "title"),
        ("spec", "expert_kind"),
        ("spec", "capabilities"),
        ("spec", "invocation"),
    ],
    "LoopDecision": [
        ("apiVersion",),
        ("kind",),
        ("metadata", "id"),
        ("metadata", "goal_id"),
        ("metadata", "created_at"),
        ("spec", "action"),
        ("spec", "reason"),
    ],
    "Approval": [
        ("apiVersion",),
        ("kind",),
        ("metadata", "id"),
        ("metadata", "goal_id"),
        ("metadata", "created_at"),
        ("spec", "requester"),
        ("spec", "approval_type"),
        ("spec", "question"),
        ("spec", "state", "status"),
    ],
}


def validate_object(obj, expected_kind=None):
    if not isinstance(obj, dict):
        raise ValidationError("object must be a dict")
    kind = obj.get("kind")
    if expected_kind and kind != expected_kind:
        raise ValidationError(f"expected kind {expected_kind}, got {kind}")
    if kind not in REQUIRED:
        raise ValidationError(f"unsupported kind: {kind}")
    if obj.get("apiVersion") != "agent.delivery.loop/v0":
        raise ValidationError("apiVersion must be agent.delivery.loop/v0")
    for path in REQUIRED[kind]:
        if _get(obj, path) in (None, ""):
            raise ValidationError(f"missing required field: {'.'.join(path)}")
    return True


def _get(obj, path):
    cur = obj
    for part in path:
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur
