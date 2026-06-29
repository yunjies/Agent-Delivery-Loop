import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "requester-sdk"))
sys.path.insert(0, str(ROOT / "adapters" / "feishu-notification"))

from agent_delivery_feishu_notification import create_notification_payload
from agent_delivery_requester import create_demand, create_goal_from_demand


class FeishuNotificationAdapterTests(unittest.TestCase):
    def make_goal(self):
        demand = create_demand(
            title="Notify supervision",
            request="Send supervision update",
            requester={"kind": "human", "id": "requester-example"},
        )
        return create_goal_from_demand(demand)

    def test_notification_payload_has_no_secret(self):
        goal = self.make_goal()
        payload = create_notification_payload(
            goal,
            message_type="status_report",
            content="Goal status report",
            target={"kind": "feishu_chat", "id": "chat-example"},
            evidence=[{"kind": "report", "path": "/tmp/report.md"}],
        )
        self.assertEqual(payload["adapter"], "feishu_notification")
        self.assertEqual(payload["message_type"], "status_report")
        self.assertNotIn("secret", payload)
        self.assertNotIn("app_secret", payload)

    def test_rejects_unsupported_message_type(self):
        goal = self.make_goal()
        with self.assertRaises(ValueError):
            create_notification_payload(
                goal,
                message_type="business_update",
                content="Not allowed",
                target={"kind": "feishu_chat", "id": "chat-example"},
            )


if __name__ == "__main__":
    unittest.main()
