from __future__ import annotations


def create_claude_code_payload(task, prompt, worktree=None, mode="supervised", allowed_tools=None):
    return {
        "adapter": "claude_code",
        "worktree": worktree,
        "mode": mode,
        "task_id": task["metadata"]["id"],
        "goal_id": task["metadata"]["goal_id"],
        "prompt": prompt,
        "allowed_tools": list(allowed_tools or []),
        "permissions": dict(task["spec"].get("permissions") or {}),
        "acceptance": dict(task["spec"].get("acceptance") or {}),
    }
