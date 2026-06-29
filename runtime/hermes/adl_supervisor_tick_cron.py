#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone


def main() -> int:
    cmd = [
        "python3",
        "/opt/data/agent-delivery-loop/framework/runtime/hermes/adl_runtime.py",
        "supervisor-tick",
    ]
    completed = subprocess.run(cmd, text=True, capture_output=True, timeout=300)
    payload = {
        "ok": completed.returncode == 0,
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "exit_code": completed.returncode,
        "stdout_tail": (completed.stdout or "")[-2000:],
        "stderr_tail": (completed.stderr or "")[-2000:],
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
