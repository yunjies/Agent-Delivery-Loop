from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages" / "delivery-core"))

from agent_delivery_loop import rank_experts, should_stop_for_budget

from .decision import create_loop_decision
from .task import create_task


def propose_next_task(goal, experts, task_spec):
    """Return (task, decision, ranked_experts) for the next supervised step."""

    budget = goal.get("spec", {}).get("budget") or {}
    if should_stop_for_budget(budget):
        decision = create_loop_decision(
            goal,
            action="stop_budget",
            reason="Goal budget is below the stop threshold.",
            budget_assessment={
                "within_budget": False,
            },
            risk_assessment={
                "high_risk": False,
                "gate_required": True,
            },
        )
        return None, decision, []

    ranked = rank_experts(
        {"spec": {"objective": task_spec["objective"], "required_capabilities": task_spec.get("required_capabilities", [])}},
        experts,
    )
    if not ranked or ranked[0]["score"] <= 0:
        decision = create_loop_decision(
            goal,
            action="mark_blocked",
            reason="No suitable expert matched the requested task.",
            risk_assessment={
                "high_risk": False,
                "gate_required": False,
            },
        )
        return None, decision, ranked

    selected = ranked[0]["expert_id"]
    high_risk = _is_high_risk(task_spec.get("permissions") or {})
    if high_risk and task_spec.get("approval") != "approved":
        decision = create_loop_decision(
            goal,
            action="request_approval",
            reason=f"Task requires high-risk permissions before routing to expert {selected}.",
            required_approval={
                "permissions": _high_risk_permissions(task_spec.get("permissions") or {}),
                "expert_id": selected,
            },
            budget_assessment={
                "within_budget": True,
            },
            risk_assessment={
                "high_risk": True,
                "gate_required": True,
            },
        )
        return None, decision, ranked

    task = create_task(
        goal,
        task_type=task_spec["task_type"],
        objective=task_spec["objective"],
        assignee={"kind": "expert", "id": selected},
        permissions=task_spec.get("permissions") or {},
        acceptance=task_spec.get("acceptance") or {"evidence_required": True},
        budget=task_spec.get("budget") or {},
        required_capabilities=task_spec.get("required_capabilities") or [],
    )
    decision = create_loop_decision(
        goal,
        action="create_task",
        reason=f"Selected expert {selected}.",
        next_task={"ref": task["metadata"]["id"]},
        budget_assessment={
            "within_budget": True,
        },
        risk_assessment={
            "high_risk": False,
            "gate_required": False,
        },
    )
    return task, decision, ranked


def _high_risk_permissions(permissions):
    return [
        key for key, value in permissions.items()
        if value and key in {"docs_write", "delete_move_archive", "cron_mutation", "workflow_mutation", "profile_mutation", "shell_exec"}
    ]


def _is_high_risk(permissions):
    return bool(_high_risk_permissions(permissions))
