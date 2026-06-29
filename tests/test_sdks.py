import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "delivery-core"))
sys.path.insert(0, str(ROOT / "packages" / "requester-sdk"))
sys.path.insert(0, str(ROOT / "packages" / "delivery-supervisor-sdk"))
sys.path.insert(0, str(ROOT / "packages" / "expert-adapter-sdk"))

from agent_delivery_expert import create_attempt
from agent_delivery_loop import validate_object
from agent_delivery_requester import create_demand, create_goal_from_demand
from agent_delivery_supervisor import create_loop_decision, create_task, propose_next_task


class SdkTests(unittest.TestCase):
    def test_requester_creates_valid_demand_and_goal(self):
        demand = create_demand(
            title="Maintain wiki health",
            request="Keep the wiki healthy",
            requester={"kind": "human", "id": "requester-example"},
            success_criteria=["lint report succeeds"],
            budget={"token_limit": 1000, "token_used_estimate": 0},
            permissions={"docs_write": False},
        )
        goal = create_goal_from_demand(demand)
        self.assertTrue(validate_object(demand))
        self.assertTrue(validate_object(goal))
        self.assertEqual(goal["metadata"]["demand_id"], demand["metadata"]["id"])

    def test_expert_creates_valid_attempt(self):
        task = {
            "apiVersion": "agent.delivery.loop/v0",
            "kind": "Task",
            "metadata": {"id": "task-1", "goal_id": "goal-1", "created_at": "2026-06-29T00:00:00+08:00"},
            "spec": {
                "task_type": "script",
                "objective": "Run a report",
                "assignee": {"kind": "script", "id": "report"},
                "permissions": {"docs_write": False},
                "acceptance": {"evidence_required": True},
                "state": {"status": "pending"},
            },
        }
        attempt = create_attempt(
            task,
            executor={"kind": "script", "id": "report"},
            status="succeeded",
            summary="Report completed",
            evidence=[{"kind": "report", "path": "/tmp/report.md"}],
            budget_used={"token_used_estimate": 0},
        )
        self.assertTrue(validate_object(attempt))
        self.assertEqual(attempt["metadata"]["task_id"], "task-1")

    def test_delivery_supervisor_creates_task_and_decision(self):
        demand = create_demand(
            title="Maintain wiki health",
            request="Keep the wiki healthy",
            requester={"kind": "human", "id": "requester-example"},
        )
        goal = create_goal_from_demand(demand)
        task = create_task(
            goal,
            task_type="workflow_run",
            objective="Run lint report",
            assignee={"kind": "hermes_workflow", "id": "mind-palace-lint"},
            permissions={"docs_write": False, "external_send": True},
            acceptance={"evidence_required": True},
            required_capabilities=["wiki_lint"],
        )
        decision = create_loop_decision(
            goal,
            action="create_task",
            reason="A lint report is the next low-risk step.",
            next_task={"ref": task["metadata"]["id"]},
            budget_assessment={"within_budget": True},
            risk_assessment={"high_risk": False, "gate_required": False},
        )
        self.assertTrue(validate_object(task))
        self.assertTrue(validate_object(decision))
        self.assertEqual(task["metadata"]["goal_id"], goal["metadata"]["id"])
        self.assertEqual(decision["spec"]["next_task"]["ref"], task["metadata"]["id"])

    def test_delivery_supervisor_requests_approval_for_high_risk_task(self):
        demand = create_demand(
            title="Archive docs",
            request="Archive stale docs",
            requester={"kind": "human", "id": "requester-example"},
        )
        goal = create_goal_from_demand(demand)
        expert = {
            "apiVersion": "agent.delivery.loop/v0",
            "kind": "Expert",
            "metadata": {"id": "archiver", "title": "Archiver"},
            "spec": {
                "expert_kind": "script",
                "capabilities": [{"id": "archive", "description": "Archive files", "priority": 100, "default_owner": True}],
                "invocation": {"adapter": "script"},
            },
        }
        task, decision, ranked = propose_next_task(
            goal,
            [expert],
            {
                "task_type": "archive",
                "objective": "Archive stale docs",
                "required_capabilities": ["archive"],
                "permissions": {"delete_move_archive": True},
                "acceptance": {"evidence_required": True},
            },
        )
        self.assertIsNone(task)
        self.assertEqual(decision["spec"]["action"], "request_approval")
        self.assertEqual(ranked[0]["expert_id"], "archiver")


if __name__ == "__main__":
    unittest.main()
