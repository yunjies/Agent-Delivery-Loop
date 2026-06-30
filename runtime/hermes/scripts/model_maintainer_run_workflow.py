#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a Model Maintainer v2 workflow")
    parser.add_argument("--workflow", required=True)
    parser.add_argument("--trigger", required=True)
    parser.add_argument("--mode", default="production", choices=["shadow", "production"])
    parser.add_argument("--max-ticks", default="8")
    args = parser.parse_args()
    cmd = [
        "/opt/hermes/.venv/bin/python",
        "/opt/data/scripts/workflow_runtime.py",
        "run",
        "--workflow",
        args.workflow,
        "--trigger",
        args.trigger,
        "--mode",
        args.mode,
        "--max-ticks",
        str(args.max_ticks),
    ]
    completed = subprocess.run(cmd, cwd="/opt/data", text=True, capture_output=True, timeout=900)
    payload = {
        "ok": completed.returncode == 0,
        "workflow": args.workflow,
        "trigger": args.trigger,
        "mode": args.mode,
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "exit_code": completed.returncode,
    }
    try:
        payload["workflow_result"] = json.loads((completed.stdout or "").strip())
    except json.JSONDecodeError:
        payload["stdout_tail"] = (completed.stdout or "")[-2000:]
    if completed.stderr:
        payload["stderr_tail"] = completed.stderr[-2000:]
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
