import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "adapters" / "filesystem"))

from agent_delivery_filesystem import FilesystemWorkspace


class FilesystemAdapterTests(unittest.TestCase):
    def test_minimal_loop_persists_all_core_objects(self):
        tempdir = tempfile.mkdtemp()
        try:
            workspace = FilesystemWorkspace(tempdir)
            expert = json.loads((ROOT / "protocol" / "fixtures" / "mind-palace-expert.example.json").read_text(encoding="utf-8"))
            workspace.register_expert(expert)
            _, goal = workspace.start_goal(
                title="Maintain wiki health",
                request="Keep the wiki healthy",
                requester={"kind": "human", "id": "requester-example"},
                success_criteria=["lint succeeds"],
                budget={"token_limit": 1000, "token_used_estimate": 0},
                permissions={"docs_write": False, "external_send": True},
            )
            task, decision, ranked = workspace.propose_task(
                goal,
                task_type="workflow_run",
                objective="Run wiki_lint and report.",
                experts=[expert],
                permissions={"docs_write": False, "external_send": True},
                acceptance={"evidence_required": True},
                required_capabilities=["wiki_lint"],
            )
            self.assertIsNotNone(task)
            self.assertEqual(ranked[0]["expert_id"], "mind-palace")
            attempt = workspace.submit_attempt(
                task,
                executor={"kind": "expert", "id": "mind-palace"},
                status="succeeded",
                summary="Done",
                evidence=[{"kind": "report", "path": "/tmp/report.md"}],
                budget_used={"token_used_estimate": 0},
            )
            workspace.accept_task(task)

            root = Path(tempdir)
            self.assertTrue((root / "goals" / f"{goal['metadata']['id']}.json").exists())
            self.assertTrue((root / "tasks" / f"{task['metadata']['id']}.json").exists())
            self.assertTrue((root / "attempts" / f"{attempt['metadata']['id']}.json").exists())
            self.assertTrue((root / "decisions" / f"{decision['metadata']['id']}.json").exists())
            self.assertTrue(any((root / "events").glob("*.jsonl")))
        finally:
            shutil.rmtree(tempdir)

    def test_supervisor_tick_reviews_submitted_attempt_once(self):
        tempdir = tempfile.mkdtemp()
        try:
            workspace = FilesystemWorkspace(tempdir)
            expert = json.loads((ROOT / "protocol" / "fixtures" / "mind-palace-expert.example.json").read_text(encoding="utf-8"))
            workspace.register_expert(expert)
            _, goal = workspace.start_goal(
                title="Maintain wiki health",
                request="Keep the wiki healthy",
                requester={"kind": "human", "id": "requester-example"},
                success_criteria=["lint succeeds"],
                budget={"token_limit": 1000, "token_used_estimate": 0},
                permissions={"docs_write": False, "external_send": True},
            )
            task, _, _ = workspace.propose_task(
                goal,
                task_type="workflow_run",
                objective="Run wiki_lint and report.",
                experts=[expert],
                permissions={"docs_write": False, "external_send": True},
                acceptance={"evidence_required": True, "expected_evidence": ["report"]},
                required_capabilities=["wiki_lint"],
            )
            attempt = workspace.submit_attempt(
                task,
                executor={"kind": "expert", "id": "mind-palace"},
                status="succeeded",
                summary="Done",
                evidence=[{"kind": "report", "path": "/tmp/report.md"}],
                budget_used={"token_used_estimate": 0},
            )

            first = workspace.supervisor_tick()
            self.assertEqual(len(first["reviewed"]), 1)
            self.assertEqual(first["reviewed"][0]["attempt_id"], attempt["metadata"]["id"])
            self.assertEqual(first["reviewed"][0]["decision_action"], "mark_complete")

            second = workspace.supervisor_tick()
            self.assertEqual(second["reviewed"], [])
            self.assertTrue(any(item.get("reason") == "status:accepted" for item in second["skipped"]))
        finally:
            shutil.rmtree(tempdir)


if __name__ == "__main__":
    unittest.main()
