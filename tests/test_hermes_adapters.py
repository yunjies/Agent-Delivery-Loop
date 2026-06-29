import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "requester-sdk"))
sys.path.insert(0, str(ROOT / "packages" / "delivery-supervisor-sdk"))
sys.path.insert(0, str(ROOT / "adapters" / "hermes-profile"))
sys.path.insert(0, str(ROOT / "adapters" / "hermes-workflow"))

from agent_delivery_hermes_profile import create_profile_task_payload
from agent_delivery_hermes_workflow import create_workflow_task_payload
from agent_delivery_requester import create_demand, create_goal_from_demand
from agent_delivery_supervisor import create_task


class HermesAdapterTests(unittest.TestCase):
    def make_task(self):
        demand = create_demand(
            title="Run wiki lint",
            request="Run wiki lint",
            requester={"kind": "human", "id": "requester-example"},
        )
        goal = create_goal_from_demand(demand)
        return create_task(
            goal,
            task_type="workflow_run",
            objective="Run Mind Palace lint",
            assignee={"kind": "hermes_workflow", "id": "mind-palace-lint"},
            permissions={"docs_write": False, "external_send": True},
            acceptance={"evidence_required": True},
        )

    def test_profile_payload_is_serializable_plan(self):
        task = self.make_task()
        payload = create_profile_task_payload(
            task,
            profile="mind-palace",
            prompt="Review lint evidence.",
            skills=["mind-palace-lint"],
        )
        self.assertEqual(payload["adapter"], "hermes_profile")
        self.assertEqual(payload["profile"], "mind-palace")
        self.assertEqual(payload["task_id"], task["metadata"]["id"])
        self.assertFalse(payload["permissions"]["docs_write"])

    def test_workflow_payload_is_serializable_plan(self):
        task = self.make_task()
        payload = create_workflow_task_payload(
            task,
            workflow="mind-palace-lint",
            trigger="agent-delivery-loop:test",
            max_ticks=4,
        )
        self.assertEqual(payload["adapter"], "hermes_workflow")
        self.assertEqual(payload["workflow"], "mind-palace-lint")
        self.assertEqual(payload["max_ticks"], 4)
        self.assertFalse(payload["permissions"]["docs_write"])


if __name__ == "__main__":
    unittest.main()
