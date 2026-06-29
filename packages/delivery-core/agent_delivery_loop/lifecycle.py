from __future__ import annotations


class TransitionError(ValueError):
    pass


GOAL_TRANSITIONS = {
    "draft": {"active", "aborted"},
    "active": {"waiting_approval", "complete", "blocked", "aborted", "budget_stopped"},
    "waiting_approval": {"active", "complete", "blocked", "aborted"},
    "blocked": {"active", "aborted"},
    "budget_stopped": {"active", "aborted"},
    "complete": set(),
    "aborted": set(),
}


TASK_TRANSITIONS = {
    "pending": {"running", "blocked", "cancelled"},
    "running": {"submitted", "blocked", "cancelled"},
    "submitted": {"accepted", "rejected", "blocked"},
    "rejected": {"pending", "cancelled"},
    "blocked": {"pending", "cancelled"},
    "accepted": set(),
    "cancelled": set(),
}


def transition_goal(goal, target_status):
    return _transition(goal, target_status, GOAL_TRANSITIONS)


def transition_task(task, target_status):
    return _transition(task, target_status, TASK_TRANSITIONS)


def _transition(obj, target_status, transitions):
    state = obj.setdefault("spec", {}).setdefault("state", {})
    current = state.get("status")
    if current not in transitions:
        raise TransitionError(f"unknown status: {current}")
    if target_status not in transitions[current]:
        raise TransitionError(f"invalid transition: {current} -> {target_status}")
    state["status"] = target_status
    return obj
