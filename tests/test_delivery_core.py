import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "delivery-core"))

from agent_delivery_loop import FilesystemStore, rank_experts, should_stop_for_budget, transition_task, validate_object


class DeliveryCoreTests(unittest.TestCase):
    def load_fixture(self, name):
        return json.loads((ROOT / "protocol" / "fixtures" / name).read_text(encoding="utf-8"))

    def test_fixtures_pass_minimal_validation(self):
        for name in [
            "minimal-demand.example.json",
            "minimal-goal.example.json",
            "minimal-task.example.json",
            "mind-palace-expert.example.json",
            "minimal-loop-decision.example.json",
        ]:
            self.assertTrue(validate_object(self.load_fixture(name)))

    def test_task_transition(self):
        task = self.load_fixture("minimal-task.example.json")
        transition_task(task, "running")
        self.assertEqual(task["spec"]["state"]["status"], "running")
        transition_task(task, "submitted")
        self.assertEqual(task["spec"]["state"]["status"], "submitted")

    def test_budget_stop(self):
        self.assertTrue(should_stop_for_budget({"token_limit": 100, "token_used_estimate": 95, "stop_when_remaining_below": 10}))
        self.assertFalse(should_stop_for_budget({"token_limit": 100, "token_used_estimate": 80, "stop_when_remaining_below": 10}))

    def test_routing_prefers_mind_palace_for_wiki_lint(self):
        task = self.load_fixture("minimal-task.example.json")
        task["spec"]["required_capabilities"] = ["wiki_lint"]
        expert = self.load_fixture("mind-palace-expert.example.json")
        ranked = rank_experts(task, [expert])
        self.assertEqual(ranked[0]["expert_id"], "mind-palace")
        self.assertGreater(ranked[0]["score"], 0)

    def test_filesystem_store_saves_objects_and_events(self):
        tempdir = tempfile.mkdtemp()
        try:
            store = FilesystemStore(tempdir).init()
            task = self.load_fixture("minimal-task.example.json")
            path = store.save(task)
            self.assertTrue(path.exists())
            loaded = store.load("Task", task["metadata"]["id"])
            self.assertEqual(loaded["metadata"]["id"], task["metadata"]["id"])
            event_path = Path(tempdir) / "events" / f"{task['metadata']['id']}.jsonl"
            self.assertTrue(event_path.exists())
        finally:
            shutil.rmtree(tempdir)


if __name__ == "__main__":
    unittest.main()
