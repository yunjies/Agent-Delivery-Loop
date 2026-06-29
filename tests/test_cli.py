import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "adl.py"), *args],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            check=True,
        )

    def test_init_status_and_list(self):
        tempdir = tempfile.mkdtemp()
        try:
            init = self.run_cli("init-workspace", tempdir)
            self.assertTrue(json.loads(init.stdout)["ok"])
            status = self.run_cli("status", tempdir)
            payload = json.loads(status.stdout)
            self.assertEqual(payload["counts"]["Goal"], 0)

            demo_workspace = Path(tempdir) / "demo"
            self.run_cli("demo", "--reset", "--workspace", str(demo_workspace))
            status = self.run_cli("status", str(demo_workspace))
            payload = json.loads(status.stdout)
            self.assertEqual(payload["counts"]["Goal"], 1)
            self.assertGreater(payload["events"], 0)

            goals = self.run_cli("list", str(demo_workspace), "Goal")
            listed = json.loads(goals.stdout)
            self.assertEqual(len(listed), 1)
            self.assertEqual(listed[0]["status"], "active")

            status = json.loads(self.run_cli("status", str(demo_workspace)).stdout)
            goal_id = next((demo_workspace / "goals").glob("*.json")).stem
            task_id = next((demo_workspace / "tasks").glob("*.json")).stem
            attempt_id = next((demo_workspace / "attempts").glob("*.json")).stem
            before_decisions = status["counts"]["LoopDecision"]
            review = self.run_cli("review-attempt", str(demo_workspace), goal_id, task_id, attempt_id)
            review_payload = json.loads(review.stdout)
            self.assertEqual(review_payload["task_status"], "accepted")
            self.assertEqual(review_payload["decision_action"], "mark_complete")
            after = json.loads(self.run_cli("status", str(demo_workspace)).stdout)
            self.assertEqual(after["counts"]["LoopDecision"], before_decisions + 1)

            tick = self.run_cli("supervisor-tick", str(demo_workspace))
            tick_payload = json.loads(tick.stdout)
            self.assertTrue(tick_payload["ok"])
            self.assertEqual(tick_payload["reviewed"], [])
        finally:
            shutil.rmtree(tempdir)

    def test_release_check(self):
        if os.environ.get("ADL_SKIP_RELEASE_CHECK_TEST") == "1":
            self.skipTest("release-check subprocess skips recursive release-check test")
        result = self.run_cli("release-check")
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual([check["name"] for check in payload["checks"]], ["protocol", "tests"])

    def test_intake_cli_can_save_and_promote_loop_candidate(self):
        tempdir = tempfile.mkdtemp()
        try:
            result = self.run_cli(
                "intake",
                "整理 Mind Palace wiki，先巡检再输出修复计划，不要直接写回，今天完成。",
                "--preferred-expert",
                "mind-palace",
                "--workspace",
                tempdir,
                "--promote",
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["assessment"]["spec"]["classification"], "loop_candidate")
            self.assertIn("promoted", payload)

            status = json.loads(self.run_cli("status", tempdir).stdout)
            self.assertEqual(status["counts"]["IntakeAssessment"], 1)
            self.assertEqual(status["counts"]["Demand"], 1)
            self.assertEqual(status["counts"]["Goal"], 1)
        finally:
            shutil.rmtree(tempdir)


if __name__ == "__main__":
    unittest.main()
