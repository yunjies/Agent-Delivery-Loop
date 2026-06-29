from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages" / "delivery-core"))
sys.path.insert(0, str(ROOT / "packages" / "requester-sdk"))
sys.path.insert(0, str(ROOT / "packages" / "delivery-supervisor-sdk"))
sys.path.insert(0, str(ROOT / "packages" / "expert-adapter-sdk"))

from agent_delivery_expert import create_attempt
from agent_delivery_loop import FilesystemStore, rank_experts, transition_task
from agent_delivery_requester import create_demand, create_goal_from_demand
from agent_delivery_supervisor import create_loop_decision, create_task, propose_next_task, review_attempt


class FilesystemWorkspace:
    """A minimal local workspace for supervised delivery loops."""

    def __init__(self, root):
        self.root = Path(root)
        self.store = FilesystemStore(self.root).init()

    def register_expert(self, expert):
        self.store.save(expert)
        return expert

    def start_goal(self, title, request, requester, success_criteria=None, budget=None, permissions=None):
        demand = create_demand(
            title=title,
            request=request,
            requester=requester,
            success_criteria=success_criteria,
            budget=budget,
            permissions=permissions,
        )
        goal = create_goal_from_demand(demand)
        self.store.save(demand)
        self.store.save(goal)
        return demand, goal

    def propose_task(self, goal, task_type, objective, experts, permissions, acceptance, required_capabilities=None, budget=None):
        task, decision, ranked = propose_next_task(
            goal,
            experts,
            {
                "task_type": task_type,
                "objective": objective,
                "permissions": permissions,
                "acceptance": acceptance,
                "required_capabilities": list(required_capabilities or []),
                "budget": budget or {},
            },
        )
        if task is not None:
            self.store.save(task)
        self.store.save(decision)
        return task, decision, ranked

    def submit_attempt(self, task, executor, status, summary, evidence=None, budget_used=None, error=None):
        running = transition_task(task, "running")
        submitted = transition_task(running, "submitted")
        attempt = create_attempt(
            submitted,
            executor=executor,
            status=status,
            summary=summary,
            evidence=evidence,
            budget_used=budget_used,
            error=error,
        )
        submitted["spec"]["state"]["latest_attempt_id"] = attempt["metadata"]["id"]
        self.store.save(submitted)
        self.store.save(attempt)
        return attempt

    def accept_task(self, task):
        task = transition_task(task, "accepted")
        self.store.save(task)
        return task

    def review_attempt(self, goal, task, attempt):
        updated_task, decision = review_attempt(goal, task, attempt)
        self.store.save(updated_task)
        self.store.save(decision)
        return updated_task, decision

    def supervisor_tick(self, max_reviews=None):
        """Review submitted tasks with unreviewed latest attempts."""

        reviewed = []
        skipped = []
        decisions = self.store.list_objects("LoopDecision")
        reviewed_attempt_ids = {
            decision.get("spec", {}).get("review_feedback", {}).get("attempt_id")
            for decision in decisions
            if decision.get("spec", {}).get("review_feedback", {}).get("attempt_id")
        }
        for task in self.store.list_objects("Task"):
            if max_reviews is not None and len(reviewed) >= max_reviews:
                break
            state = task.get("spec", {}).get("state", {})
            if state.get("status") != "submitted":
                skipped.append({"task_id": task["metadata"]["id"], "reason": f"status:{state.get('status')}"})
                continue
            attempt_id = state.get("latest_attempt_id")
            if not attempt_id:
                skipped.append({"task_id": task["metadata"]["id"], "reason": "missing_latest_attempt"})
                continue
            if attempt_id in reviewed_attempt_ids:
                skipped.append({"task_id": task["metadata"]["id"], "attempt_id": attempt_id, "reason": "already_reviewed"})
                continue
            goal = self.store.load("Goal", task["metadata"]["goal_id"])
            attempt = self.store.load("Attempt", attempt_id)
            updated_task, decision = self.review_attempt(goal, task, attempt)
            reviewed.append(
                {
                    "task_id": updated_task["metadata"]["id"],
                    "attempt_id": attempt_id,
                    "task_status": updated_task["spec"]["state"]["status"],
                    "decision_id": decision["metadata"]["id"],
                    "decision_action": decision["spec"]["action"],
                }
            )
            reviewed_attempt_ids.add(attempt_id)
        return {"reviewed": reviewed, "skipped": skipped}
