import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime" / "hermes" / "scripts"))

from path_governance_check import check_paths


class PathGovernanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.config = Path(self.temp.name) / "path-governance.json"
        self.config.write_text(
            json.dumps(
                {
                    "version": 1,
                    "rules": [
                        {
                            "id": "framework",
                            "owner_profile": "framework-maintainer",
                            "allowed_profiles": ["framework-maintainer"],
                            "match": ["/opt/data/profiles/**", "/opt/data/workflows/specs/**"],
                            "decision": "block",
                        },
                        {
                            "id": "wiki",
                            "owner_profile": "mind-palace",
                            "allowed_profiles": ["mind-palace"],
                            "delegate_profile": "mind-palace",
                            "delegate_action": "delegate_task",
                            "match": ["/mnt/user/Docs/wiki/**"],
                            "decision": "block",
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_framework_actor_can_touch_framework_paths(self):
        payload = check_paths(
            "framework-maintainer",
            ["/opt/data/profiles/home-media/config.yaml", "/opt/data/workflows/specs/media.workflow.yaml"],
            config_path=self.config,
            check_mode="planned",
            session_id="session-test",
            reason="unit test",
        )
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["violations"], [])
        self.assertEqual(payload["check_mode"], "planned")
        self.assertEqual(payload["session_id"], "session-test")
        self.assertEqual(payload["reason"], "unit test")

    def test_other_actor_is_blocked_on_framework_path(self):
        payload = check_paths("home-media", ["/opt/data/workflows/specs/media.workflow.yaml"], config_path=self.config)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["violations"][0]["owner_profile"], "framework-maintainer")

    def test_wiki_owner_can_touch_wiki_path(self):
        payload = check_paths("mind-palace", ["/mnt/user/Docs/wiki/index.md"], config_path=self.config)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["violations"], [])

    def test_non_wiki_actor_is_blocked_on_wiki_path(self):
        payload = check_paths("framework-maintainer", ["/mnt/user/Docs/wiki/index.md"], config_path=self.config)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["violations"][0]["owner_profile"], "mind-palace")
        self.assertEqual(payload["violations"][0]["delegate_profile"], "mind-palace")
        self.assertEqual(payload["violations"][0]["delegate_action"], "delegate_task")

    def test_strict_unowned_path_fails(self):
        payload = check_paths("framework-maintainer", ["/tmp/unowned.txt"], config_path=self.config, strict_unowned=True)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["violations"][0]["message"], "unowned path")


if __name__ == "__main__":
    unittest.main()
