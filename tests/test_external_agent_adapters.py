import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "requester-sdk"))
sys.path.insert(0, str(ROOT / "packages" / "delivery-supervisor-sdk"))
sys.path.insert(0, str(ROOT / "adapters" / "codex-thread"))
sys.path.insert(0, str(ROOT / "adapters" / "claude-code"))

from agent_delivery_claude_code import create_claude_code_payload
from agent_delivery_codex_thread import create_codex_thread_payload
from agent_delivery_requester import create_demand, create_goal_from_demand
from agent_delivery_supervisor import create_task


class ExternalAgentAdapterTests(unittest.TestCase):
    def make_task(self):
        demand = create_demand(
            title="Implement code",
            request="Implement a small feature",
            requester={"kind": "human", "id": "requester-example"},
        )
        goal = create_goal_from_demand(demand)
        return create_task(
            goal,
            task_type="code_change",
            objective="Implement a small feature",
            assignee={"kind": "codex_thread", "id": "codex"},
            permissions={"code_write": True, "shell_exec": False},
            acceptance={"evidence_required": True, "expected_evidence": ["diff", "tests"]},
        )

    def test_codex_payload_is_plan_only(self):
        task = self.make_task()
        payload = create_codex_thread_payload(
            task,
            prompt="Implement the feature and return evidence.",
            thread_id="thread-example",
            repository="example/repo",
        )
        self.assertEqual(payload["adapter"], "codex_thread")
        self.assertEqual(payload["thread_id"], "thread-example")
        self.assertTrue(payload["permissions"]["code_write"])
        self.assertFalse(payload["permissions"]["shell_exec"])

    def test_claude_code_payload_is_plan_only(self):
        task = self.make_task()
        payload = create_claude_code_payload(
            task,
            prompt="Implement the feature and return evidence.",
            worktree="/tmp/example",
            allowed_tools=["edit", "test"],
        )
        self.assertEqual(payload["adapter"], "claude_code")
        self.assertEqual(payload["worktree"], "/tmp/example")
        self.assertEqual(payload["allowed_tools"], ["edit", "test"])
        self.assertTrue(payload["permissions"]["code_write"])


if __name__ == "__main__":
    unittest.main()
