from __future__ import annotations


ALLOWED_MESSAGE_TYPES = {
    "status_report",
    "acceptance_result",
    "approval_request",
    "blocked_notice",
    "budget_stop",
    "next_step_proposal",
}


def create_notification_payload(goal, message_type, content, target, task=None, evidence=None):
    if message_type not in ALLOWED_MESSAGE_TYPES:
        raise ValueError(f"unsupported message_type: {message_type}")
    payload = {
        "adapter": "feishu_notification",
        "message_type": message_type,
        "target": dict(target),
        "goal_id": goal["metadata"]["id"],
        "content": content,
        "evidence": list(evidence or []),
    }
    if task is not None:
        payload["task_id"] = task["metadata"]["id"]
    return payload
