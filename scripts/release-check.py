#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    checks = [
        ["protocol", [sys.executable, str(ROOT / "scripts" / "adl.py"), "validate"]],
        ["tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]],
    ]
    results = []
    for name, command in checks:
        env = dict(os.environ)
        env["ADL_SKIP_RELEASE_CHECK_TEST"] = "1"
        proc = subprocess.run(command, cwd=str(ROOT), text=True, capture_output=True, env=env)
        results.append(
            {
                "name": name,
                "ok": proc.returncode == 0,
                "returncode": proc.returncode,
                "stdout_tail": _tail(proc.stdout),
                "stderr_tail": _tail(proc.stderr),
            }
        )
    ok = all(result["ok"] for result in results)
    print(json.dumps({"ok": ok, "checks": results}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


def _tail(text, limit=20):
    lines = [line for line in text.splitlines() if line.strip()]
    return lines[-limit:]


if __name__ == "__main__":
    raise SystemExit(main())
