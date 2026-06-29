import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "delivery-core"))
sys.path.insert(0, str(ROOT / "packages" / "requester-sdk"))
sys.path.insert(0, str(ROOT / "adapters" / "human-approval"))

from agent_delivery_human_approval import approve, create_approval_request, reject
from agent_delivery_loop import validate_object
from agent_delivery_requester import create_demand, create_goal_from_demand


class HumanApprovalAdapterTests(unittest.TestCase):
    def make_goal(self):
        demand = create_demand(
            title="Risky action",
            request="Approve a risky action",
            requester={"kind": "human", "id": "requester-example"},
        )
        return create_goal_from_demand(demand)

    def test_create_and_approve_request(self):
        goal = self.make_goal()
        approval = create_approval_request(
            goal,
            approval_type="docs_write",
            question="Allow Docs writeback?",
            context={"path": "/mnt/user/Docs/wiki/example.md"},
        )
        self.assertTrue(validate_object(approval))
        self.assertEqual(approval["spec"]["state"]["status"], "pending")
        approved = approve(approval, actor={"kind": "human", "id": "requester-example"}, reason="Approved for test")
        self.assertEqual(approved["spec"]["state"]["status"], "approved")
        self.assertIsNotNone(approved["metadata"]["resolved_at"])

    def test_reject_request(self):
        goal = self.make_goal()
        approval = create_approval_request(goal, "cron_mutation", "Allow cron change?")
        rejected = reject(approval, actor={"kind": "human", "id": "requester-example"}, reason="Too risky")
        self.assertEqual(rejected["spec"]["state"]["status"], "rejected")

    def test_cannot_resolve_twice(self):
        goal = self.make_goal()
        approval = create_approval_request(goal, "archive", "Allow archive?")
        approve(approval, actor={"kind": "human", "id": "requester-example"})
        with self.assertRaises(ValueError):
            reject(approval, actor={"kind": "human", "id": "requester-example"})


if __name__ == "__main__":
    unittest.main()
