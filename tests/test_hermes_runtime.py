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
from adl_runtime import _extract_message_id, _topic_root_text


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
            ["home-media", "lark-operator", "mind-palace", "model-maintainer", "ops-auditor"],
        )
        home_media = json.loads((Path(self.tempdir) / "experts" / "home-media.json").read_text(encoding="utf-8"))
        self.assertEqual(home_media["spec"]["invocation"]["adapter"], "hermes_workflow")
        self.assertEqual(home_media["spec"]["invocation"]["profile"], "home-media")
        self.assertIn("media-pipeline", home_media["spec"]["invocation"]["workflows"])
        model_expert = json.loads((Path(self.tempdir) / "experts" / "model-maintainer.json").read_text(encoding="utf-8"))
        self.assertEqual(model_expert["spec"]["invocation"]["adapter"], "hermes_workflow")
        self.assertEqual(model_expert["spec"]["invocation"]["profile"], "model-maintainer")
        second = json.loads(self.run_runtime("register-default-experts").stdout)
        self.assertEqual(sorted(second["skipped"]), ["home-media", "lark-operator", "mind-palace", "model-maintainer", "ops-auditor"])

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

    def test_notify_enqueue_uses_configured_default_target(self):
        config_dir = Path(self.tempdir) / "config"
        config_dir.mkdir(parents=True)
        (config_dir / "notification-targets.json").write_text(
            json.dumps({"default": {"chat_id": "oc_configured", "thread_per_goal": True, "topic_root_prefix": "[ADL Topic]"}}),
            encoding="utf-8",
        )
        ingest = json.loads(
            self.run_runtime(
                "feishu-ingest",
                "#wiki Inspect Mind Palace wiki, produce a fix plan, do not write back, finish today.",
                "--requester-id",
                "ou_test",
                "--promote",
            ).stdout
        )
        result = self.run_runtime(
            "notify-enqueue",
            "--goal-id",
            ingest["promoted"]["goal_id"],
            "--message-type",
            "status_report",
            "--content",
            "ADL smoke",
        )
        payload = json.loads(result.stdout)
        outbox = json.loads(Path(payload["path"]).read_text(encoding="utf-8"))
        self.assertEqual(outbox["target"]["chat_id"], "oc_configured")
        self.assertTrue(outbox["target"]["thread_per_goal"])
        self.assertEqual(outbox["target"]["topic_root_prefix"], "[ADL Topic]")

    def test_extract_message_id_from_lark_cli_response(self):
        stdout = json.dumps({"ok": True, "data": {"message_id": "om_test"}})
        self.assertEqual(_extract_message_id(stdout), "om_test")

    def test_topic_root_text_marks_follow_up_thread(self):
        text = _topic_root_text(
            {
                "goal_id": "goal-test",
                "message_type": "status_report",
                "content": "Loop accepted.",
                "target": {"topic_root_prefix": "[ADL Topic]"},
            }
        )
        self.assertIn("[ADL Topic] status_report", text)
        self.assertIn("goal: goal-test", text)
        self.assertIn("All follow-up logs", text)

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

    def test_feishu_listener_accepts_home_media_prefix(self):
        command = build_intake_command(
            {"content": "#media Check missing media and report only, finish today.", "sender_id": "ou_test"},
            state_root=self.tempdir,
        )
        self.assertIsNotNone(command)
        self.assertIn("feishu-ingest", command)


if __name__ == "__main__":
    unittest.main()
