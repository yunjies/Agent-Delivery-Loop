from __future__ import annotations


def create_codex_thread_payload(task, prompt, thread_id=None, repository=None, mode="supervised"):
    return {
        "adapter": "codex_thread",
        "thread_id": thread_id,
        "repository": repository,
        "mode": mode,
        "task_id": task["metadata"]["id"],
        "goal_id": task["metadata"]["goal_id"],
        "prompt": prompt,
        "permissions": dict(task["spec"].get("permissions") or {}),
        "acceptance": dict(task["spec"].get("acceptance") or {}),
    }
