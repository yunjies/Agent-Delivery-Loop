import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime" / "hermes" / "scripts"))

from framework_operation_plan import create_plan


class Args:
    def __init__(self, **kwargs):
        self.operation = kwargs.get("operation", "workflow:update")
        self.title = kwargs.get("title", "Update workflow")
        self.intent = kwargs.get("intent", "Update a governed workflow.")
        self.actor_profile = kwargs.get("actor_profile", "framework-maintainer")
        self.target_profile = kwargs.get("target_profile")
        self.target_skill = kwargs.get("target_skill")
        self.target_workflow = kwargs.get("target_workflow", "media-wishlist")
        self.changed_path = kwargs.get("changed_path", [])
        self.state_root = kwargs["state_root"]
        self.session_id = kwargs.get("session_id", "session-test")
        self.strict_unowned = kwargs.get("strict_unowned", False)


class FrameworkOperationPlanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "config").mkdir(parents=True)
        (self.root / "config" / "path-governance.json").write_text(
            '{"version":1,"rules":[{"id":"framework","owner_profile":"framework-maintainer","allowed_profiles":["framework-maintainer"],"match":["/opt/data/workflows/specs/**","/opt/data/profiles/**","/opt/data/cron/**","/opt/data/config.yaml"],"decision":"block"}]}',
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_workflow_plan_derives_path_and_passes_governance(self):
        payload = create_plan(Args(state_root=str(self.root)))
        self.assertTrue(payload["ok"])
        self.assertIn("/opt/data/workflows/specs/media-wishlist.workflow.yaml", payload["changed_paths"])
        self.assertIn("workflow_smoke_ok", payload["activation"]["checks_required_before_active"])

    def test_non_framework_actor_fails_validation(self):
        payload = create_plan(Args(state_root=str(self.root), actor_profile="home-media"))
        self.assertFalse(payload["ok"])
        self.assertIn("framework operations must use actor_profile=framework-maintainer", payload["validation"]["errors"])

    def test_skill_plan_requires_profile_and_skill(self):
        payload = create_plan(Args(state_root=str(self.root), operation="skill:create", target_workflow=None))
        self.assertFalse(payload["ok"])
        self.assertIn("skill operations require --target-profile and --target-skill", payload["validation"]["errors"])


if __name__ == "__main__":
    unittest.main()
