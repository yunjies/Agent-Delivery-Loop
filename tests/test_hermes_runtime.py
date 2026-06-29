import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime" / "hermes" / "adl_runtime.py"
sys.path.insert(0, str(ROOT / "runtime" / "hermes"))

from adl_feishu_intake_listener import build_intake_command


class HermesRuntimeTests(unittest.TestCase):
    def run_runtime(self, *args, check=True):
        return subprocess.run(
            [sys.executable, str(RUNTIME), "--state-root", self.tempdir, *args],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            check=check,
        )

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.tempdir = self.temp.name

    def tearDown(self):
        self.temp.cleanup()

    def test_feishu_ingest_promotes_loop_candidate(self):
        result = self.run_runtime(
            "feishu-ingest",
            "#wiki Inspect Mind Palace wiki, produce a fix plan, do not write back, finish today.",
            "--requester-id",
            "ou_test",
            "--promote",
        )
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["assessment"]["spec"]["classification"], "loop_candidate")
        self.assertIn("promoted", payload)

    def test_register_default_experts(self):
        result = self.run_runtime("register-default-experts")
        payload = json.loads(result.stdout)
        self.assertEqual(
            sorted(payload["registered"]),
            ["lark-operator", "mind-palace", "model-maintainer", "ops-auditor"],
        )
        second = json.loads(self.run_runtime("register-default-experts").stdout)
        self.assertEqual(sorted(second["skipped"]), ["lark-operator", "mind-palace", "model-maintainer", "ops-auditor"])

    def test_notify_enqueue_writes_outbox(self):
        ingest = json.loads(
            self.run_runtime(
                "feishu-ingest",
                "#wiki Inspect Mind Palace wiki, produce a fix plan, do not write back, finish today.",
                "--requester-id",
                "ou_test",
                "--promote",
            ).stdout
        )
        goal_id = ingest["promoted"]["goal_id"]
        result = self.run_runtime(
            "notify-enqueue",
            "--goal-id",
            goal_id,
            "--message-type",
            "status_report",
            "--content",
            "ADL smoke",
            "--chat-id",
            "oc_test",
        )
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertTrue(Path(payload["path"]).exists())

    def test_feishu_listener_builds_intake_command_for_keyword_message(self):
        command = build_intake_command(
            {
                "content": "#loop Inspect model registry, produce a fix plan, finish today.",
                "sender_id": "ou_test",
                "chat_id": "oc_test",
            },
            state_root=self.tempdir,
        )
        self.assertIsNotNone(command)
        self.assertIn("feishu-ingest", command)
        self.assertIn("--promote", command)
        self.assertIn("ou_test", command)

    def test_feishu_listener_ignores_plain_message(self):
        command = build_intake_command({"content": "hello", "sender_id": "ou_test"}, state_root=self.tempdir)
        self.assertIsNone(command)


if __name__ == "__main__":
    unittest.main()
