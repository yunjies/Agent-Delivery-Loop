import json
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
        finally:
            shutil.rmtree(tempdir)


if __name__ == "__main__":
    unittest.main()
