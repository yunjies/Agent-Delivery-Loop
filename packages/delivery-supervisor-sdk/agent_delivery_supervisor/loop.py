from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages" / "delivery-core"))

from agent_delivery_loop import rank_experts, should_stop_for_budget
from agent_delivery_loop import transition_task

from .decision import create_loop_decision
from .task import create_task


def propose_next_task(goal, experts, task_spec, path_governance_evaluator=None):
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

    path_preflight = _evaluate_path_governance(task_spec, selected, path_governance_evaluator)
    if path_preflight and not path_preflight.get("ok"):
        rerouted = _try_reroute_path_governance(goal, experts, task_spec, selected, path_preflight, path_governance_evaluator)
        if rerouted:
            return rerouted
        next_prompt = _path_governance_block_prompt(task_spec, selected, path_preflight)
        decision = create_loop_decision(
            goal,
            action="mark_blocked",
            reason=f"Path governance preflight failed before creating a task for expert {selected}; no valid owner reroute was available.",
            budget_assessment={
                "within_budget": True,
            },
            risk_assessment={
                "high_risk": True,
                "gate_required": True,
            },
            review_feedback={
                "expert_id": selected,
                "path_governance": path_preflight,
            },
            next_prompt=next_prompt,
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
        path_governance=task_spec.get("path_governance"),
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


def _try_reroute_path_governance(goal, experts, task_spec, selected_expert, path_preflight, evaluator):
    delegate = _single_delegate_profile(path_preflight)
    if not delegate or delegate == selected_expert or not _expert_exists(experts, delegate):
        return None
    corrected_spec = _correct_task_spec_for_delegate(task_spec, delegate)
    corrected_preflight = _evaluate_path_governance(corrected_spec, delegate, evaluator)
    if corrected_preflight and not corrected_preflight.get("ok"):
        return None
    task = create_task(
        goal,
        task_type=corrected_spec["task_type"],
        objective=corrected_spec["objective"],
        assignee={"kind": "expert", "id": delegate},
        permissions=corrected_spec.get("permissions") or {},
        acceptance=corrected_spec.get("acceptance") or {"evidence_required": True},
        budget=corrected_spec.get("budget") or {},
        required_capabilities=corrected_spec.get("required_capabilities") or [],
        path_governance=corrected_spec.get("path_governance"),
    )
    decision = create_loop_decision(
        goal,
        action="create_task",
        reason=f"Rerouted task from {selected_expert} to owning profile {delegate} based on path governance.",
        next_task={
            "ref": task["metadata"]["id"],
            "rerouted_from": selected_expert,
            "rerouted_to": delegate,
            "path_governance": corrected_preflight,
        },
        budget_assessment={
            "within_budget": True,
        },
        risk_assessment={
            "high_risk": False,
            "gate_required": False,
        },
        review_feedback={
            "path_governance_original": path_preflight,
            "path_governance_corrected": corrected_preflight,
        },
    )
    return task, decision, rank_experts(
        {"spec": {"objective": corrected_spec["objective"], "required_capabilities": corrected_spec.get("required_capabilities", [])}},
        experts,
    )


def _single_delegate_profile(path_preflight):
    violations = path_preflight.get("violations") or []
    delegates = sorted({item.get("delegate_profile") or item.get("owner_profile") for item in violations if item.get("delegate_profile") or item.get("owner_profile")})
    return delegates[0] if len(delegates) == 1 else None


def _expert_exists(experts, expert_id):
    return any((expert.get("metadata") or {}).get("id") == expert_id for expert in experts)


def _correct_task_spec_for_delegate(task_spec, delegate):
    corrected = dict(task_spec)
    path_governance = dict(corrected.get("path_governance") or {})
    path_governance["actor_profile"] = delegate
    corrected["path_governance"] = path_governance
    return corrected


def _evaluate_path_governance(task_spec, selected_expert, evaluator):
    path_governance = task_spec.get("path_governance") or {}
    planned_paths = path_governance.get("planned_paths") or path_governance.get("changed_paths") or []
    if not planned_paths:
        return None
    if evaluator is None:
        return {
            "ok": False,
            "error": "path governance evaluator is required before task creation",
            "expert_id": selected_expert,
            "actor_profile": path_governance.get("actor_profile") or selected_expert,
            "changed_path_count": len(planned_paths),
            "violations": [{"message": "missing path governance evaluator"}],
            "warnings": [],
            "results": [],
        }
    return evaluator(task_spec=task_spec, selected_expert=selected_expert)


def _path_governance_block_prompt(task_spec, selected_expert, path_preflight):
    violations = path_preflight.get("violations") or []
    owners = sorted({item.get("owner_profile") for item in violations if item.get("owner_profile")})
    delegates = sorted({item.get("delegate_profile") for item in violations if item.get("delegate_profile")})
    paths = [item.get("path") for item in violations if item.get("path")]
    owner_text = ", ".join(owners) if owners else "the owning profile"
    delegate_text = ", ".join(delegates) if delegates else owner_text
    path_text = ", ".join(paths[:5]) if paths else "the governed paths"
    return (
        f"Clarify and reset this goal before creating a task. The proposed task for expert {selected_expert} "
        f"would touch {path_text}, which is owned by {owner_text}. "
        f"The correct owner route is {delegate_text}, but automatic reroute was not available. "
        "Adjust the task so each write is performed by the correct profile. "
        "Preserve the original objective and include the corrected "
        "`path_governance.actor_profile` and `planned_paths`."
    )


def review_attempt(goal, task, attempt):
    """Return (updated_task, decision) after deterministic supervisor review."""

    _assert_attempt_matches(goal, task, attempt)
    if should_stop_for_budget(goal.get("spec", {}).get("budget") or {}):
        decision = create_loop_decision(
            goal,
            action="stop_budget",
            reason="Goal budget is below the stop threshold during attempt review.",
            budget_assessment={"within_budget": False},
            risk_assessment={"high_risk": False, "gate_required": True},
            review_feedback={"task_id": task["metadata"]["id"], "attempt_id": attempt["metadata"]["id"]},
        )
        return task, decision

    result = attempt["spec"]["result"]
    status = result["status"]
    if status == "succeeded":
        evidence_check = _with_review_refs(_check_evidence(task, attempt), task, attempt)
        if not evidence_check["ok"]:
            updated = _transition_review_task(task, "rejected")
            prompt = _rework_prompt(task, attempt, evidence_check["reason"])
            decision = create_loop_decision(
                goal,
                action="create_task",
                reason="Attempt succeeded but did not satisfy acceptance evidence requirements.",
                next_task={
                    "source_task_id": task["metadata"]["id"],
                    "objective": prompt,
                    "required_capabilities": task["spec"].get("required_capabilities", []),
                },
                budget_assessment={"within_budget": True},
                risk_assessment={"high_risk": False, "gate_required": False},
                review_feedback=evidence_check,
                next_prompt=prompt,
            )
            return updated, decision

        if task["spec"].get("acceptance", {}).get("human_approval_required"):
            decision = create_loop_decision(
                goal,
                action="request_approval",
                reason="Attempt satisfies deterministic checks but requires human approval.",
                required_approval={
                    "task_id": task["metadata"]["id"],
                    "attempt_id": attempt["metadata"]["id"],
                    "approval_type": "human_acceptance",
                },
                budget_assessment={"within_budget": True},
                risk_assessment={"high_risk": False, "gate_required": True},
                review_feedback=evidence_check,
            )
            return task, decision

        updated = _transition_review_task(task, "accepted")
        decision = create_loop_decision(
            goal,
            action="mark_complete",
            reason="Attempt satisfies acceptance requirements.",
            budget_assessment={"within_budget": True},
            risk_assessment={"high_risk": False, "gate_required": False},
            review_feedback=evidence_check,
        )
        return updated, decision

    if status == "blocked":
        updated = _transition_review_task(task, "blocked")
        decision = create_loop_decision(
            goal,
            action="mark_blocked",
            reason=result.get("error") or result.get("summary") or "Expert reported the task as blocked.",
            budget_assessment={"within_budget": True},
            risk_assessment={"high_risk": False, "gate_required": False},
            review_feedback={"task_id": task["metadata"]["id"], "attempt_id": attempt["metadata"]["id"], "status": status},
        )
        return updated, decision

    updated = _transition_review_task(task, "rejected")
    prompt = _rework_prompt(task, attempt, result.get("error") or result.get("summary") or f"Attempt status was {status}.")
    decision = create_loop_decision(
        goal,
        action="create_task",
        reason=f"Attempt did not complete successfully: {status}.",
        next_task={
            "source_task_id": task["metadata"]["id"],
            "objective": prompt,
            "required_capabilities": task["spec"].get("required_capabilities", []),
        },
        budget_assessment={"within_budget": True},
        risk_assessment={"high_risk": False, "gate_required": False},
        review_feedback={"task_id": task["metadata"]["id"], "attempt_id": attempt["metadata"]["id"], "status": status},
        next_prompt=prompt,
    )
    return updated, decision


def _high_risk_permissions(permissions):
    return [
        key for key, value in permissions.items()
        if value and key in {"docs_write", "delete_move_archive", "cron_mutation", "workflow_mutation", "profile_mutation", "shell_exec"}
    ]


def _is_high_risk(permissions):
    return bool(_high_risk_permissions(permissions))


def _assert_attempt_matches(goal, task, attempt):
    goal_id = goal["metadata"]["id"]
    task_id = task["metadata"]["id"]
    if task["metadata"]["goal_id"] != goal_id:
        raise ValueError("task does not belong to goal")
    if attempt["metadata"]["goal_id"] != goal_id:
        raise ValueError("attempt does not belong to goal")
    if attempt["metadata"]["task_id"] != task_id:
        raise ValueError("attempt does not belong to task")


def _check_evidence(task, attempt):
    acceptance = task["spec"].get("acceptance") or {}
    evidence = attempt["spec"]["result"].get("evidence") or []
    if acceptance.get("evidence_required") and not evidence:
        return {"ok": False, "reason": "required evidence is missing", "evidence_count": 0}

    expected = list(acceptance.get("expected_evidence") or [])
    missing = []
    for item in expected:
        if not _evidence_matches(item, evidence):
            missing.append(item)
    if missing:
        return {
            "ok": False,
            "reason": "expected evidence is missing",
            "missing_evidence": missing,
            "evidence_count": len(evidence),
        }
    return {"ok": True, "reason": "acceptance evidence satisfied", "evidence_count": len(evidence)}


def _with_review_refs(feedback, task, attempt):
    enriched = dict(feedback)
    enriched["task_id"] = task["metadata"]["id"]
    enriched["attempt_id"] = attempt["metadata"]["id"]
    return enriched


def _evidence_matches(expected, evidence):
    expected = str(expected).lower()
    for item in evidence:
        kind = str(item.get("kind", "")).lower()
        path = str(item.get("path", "")).lower()
        title = str(item.get("title", "")).lower()
        if expected in {kind, title} or expected in path:
            return True
    return False


def _transition_review_task(task, target_status):
    current = task["spec"]["state"]["status"]
    if current == target_status:
        return task
    if current == "submitted":
        return transition_task(task, target_status)
    if current in {"pending", "running"}:
        submitted = transition_task(task, "submitted") if current == "running" else transition_task(transition_task(task, "running"), "submitted")
        return transition_task(submitted, target_status)
    raise ValueError(f"task cannot be reviewed from status: {current}")


def _rework_prompt(task, attempt, reason):
    return (
        f"Rework task {task['metadata']['id']}: {task['spec']['objective']} "
        f"The previous attempt {attempt['metadata']['id']} was not acceptable because {reason}. "
        "Return a new attempt with complete evidence and a concise summary."
    )
